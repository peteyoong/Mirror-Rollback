/**
 * Enneagram Assessment V3
 * =======================
 * Adaptive 4-phase assessment: 40-90 questions, 15-25 min completion
 * 
 * Phase 1: Triad Lock (20 questions) - Fear/Shame/Anger
 * Phase 2: Core Type (12-15 questions) - Specific type within triad
 * Phase 3: Wing & Subtype (22 questions) - Wing and instinctual stacking
 * Phase 4: Validation (0-15 questions) - Mistyping checks
 * 
 * Result format: "4w5 sx/sp" (type + wing + subtype)
 * Target: 85%+ accuracy
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
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { navigateToLenses } from '../../utils/navigation';
import {
  startV3Assessment,
  submitV3Answer,
  resumeV3Assessment,
  getV3AssessmentStatus,
  V3Question,
  V3Progress,
  V3AnswerResponse,
  V3TriadResult,
} from '../../services/api';

// Session storage key
const V3_SESSION_STORAGE_KEY = 'enneagram_v3_assessment_session';

// Session TTL (2 hours in milliseconds)
const SESSION_TTL_MS = 2 * 60 * 60 * 1000;

// Stored session interface
interface StoredSession {
  session_id: string;
  user_id: string;
  created_at_iso: string;
  updated_at_iso: string;
}

// View states
type ViewState = 'loading' | 'intro' | 'questions' | 'phase_complete' | 'computing' | 'done' | 'error';

export default function V3Assessment() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { user } = useAppStore();

  // State
  const [viewState, setViewState] = useState<ViewState>('loading');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Session state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<V3Question | null>(null);
  const [progress, setProgress] = useState<V3Progress | null>(null);
  const [phaseLabel, setPhaseLabel] = useState<string>('');
  const [phaseNumber, setPhaseNumber] = useState<number>(1);
  const [selectedValue, setSelectedValue] = useState<number | null>(null);
  
  // Phase completion state
  const [phaseResult, setPhaseResult] = useState<V3TriadResult | null>(null);
  
  // Final result state
  const [finalResult, setFinalResult] = useState<any>(null);
  
  // Track if user has answered any questions
  const hasStarted = useRef(false);
  const hasInitializedRef = useRef(false);

  // ============================================
  // SESSION PERSISTENCE HELPERS
  // ============================================
  
  const saveSession = useCallback(async (session: StoredSession) => {
    try {
      await AsyncStorage.setItem(V3_SESSION_STORAGE_KEY, JSON.stringify(session));
    } catch (err) {
      console.error('[V3Assessment] Failed to save session:', err);
    }
  }, []);

  const clearSession = useCallback(async () => {
    try {
      await AsyncStorage.removeItem(V3_SESSION_STORAGE_KEY);
    } catch (err) {
      console.error('[V3Assessment] Failed to clear session:', err);
    }
  }, []);

  const loadStoredSession = useCallback(async (): Promise<StoredSession | null> => {
    try {
      const stored = await AsyncStorage.getItem(V3_SESSION_STORAGE_KEY);
      if (!stored) return null;
      
      const session: StoredSession = JSON.parse(stored);
      
      // Check if session is within TTL
      const updatedAt = new Date(session.updated_at_iso).getTime();
      const now = Date.now();
      
      if (now - updatedAt > SESSION_TTL_MS) {
        await clearSession();
        return null;
      }
      
      if (session.user_id !== user?.id) {
        await clearSession();
        return null;
      }
      
      return session;
    } catch (err) {
      console.error('[V3Assessment] Failed to load session:', err);
      return null;
    }
  }, [user?.id, clearSession]);

  // ============================================
  // CHECK FOR EXISTING SESSION ON MOUNT
  // ============================================
  
  useEffect(() => {
    if (hasInitializedRef.current) return;
    
    const checkExistingSession = async () => {
      hasInitializedRef.current = true;
      
      if (!user?.id) {
        setViewState('intro');
        return;
      }

      try {
        const stored = await loadStoredSession();
        
        if (stored) {
          try {
            const status = await getV3AssessmentStatus(stored.session_id);
            
            if (status.found && status.phase !== 'done') {
              // Resume session
              const resumeData = await resumeV3Assessment(stored.session_id);
              
              if (resumeData.can_resume && resumeData.question) {
                setSessionId(stored.session_id);
                setCurrentQuestion(resumeData.question);
                setProgress(resumeData.progress || null);
                setPhaseLabel(resumeData.phase_label || '');
                setPhaseNumber(resumeData.phase_number || 1);
                setViewState('questions');
                hasStarted.current = true;
                return;
              }
            }
          } catch (err) {
            await clearSession();
          }
        }
        
        setViewState('intro');
      } catch (err) {
        console.error('[V3Assessment] Session check failed:', err);
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
            'Your progress will be saved. You can resume within 2 hours.',
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
      const response = await startV3Assessment(user.id);
      
      setSessionId(response.session_id);
      setCurrentQuestion(response.question);
      setProgress(response.progress);
      setPhaseLabel(response.phase_label);
      setPhaseNumber(response.phase_number);
      setSelectedValue(null);
      setViewState('questions');
      hasStarted.current = true;
      
      // Save session
      const now = new Date().toISOString();
      await saveSession({
        session_id: response.session_id,
        user_id: user.id,
        created_at_iso: now,
        updated_at_iso: now,
      });
      
    } catch (err: any) {
      console.error('[V3Assessment] Start error:', err);
      setError(err?.response?.data?.detail || 'Failed to start assessment. Please try again.');
      setViewState('error');
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, saveSession]);

  // Select an answer
  const handleSelectAnswer = useCallback((value: number) => {
    setSelectedValue(value);
  }, []);

  // Submit answer and get next question
  const handleContinue = useCallback(async () => {
    if (!user?.id || !sessionId || !currentQuestion || selectedValue === null) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await submitV3Answer(
        user.id,
        sessionId,
        currentQuestion.id,
        selectedValue
      );
      
      // Update session timestamp
      const stored = await loadStoredSession();
      await saveSession({
        session_id: sessionId,
        user_id: user.id,
        created_at_iso: stored?.created_at_iso || new Date().toISOString(),
        updated_at_iso: new Date().toISOString(),
      });
      
      if (response.status === 'continue') {
        // Next question (may include phase transition)
        setCurrentQuestion(response.question || null);
        setProgress(response.progress || null);
        setPhaseLabel(response.phase_label || phaseLabel);
        setPhaseNumber(response.phase_number || phaseNumber);
        setSelectedValue(null);
        
        // If phase transition occurred, show a brief indicator
        if (response.phase_transition && response.phase_result) {
          // Could show a brief toast or animation here
          console.log('[V3Assessment] Phase transition:', response.phase_result);
        }
        
      } else if (response.status === 'phase_complete') {
        // Phase complete - show results
        setPhaseResult(response.phase_result || null);
        setPhaseNumber(response.phase_completed || phaseNumber);
        setViewState('phase_complete');
        
      } else if (response.status === 'done') {
        // Assessment complete - save final result and show done screen
        await clearSession();
        setFinalResult(response.final_result || null);
        setViewState('done');
        
      } else {
        console.error('[V3Assessment] Unexpected response:', response);
        setError('Unexpected response from server');
        setViewState('error');
      }
      
    } catch (err: any) {
      console.error('[V3Assessment] Submit error:', err);
      
      if (err?.response?.status === 404) {
        await clearSession();
        setError('Your session expired. Please start again.');
      } else {
        setError(err?.response?.data?.detail || 'Failed to submit answer. Please try again.');
      }
      setViewState('error');
    } finally {
      setIsSubmitting(false);
    }
  }, [user?.id, sessionId, currentQuestion, selectedValue, phaseLabel, phaseNumber, clearSession, loadStoredSession, saveSession]);

  // Restart assessment
  const handleRestart = useCallback(async () => {
    await clearSession();
    setSessionId(null);
    setCurrentQuestion(null);
    setProgress(null);
    setSelectedValue(null);
    setPhaseResult(null);
    setError(null);
    hasStarted.current = false;
    setViewState('intro');
  }, [clearSession]);

  // Navigate to results
  const handleViewResults = useCallback(() => {
    router.replace('/enneagram/results');
  }, [router]);

  // ============================================
  // RENDER FUNCTIONS
  // ============================================

  // Intro Screen
  const renderIntro = () => (
    <ScrollView 
      style={styles.introContainer}
      contentContainerStyle={styles.introContent}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.introHeader}>
        <Ionicons name="compass-outline" size={64} color={Colors.textSecondary} />
        <Text style={styles.introTitle}>Discover Your Enneagram Type</Text>
        <Text style={styles.introSubtitle}>
          A deeper, more accurate assessment
        </Text>
      </View>
      
      <View style={styles.introBody}>
        <Text style={styles.introDescription}>
          This adaptive assessment uses 4 phases to identify your type with high accuracy:
        </Text>
        
        <View style={styles.phaseList}>
          <View style={styles.phaseItem}>
            <View style={styles.phaseIcon}>
              <Text style={styles.phaseIconText}>1</Text>
            </View>
            <View style={styles.phaseInfo}>
              <Text style={styles.phaseTitle}>Triad Lock</Text>
              <Text style={styles.phaseDesc}>Identify your core center (Fear, Shame, or Anger)</Text>
            </View>
          </View>
          
          <View style={styles.phaseItem}>
            <View style={[styles.phaseIcon, styles.phaseIconLocked]}>
              <Text style={styles.phaseIconTextLocked}>2</Text>
            </View>
            <View style={styles.phaseInfo}>
              <Text style={styles.phaseTitleLocked}>Core Type</Text>
              <Text style={styles.phaseDescLocked}>Narrow down to your specific type</Text>
            </View>
          </View>
          
          <View style={styles.phaseItem}>
            <View style={[styles.phaseIcon, styles.phaseIconLocked]}>
              <Text style={styles.phaseIconTextLocked}>3</Text>
            </View>
            <View style={styles.phaseInfo}>
              <Text style={styles.phaseTitleLocked}>Wing & Subtype</Text>
              <Text style={styles.phaseDescLocked}>Determine your wing and instinctual stack</Text>
            </View>
          </View>
          
          <View style={styles.phaseItem}>
            <View style={[styles.phaseIcon, styles.phaseIconLocked]}>
              <Text style={styles.phaseIconTextLocked}>4</Text>
            </View>
            <View style={styles.phaseInfo}>
              <Text style={styles.phaseTitleLocked}>Validation</Text>
              <Text style={styles.phaseDescLocked}>Confirm accuracy with mistype checks</Text>
            </View>
          </View>
        </View>
        
        <View style={styles.timeEstimate}>
          <Ionicons name="time-outline" size={18} color={Colors.textTertiary} />
          <Text style={styles.timeText}>15-25 minutes • 40-90 questions</Text>
        </View>
      </View>
      
      <TouchableOpacity 
        style={styles.beginButton}
        onPress={handleBegin}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color={Colors.surface} />
        ) : (
          <>
            <Text style={styles.beginButtonText}>Begin Assessment</Text>
            <Ionicons name="arrow-forward" size={18} color={Colors.surface} />
          </>
        )}
      </TouchableOpacity>
    </ScrollView>
  );

  // Question Screen
  const renderQuestion = () => {
    if (!currentQuestion) return null;
    
    return (
      <View style={styles.questionContainer}>
        {/* Progress Header */}
        <View style={styles.progressHeader}>
          <Text style={styles.progressPhase}>{phaseLabel}</Text>
          <Text style={styles.progressCount}>
            Question {progress?.current || 1} of ~{progress?.estimated_total || 45}
          </Text>
        </View>
        
        {/* Confidence Hint */}
        {progress?.confidence_hint && (
          <View style={styles.confidenceHint}>
            <Ionicons name="sparkles-outline" size={14} color={Colors.accent} />
            <Text style={styles.confidenceText}>{progress.confidence_hint}</Text>
          </View>
        )}
        
        {/* Question */}
        <ScrollView 
          style={styles.questionScroll}
          contentContainerStyle={styles.questionContent}
          showsVerticalScrollIndicator={false}
        >
          <Text style={styles.questionText}>{currentQuestion.question}</Text>
          
          {/* Options */}
          <View style={styles.optionsContainer}>
            {currentQuestion.options.map((option) => (
              <TouchableOpacity
                key={option.value}
                style={[
                  styles.optionButton,
                  selectedValue === option.value && styles.optionButtonSelected
                ]}
                onPress={() => handleSelectAnswer(option.value)}
              >
                <View style={[
                  styles.optionRadio,
                  selectedValue === option.value && styles.optionRadioSelected
                ]}>
                  {selectedValue === option.value && (
                    <Ionicons name="checkmark" size={14} color={Colors.surface} />
                  )}
                </View>
                <Text style={[
                  styles.optionText,
                  selectedValue === option.value && styles.optionTextSelected
                ]}>
                  {option.text}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
        
        {/* Continue Button */}
        <View style={[styles.buttonContainer, { paddingBottom: Math.max(insets.bottom, 16) }]}>
          <TouchableOpacity
            style={[
              styles.continueButton,
              selectedValue === null && styles.continueButtonDisabled
            ]}
            onPress={handleContinue}
            disabled={selectedValue === null || isSubmitting}
          >
            {isSubmitting ? (
              <ActivityIndicator color={Colors.surface} />
            ) : (
              <>
                <Text style={styles.continueButtonText}>Continue</Text>
                <Ionicons name="arrow-forward" size={18} color={Colors.surface} />
              </>
            )}
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  // Phase Complete Screen
  const renderPhaseComplete = () => {
    const triadColors: Record<string, string> = {
      fear: '#6B7BE3',
      shame: '#E36B8A',
      anger: '#E3A16B',
    };
    
    const triadDescriptions: Record<string, string> = {
      fear: 'The Fear triad (Head center) includes Types 5, 6, and 7. These types process the world primarily through thinking and tend to experience fear or anxiety as their core emotion.',
      shame: 'The Shame triad (Heart center) includes Types 2, 3, and 4. These types are focused on identity and image, with shame being the underlying emotional pattern.',
      anger: 'The Anger triad (Gut center) includes Types 8, 9, and 1. These types are body-based and deal with anger or frustration as their core emotion.',
    };
    
    const typeNames: Record<number, string> = {
      1: 'The Reformer',
      2: 'The Helper',
      3: 'The Achiever',
      4: 'The Individualist',
      5: 'The Investigator',
      6: 'The Loyalist',
      7: 'The Enthusiast',
      8: 'The Challenger',
      9: 'The Peacemaker',
    };
    
    // Check if this is Phase 2 completion (has core_type_locked)
    const isPhase2 = phaseResult?.core_type_locked !== undefined;
    
    if (isPhase2) {
      // Phase 2 Complete - Core Type Identified
      const coreType = phaseResult?.core_type_locked || 0;
      const confidence = phaseResult?.core_type_confidence || 0;
      const triadName = phaseResult?.triad || 'unknown';
      
      return (
        <View style={styles.phaseCompleteContainer}>
          <View style={styles.phaseCompleteContent}>
            <View style={[styles.triadBadge, { backgroundColor: triadColors[triadName] || Colors.accent }]}>
              <Text style={styles.triadBadgeText}>Type {coreType}</Text>
            </View>
            
            <Text style={styles.phaseCompleteTitle}>{typeNames[coreType] || `Type ${coreType}`}</Text>
            
            <Text style={styles.phaseCompleteDescription}>
              You've been identified as a Type {coreType} in the {triadName.charAt(0).toUpperCase() + triadName.slice(1)} triad.
            </Text>
            
            {phaseResult?.type_percentages && (
              <View style={styles.typesInTriad}>
                <Text style={styles.typesLabel}>Type Scores:</Text>
                <View style={styles.typesRow}>
                  {Object.entries(phaseResult.type_percentages).map(([type, pct]) => (
                    <View 
                      key={type} 
                      style={[
                        styles.typeBadge,
                        parseInt(type) === coreType && { backgroundColor: Colors.accent }
                      ]}
                    >
                      <Text style={[
                        styles.typeBadgeText,
                        parseInt(type) === coreType && { color: Colors.surface }
                      ]}>
                        {type}: {typeof pct === 'number' ? Math.round(pct) : pct}%
                      </Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
            
            <View style={styles.confidenceScore}>
              <Text style={styles.confidenceLabel}>Confidence</Text>
              <Text style={styles.confidenceValue}>
                {Math.round(confidence)}%
              </Text>
            </View>
          </View>
          
          <View style={styles.phaseCompleteFooter}>
            <Text style={styles.comingSoonText}>
              Phase 3 (Wing & Subtype) coming soon!
            </Text>
            <TouchableOpacity 
              style={styles.returnButton}
              onPress={() => navigateToLenses(router)}
            >
              <Text style={styles.returnButtonText}>Return to Lenses</Text>
            </TouchableOpacity>
          </View>
        </View>
      );
    }
    
    // Phase 1 Complete - Triad Locked
    const triadName = phaseResult?.triad_locked || 'unknown';
    
    return (
      <View style={styles.phaseCompleteContainer}>
        <View style={styles.phaseCompleteContent}>
          <View style={[styles.triadBadge, { backgroundColor: triadColors[triadName] || Colors.accent }]}>
            <Text style={styles.triadBadgeText}>
              {triadName.charAt(0).toUpperCase() + triadName.slice(1)} Triad
            </Text>
          </View>
          
          <Text style={styles.phaseCompleteTitle}>Phase 1 Complete!</Text>
          
          <Text style={styles.phaseCompleteDescription}>
            {triadDescriptions[triadName]}
          </Text>
          
          {phaseResult?.types_in_triad && (
            <View style={styles.typesInTriad}>
              <Text style={styles.typesLabel}>Your type is one of:</Text>
              <View style={styles.typesRow}>
                {phaseResult.types_in_triad.map((type) => (
                  <View key={type} style={styles.typeBadge}>
                    <Text style={styles.typeBadgeText}>Type {type}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}
          
          <View style={styles.confidenceScore}>
            <Text style={styles.confidenceLabel}>Confidence</Text>
            <Text style={styles.confidenceValue}>
              {Math.round(phaseResult?.triad_confidence || 0)}%
            </Text>
          </View>
        </View>
        
        <View style={styles.phaseCompleteFooter}>
          <Text style={styles.comingSoonText}>
            Phase 2 (Core Type) coming soon!
          </Text>
          <TouchableOpacity 
            style={styles.returnButton}
            onPress={() => navigateToLenses(router)}
          >
            <Text style={styles.returnButtonText}>Return to Lenses</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  // Final Results Screen (Done)
  const renderDone = () => {
    const instinctLabels: Record<string, string> = {
      sp: 'Self-Preservation',
      so: 'Social',
      sx: 'Sexual/Intimate',
    };
    
    const triadColors: Record<string, string> = {
      fear: '#6B7BE3',
      shame: '#E36B8A',
      anger: '#E3A16B',
    };
    
    if (!finalResult) {
      return (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Results not available</Text>
          <TouchableOpacity style={styles.errorButton} onPress={() => navigateToLenses(router)}>
            <Text style={styles.errorButtonText}>Return to Lenses</Text>
          </TouchableOpacity>
        </View>
      );
    }
    
    return (
      <ScrollView style={styles.doneContainer} contentContainerStyle={styles.doneContent}>
        {/* Big Type Badge */}
        <View style={[styles.finalTypeBadge, { backgroundColor: triadColors[finalResult.triad] || Colors.accent }]}>
          <Text style={styles.finalTypeString}>{finalResult.full_type_string}</Text>
        </View>
        
        {/* Type Name */}
        <Text style={styles.finalTypeName}>{finalResult.core_type_name}</Text>
        
        {/* Details Card */}
        <View style={styles.detailsCard}>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Core Type</Text>
            <Text style={styles.detailValue}>Type {finalResult.core_type}</Text>
          </View>
          
          <View style={styles.detailDivider} />
          
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Wing</Text>
            <Text style={styles.detailValue}>
              {finalResult.wing === 'balanced' ? 'Balanced Wings' : `Wing ${finalResult.wing}`}
            </Text>
          </View>
          
          <View style={styles.detailDivider} />
          
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Triad</Text>
            <Text style={styles.detailValue}>
              {finalResult.triad?.charAt(0).toUpperCase() + finalResult.triad?.slice(1)} Center
            </Text>
          </View>
          
          <View style={styles.detailDivider} />
          
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Dominant Instinct</Text>
            <Text style={styles.detailValue}>
              {instinctLabels[finalResult.dominant_instinct] || finalResult.dominant_instinct}
            </Text>
          </View>
          
          <View style={styles.detailDivider} />
          
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Instinct Stack</Text>
            <Text style={styles.detailValue}>
              {finalResult.instinct_stack?.map((i: string) => i.toUpperCase()).join(' > ')}
            </Text>
          </View>
        </View>
        
        {/* Confidence Score */}
        <View style={styles.confidenceCard}>
          <Text style={styles.confidenceCardLabel}>Assessment Confidence</Text>
          <Text style={styles.confidenceCardValue}>{Math.round(finalResult.confidence_percentage)}%</Text>
        </View>
        
        {/* Action Buttons */}
        <View style={styles.doneActions}>
          <TouchableOpacity 
            style={styles.primaryButton}
            onPress={() => navigateToLenses(router)}
          >
            <Text style={styles.primaryButtonText}>View Your Profile</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.secondaryButton}
            onPress={handleRestart}
          >
            <Text style={styles.secondaryButtonText}>Retake Assessment</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  };

  // Error Screen
  const renderError = () => (
    <View style={styles.errorContainer}>
      <Ionicons name="alert-circle-outline" size={48} color={Colors.textSecondary} />
      <Text style={styles.errorText}>{error}</Text>
      <View style={styles.errorButtons}>
        <Pressable style={styles.errorButton} onPress={handleRestart}>
          <Text style={styles.errorButtonText}>Try Again</Text>
        </Pressable>
        <Pressable 
          style={[styles.errorButton, styles.errorButtonSecondary]} 
          onPress={() => navigateToLenses(router)}
        >
          <Text style={[styles.errorButtonText, styles.errorButtonTextSecondary]}>Go Back</Text>
        </Pressable>
      </View>
    </View>
  );

  // Loading Screen
  const renderLoading = () => (
    <View style={styles.loadingContainer}>
      <ActivityIndicator size="large" color={Colors.accent} />
      <Text style={styles.loadingText}>Loading...</Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <StatusBar style="light" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => {
            if (hasStarted.current && viewState === 'questions') {
              Alert.alert(
                'Leave Assessment?',
                'Your progress will be saved.',
                [
                  { text: 'Stay', style: 'cancel' },
                  { text: 'Leave', onPress: () => navigateToLenses(router) },
                ]
              );
            } else {
              navigateToLenses(router);
            }
          }}
        >
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Enneagram Assessment V3</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Main Content */}
      <View style={styles.content}>
        {viewState === 'loading' && renderLoading()}
        {viewState === 'intro' && renderIntro()}
        {viewState === 'questions' && renderQuestion()}
        {viewState === 'phase_complete' && renderPhaseComplete()}
        {viewState === 'error' && renderError()}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.text,
  },
  content: {
    flex: 1,
  },
  
  // Loading
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
    color: Colors.textSecondary,
  },
  
  // Intro
  introContainer: {
    flex: 1,
  },
  introContent: {
    padding: 24,
    paddingBottom: 48,
  },
  introHeader: {
    alignItems: 'center',
    marginBottom: 32,
  },
  introTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.text,
    marginTop: 16,
    textAlign: 'center',
  },
  introSubtitle: {
    fontSize: 15,
    color: Colors.textSecondary,
    marginTop: 8,
    textAlign: 'center',
  },
  introBody: {
    marginBottom: 32,
  },
  introDescription: {
    fontSize: 15,
    color: Colors.textSecondary,
    lineHeight: 22,
    marginBottom: 24,
  },
  phaseList: {
    gap: 16,
    marginBottom: 24,
  },
  phaseItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  phaseIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  phaseIconLocked: {
    backgroundColor: Colors.border,
  },
  phaseIconText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.surface,
  },
  phaseIconTextLocked: {
    color: Colors.textTertiary,
  },
  phaseInfo: {
    flex: 1,
  },
  phaseTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 2,
  },
  phaseTitleLocked: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.textTertiary,
    marginBottom: 2,
  },
  phaseDesc: {
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 18,
  },
  phaseDescLocked: {
    fontSize: 13,
    color: Colors.textTertiary,
    lineHeight: 18,
  },
  timeEstimate: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    justifyContent: 'center',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  timeText: {
    fontSize: 14,
    color: Colors.textTertiary,
  },
  beginButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    borderRadius: 12,
  },
  beginButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.surface,
  },
  
  // Question
  questionContainer: {
    flex: 1,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  progressPhase: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.accent,
  },
  progressCount: {
    fontSize: 13,
    color: Colors.textTertiary,
  },
  confidenceHint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 24,
    paddingVertical: 8,
    backgroundColor: Colors.surfaceLight,
  },
  confidenceText: {
    fontSize: 13,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  questionScroll: {
    flex: 1,
  },
  questionContent: {
    padding: 24,
    paddingBottom: 16,
  },
  questionText: {
    fontSize: 18,
    fontWeight: '500',
    color: Colors.text,
    lineHeight: 26,
    marginBottom: 24,
    textAlign: 'center',
  },
  optionsContainer: {
    gap: 12,
  },
  optionButton: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 16,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: 12,
  },
  optionButtonSelected: {
    borderColor: Colors.accent,
    backgroundColor: Colors.surfaceLight,
  },
  optionRadio: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  optionRadioSelected: {
    borderColor: Colors.accent,
    backgroundColor: Colors.accent,
  },
  optionText: {
    flex: 1,
    fontSize: 15,
    color: Colors.text,
    lineHeight: 22,
  },
  optionTextSelected: {
    fontWeight: '500',
  },
  buttonContainer: {
    paddingHorizontal: 24,
    paddingTop: 12,
    backgroundColor: Colors.background,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  continueButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    borderRadius: 12,
  },
  continueButtonDisabled: {
    opacity: 0.4,
  },
  continueButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.surface,
  },
  
  // Phase Complete
  phaseCompleteContainer: {
    flex: 1,
    justifyContent: 'space-between',
    padding: 24,
  },
  phaseCompleteContent: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  triadBadge: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 24,
    marginBottom: 24,
  },
  triadBadgeText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.surface,
  },
  phaseCompleteTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 16,
    textAlign: 'center',
  },
  phaseCompleteDescription: {
    fontSize: 15,
    color: Colors.textSecondary,
    lineHeight: 22,
    textAlign: 'center',
    marginBottom: 24,
  },
  typesInTriad: {
    alignItems: 'center',
    marginBottom: 24,
  },
  typesLabel: {
    fontSize: 14,
    color: Colors.textTertiary,
    marginBottom: 12,
  },
  typesRow: {
    flexDirection: 'row',
    gap: 12,
  },
  typeBadge: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: Colors.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  typeBadgeText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.text,
  },
  confidenceScore: {
    alignItems: 'center',
  },
  confidenceLabel: {
    fontSize: 13,
    color: Colors.textTertiary,
    marginBottom: 4,
  },
  confidenceValue: {
    fontSize: 32,
    fontWeight: '700',
    color: Colors.accent,
  },
  phaseCompleteFooter: {
    alignItems: 'center',
    gap: 16,
  },
  comingSoonText: {
    fontSize: 14,
    color: Colors.textTertiary,
    fontStyle: 'italic',
  },
  returnButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: Colors.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  returnButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.text,
  },
  
  // Error
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
});
