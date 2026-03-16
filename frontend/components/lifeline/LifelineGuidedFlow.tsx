/**
 * LifelineGuidedFlow Component
 * 
 * A guided 5-moment entry flow that helps users quickly add meaningful
 * life events to unlock Pattern Reveal. Feels like guided life reflection,
 * not database entry.
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Animated,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import api from '../../services/api';

// =============================================================================
// CONSTANTS
// =============================================================================

const TARGET_MOMENTS = 5;
const TEASER_THRESHOLD = 3;

// Identity-based progress messages
const PROGRESS_MESSAGES: Record<number, string> = {
  0: 'Begin your discovery',
  1: 'Your timeline begins',
  2: 'Your story expands',
  3: 'Something interesting may be forming',
  4: 'One more turning point reveals your pattern',
  5: 'Your first life pattern appears',
};

// First entry memory trigger - strong autobiographical opening
const FIRST_ENTRY_PROMPT = {
  primary: "Do you remember the moment everything changed?",
  supporting: "Start with moments like that.",
  helper: "You don't need the whole story.\nJust begin with one moment you still remember clearly.",
};

// Second entry bridge - transitional prompt
const SECOND_ENTRY_BRIDGE = {
  affirmation: "Good start.",
  prompt: "What happened next that also changed your direction?",
};

// Rotating prompts for memory recall (used after first two entries)
const PROMPTS = [
  "A moment when everything changed",
  "A moment that forced a decision",
  "A moment that changed how you saw yourself",
  "A moment when your path no longer felt the same",
  "A moment that opened a new chapter",
];

// Enhanced hint chips as memory triggers (not categories)
const HINT_CHIPS = [
  'Everything changed',
  'Forced decision',
  'New chapter',
  'Path shifted',
  'Identity changed',
  'Reinvention',
  'Breakthrough',
  'Crisis',
];

// =============================================================================
// TYPES
// =============================================================================

interface LifelineGuidedFlowProps {
  initialCount: number;
  onComplete: () => void;
  onExit: () => void;
}

interface MomentData {
  title: string;
  year: string;
  age: string;
  description: string;
  // Task 61: New two-scale rating model
  emotionalValence: number;  // 1-10: 1=very difficult, 5=mixed, 10=very positive
  significanceScore: number; // 1-10: 1=very low, 5=meaningful, 10=life-changing
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function LifelineGuidedFlow({ 
  initialCount, 
  onComplete, 
  onExit 
}: LifelineGuidedFlowProps) {
  const { theme } = useTheme();
  const { user } = useAppStore();
  
  // Progress state
  const [currentCount, setCurrentCount] = useState(initialCount);
  const [isCompleted, setIsCompleted] = useState(false);
  
  // Form state
  const [moment, setMoment] = useState<MomentData>({
    title: '',
    year: '',
    age: '',
    description: '',
    impactScore: 7,
  });
  
  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [showTeaser, setShowTeaser] = useState(false);
  const [revealStep, setRevealStep] = useState(0); // 0=none, 1=analyzing, 2=interesting, 3=arc, 4=explanation
  const [patternConfidence, setPatternConfidence] = useState<'high' | 'low'>('high');
  
  // Animation
  const progressAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const revealFadeAnim = useRef(new Animated.Value(0)).current;
  const arcAnim1 = useRef(new Animated.Value(0)).current;
  const arcAnim2 = useRef(new Animated.Value(0)).current;
  const arcAnim3 = useRef(new Animated.Value(0)).current;
  const arcLineAnim = useRef(new Animated.Value(0)).current;
  
  // Get current prompt based on count
  const currentPrompt = PROMPTS[currentCount % PROMPTS.length];
  
  // Calculate progress percentage
  const progressPercentage = (currentCount / TARGET_MOMENTS) * 100;
  
  // Update progress animation
  useEffect(() => {
    Animated.timing(progressAnim, {
      toValue: progressPercentage,
      duration: 400,
      useNativeDriver: false,
    }).start();
  }, [currentCount]);
  
  // Check if teaser should show
  useEffect(() => {
    if (currentCount === TEASER_THRESHOLD && !showTeaser) {
      setShowTeaser(true);
    }
  }, [currentCount]);
  
  // Reset form for next entry
  const resetForm = () => {
    setMoment({
      title: '',
      year: '',
      age: '',
      description: '',
      impactScore: 7,
    });
    setError('');
  };
  
  // Handle hint chip tap
  const handleHintChip = (hint: string) => {
    if (!moment.title) {
      setMoment(prev => ({ ...prev, title: hint }));
    }
  };
  
  // Validate and save moment
  const handleSave = async () => {
    // Validation
    if (!moment.title.trim()) {
      setError('Please add a title for this moment');
      return;
    }
    
    const yearNum = moment.year ? parseInt(moment.year, 10) : undefined;
    const ageNum = moment.age ? parseInt(moment.age, 10) : undefined;
    
    if (moment.year && (isNaN(yearNum!) || yearNum! < 1900 || yearNum! > 2100)) {
      setError('Please enter a valid year');
      return;
    }
    
    if (moment.age && (isNaN(ageNum!) || ageNum! < 0 || ageNum! > 120)) {
      setError('Please enter a valid age');
      return;
    }
    
    setError('');
    setIsSaving(true);
    
    try {
      // Save to API
      await api.post('/lifeline/event', {
        user_id: user?.id,
        title: moment.title.trim(),
        description: moment.description.trim() || undefined,
        year: yearNum,
        age: ageNum,
        impact_score: moment.impactScore,
        category: 'Turning Point',
        emotional_tone: 'mixed',
        privacy_level: 'private',
      });
      
      const newCount = currentCount + 1;
      setCurrentCount(newCount);
      
      // Check if this is the 5th moment
      if (newCount >= TARGET_MOMENTS) {
        handleUnlock();
      } else {
        // Animate transition to next entry
        Animated.sequence([
          Animated.timing(fadeAnim, {
            toValue: 0,
            duration: 200,
            useNativeDriver: true,
          }),
          Animated.timing(fadeAnim, {
            toValue: 1,
            duration: 200,
            useNativeDriver: true,
          }),
        ]).start();
        
        setTimeout(() => {
          resetForm();
          // Show teaser at 3 moments
          if (newCount === TEASER_THRESHOLD) {
            setShowTeaser(true);
          }
        }, 200);
      }
      
    } catch (err: any) {
      console.error('[GuidedFlow] Save error:', err);
      setError(err.response?.data?.detail || 'Failed to save. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };
  
  // Handle 5th moment unlock - Cinematic reveal sequence
  const handleUnlock = async () => {
    // Step 1: "Analyzing your timeline..."
    setRevealStep(1);
    animateRevealFade();
    
    // Optionally fetch pattern confidence from API
    try {
      const response = await api.get(`/lifeline/${user?.id}/summary`);
      const confidence = response.data?.pattern_count >= 2 ? 'high' : 'low';
      setPatternConfidence(confidence);
    } catch {
      setPatternConfidence('high'); // Default to high confidence
    }
    
    // Step 2: "Something interesting appears." (after 800ms)
    setTimeout(() => {
      setRevealStep(2);
      animateRevealFade();
    }, 800);
    
    // Step 3: Pattern arc animation (after 1600ms)
    setTimeout(() => {
      setRevealStep(3);
      animateRevealFade();
      animatePatternArc();
    }, 1600);
    
    // Step 4: Explanation (after 2600ms)
    setTimeout(() => {
      setRevealStep(4);
      animateRevealFade();
    }, 2600);
    
    // Step 5: Navigate to Pattern Lens (after 3500ms)
    setTimeout(() => {
      onComplete();
    }, 3500);
  };
  
  // Animate fade transition between steps
  const animateRevealFade = () => {
    revealFadeAnim.setValue(0);
    Animated.timing(revealFadeAnim, {
      toValue: 1,
      duration: 300,
      useNativeDriver: false, // Web compatibility
    }).start();
  };
  
  // Animate pattern arc nodes appearing
  const animatePatternArc = () => {
    arcAnim1.setValue(0);
    arcAnim2.setValue(0);
    arcAnim3.setValue(0);
    arcLineAnim.setValue(0);
    
    Animated.stagger(200, [
      Animated.timing(arcAnim1, {
        toValue: 1,
        duration: 250,
        useNativeDriver: false, // Web compatibility
      }),
      Animated.timing(arcLineAnim, {
        toValue: 0.5,
        duration: 150,
        useNativeDriver: false,
      }),
      Animated.timing(arcAnim2, {
        toValue: 1,
        duration: 250,
        useNativeDriver: false,
      }),
      Animated.timing(arcLineAnim, {
        toValue: 1,
        duration: 150,
        useNativeDriver: false,
      }),
      Animated.timing(arcAnim3, {
        toValue: 1,
        duration: 250,
        useNativeDriver: false,
      }),
    ]).start();
  };
  
  // Handle exit
  const handleExit = () => {
    onExit();
  };
  
  // Dismiss teaser
  const dismissTeaser = () => {
    setShowTeaser(false);
  };
  
  // =============================================================================
  // RENDER: CINEMATIC REVEAL SEQUENCE
  // =============================================================================
  
  if (revealStep > 0) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.revealContainer}>
          {/* Step 1: Analyzing */}
          {revealStep === 1 && (
            <Animated.View style={[styles.revealContent, { opacity: revealFadeAnim }]}>
              <ActivityIndicator size="small" color={theme.accent} style={styles.revealLoader} />
              <Text style={[styles.revealText, { color: theme.textSecondary }]}>
                Analyzing your timeline…
              </Text>
            </Animated.View>
          )}
          
          {/* Step 2: Something interesting appears */}
          {revealStep === 2 && (
            <Animated.View style={[styles.revealContent, { opacity: revealFadeAnim }]}>
              <Text style={[styles.revealTextMain, { color: theme.text }]}>
                Something interesting appears.
              </Text>
            </Animated.View>
          )}
          
          {/* Step 3: Pattern arc animation */}
          {revealStep === 3 && (
            <Animated.View style={[styles.revealContent, { opacity: revealFadeAnim }]}>
              {patternConfidence === 'high' ? (
                <View style={styles.patternArcContainer}>
                  {/* Arc nodes with connecting lines */}
                  <View style={styles.arcRow}>
                    <Animated.View 
                      style={[
                        styles.arcNode,
                        { 
                          backgroundColor: `${theme.accent}15`,
                          borderColor: theme.accent,
                          opacity: arcAnim1,
                          transform: [{ scale: arcAnim1 }],
                        }
                      ]}
                    >
                      <Text style={[styles.arcNodeText, { color: theme.accent }]}>Ambition</Text>
                    </Animated.View>
                    
                    <Animated.View 
                      style={[
                        styles.arcLine,
                        { 
                          backgroundColor: theme.accent,
                          opacity: arcLineAnim,
                        }
                      ]}
                    />
                    
                    <Animated.View 
                      style={[
                        styles.arcNode,
                        { 
                          backgroundColor: `${theme.accent}15`,
                          borderColor: theme.accent,
                          opacity: arcAnim2,
                          transform: [{ scale: arcAnim2 }],
                        }
                      ]}
                    >
                      <Text style={[styles.arcNodeText, { color: theme.accent }]}>Pressure</Text>
                    </Animated.View>
                    
                    <Animated.View 
                      style={[
                        styles.arcLine,
                        { 
                          backgroundColor: theme.accent,
                          opacity: arcLineAnim,
                        }
                      ]}
                    />
                    
                    <Animated.View 
                      style={[
                        styles.arcNode,
                        { 
                          backgroundColor: `${theme.accent}15`,
                          borderColor: theme.accent,
                          opacity: arcAnim3,
                          transform: [{ scale: arcAnim3 }],
                        }
                      ]}
                    >
                      <Text style={[styles.arcNodeText, { color: theme.accent }]}>Transformation</Text>
                    </Animated.View>
                  </View>
                </View>
              ) : (
                <Text style={[styles.revealTextMain, { color: theme.text }]}>
                  Your timeline is beginning to form patterns.
                </Text>
              )}
            </Animated.View>
          )}
          
          {/* Step 4: Explanation */}
          {revealStep === 4 && (
            <Animated.View style={[styles.revealContent, { opacity: revealFadeAnim }]}>
              {patternConfidence === 'high' ? (
                <>
                  <View style={[styles.unlockIcon, { backgroundColor: `${theme.accent}15` }]}>
                    <Ionicons name="sparkles" size={36} color={theme.accent} />
                  </View>
                  <Text style={[styles.revealExplanation, { color: theme.textSecondary }]}>
                    This sequence appears across multiple turning points in your life.
                  </Text>
                </>
              ) : (
                <>
                  <View style={[styles.unlockIcon, { backgroundColor: `${theme.accent}15` }]}>
                    <Ionicons name="eye-outline" size={36} color={theme.accent} />
                  </View>
                  <Text style={[styles.revealExplanation, { color: theme.textSecondary }]}>
                    Add more moments to reveal deeper patterns.
                  </Text>
                </>
              )}
            </Animated.View>
          )}
        </View>
      </SafeAreaView>
    );
  }
  
  // =============================================================================
  // RENDER: MAIN GUIDED FLOW
  // =============================================================================
  
  // Get identity-based progress message
  const progressMessage = PROGRESS_MESSAGES[Math.min(currentCount, TARGET_MOMENTS)] || PROGRESS_MESSAGES[0];
  
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <KeyboardAvoidingView 
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Header with progress */}
        <View style={styles.header}>
          <TouchableOpacity 
            style={styles.exitButton}
            onPress={handleExit}
          >
            <Ionicons name="close" size={24} color={theme.textSecondary} />
          </TouchableOpacity>
          
          <View style={styles.progressSection}>
            <View style={styles.progressHeader}>
              <Text style={[styles.progressText, { color: theme.text }]}>
                {currentCount} / {TARGET_MOMENTS} turning points
              </Text>
              <Text style={[styles.progressMessage, { color: theme.textSecondary }]}>
                {progressMessage}
              </Text>
            </View>
            <View style={[styles.progressBar, { backgroundColor: theme.border }]}>
              <Animated.View 
                style={[
                  styles.progressFill, 
                  { 
                    backgroundColor: theme.accent,
                    width: progressAnim.interpolate({
                      inputRange: [0, 100],
                      outputRange: ['0%', '100%'],
                    }),
                  }
                ]} 
              />
            </View>
          </View>
        </View>
        
        <ScrollView 
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Mid-progress teaser at 3 moments */}
          {showTeaser && (
            <View style={[styles.teaserCard, { backgroundColor: `${theme.accent}08`, borderColor: `${theme.accent}30` }]}>
              <View style={styles.teaserHeader}>
                <Text style={[styles.teaserTitle, { color: theme.text }]}>
                  Something interesting may be forming.
                </Text>
                <TouchableOpacity onPress={dismissTeaser}>
                  <Ionicons name="close" size={20} color={theme.textSecondary} />
                </TouchableOpacity>
              </View>
              
              <Text style={[styles.teaserBody, { color: theme.textSecondary }]}>
                Your turning points may already be beginning to trace a sequence.
              </Text>
              
              {/* Partial pattern arc preview */}
              <View style={styles.partialArc}>
                <View style={[styles.partialArcNode, { backgroundColor: `${theme.accent}15`, borderColor: theme.accent }]}>
                  <Text style={[styles.partialArcText, { color: theme.accent }]}>Ambition</Text>
                </View>
                <View style={[styles.partialArcConnector, { backgroundColor: `${theme.accent}40` }]} />
                <View style={[styles.partialArcNode, { backgroundColor: `${theme.accent}15`, borderColor: theme.accent }]}>
                  <Text style={[styles.partialArcText, { color: theme.accent }]}>Pressure</Text>
                </View>
                <Text style={[styles.partialArcQuestion, { color: theme.textTertiary }]}>→ ?</Text>
              </View>
              
              <Text style={[styles.teaserCta, { color: theme.textSecondary }]}>
                Add two more moments to see whether the pattern continues.
              </Text>
            </View>
          )}
          
          <Animated.View style={{ opacity: fadeAnim }}>
            {/* Memory Trigger Prompts - Different for first two entries */}
            <View style={styles.promptSection}>
              {currentCount === 0 ? (
                // First entry - Strong autobiographical opening
                <>
                  <Text style={[styles.memoryTrigger, { color: theme.text }]}>
                    {FIRST_ENTRY_PROMPT.primary}
                  </Text>
                  <Text style={[styles.memorySupportText, { color: theme.textSecondary }]}>
                    {FIRST_ENTRY_PROMPT.supporting}
                  </Text>
                  <Text style={[styles.memoryHelper, { color: theme.textTertiary }]}>
                    {FIRST_ENTRY_PROMPT.helper}
                  </Text>
                </>
              ) : currentCount === 1 ? (
                // Second entry - Bridge transition
                <>
                  <Text style={[styles.bridgeAffirmation, { color: theme.accent }]}>
                    {SECOND_ENTRY_BRIDGE.affirmation}
                  </Text>
                  <Text style={[styles.memoryTrigger, { color: theme.text }]}>
                    {SECOND_ENTRY_BRIDGE.prompt}
                  </Text>
                </>
              ) : (
                // Subsequent entries - Rotating prompts
                <>
                  <Text style={[styles.mainPrompt, { color: theme.text }]}>
                    Add a moment that changed your direction.
                  </Text>
                  <Text style={[styles.subPrompt, { color: theme.textSecondary }]}>
                    {currentPrompt}
                  </Text>
                </>
              )}
            </View>
            
            {/* Hint chips */}
            <View style={styles.hintChips}>
              {HINT_CHIPS.map((hint) => (
                <TouchableOpacity
                  key={hint}
                  style={[
                    styles.hintChip,
                    { 
                      backgroundColor: moment.title === hint ? `${theme.accent}20` : theme.surface,
                      borderColor: moment.title === hint ? theme.accent : theme.border,
                    }
                  ]}
                  onPress={() => handleHintChip(hint)}
                >
                  <Text style={[
                    styles.hintChipText, 
                    { color: moment.title === hint ? theme.accent : theme.textSecondary }
                  ]}>
                    {hint}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            
            {/* Error message */}
            {error ? (
              <View style={[styles.errorBox, { backgroundColor: '#E5737315' }]}>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            ) : null}
            
            {/* Title input */}
            <View style={styles.fieldGroup}>
              <Text style={[styles.label, { color: theme.text }]}>What happened? *</Text>
              <TextInput
                style={[
                  styles.input, 
                  { 
                    backgroundColor: theme.surface, 
                    borderColor: theme.border, 
                    color: theme.text 
                  }
                ]}
                value={moment.title}
                onChangeText={(text) => setMoment(prev => ({ ...prev, title: text }))}
                placeholder="e.g., Quit my job to start something new"
                placeholderTextColor={theme.textTertiary}
                maxLength={100}
              />
            </View>
            
            {/* Year / Age */}
            <View style={styles.rowFields}>
              <View style={[styles.fieldGroup, { flex: 1 }]}>
                <Text style={[styles.label, { color: theme.text }]}>Year</Text>
                <TextInput
                  style={[
                    styles.input, 
                    { 
                      backgroundColor: theme.surface, 
                      borderColor: theme.border, 
                      color: theme.text 
                    }
                  ]}
                  value={moment.year}
                  onChangeText={(text) => setMoment(prev => ({ ...prev, year: text }))}
                  placeholder="2015"
                  placeholderTextColor={theme.textTertiary}
                  keyboardType="number-pad"
                  maxLength={4}
                />
              </View>
              <Text style={[styles.orText, { color: theme.textTertiary }]}>or</Text>
              <View style={[styles.fieldGroup, { flex: 1 }]}>
                <Text style={[styles.label, { color: theme.text }]}>Age</Text>
                <TextInput
                  style={[
                    styles.input, 
                    { 
                      backgroundColor: theme.surface, 
                      borderColor: theme.border, 
                      color: theme.text 
                    }
                  ]}
                  value={moment.age}
                  onChangeText={(text) => setMoment(prev => ({ ...prev, age: text }))}
                  placeholder="25"
                  placeholderTextColor={theme.textTertiary}
                  keyboardType="number-pad"
                  maxLength={3}
                />
              </View>
            </View>
            
            {/* Description */}
            <View style={styles.fieldGroup}>
              <Text style={[styles.label, { color: theme.text }]}>
                Brief description <Text style={{ color: theme.textTertiary }}>(optional)</Text>
              </Text>
              <TextInput
                style={[
                  styles.textArea, 
                  { 
                    backgroundColor: theme.surface, 
                    borderColor: theme.border, 
                    color: theme.text 
                  }
                ]}
                value={moment.description}
                onChangeText={(text) => setMoment(prev => ({ ...prev, description: text }))}
                placeholder="What made this moment significant?"
                placeholderTextColor={theme.textTertiary}
                multiline
                numberOfLines={3}
                textAlignVertical="top"
                maxLength={300}
              />
            </View>
            
            {/* Impact score */}
            <View style={styles.fieldGroup}>
              <Text style={[styles.label, { color: theme.text }]}>How much impact?</Text>
              <View style={styles.impactRow}>
                {IMPACT_LEVELS.map((level) => (
                  <TouchableOpacity
                    key={level.value}
                    style={[
                      styles.impactButton,
                      { 
                        borderColor: moment.impactScore === level.value ? level.color : theme.border,
                        backgroundColor: moment.impactScore === level.value ? `${level.color}20` : 'transparent',
                      }
                    ]}
                    onPress={() => setMoment(prev => ({ ...prev, impactScore: level.value }))}
                  >
                    <View style={[styles.impactDot, { backgroundColor: level.color }]} />
                    <Text style={[
                      styles.impactText, 
                      { color: moment.impactScore === level.value ? theme.text : theme.textSecondary }
                    ]}>
                      {level.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </Animated.View>
        </ScrollView>
        
        {/* Actions */}
        <View style={[styles.actionsContainer, { borderTopColor: theme.border }]}>
          <TouchableOpacity
            style={[styles.saveButton, { backgroundColor: theme.accent }]}
            onPress={handleSave}
            disabled={isSaving}
            activeOpacity={0.8}
          >
            {isSaving ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.saveButtonText}>
                {currentCount >= TARGET_MOMENTS - 1 ? 'Add & Unlock Patterns' : 'Add Moment'}
              </Text>
            )}
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.exitLink}
            onPress={handleExit}
            activeOpacity={0.7}
          >
            <Text style={[styles.exitLinkText, { color: theme.textSecondary }]}>
              Save and continue later
            </Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  flex: {
    flex: 1,
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 16,
  },
  exitButton: {
    padding: 8,
    marginRight: 8,
  },
  progressSection: {
    flex: 1,
  },
  progressHeader: {
    marginBottom: 8,
  },
  progressText: {
    fontSize: 15,
    fontWeight: '600',
  },
  progressMessage: {
    fontSize: 13,
    marginTop: 2,
    fontStyle: 'italic',
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  
  // Scroll
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 24,
    paddingBottom: 24,
  },
  
  // Teaser
  teaserCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
    marginBottom: 24,
  },
  teaserHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  teaserTitle: {
    fontSize: 17,
    fontWeight: '600',
    flex: 1,
    marginRight: 8,
  },
  teaserBody: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  teaserCta: {
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  
  // Partial pattern arc in teaser
  partialArc: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    paddingVertical: 8,
  },
  partialArcNode: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 14,
    borderWidth: 1,
  },
  partialArcText: {
    fontSize: 12,
    fontWeight: '600',
  },
  partialArcConnector: {
    width: 16,
    height: 2,
    marginHorizontal: 4,
  },
  partialArcQuestion: {
    fontSize: 16,
    marginLeft: 4,
    fontWeight: '500',
  },
  
  // Prompts
  promptSection: {
    marginBottom: 20,
  },
  mainPrompt: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 8,
  },
  subPrompt: {
    fontSize: 15,
    fontStyle: 'italic',
  },
  
  // First entry memory trigger
  memoryTrigger: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 8,
    lineHeight: 30,
  },
  memorySupportText: {
    fontSize: 16,
    marginBottom: 16,
  },
  memoryHelper: {
    fontSize: 14,
    lineHeight: 22,
    fontStyle: 'italic',
    marginBottom: 8,
  },
  
  // Second entry bridge
  bridgeAffirmation: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 6,
  },
  
  // Hint chips
  hintChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 24,
  },
  hintChip: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 20,
    borderWidth: 1,
  },
  hintChipText: {
    fontSize: 13,
    fontWeight: '500',
  },
  
  // Error
  errorBox: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 14,
    color: '#E57373',
    textAlign: 'center',
  },
  
  // Fields
  fieldGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
  },
  textArea: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    minHeight: 80,
  },
  rowFields: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
  },
  orText: {
    fontSize: 13,
    marginBottom: 16,
  },
  
  // Impact
  impactRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  impactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 20,
    borderWidth: 1,
    gap: 6,
  },
  impactDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  impactText: {
    fontSize: 13,
    fontWeight: '500',
  },
  
  // Actions
  actionsContainer: {
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: 12,
  },
  saveButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 52,
  },
  saveButtonText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '600',
  },
  exitLink: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  exitLinkText: {
    fontSize: 14,
  },
  
  // Cinematic reveal sequence
  revealContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  revealContent: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  revealLoader: {
    marginBottom: 16,
  },
  revealText: {
    fontSize: 17,
    textAlign: 'center',
  },
  revealTextMain: {
    fontSize: 22,
    fontWeight: '500',
    textAlign: 'center',
    lineHeight: 30,
  },
  revealExplanation: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 24,
    marginTop: 16,
    paddingHorizontal: 16,
  },
  
  // Pattern arc animation
  patternArcContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  arcRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  arcNode: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 20,
    borderWidth: 1.5,
    minWidth: 80,
    alignItems: 'center',
  },
  arcNodeText: {
    fontSize: 13,
    fontWeight: '600',
  },
  arcLine: {
    width: 24,
    height: 2,
    marginHorizontal: 4,
  },
  
  // Unlock icon (reused in reveal)
  unlockIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
