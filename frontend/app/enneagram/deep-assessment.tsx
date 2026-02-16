/**
 * P1: Deep Enneagram Assessment Flow
 * ==================================
 * 
 * A 45-question, 15-20 minute assessment for more accurate Enneagram typing.
 * 
 * Features:
 * - Opt-in only (CTA from results screen)
 * - Resumable (persists session_id in AsyncStorage)
 * - Non-diagnostic tone
 * - Supports all 3 question types: forced_choice, likert, ranked
 * - Time-based progress indicator
 * - Auto-saves answers
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter, useLocalSearchParams } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { navigateToLenses } from '../../utils/navigation';
import {
  startDeepAssessment,
  getDeepAssessmentSession,
  submitDeepAssessmentAnswer,
  completeDeepAssessment,
  DeepAssessmentSession,
  DeepAssessmentQuestion,
  DeepAssessmentResponse,
  DeepAssessmentResult,
} from '../../services/api';

// Debug mode flag
const DEBUG_MIRROR = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

// AsyncStorage key for session persistence
const DEEP_SESSION_KEY = 'DEEP_ENNEAGRAM_SESSION_ID';

// Estimated time per question (in seconds)
const SECONDS_PER_QUESTION = 25;

// View states
type ViewState = 'loading' | 'intro' | 'questions' | 'computing' | 'error';

// ============================================
// QUESTION TYPE COMPONENTS
// ============================================

interface ForcedChoiceProps {
  question: DeepAssessmentQuestion;
  selectedValue: string | null;
  onSelect: (value: string) => void;
}

const ForcedChoiceQuestion: React.FC<ForcedChoiceProps> = ({
  question,
  selectedValue,
  onSelect,
}) => {
  return (
    <View style={styles.optionsContainer}>
      {question.options?.map((option) => (
        <TouchableOpacity
          key={option.id}
          style={[
            styles.optionCard,
            selectedValue === option.id && styles.optionCardSelected,
          ]}
          onPress={() => onSelect(option.id)}
          activeOpacity={0.7}
        >
          <View style={styles.optionHeader}>
            <View style={[
              styles.optionBadge,
              selectedValue === option.id && styles.optionBadgeSelected,
            ]}>
              <Text style={[
                styles.optionBadgeText,
                selectedValue === option.id && styles.optionBadgeTextSelected,
              ]}>
                {option.id}
              </Text>
            </View>
            {selectedValue === option.id && (
              <Ionicons name="checkmark-circle" size={22} color={Colors.text} />
            )}
          </View>
          <Text style={[
            styles.optionText,
            selectedValue === option.id && styles.optionTextSelected,
          ]}>
            {option.text}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};

interface LikertProps {
  question: DeepAssessmentQuestion;
  selectedValue: number | null;
  onSelect: (value: number) => void;
}

const LikertQuestion: React.FC<LikertProps> = ({
  question,
  selectedValue,
  onSelect,
}) => {
  const scale = question.scale || { min: 1, max: 5, labels: [] };
  const values = Array.from(
    { length: scale.max - scale.min + 1 },
    (_, i) => scale.min + i
  );
  
  const labels = scale.labels || ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'];
  
  return (
    <View style={styles.likertContainer}>
      <View style={styles.likertLabels}>
        <Text style={styles.likertLabelText}>{labels[0]}</Text>
        <Text style={styles.likertLabelText}>{labels[labels.length - 1]}</Text>
      </View>
      <View style={styles.likertScale}>
        {values.map((value) => (
          <TouchableOpacity
            key={value}
            style={[
              styles.likertButton,
              selectedValue === value && styles.likertButtonSelected,
            ]}
            onPress={() => onSelect(value)}
            activeOpacity={0.7}
          >
            <Text style={[
              styles.likertButtonText,
              selectedValue === value && styles.likertButtonTextSelected,
            ]}>
              {value}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      {selectedValue !== null && labels[selectedValue - 1] && (
        <Text style={styles.likertSelectedLabel}>
          {labels[selectedValue - 1]}
        </Text>
      )}
    </View>
  );
};

interface RankedProps {
  question: DeepAssessmentQuestion;
  selectedValue: string[] | null;
  onSelect: (value: string[]) => void;
}

const RankedQuestion: React.FC<RankedProps> = ({
  question,
  selectedValue,
  onSelect,
}) => {
  // Ensure ranking is always an array
  const ranking = Array.isArray(selectedValue) ? selectedValue : [];
  const options = question.options || [];
  
  const handleOptionPress = (optionId: string) => {
    const currentIndex = ranking.indexOf(optionId);
    
    if (currentIndex >= 0) {
      // Remove from ranking (deselect)
      const newRanking = ranking.filter((id) => id !== optionId);
      onSelect(newRanking);
    } else {
      // Add to ranking
      const newRanking = [...ranking, optionId];
      onSelect(newRanking);
    }
  };
  
  const getRankNumber = (optionId: string): number | null => {
    const index = ranking.indexOf(optionId);
    return index >= 0 ? index + 1 : null;
  };
  
  const isComplete = ranking.length === options.length;
  
  return (
    <View style={styles.rankedContainer}>
      <Text style={styles.rankedInstructions}>
        Tap options in order of preference (1 = most like me)
      </Text>
      {options.map((option) => {
        const rank = getRankNumber(option.id);
        const isSelected = rank !== null;
        
        return (
          <TouchableOpacity
            key={option.id}
            style={[
              styles.rankedOption,
              isSelected && styles.rankedOptionSelected,
            ]}
            onPress={() => handleOptionPress(option.id)}
            activeOpacity={0.7}
          >
            <View style={[
              styles.rankedBadge,
              isSelected && styles.rankedBadgeSelected,
            ]}>
              {isSelected ? (
                <Text style={styles.rankedBadgeTextSelected}>{rank}</Text>
              ) : (
                <Text style={styles.rankedBadgeText}>{option.id}</Text>
              )}
            </View>
            <Text style={[
              styles.rankedText,
              isSelected && styles.rankedTextSelected,
            ]}>
              {option.text}
            </Text>
          </TouchableOpacity>
        );
      })}
      {!isComplete && ranking.length > 0 && (
        <Text style={styles.rankedHint}>
          {options.length - ranking.length} more to rank
        </Text>
      )}
    </View>
  );
};

// ============================================
// PROGRESS INDICATOR
// ============================================

interface ProgressIndicatorProps {
  currentIndex: number;
  totalQuestions: number;
  currentSection?: string;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  currentIndex,
  totalQuestions,
  currentSection,
}) => {
  const questionsRemaining = totalQuestions - currentIndex;
  const minutesRemaining = Math.ceil((questionsRemaining * SECONDS_PER_QUESTION) / 60);
  
  const progressPercent = ((currentIndex) / totalQuestions) * 100;
  
  return (
    <View style={styles.progressContainer}>
      <View style={styles.progressBar}>
        <View style={[styles.progressFill, { width: `${progressPercent}%` }]} />
      </View>
      <View style={styles.progressInfo}>
        <Text style={styles.progressTime}>
          ~{minutesRemaining} min remaining
        </Text>
        {currentSection && (
          <Text style={styles.progressSection}>{currentSection}</Text>
        )}
      </View>
    </View>
  );
};

// ============================================
// MAIN COMPONENT
// ============================================

export default function DeepAssessmentScreen() {
  const router = useRouter();
  const user = useAppStore((state) => state.user);
  const params = useLocalSearchParams();
  
  // State
  const [viewState, setViewState] = useState<ViewState>('loading');
  const [session, setSession] = useState<DeepAssessmentSession | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentResponse, setCurrentResponse] = useState<any>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DeepAssessmentResult | null>(null);
  
  // Refs
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // ============================================
  // SESSION MANAGEMENT
  // ============================================
  
  // Initialize session
  useEffect(() => {
    initializeSession();
  }, [user?.id]);
  
  const initializeSession = async () => {
    if (!user?.id) {
      router.replace('/');
      return;
    }
    
    try {
      setViewState('loading');
      
      // Check for existing session in storage
      const storedSessionId = await AsyncStorage.getItem(DEEP_SESSION_KEY);
      
      if (storedSessionId) {
        // Try to resume existing session
        try {
          const existingSession = await getDeepAssessmentSession(storedSessionId);
          
          if (existingSession.status === 'in_progress') {
            setSession(existingSession);
            
            // Find first unanswered question
            const answeredIds = new Set(existingSession.responses.map(r => r.question_id));
            const firstUnanswered = existingSession.questions.findIndex(
              q => !answeredIds.has(q.id)
            );
            
            setCurrentQuestionIndex(firstUnanswered >= 0 ? firstUnanswered : 0);
            setViewState('questions');
            return;
          } else if (existingSession.status === 'completed' && existingSession.result) {
            // Already completed - navigate to results
            setResult(existingSession.result);
            await AsyncStorage.removeItem(DEEP_SESSION_KEY);
            router.replace({
              pathname: '/enneagram/results',
              params: { deepResult: 'true' }
            });
            return;
          }
        } catch (e) {
          // Session not found or error - will create new one
          await AsyncStorage.removeItem(DEEP_SESSION_KEY);
        }
      }
      
      // No valid session - show intro
      setViewState('intro');
      
    } catch (err) {
      console.error('[DeepAssessment] Init error:', err);
      setError('Failed to initialize assessment');
      setViewState('error');
    }
  };
  
  const startNewSession = async () => {
    if (!user?.id) return;
    
    try {
      setViewState('loading');
      
      const newSession = await startDeepAssessment(user.id);
      
      // Store session ID
      await AsyncStorage.setItem(DEEP_SESSION_KEY, newSession.session_id);
      
      setSession(newSession);
      setCurrentQuestionIndex(0);
      setViewState('questions');
      
    } catch (err) {
      console.error('[DeepAssessment] Start error:', err);
      setError('Failed to start assessment. Please try again.');
      setViewState('error');
    }
  };
  
  // ============================================
  // ANSWER HANDLING
  // ============================================
  
  const currentQuestion = session?.questions?.[currentQuestionIndex];
  
  // Get existing response for current question
  const existingResponse = session?.responses?.find(
    r => r.question_id === currentQuestion?.id
  );
  
  // Set initial response when question changes
  useEffect(() => {
    if (existingResponse) {
      // Ensure ranked questions get an array
      const value = existingResponse.response.value;
      if (currentQuestion?.type === 'ranked' && !Array.isArray(value)) {
        setCurrentResponse([]);
      } else {
        setCurrentResponse(value);
      }
    } else {
      // Initialize with appropriate default for question type
      if (currentQuestion?.type === 'ranked') {
        setCurrentResponse([]);
      } else {
        setCurrentResponse(null);
      }
    }
    setSaveStatus('idle');
  }, [currentQuestionIndex, existingResponse?.response?.value, currentQuestion?.type]);
  
  const handleResponseChange = (value: any) => {
    setCurrentResponse(value);
    setSaveStatus('idle');
    
    // Auto-save after a delay
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    
    saveTimeoutRef.current = setTimeout(() => {
      saveCurrentAnswer(value);
    }, 500);
  };
  
  const saveCurrentAnswer = async (value: any) => {
    if (!session || !currentQuestion || value === null || value === undefined) return;
    
    // Don't save incomplete ranked responses
    if (currentQuestion.type === 'ranked') {
      const requiredCount = currentQuestion.options?.length || 0;
      if (!Array.isArray(value) || value.length < requiredCount) return;
    }
    
    try {
      setSaveStatus('saving');
      
      const response: DeepAssessmentResponse = {
        type: currentQuestion.type,
        value: value,
      };
      
      await submitDeepAssessmentAnswer(session.session_id, currentQuestion.id, response);
      
      // Update local session state
      setSession(prev => {
        if (!prev) return prev;
        
        const newResponses = [...prev.responses];
        const existingIdx = newResponses.findIndex(r => r.question_id === currentQuestion.id);
        
        const responseRecord = {
          question_id: currentQuestion.id,
          response: response,
          answered_at: new Date().toISOString(),
        };
        
        if (existingIdx >= 0) {
          newResponses[existingIdx] = responseRecord;
        } else {
          newResponses.push(responseRecord);
        }
        
        return { ...prev, responses: newResponses };
      });
      
      setSaveStatus('saved');
      
    } catch (err) {
      console.error('[DeepAssessment] Save error:', err);
      setSaveStatus('error');
    }
  };
  
  const isCurrentAnswerValid = (): boolean => {
    if (!currentQuestion || currentResponse === null || currentResponse === undefined) {
      return false;
    }
    
    if (currentQuestion.type === 'ranked') {
      const requiredCount = currentQuestion.options?.length || 0;
      return Array.isArray(currentResponse) && currentResponse.length === requiredCount;
    }
    
    return true;
  };
  
  // ============================================
  // NAVIGATION
  // ============================================
  
  const goToNext = async () => {
    if (!session || !currentQuestion) {
      console.error('[DeepAssessment] goToNext: session or currentQuestion is null');
      return;
    }
    
    console.log(`[DeepAssessment] goToNext called: index=${currentQuestionIndex}, total=${session.questions.length}`);
    
    try {
      // Cancel any pending auto-save
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
        saveTimeoutRef.current = null;
      }
      
      // Save current answer first (if valid and not already saved)
      if (isCurrentAnswerValid() && saveStatus !== 'saved') {
        console.log('[DeepAssessment] Saving answer before navigation...');
        await saveCurrentAnswer(currentResponse);
      }
      
      const isLastQuestion = currentQuestionIndex === session.questions.length - 1;
      console.log(`[DeepAssessment] isLastQuestion=${isLastQuestion}`);
      
      if (isLastQuestion) {
        // Complete assessment
        console.log('[DeepAssessment] Calling handleComplete...');
        await handleComplete();
      } else {
        setCurrentQuestionIndex(prev => prev + 1);
      }
    } catch (err: any) {
      console.error('[DeepAssessment] Navigation error:', err);
      // Don't block navigation on save errors - allow user to proceed
      // The answer can be re-saved when they navigate back
      const isLastQuestion = currentQuestionIndex === session.questions.length - 1;
      if (!isLastQuestion) {
        setCurrentQuestionIndex(prev => prev + 1);
      } else {
        // For last question, show error
        Alert.alert(
          'Save Error',
          'There was an issue saving your last answer. Please try again.',
          [{ text: 'OK' }]
        );
      }
    }
  };
  
  const goToPrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };
  
  const handleComplete = async () => {
    if (!session) return;
    
    try {
      setViewState('computing');
      
      const completion = await completeDeepAssessment(session.session_id);
      
      // Clear stored session
      await AsyncStorage.removeItem(DEEP_SESSION_KEY);
      
      setResult(completion.result);
      
      // Navigate to results with deep result flag
      router.replace({
        pathname: '/enneagram/results',
        params: { 
          deepResult: 'true',
          fromDeepAssessment: 'true'
        }
      });
      
    } catch (err: any) {
      console.error('[DeepAssessment] Complete error:', err);
      
      if (err?.response?.data?.detail?.includes('All questions must be answered')) {
        // Find missing questions
        const answeredIds = new Set(session.responses.map(r => r.question_id));
        const firstMissing = session.questions.findIndex(q => !answeredIds.has(q.id));
        
        if (firstMissing >= 0) {
          setCurrentQuestionIndex(firstMissing);
          setViewState('questions');
          Alert.alert(
            'Questions Missing',
            'Please answer all questions before completing the assessment.',
            [{ text: 'OK' }]
          );
        }
      } else {
        setError('Failed to complete assessment. Please try again.');
        setViewState('error');
      }
    }
  };
  
  const handleExit = () => {
    Alert.alert(
      'Exit Assessment',
      'Your progress will be saved. You can resume anytime.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Exit',
          onPress: () => navigateToLenses(router)
        }
      ]
    );
  };
  
  // ============================================
  // SECTION INFO
  // ============================================
  
  const getCurrentSection = (): string | undefined => {
    if (!currentQuestion || !session?.sections) return undefined;
    
    const section = session.sections.find(s => s.id === currentQuestion.section);
    return section?.title;
  };
  
  // ============================================
  // RENDER FUNCTIONS
  // ============================================
  
  const renderLoading = () => (
    <View style={styles.centerContainer}>
      <ActivityIndicator size="large" color={Colors.text} />
      <Text style={styles.loadingText}>Loading assessment...</Text>
    </View>
  );
  
  const renderIntro = () => (
    <ScrollView contentContainerStyle={styles.introContainer}>
      <View style={styles.introContent}>
        <Ionicons name="layers-outline" size={48} color={Colors.text} style={styles.introIcon} />
        
        <Text style={styles.introTitle}>Deep Assessment</Text>
        
        <Text style={styles.introSubtitle}>
          A more thorough exploration of your patterns
        </Text>
        
        <View style={styles.introInfoCard}>
          <View style={styles.introInfoRow}>
            <Ionicons name="time-outline" size={20} color={Colors.textSecondary} />
            <Text style={styles.introInfoText}>About 15-20 minutes</Text>
          </View>
          <View style={styles.introInfoRow}>
            <Ionicons name="help-circle-outline" size={20} color={Colors.textSecondary} />
            <Text style={styles.introInfoText}>45 questions</Text>
          </View>
          <View style={styles.introInfoRow}>
            <Ionicons name="save-outline" size={20} color={Colors.textSecondary} />
            <Text style={styles.introInfoText}>Auto-saves, resume anytime</Text>
          </View>
        </View>
        
        <Text style={styles.introDescription}>
          This is not a test with right or wrong answers. There's no passing or failing.
          {'\n\n'}
          Simply reflect on each question and choose what feels most true for you — 
          not what you wish were true, or what you think you should say.
          {'\n\n'}
          Your responses help paint a clearer picture of your patterns. 
          The goal is insight, not labeling.
        </Text>
        
        <TouchableOpacity
          style={styles.startButton}
          onPress={startNewSession}
          activeOpacity={0.8}
        >
          <Text style={styles.startButtonText}>Begin</Text>
          <Ionicons name="arrow-forward" size={20} color={Colors.background} />
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.backLink}
          onPress={() => router.replace('/(tabs)/lenses')}
        >
          <Text style={styles.backLinkText}>Maybe later</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
  
  const renderQuestions = () => {
    if (!session || !currentQuestion) return null;
    
    const isLastQuestion = currentQuestionIndex === session.questions.length - 1;
    const canGoNext = isCurrentAnswerValid();
    
    return (
      <>
        {/* Progress */}
        <ProgressIndicator
          currentIndex={currentQuestionIndex}
          totalQuestions={session.questions.length}
          currentSection={getCurrentSection()}
        />
        
        {/* Question */}
        <ScrollView 
          style={styles.questionScroll}
          contentContainerStyle={styles.questionContent}
          showsVerticalScrollIndicator={false}
        >
          <Text style={styles.questionNumber}>
            Question {currentQuestionIndex + 1} of {session.questions.length}
          </Text>
          
          <Text style={styles.questionStem}>
            {currentQuestion.stem}
          </Text>
          
          {/* Question Type Renderer */}
          {currentQuestion.type === 'forced_choice' && (
            <ForcedChoiceQuestion
              question={currentQuestion}
              selectedValue={currentResponse}
              onSelect={handleResponseChange}
            />
          )}
          
          {currentQuestion.type === 'likert' && (
            <LikertQuestion
              question={currentQuestion}
              selectedValue={currentResponse}
              onSelect={handleResponseChange}
            />
          )}
          
          {currentQuestion.type === 'ranked' && (
            <RankedQuestion
              question={currentQuestion}
              selectedValue={currentResponse}
              onSelect={handleResponseChange}
            />
          )}
          
          {/* Save Status */}
          {saveStatus !== 'idle' && (
            <View style={styles.saveStatus}>
              {saveStatus === 'saving' && (
                <>
                  <ActivityIndicator size="small" color={Colors.textTertiary} />
                  <Text style={styles.saveStatusText}>Saving...</Text>
                </>
              )}
              {saveStatus === 'saved' && (
                <>
                  <Ionicons name="checkmark-circle" size={16} color="#4CAF50" />
                  <Text style={[styles.saveStatusText, { color: '#4CAF50' }]}>Saved</Text>
                </>
              )}
              {saveStatus === 'error' && (
                <>
                  <Ionicons name="alert-circle" size={16} color="#FF6B6B" />
                  <Text style={[styles.saveStatusText, { color: '#FF6B6B' }]}>
                    Couldn't save. Try again.
                  </Text>
                </>
              )}
            </View>
          )}
          
          {/* DEBUG Panel */}
          {DEBUG_MIRROR && (
            <View style={styles.debugPanel}>
              <Text style={styles.debugTitle}>DEBUG</Text>
              <Text style={styles.debugText}>session: ...{session.session_id.slice(-8)}</Text>
              <Text style={styles.debugText}>index: {currentQuestionIndex + 1}/{session.questions.length}</Text>
              <Text style={styles.debugText}>answered: {session.responses.length}</Text>
              <Text style={styles.debugText}>save: {saveStatus}</Text>
            </View>
          )}
        </ScrollView>
        
        {/* Navigation */}
        <View style={styles.navContainer}>
          <TouchableOpacity
            style={[styles.navButton, styles.navButtonSecondary]}
            onPress={goToPrevious}
            disabled={currentQuestionIndex === 0}
          >
            <Ionicons 
              name="chevron-back" 
              size={20} 
              color={currentQuestionIndex === 0 ? Colors.textTertiary : Colors.text} 
            />
            <Text style={[
              styles.navButtonText,
              currentQuestionIndex === 0 && styles.navButtonTextDisabled
            ]}>
              Back
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[
              styles.navButton,
              styles.navButtonPrimary,
              !canGoNext && styles.navButtonDisabled,
            ]}
            onPress={goToNext}
            disabled={!canGoNext}
          >
            <Text style={[
              styles.navButtonTextPrimary,
              !canGoNext && styles.navButtonTextDisabled,
            ]}>
              {isLastQuestion ? 'Complete' : 'Next'}
            </Text>
            <Ionicons 
              name={isLastQuestion ? 'checkmark' : 'chevron-forward'} 
              size={20} 
              color={canGoNext ? Colors.background : Colors.textTertiary} 
            />
          </TouchableOpacity>
        </View>
      </>
    );
  };
  
  const renderComputing = () => (
    <View style={styles.centerContainer}>
      <ActivityIndicator size="large" color={Colors.text} />
      <Text style={styles.computingTitle}>Processing your responses...</Text>
      <Text style={styles.computingSubtitle}>
        This will take just a moment.
      </Text>
    </View>
  );
  
  const renderError = () => (
    <View style={styles.centerContainer}>
      <Ionicons name="alert-circle-outline" size={48} color="#FF6B6B" />
      <Text style={styles.errorTitle}>Something went wrong</Text>
      <Text style={styles.errorText}>{error}</Text>
      <TouchableOpacity
        style={styles.retryButton}
        onPress={initializeSession}
      >
        <Text style={styles.retryButtonText}>Try Again</Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={styles.backLink}
        onPress={() => router.replace('/(tabs)/lenses')}
      >
        <Text style={styles.backLinkText}>Go back</Text>
      </TouchableOpacity>
    </View>
  );
  
  // ============================================
  // MAIN RENDER
  // ============================================
  
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleExit} style={styles.headerButton}>
          <Ionicons name="close" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>
          {viewState === 'questions' ? 'Deep Assessment' : ''}
        </Text>
        <View style={styles.headerSpacer} />
      </View>
      
      {/* Content */}
      <View style={styles.content}>
        {viewState === 'loading' && renderLoading()}
        {viewState === 'intro' && renderIntro()}
        {viewState === 'questions' && renderQuestions()}
        {viewState === 'computing' && renderComputing()}
        {viewState === 'error' && renderError()}
      </View>
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
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.text,
  },
  headerSpacer: {
    width: 32,
  },
  
  content: {
    flex: 1,
  },
  
  // Center Container (loading, computing, error)
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: Colors.textSecondary,
  },
  
  // Intro Screen
  introContainer: {
    flexGrow: 1,
    padding: 24,
  },
  introContent: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  introIcon: {
    marginBottom: 16,
  },
  introTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 8,
  },
  introSubtitle: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginBottom: 24,
  },
  introInfoCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    width: '100%',
    marginBottom: 24,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  introInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  introInfoText: {
    fontSize: 15,
    color: Colors.textSecondary,
  },
  introDescription: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 32,
  },
  startButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.text,
    paddingVertical: 16,
    paddingHorizontal: 48,
    borderRadius: 12,
    marginBottom: 16,
  },
  startButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.background,
  },
  backLink: {
    padding: 8,
  },
  backLinkText: {
    fontSize: 15,
    color: Colors.textTertiary,
  },
  
  // Progress
  progressContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: Colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  progressBar: {
    height: 4,
    backgroundColor: Colors.border,
    borderRadius: 2,
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: Colors.text,
    borderRadius: 2,
  },
  progressInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  progressTime: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
  progressSection: {
    fontSize: 13,
    color: Colors.textTertiary,
    fontStyle: 'italic',
  },
  
  // Question
  questionScroll: {
    flex: 1,
  },
  questionContent: {
    padding: 20,
    paddingBottom: 40,
  },
  questionNumber: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.textTertiary,
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  questionStem: {
    fontSize: 20,
    fontWeight: '500',
    color: Colors.text,
    lineHeight: 28,
    marginBottom: 24,
  },
  
  // Forced Choice Options
  optionsContainer: {
    gap: 12,
  },
  optionCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: Colors.border,
  },
  optionCardSelected: {
    borderColor: Colors.text,
    backgroundColor: Colors.background,
  },
  optionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  optionBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  optionBadgeSelected: {
    backgroundColor: Colors.text,
  },
  optionBadgeText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  optionBadgeTextSelected: {
    color: Colors.background,
  },
  optionText: {
    fontSize: 16,
    lineHeight: 22,
    color: Colors.text,
  },
  optionTextSelected: {
    fontWeight: '500',
  },
  
  // Likert
  likertContainer: {
    alignItems: 'center',
  },
  likertLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    marginBottom: 12,
  },
  likertLabelText: {
    fontSize: 12,
    color: Colors.textTertiary,
    maxWidth: '40%',
  },
  likertScale: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  likertButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: Colors.border,
  },
  likertButtonSelected: {
    backgroundColor: Colors.text,
    borderColor: Colors.text,
  },
  likertButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
  },
  likertButtonTextSelected: {
    color: Colors.background,
  },
  likertSelectedLabel: {
    fontSize: 14,
    color: Colors.text,
    fontWeight: '500',
  },
  
  // Ranked
  rankedContainer: {
    gap: 12,
  },
  rankedInstructions: {
    fontSize: 13,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    marginBottom: 8,
  },
  rankedOption: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 14,
    gap: 12,
    borderWidth: 2,
    borderColor: Colors.border,
  },
  rankedOptionSelected: {
    borderColor: Colors.text,
  },
  rankedBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rankedBadgeSelected: {
    backgroundColor: Colors.text,
  },
  rankedBadgeText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  rankedBadgeTextSelected: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.background,
  },
  rankedText: {
    flex: 1,
    fontSize: 15,
    lineHeight: 21,
    color: Colors.text,
  },
  rankedTextSelected: {
    fontWeight: '500',
  },
  rankedHint: {
    fontSize: 13,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginTop: 8,
  },
  
  // Save Status
  saveStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 16,
  },
  saveStatusText: {
    fontSize: 13,
    color: Colors.textTertiary,
  },
  
  // Navigation
  navContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    backgroundColor: Colors.background,
  },
  navButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 10,
  },
  navButtonSecondary: {
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  navButtonPrimary: {
    backgroundColor: Colors.text,
  },
  navButtonDisabled: {
    backgroundColor: Colors.border,
  },
  navButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.text,
  },
  navButtonTextPrimary: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.background,
  },
  navButtonTextDisabled: {
    color: Colors.textTertiary,
  },
  
  // Computing
  computingTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginTop: 24,
    marginBottom: 8,
  },
  computingSubtitle: {
    fontSize: 15,
    color: Colors.textSecondary,
  },
  
  // Error
  errorTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
  },
  retryButton: {
    backgroundColor: Colors.text,
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 10,
    marginBottom: 16,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.background,
  },
  
  // Debug Panel
  debugPanel: {
    marginTop: 24,
    padding: 12,
    backgroundColor: '#1a1a2e',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FF6B6B',
    borderStyle: 'dashed',
  },
  debugTitle: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FF6B6B',
    marginBottom: 8,
    letterSpacing: 1,
  },
  debugText: {
    fontSize: 11,
    color: '#aaaacc',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    lineHeight: 16,
  },
});
