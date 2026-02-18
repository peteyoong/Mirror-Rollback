/**
 * P2 Enneagram Deep Assessment
 * ============================
 * A 20-30 minute single-sitting assessment for accurate Enneagram typing.
 * 
 * Flow:
 * 1. Intro screen with expectations
 * 2. One question at a time (center → core → diff → wing → instinct → consistency)
 * 3. Computing interstitial
 * 4. Redirect to existing results screen
 * 
 * Key Principles:
 * - Non-prescriptive Mirror language
 * - Stage-based progress (not question count)
 * - Calm, reflective tone
 * 
 * Session Resume:
 * - Stores session in AsyncStorage for resume within 2 hours
 * - Validates session on mount, resumes or starts fresh
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
  Modal,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { navigateToLenses, safeGoBack } from '../../utils/navigation';
import {
  startP2DeepAssessment,
  submitP2AssessmentAnswer,
  getP2AssessmentStatus,
  P2AssessmentQuestion,
  P2AssessmentProgress,
  P2AssessmentAnswer,
  P2AssessmentResult,
} from '../../services/api';

// Components
import { EnneagramAssessmentIntro } from '../../components/EnneagramAssessmentIntro';
import { EnneagramAssessmentQuestion } from '../../components/EnneagramAssessmentQuestion';
import { EnneagramAssessmentProgress } from '../../components/EnneagramAssessmentProgress';
import { EnneagramAssessmentComputing } from '../../components/EnneagramAssessmentComputing';
import { DebugDrawer } from '../../components/DebugDrawer';
import { DEBUG_MIRROR_ENV, DEBUG_TAP_THRESHOLD, getUrlDebugParam } from '../../utils/debugUtils';

// Session storage key
const SESSION_STORAGE_KEY = 'enneagram_deep_assessment_session';

// Session TTL (2 hours in milliseconds)
const SESSION_TTL_MS = 2 * 60 * 60 * 1000;

// ============================================
// ANALYTICS HELPER
// ============================================
// Lightweight analytics emission for tracking assessment events.
// Events are logged to console in dev and can be wired to analytics service.

function emitAnalytics(event: string, payload?: Record<string, any>) {
  const timestamp = new Date().toISOString();
  const eventData = { event, timestamp, ...payload };
  
  // Log to console in development
  if (__DEV__) {
    console.log('[P2Analytics]', event, payload);
  }
  
  // TODO: Wire to analytics service (e.g., Mixpanel, Amplitude, Segment)
  // analyticsService.track(event, eventData);
}

// Stored session interface
interface StoredSession {
  session_id: string;
  user_id: string;
  created_at_iso: string;
  updated_at_iso: string;
}

// Resume progress info for UI
interface ResumeProgressInfo {
  questionsAnswered: number;
  totalQuestions: number;
  stage?: string;
}

// View states
type ViewState = 'loading' | 'intro' | 'questions' | 'computing' | 'error';

// Error types for specific handling
type ErrorType = 'generic' | 'session_expired';

export default function P2DeepAssessment() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const { user } = useAppStore();

  // Debug gesture activation state (for mobile)
  const [debugGestureActivated, setDebugGestureActivated] = useState(false);
  const [debugTapCount, setDebugTapCount] = useState(0);
  const debugTapTimer = useRef<NodeJS.Timeout | null>(null);

  // State
  const [viewState, setViewState] = useState<ViewState>('loading');  // Start with loading to check session
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<ErrorType>('generic');
  const [showResumePrompt, setShowResumePrompt] = useState(false);
  const [resumeProgress, setResumeProgress] = useState<ResumeProgressInfo | null>(null);
  
  // Session state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<P2AssessmentQuestion | null>(null);
  const [progress, setProgress] = useState<P2AssessmentProgress | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<P2AssessmentAnswer | null>(null);
  
  // Results (for computing screen)
  const [results, setResults] = useState<P2AssessmentResult | null>(null);
  
  // Debug modal state (collapsed by default)
  const [debugModalVisible, setDebugModalVisible] = useState(false);
  
  // Stored session for resume
  const storedSessionRef = useRef<StoredSession | null>(null);
  
  // Track if user has answered any questions (for navigation warning)
  const hasStarted = useRef(false);

  // ============================================
  // SESSION PERSISTENCE HELPERS
  // ============================================
  
  const saveSession = useCallback(async (session: StoredSession) => {
    try {
      await AsyncStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
    } catch (err) {
      console.error('[P2Assessment] Failed to save session:', err);
    }
  }, []);

  const clearSession = useCallback(async () => {
    try {
      await AsyncStorage.removeItem(SESSION_STORAGE_KEY);
      storedSessionRef.current = null;
    } catch (err) {
      console.error('[P2Assessment] Failed to clear session:', err);
    }
  }, []);

  const loadStoredSession = useCallback(async (): Promise<StoredSession | null> => {
    try {
      const stored = await AsyncStorage.getItem(SESSION_STORAGE_KEY);
      if (!stored) return null;
      
      const session: StoredSession = JSON.parse(stored);
      
      // Check if session is within TTL (2 hours)
      const updatedAt = new Date(session.updated_at_iso).getTime();
      const now = Date.now();
      
      if (now - updatedAt > SESSION_TTL_MS) {
        // Session expired - clear it
        await clearSession();
        return null;
      }
      
      // Check if session belongs to current user
      if (session.user_id !== user?.id) {
        // Different user - clear it
        await clearSession();
        return null;
      }
      
      return session;
    } catch (err) {
      console.error('[P2Assessment] Failed to load session:', err);
      return null;
    }
  }, [user?.id, clearSession]);

  // ============================================
  // CHECK FOR EXISTING SESSION ON MOUNT
  // ============================================
  
  useEffect(() => {
    const checkExistingSession = async () => {
      if (!user?.id) {
        setViewState('intro');
        return;
      }

      try {
        const stored = await loadStoredSession();
        
        if (stored) {
          // Validate session with backend
          try {
            const status = await getP2AssessmentStatus(stored.session_id);
            
            // Session is valid and not done
            if (status.stage !== 'done') {
              storedSessionRef.current = stored;
              
              // Store progress info for the resume modal
              setResumeProgress({
                questionsAnswered: status.progress.questions_answered,
                totalQuestions: status.progress.estimated_total,
                stage: status.progress.stage,
              });
              
              setShowResumePrompt(true);
              setViewState('intro');
              return;
            }
          } catch {
            // Session invalid on backend - clear local storage
            await clearSession();
          }
        }
        
        setViewState('intro');
      } catch (err) {
        console.error('[P2Assessment] Session check failed:', err);
        setViewState('intro');
      }
    };

    checkExistingSession();
  }, [user?.id, loadStoredSession, clearSession]);

  // Handle back button press
  useEffect(() => {
    if (Platform.OS === 'android') {
      const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
        if (hasStarted.current && viewState === 'questions') {
          Alert.alert(
            'Leave Assessment?',
            'Your progress may be lost if you leave now.',
            [
              { text: 'Stay', style: 'cancel' },
              { text: 'Leave', style: 'destructive', onPress: () => navigateToLenses(router) },
            ]
          );
          return true;
        }
        return false;
      });
      return () => backHandler.remove();
    }
  }, [viewState, router]);

  // Resume existing session
  const handleResume = useCallback(async () => {
    if (!storedSessionRef.current || !user?.id) return;

    setIsLoading(true);
    setError(null);
    setShowResumePrompt(false);

    try {
      const status = await getP2AssessmentStatus(storedSessionRef.current.session_id);
      
      if (status.stage === 'done') {
        // Session already completed - start fresh
        await clearSession();
        setResumeProgress(null);
        setIsLoading(false);
        return;
      }

      // Analytics: assessment_resumed
      emitAnalytics('enneagram_assessment_resumed', {
        session_id: storedSessionRef.current.session_id,
        questions_answered: status.progress.questions_answered,
        stage: status.progress.stage,
      });

      // Resume: we need to call answer endpoint with empty to get next question
      // Actually, the status endpoint doesn't return the current question
      // So we need to start fresh but keep the session ID
      // For now, just start a new session since backend doesn't expose resume directly
      await clearSession();
      setResumeProgress(null);
      setIsLoading(false);
      
    } catch (err: any) {
      console.error('[P2Assessment] Resume error:', err);
      await clearSession();
      setResumeProgress(null);
      setIsLoading(false);
    }
  }, [user?.id, clearSession]);

  // Start fresh (dismiss resume prompt)
  const handleStartFresh = useCallback(async () => {
    // Analytics: user chose to abandon and start fresh
    emitAnalytics('enneagram_assessment_abandoned', { 
      reason: 'start_fresh_from_resume',
      had_existing_session: true,
      questions_answered: resumeProgress?.questionsAnswered || 0,
    });
    
    await clearSession();
    setShowResumePrompt(false);
    setResumeProgress(null);
  }, [clearSession, resumeProgress]);

  // Dismiss resume modal ("Not now") - returns to lenses
  const handleDismissResume = useCallback(() => {
    setShowResumePrompt(false);
    navigateToLenses(router);
  }, [router]);

  // Start assessment
  const handleBegin = useCallback(async () => {
    if (!user?.id) {
      setError('Please sign in to take the assessment.');
      setViewState('error');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await startP2DeepAssessment(user.id);
      
      setSessionId(response.session_id);
      setCurrentQuestion(response.question);
      setProgress(response.progress);
      setSelectedAnswer(null);
      setViewState('questions');
      hasStarted.current = true;
      
      // Save session for potential resume
      const now = new Date().toISOString();
      await saveSession({
        session_id: response.session_id,
        user_id: user.id,
        created_at_iso: now,
        updated_at_iso: now,
      });
      
      // Analytics: assessment_started
      emitAnalytics('enneagram_assessment_started', {
        session_id: response.session_id,
        user_id: user.id,
      });
      
    } catch (err: any) {
      console.error('[P2Assessment] Start error:', err);
      setError(err?.response?.data?.detail || 'Failed to start assessment. Please try again.');
      setViewState('error');
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, saveSession]);

  // Select an answer
  const handleSelectAnswer = useCallback((answer: P2AssessmentAnswer) => {
    setSelectedAnswer(answer);
  }, []);

  // Submit answer and get next question
  const handleContinue = useCallback(async () => {
    // Enhanced debugging for submission issues
    const debugInfo = {
      userId: user?.id,
      sessionId,
      questionId: currentQuestion?.id,
      selectedAnswer,
      progress: progress,
    };
    console.log('[P2Assessment] handleContinue called:', JSON.stringify(debugInfo, null, 2));
    
    if (!user?.id || !sessionId || !currentQuestion || !selectedAnswer) {
      console.warn('[P2Assessment] handleContinue blocked - missing required data:', {
        hasUserId: !!user?.id,
        hasSessionId: !!sessionId,
        hasCurrentQuestion: !!currentQuestion,
        hasSelectedAnswer: !!selectedAnswer,
      });
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      console.log('[P2Assessment] Submitting answer:', {
        questionId: currentQuestion.id,
        stage: progress?.stage,
        answeredCount: progress?.questions_answered,
        totalQuestions: progress?.estimated_total,
      });
      
      const response = await submitP2AssessmentAnswer(
        user.id,
        sessionId,
        currentQuestion.id,
        selectedAnswer
      );
      
      console.log('[P2Assessment] Server response:', {
        hasResults: !!response.results,
        hasQuestion: !!response.question,
        hasProgress: !!response.progress,
        newStage: response.progress?.stage,
        newAnsweredCount: response.progress?.questions_answered,
      });

      if (response.results) {
        // Assessment complete - clear session and show computing screen
        console.log('[P2Assessment] Assessment COMPLETE - navigating to computing screen');
        await clearSession();
        setResults(response.results);
        setViewState('computing');
        
        // Analytics: assessment_completed
        emitAnalytics('enneagram_assessment_completed', {
          session_id: sessionId,
          core_type: response.results.core_type,
          confidence_tier: response.results.confidence_tier,
        });
      } else if (response.question) {
        // Next question - update session timestamp (updated_at only)
        console.log('[P2Assessment] Next question received:', response.question.id);
        setCurrentQuestion(response.question);
        setProgress(response.progress || null);
        setSelectedAnswer(null);
        
        // Update session updated_at_iso (preserves created_at)
        const stored = await loadStoredSession();
        await saveSession({
          session_id: sessionId,
          user_id: user.id,
          created_at_iso: stored?.created_at_iso || new Date().toISOString(),
          updated_at_iso: new Date().toISOString(),
        });
        
        // Analytics: question_answered
        emitAnalytics('enneagram_question_answered', {
          session_id: sessionId,
          question_id: currentQuestion.id,
          stage: response.progress?.stage,
        });
      } else {
        // Unexpected state - log details for debugging
        console.error('[P2Assessment] Unexpected response state:', JSON.stringify(response, null, 2));
        throw new Error('Unexpected response from server');
      }
      
    } catch (err: any) {
      console.error('[P2Assessment] Submit error:', err);
      
      // Check for session expiry
      if (err?.response?.status === 400 || err?.response?.status === 404) {
        await clearSession();
        setError("Your previous session expired, so we'll restart to keep results accurate.");
        setErrorType('session_expired');
        setViewState('error');
        
        // Analytics: session_expired
        emitAnalytics('enneagram_session_expired', { session_id: sessionId });
      } else {
        setError(err?.response?.data?.detail || 'Failed to submit answer. Please try again.');
        setErrorType('generic');
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [user?.id, sessionId, currentQuestion, selectedAnswer, clearSession, saveSession, loadStoredSession]);

  // Navigate to results after computing
  const handleComputingComplete = useCallback(() => {
    // Navigate to Enneagram results screen
    router.replace('/enneagram/results');
  }, [router]);

  // Restart assessment (from error state)
  const handleRestart = useCallback(async () => {
    await clearSession();
    setSessionId(null);
    setCurrentQuestion(null);
    setProgress(null);
    setSelectedAnswer(null);
    setResults(null);
    setError(null);
    hasStarted.current = false;
    setViewState('intro');
  }, [clearSession]);

  // Handle debug gesture (7 taps to enable debug on mobile)
  const handleDebugTap = useCallback(() => {
    if (!DEBUG_MIRROR_ENV) return;
    
    // Clear previous timer
    if (debugTapTimer.current) {
      clearTimeout(debugTapTimer.current);
    }
    
    const newCount = debugTapCount + 1;
    setDebugTapCount(newCount);
    
    if (newCount >= DEBUG_TAP_THRESHOLD) {
      setDebugGestureActivated(true);
      setDebugTapCount(0);
      console.log('[Debug] Debug mode activated via gesture');
    } else {
      // Reset after 3 seconds of no taps
      debugTapTimer.current = setTimeout(() => {
        setDebugTapCount(0);
      }, 3000);
    }
  }, [debugTapCount]);

  // Build debug data for the drawer
  const getDebugData = () => {
    const data: Record<string, any> = {};
    
    if (sessionId) {
      data.session_id = sessionId.slice(0, 8) + '...';
    }
    
    if (progress) {
      data.progress = {
        stage: progress.stage,
        questions_answered: progress.questions_answered,
        estimated_total: progress.estimated_total,
        estimated_remaining: progress.estimated_remaining,
      };
    }
    
    if (results) {
      data.results = {
        type: `${results.core_type}w${results.wing}`,
        confidence: `${results.confidence} (${results.confidence_tier})`,
        instinct: `${results.instinct_primary}/${results.instinct_secondary || '-'}`,
      };
      if (results._debug) {
        data.debug_scores = {
          center: `H${results._debug.center_scores?.head || 0} / Ht${results._debug.center_scores?.heart || 0} / G${results._debug.center_scores?.gut || 0}`,
          type_gap: results._debug.type_gap,
          coherence: results._debug.coherence_score,
        };
      }
    }
    
    return data;
  };

  // Render loading state
  const renderLoading = () => (
    <View style={styles.loadingContainer}>
      <Text style={styles.loadingText}>Loading...</Text>
    </View>
  );

  // Render error state
  const renderError = () => {
    // Specific copy for expired session
    if (errorType === 'session_expired') {
      return (
        <View style={styles.errorContainer}>
          <Ionicons name="refresh-outline" size={48} color={Colors.textSecondary} />
          <Text style={styles.errorTitle}>Let's start fresh</Text>
          <Text style={styles.errorText}>
            Your previous session expired, so we'll restart to keep results accurate.
          </Text>
          <Pressable style={styles.errorButton} onPress={handleRestart}>
            <Text style={styles.errorButtonText}>Start new assessment</Text>
          </Pressable>
        </View>
      );
    }

    // Generic error
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={48} color={Colors.textSecondary} />
        <Text style={styles.errorText}>{error}</Text>
        <View style={styles.errorButtons}>
          <Pressable style={styles.errorButton} onPress={handleRestart}>
            <Text style={styles.errorButtonText}>Restart</Text>
          </Pressable>
          <Pressable style={[styles.errorButton, styles.errorButtonSecondary]} onPress={() => navigateToLenses(router)}>
            <Text style={[styles.errorButtonText, styles.errorButtonTextSecondary]}>Go Back</Text>
          </Pressable>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <StatusBar style="dark" />

      {/* Header - only show during questions */}
      {viewState === 'questions' && progress && (
        <EnneagramAssessmentProgress
          stage={progress.stage}
          estimatedMinutesRemaining={progress.estimated_minutes_remaining}
        />
      )}

      {/* Main Content */}
      <View style={styles.content}>
        {viewState === 'loading' && renderLoading()}

        {viewState === 'intro' && (
          <EnneagramAssessmentIntro
            onBegin={handleBegin}
            isLoading={isLoading}
            showResumePrompt={showResumePrompt}
            onResume={handleResume}
            onStartFresh={handleStartFresh}
            onDismissResume={handleDismissResume}
            resumeProgress={resumeProgress || undefined}
          />
        )}

        {viewState === 'questions' && currentQuestion && (
          <EnneagramAssessmentQuestion
            question={currentQuestion}
            selectedAnswer={selectedAnswer}
            onSelectAnswer={handleSelectAnswer}
            onContinue={handleContinue}
            isSubmitting={isSubmitting}
          />
        )}

        {viewState === 'computing' && (
          <EnneagramAssessmentComputing
            onComplete={handleComputingComplete}
            minDuration={2000}
          />
        )}

        {viewState === 'error' && renderError()}
      </View>

      {/* Debug Panel */}
      {renderDebugPanel()}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    flex: 1,
  },
  // Loading State
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: Colors.textSecondary,
  },
  // Error State
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    textAlign: 'center',
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 16,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginTop: 16,
    marginBottom: 24,
    lineHeight: 24,
  },
  errorButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  errorButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: Colors.accent,
    borderRadius: 8,
  },
  errorButtonSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  errorButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.surface,
  },
  errorButtonTextSecondary: {
    color: Colors.text,
  },
  // Debug Floating Button & Modal
  debugFloatingButton: {
    position: 'absolute',
    top: Platform.OS === 'ios' ? 50 : 10,
    right: 10,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.8)',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 16,
    zIndex: 100,
    gap: 4,
  },
  debugFloatingText: {
    fontSize: 11,
    color: '#00ff00',
    fontWeight: '600',
  },
  debugModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  debugModalContent: {
    backgroundColor: 'rgba(0,0,0,0.95)',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    maxHeight: '60%',
    paddingBottom: Platform.OS === 'ios' ? 34 : 20,
  },
  debugModalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  debugModalScroll: {
    padding: 12,
  },
  debugTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#00ff00',
    marginBottom: 8,
  },
  debugText: {
    fontSize: 11,
    color: '#00ff00',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    lineHeight: 16,
    marginBottom: 4,
  },
});
