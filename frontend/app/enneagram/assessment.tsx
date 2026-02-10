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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import {
  startP2DeepAssessment,
  submitP2AssessmentAnswer,
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

// Debug flag
const DEBUG_MIRROR = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

// View states
type ViewState = 'intro' | 'questions' | 'computing' | 'error';

export default function P2DeepAssessment() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const { user } = useAppStore();

  // Check for debug mode from URL param
  const isDebugMode = DEBUG_MIRROR || params.debug === '1' || params.debug === 'true';

  // State
  const [viewState, setViewState] = useState<ViewState>('intro');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Session state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<P2AssessmentQuestion | null>(null);
  const [progress, setProgress] = useState<P2AssessmentProgress | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<P2AssessmentAnswer | null>(null);
  
  // Results (for computing screen)
  const [results, setResults] = useState<P2AssessmentResult | null>(null);
  
  // Track if user has answered any questions (for navigation warning)
  const hasStarted = useRef(false);

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
              { text: 'Leave', style: 'destructive', onPress: () => router.back() },
            ]
          );
          return true;
        }
        return false;
      });
      return () => backHandler.remove();
    }
  }, [viewState, router]);

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
      
    } catch (err: any) {
      console.error('[P2Assessment] Start error:', err);
      setError(err?.response?.data?.detail || 'Failed to start assessment. Please try again.');
      setViewState('error');
    } finally {
      setIsLoading(false);
    }
  }, [user?.id]);

  // Select an answer
  const handleSelectAnswer = useCallback((answer: P2AssessmentAnswer) => {
    setSelectedAnswer(answer);
  }, []);

  // Submit answer and get next question
  const handleContinue = useCallback(async () => {
    if (!user?.id || !sessionId || !currentQuestion || !selectedAnswer) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await submitP2AssessmentAnswer(
        user.id,
        sessionId,
        currentQuestion.id,
        selectedAnswer
      );

      if (response.results) {
        // Assessment complete - show computing screen
        setResults(response.results);
        setViewState('computing');
      } else if (response.question) {
        // Next question
        setCurrentQuestion(response.question);
        setProgress(response.progress || null);
        setSelectedAnswer(null);
      } else {
        // Unexpected state
        throw new Error('Unexpected response from server');
      }
      
    } catch (err: any) {
      console.error('[P2Assessment] Submit error:', err);
      
      // Check for session expiry
      if (err?.response?.status === 400 || err?.response?.status === 404) {
        setError('This session has expired. You can restart the assessment.');
        setViewState('error');
      } else {
        setError(err?.response?.data?.detail || 'Failed to submit answer. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [user?.id, sessionId, currentQuestion, selectedAnswer]);

  // Navigate to results after computing
  const handleComputingComplete = useCallback(() => {
    // Navigate to Enneagram results screen
    router.replace('/enneagram/results');
  }, [router]);

  // Restart assessment (from error state)
  const handleRestart = useCallback(() => {
    setSessionId(null);
    setCurrentQuestion(null);
    setProgress(null);
    setSelectedAnswer(null);
    setResults(null);
    setError(null);
    hasStarted.current = false;
    setViewState('intro');
  }, []);

  // Render debug panel
  const renderDebugPanel = () => {
    if (!isDebugMode || !progress) return null;

    return (
      <View style={styles.debugPanel}>
        <Text style={styles.debugTitle}>Debug Info</Text>
        <Text style={styles.debugText}>Session: {sessionId?.slice(0, 8)}...</Text>
        <Text style={styles.debugText}>Stage: {progress.stage}</Text>
        <Text style={styles.debugText}>Questions: {progress.questions_answered}/{progress.estimated_total}</Text>
        <Text style={styles.debugText}>Est. Remaining: {progress.estimated_remaining}</Text>
        {results && (
          <>
            <Text style={styles.debugTitle}>Results</Text>
            <Text style={styles.debugText}>Type: {results.core_type}w{results.wing}</Text>
            <Text style={styles.debugText}>Confidence: {results.confidence} ({results.confidence_tier})</Text>
            <Text style={styles.debugText}>Instinct: {results.instinct_primary}/{results.instinct_secondary || '-'}</Text>
            {results._debug && (
              <>
                <Text style={styles.debugText}>Center: H{results._debug.center_scores?.head || 0} / Ht{results._debug.center_scores?.heart || 0} / G{results._debug.center_scores?.gut || 0}</Text>
                <Text style={styles.debugText}>Type Gap: {results._debug.type_gap}</Text>
                <Text style={styles.debugText}>Coherence: {results._debug.coherence_score}</Text>
              </>
            )}
          </>
        )}
      </View>
    );
  };

  // Render error state
  const renderError = () => (
    <View style={styles.errorContainer}>
      <Ionicons name="alert-circle-outline" size={48} color={Colors.textSecondary} />
      <Text style={styles.errorText}>{error}</Text>
      <View style={styles.errorButtons}>
        <Pressable style={styles.errorButton} onPress={handleRestart}>
          <Text style={styles.errorButtonText}>Restart</Text>
        </Pressable>
        <Pressable style={[styles.errorButton, styles.errorButtonSecondary]} onPress={() => router.back()}>
          <Text style={[styles.errorButtonText, styles.errorButtonTextSecondary]}>Go Back</Text>
        </Pressable>
      </View>
    </View>
  );

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
        {viewState === 'intro' && (
          <EnneagramAssessmentIntro
            onBegin={handleBegin}
            isLoading={isLoading}
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
  // Error State
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
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
  // Debug Panel
  debugPanel: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0,0,0,0.85)',
    padding: 12,
    maxHeight: 200,
  },
  debugTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: '#00ff00',
    marginTop: 8,
    marginBottom: 4,
  },
  debugText: {
    fontSize: 10,
    color: '#00ff00',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    lineHeight: 14,
  },
});
