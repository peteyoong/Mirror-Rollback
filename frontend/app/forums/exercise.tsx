import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { useForumContext } from '../../contexts/ForumContext';
import { 
  getForumExercise, 
  submitForumReflection, 
  PatternDomain, 
  getHumanDesignMechanics, 
  HumanDesignMechanics,
  getPatternGraph,
  PatternGraphCategory,
  getPatternInterpretation,
  PatternInterpretationResponse,
  createJournalEntry
} from '../../services/api';

// Step types for the exercise flow
type Step = 'intro' | 'source' | 'domain' | 'mirror-lens' | 'mirror-insight' | 'guidance' | 'prompts' | 'privacy' | 'complete';
type SourceType = 'patterns' | 'mirror' | null;
type MirrorLens = 'human-design' | 'enneagram' | 'daily-insight' | null;

// Human Design insight items with guidance content
interface HDInsight {
  id: string;
  name: string;
  value: string;
  theme: string;
  strength: string;
  challenge: string;
  guidance: string;
}

// Generate HD insights from mechanics data
const generateHDInsights = (mechanics: HumanDesignMechanics['core_mechanics']): HDInsight[] => {
  const insights: HDInsight[] = [];
  
  if (mechanics.type && mechanics.type !== 'Unknown') {
    insights.push({
      id: 'type',
      name: 'Type',
      value: mechanics.type,
      theme: getTypeTheme(mechanics.type),
      strength: getTypeStrength(mechanics.type),
      challenge: getTypeChallenge(mechanics.type),
      guidance: getTypeGuidance(mechanics.type),
    });
  }
  
  if (mechanics.strategy && mechanics.strategy !== 'Unknown') {
    insights.push({
      id: 'strategy',
      name: 'Strategy',
      value: mechanics.strategy,
      theme: 'Your natural way of engaging with life and making decisions.',
      strength: 'Following this approach brings flow and reduces resistance.',
      challenge: 'Acting against this strategy creates friction and frustration.',
      guidance: 'Notice when you naturally follow this pattern vs. when you override it.',
    });
  }
  
  if (mechanics.authority && mechanics.authority !== 'Unknown') {
    insights.push({
      id: 'authority',
      name: 'Authority',
      value: mechanics.authority,
      theme: getAuthorityTheme(mechanics.authority),
      strength: getAuthorityStrength(mechanics.authority),
      challenge: getAuthorityChallenge(mechanics.authority),
      guidance: getAuthorityGuidance(mechanics.authority),
    });
  }
  
  if (mechanics.profile && mechanics.profile !== 'Unknown') {
    insights.push({
      id: 'profile',
      name: 'Profile',
      value: mechanics.profile,
      theme: 'Your life theme and way of learning.',
      strength: 'Embracing your profile brings natural fulfillment.',
      challenge: 'Resisting it creates friction with your purpose.',
      guidance: 'Consider how this profile shapes your relationships and work.',
    });
  }
  
  if (mechanics.incarnation_cross && mechanics.incarnation_cross !== 'Unknown') {
    insights.push({
      id: 'incarnation_cross',
      name: 'Incarnation Cross',
      value: mechanics.incarnation_cross,
      theme: 'Your life purpose and contribution.',
      strength: 'Living aligned with this theme brings deep satisfaction.',
      challenge: 'Ignoring it leads to a sense of meaninglessness.',
      guidance: 'Reflect on how this purpose shows up in your current life chapter.',
    });
  }
  
  return insights;
};

// Type-specific content
const getTypeTheme = (type: string): string => {
  const themes: Record<string, string> = {
    'Generator': 'You are here to respond to life and find satisfaction through doing what you love.',
    'Manifesting Generator': 'You are here to respond and then initiate, finding satisfaction through efficient mastery.',
    'Projector': 'You are here to guide others, finding success through being recognized and invited.',
    'Manifestor': 'You are here to initiate and impact, finding peace through informing others.',
    'Reflector': 'You are here to reflect the health of your community, finding surprise through your unique lunar cycle.',
  };
  return themes[type] || 'Your unique energy type shapes how you engage with the world.';
};

const getTypeStrength = (type: string): string => {
  const strengths: Record<string, string> = {
    'Generator': 'Sustainable life force energy, capacity for mastery, deep satisfaction when engaged.',
    'Manifesting Generator': 'Speed, efficiency, multi-passionate energy, ability to skip steps.',
    'Projector': 'Seeing the big picture, guiding others, wisdom about systems and people.',
    'Manifestor': 'Initiating impact, independence, catalyzing change in others.',
    'Reflector': 'Objectivity, sampling all perspectives, reflecting community health.',
  };
  return strengths[type] || 'Unique gifts that emerge when you are aligned.';
};

const getTypeChallenge = (type: string): string => {
  const challenges: Record<string, string> = {
    'Generator': 'Frustration when stuck in work that doesn\'t light you up.',
    'Manifesting Generator': 'Frustration when forced to slow down or explain steps to others.',
    'Projector': 'Bitterness when unrecognized or when trying to keep up with Generator energy.',
    'Manifestor': 'Anger when constrained or when others don\'t understand your need for autonomy.',
    'Reflector': 'Disappointment when environment is unhealthy or when pressured to decide quickly.',
  };
  return challenges[type] || 'Common patterns that arise when out of alignment.';
};

const getTypeGuidance = (type: string): string => {
  const guidance: Record<string, string> = {
    'Generator': 'Wait to respond. Notice your gut response—does it feel expansive or contracting?',
    'Manifesting Generator': 'Wait to respond, then inform before acting. Trust your non-linear path.',
    'Projector': 'Wait for recognition and invitation. Rest is productive for you.',
    'Manifestor': 'Inform others before you act. This reduces resistance from others.',
    'Reflector': 'Wait a full lunar cycle for major decisions. Sample different perspectives.',
  };
  return guidance[type] || 'Follow your natural rhythm.';
};

// Authority-specific content
const getAuthorityTheme = (authority: string): string => {
  if (authority.includes('Emotional') || authority.includes('Solar Plexus')) {
    return 'You make decisions through emotional clarity over time.';
  } else if (authority.includes('Sacral')) {
    return 'You make decisions through your gut response in the moment.';
  } else if (authority.includes('Splenic')) {
    return 'You make decisions through instant intuitive knowing.';
  } else if (authority.includes('Ego') || authority.includes('Heart')) {
    return 'You make decisions through what you have the willpower for.';
  } else if (authority.includes('Self') || authority.includes('G Center')) {
    return 'You make decisions through your sense of identity and direction.';
  } else if (authority.includes('Mental') || authority.includes('Environment')) {
    return 'You make decisions by talking through options with trusted others.';
  } else if (authority.includes('Lunar') || authority.includes('Moon')) {
    return 'You make decisions over a full lunar cycle.';
  }
  return 'Your unique way of arriving at clarity.';
};

const getAuthorityStrength = (authority: string): string => {
  if (authority.includes('Emotional') || authority.includes('Solar Plexus')) {
    return 'Deep emotional wisdom, decisions that stand the test of time.';
  } else if (authority.includes('Sacral')) {
    return 'Reliable gut knowing, consistent life force direction.';
  } else if (authority.includes('Splenic')) {
    return 'Immediate survival intelligence, instinctive accuracy.';
  }
  return 'Reliable clarity when you follow your process.';
};

const getAuthorityChallenge = (authority: string): string => {
  if (authority.includes('Emotional') || authority.includes('Solar Plexus')) {
    return 'Deciding too quickly when emotional, missing clarity.';
  } else if (authority.includes('Sacral')) {
    return 'Overriding gut response with mental reasoning.';
  } else if (authority.includes('Splenic')) {
    return 'Second-guessing the instant knowing.';
  }
  return 'Not trusting your natural process.';
};

const getAuthorityGuidance = (authority: string): string => {
  if (authority.includes('Emotional') || authority.includes('Solar Plexus')) {
    return 'Sleep on important decisions. Notice your emotional wave over time.';
  } else if (authority.includes('Sacral')) {
    return 'Ask yourself yes/no questions. Notice what makes your body say "uh-huh" or "un-un".';
  } else if (authority.includes('Splenic')) {
    return 'Trust your first instinct. The moment passes quickly—honor the immediate hit.';
  }
  return 'Honor your unique clarity process.';
};

export default function ExerciseScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const { forumId, prefilled } = useLocalSearchParams();
  const { prefilledSource, setPrefilledSource } = useForumContext();
  
  // Exercise state
  const [step, setStep] = useState<Step>('intro');
  const [exercise, setExercise] = useState<any | null>(null);
  const [domains, setDomains] = useState<PatternDomain[]>([]);
  
  // Source selection state
  const [sourceType, setSourceType] = useState<SourceType>(null);
  const [mirrorLens, setMirrorLens] = useState<MirrorLens>(null);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [selectedDomainName, setSelectedDomainName] = useState<string>('');
  
  // Human Design state
  const [hdMechanics, setHdMechanics] = useState<HumanDesignMechanics | null>(null);
  const [hdInsights, setHdInsights] = useState<HDInsight[]>([]);
  const [selectedHDInsight, setSelectedHDInsight] = useState<HDInsight | null>(null);
  
  // Reflection state
  const [reflectionText, setReflectionText] = useState('');
  const [isShared, setIsShared] = useState(true); // Default: share with forum
  const [saveToJournal, setSaveToJournal] = useState(false); // Default: don't save to journal
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [loadingHD, setLoadingHD] = useState(false);
  
  // Pattern Graph state (live pattern data)
  const [patternCategories, setPatternCategories] = useState<PatternGraphCategory[]>([]);
  const [patternInterpretation, setPatternInterpretation] = useState<PatternInterpretationResponse | null>(null);
  const [loadingInterpretation, setLoadingInterpretation] = useState(false);

  // Handle prefilled source from forum context
  useEffect(() => {
    if (prefilled === 'true' && prefilledSource) {
      // Set up the exercise with the prefilled source
      setSourceType(prefilledSource.sourceType);
      if (prefilledSource.lens) {
        setMirrorLens(prefilledSource.lens);
      }
      // Create an HD insight from the prefilled source
      const prefilledInsight: HDInsight = {
        id: prefilledSource.insightId,
        name: prefilledSource.insightName,
        value: prefilledSource.insightValue,
        theme: prefilledSource.theme,
        strength: prefilledSource.strength,
        challenge: prefilledSource.challenge,
        guidance: prefilledSource.guidance,
      };
      setSelectedHDInsight(prefilledInsight);
      // Skip directly to guidance step
      setStep('guidance');
    }
  }, [prefilled, prefilledSource]);

  const fetchExercise = useCallback(async () => {
    if (!user?.id || !forumId) return;
    
    setLoading(true);
    try {
      // Fetch exercise and pattern graph data in parallel
      const [exerciseData, patternData] = await Promise.all([
        getForumExercise(forumId as string, user.id),
        getPatternGraph(user.id).catch(() => null)
      ]);
      
      setExercise(exerciseData.exercise);
      setDomains(exerciseData.domains);
      
      // Map pattern graph categories to the same order as domains
      if (patternData?.categories) {
        setPatternCategories(patternData.categories);
      }
    } catch (err) {
      console.error('[Exercise] Error fetching exercise:', err);
      Alert.alert('Error', 'Unable to load exercise.');
    } finally {
      setLoading(false);
    }
  }, [user?.id, forumId]);

  useEffect(() => {
    fetchExercise();
  }, [fetchExercise]);

  // Fetch HD mechanics when user selects Human Design
  const fetchHDMechanics = async () => {
    if (!user?.id) return;
    
    setLoadingHD(true);
    try {
      const data = await getHumanDesignMechanics(user.id);
      setHdMechanics(data);
      setHdInsights(generateHDInsights(data.core_mechanics));
    } catch (err) {
      console.error('[Exercise] Error fetching HD mechanics:', err);
      Alert.alert('Human Design Not Available', 'Your Human Design profile is not set up yet. Please complete onboarding first.');
      setStep('source');
    } finally {
      setLoadingHD(false);
    }
  };

  const handleBack = () => {
    if (step === 'intro') {
      router.back();
    } else if (step === 'source') {
      setStep('intro');
    } else if (step === 'domain') {
      setStep('source');
      setSourceType(null);
    } else if (step === 'mirror-lens') {
      setStep('source');
      setSourceType(null);
    } else if (step === 'mirror-insight') {
      setStep('mirror-lens');
      setMirrorLens(null);
    } else if (step === 'guidance') {
      if (sourceType === 'patterns') {
        setStep('domain');
      } else {
        setStep('mirror-insight');
      }
    } else if (step === 'prompts') {
      setStep('guidance');
    } else if (step === 'privacy') {
      setStep('prompts');
    } else {
      router.back();
    }
  };

  const handleSubmit = async () => {
    if (!user?.id || !forumId) return;
    
    // Must have at least one destination selected
    if (!isShared && !saveToJournal) {
      Alert.alert('No destination', 'Please select at least one destination for your reflection.');
      return;
    }
    
    // Determine domain to submit
    let domainToSubmit = selectedDomain || '';
    let domainNameToSubmit = selectedDomainName;
    
    if (sourceType === 'mirror' && selectedHDInsight) {
      domainToSubmit = `hd_${selectedHDInsight.id}`;
      domainNameToSubmit = `Human Design – ${selectedHDInsight.name}`;
    }
    
    setSubmitting(true);
    try {
      const promises: Promise<any>[] = [];
      
      // Save to Forum if selected
      if (isShared) {
        promises.push(
          submitForumReflection(forumId as string, {
            user_id: user.id,
            selected_domain: domainToSubmit,
            reflection_text: reflectionText,
            is_shared: true, // Always shared when saving to forum
          })
        );
      }
      
      // Save to Journal if selected
      if (saveToJournal) {
        promises.push(
          createJournalEntry(user.id, reflectionText, {
            journal_source: 'forum_exercise',
            pattern_category: domainToSubmit,
            source_domain: domainNameToSubmit,
            source_name: exercise?.title || 'Forum Exercise',
          })
        );
      }
      
      await Promise.all(promises);
      setStep('complete');
    } catch (err) {
      console.error('[Exercise] Error submitting reflection:', err);
      Alert.alert('Error', 'Unable to submit reflection. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleFinish = () => {
    router.replace(`/forums/${forumId}`);
  };

  // Get current step number for indicator
  const getStepNumber = () => {
    const stepMap: Record<Step, number> = {
      'intro': 0,
      'source': 1,
      'domain': 2,
      'mirror-lens': 2,
      'mirror-insight': 3,
      'guidance': 3,
      'prompts': 4,
      'privacy': 5,
      'complete': 6,
    };
    return stepMap[step] || 0;
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.accent} />
        </View>
      </SafeAreaView>
    );
  }

  // Step indicator
  const renderStepIndicator = () => {
    const totalSteps = 5;
    const currentStep = getStepNumber();
    if (step === 'complete') return null;
    
    return (
      <View style={styles.stepIndicator}>
        {Array.from({ length: totalSteps }).map((_, i) => (
          <View
            key={i}
            style={[
              styles.stepDot,
              { backgroundColor: i <= currentStep ? theme.accent : theme.border }
            ]}
          />
        ))}
      </View>
    );
  };

  // INTRO STEP - Now shows live pattern landscape preview with interpretive summaries
  if (step === 'intro') {
    // Helper to get pattern status and summary for intro
    // Note: API returns 'active', 'recurring', 'stable' (not 'emerging', 'quiet')
    const getIntroPatternData = (domainId: string): { status: string; color: string; summary: string | null } => {
      const category = patternCategories.find(c => c.category_id === domainId);
      if (!category) return { status: 'Stable', color: theme.textTertiary, summary: null };
      
      const signalStrength = category.signal_strength;
      if (signalStrength === 'active') {
        return { status: 'Active', color: theme.accent, summary: category.summary };
      } else if (signalStrength === 'recurring' || signalStrength === 'emerging') {
        return { status: 'Recurring', color: '#F59E0B', summary: category.summary };
      } else {
        // 'stable', 'quiet', or any other value
        return { status: 'Stable', color: theme.textTertiary, summary: category.summary };
      }
    };

    // Count active patterns - check for both 'recurring' and 'emerging' for compatibility
    const activeCount = patternCategories.filter(c => c.signal_strength === 'active').length;
    const recurringCount = patternCategories.filter(c => 
      c.signal_strength === 'recurring' || c.signal_strength === 'emerging'
    ).length;

    // Sort domains to show active/recurring first
    const sortedDomains = [...domains].sort((a, b) => {
      const aCategory = patternCategories.find(c => c.category_id === a.id);
      const bCategory = patternCategories.find(c => c.category_id === b.id);
      // Handle both API formats: 'recurring'/'stable' and 'emerging'/'quiet'
      const getOrder = (strength: string | undefined) => {
        if (strength === 'active') return 0;
        if (strength === 'recurring' || strength === 'emerging') return 1;
        return 2; // stable, quiet, or undefined
      };
      const aOrder = aCategory ? getOrder(aCategory.signal_strength) : 2;
      const bOrder = bCategory ? getOrder(bCategory.signal_strength) : 2;
      return aOrder - bOrder;
    });

    // Handle domain selection on intro screen
    const handleIntroDomainSelect = async (domainId: string, domainName: string) => {
      setSelectedDomain(domainId);
      setSelectedDomainName(domainName);
      setPatternInterpretation(null);
      setSourceType('patterns');
      
      if (user?.id) {
        setLoadingInterpretation(true);
        try {
          const interpretation = await getPatternInterpretation(user.id, domainId);
          setPatternInterpretation(interpretation);
        } catch (err) {
          console.error('[Exercise] Error fetching interpretation:', err);
        } finally {
          setLoadingInterpretation(false);
        }
      }
    };

    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          <Text style={[styles.title, { color: theme.text }]}>
            {exercise?.title || 'The Pattern Running Me'}
          </Text>
          
          {/* Different intro text based on selection state */}
          {!selectedDomain ? (
            <Text style={[styles.introText, { color: theme.textSecondary }]}>
              Select a pattern domain below to explore its meaning before reflecting.
            </Text>
          ) : (
            <Text style={[styles.introText, { color: theme.textSecondary }]}>
              Review the interpretation below, then continue to write your reflection.
            </Text>
          )}

          {/* Live Pattern Landscape */}
          <View style={styles.patternLandscapeSection}>
            <View style={styles.landscapeHeaderRow}>
              <Text style={[styles.landscapeSectionTitle, { color: theme.text }]}>Your Pattern Landscape</Text>
              {selectedDomain && (
                <TouchableOpacity 
                  onPress={() => {
                    setSelectedDomain(null);
                    setSelectedDomainName('');
                    setPatternInterpretation(null);
                  }}
                  style={styles.changeSelectionButton}
                >
                  <Text style={[styles.changeSelectionText, { color: theme.accent }]}>Change</Text>
                </TouchableOpacity>
              )}
            </View>
            
            {loading ? (
              <View style={[styles.landscapeLoadingCard, { backgroundColor: theme.surface }]}>
                <ActivityIndicator size="small" color={theme.accent} />
                <Text style={[styles.landscapeLoadingText, { color: theme.textTertiary }]}>
                  Loading your patterns...
                </Text>
              </View>
            ) : (
              <>
                {/* Status summary pills */}
                {(activeCount > 0 || recurringCount > 0) && (
                  <View style={styles.landscapeSummaryRow}>
                    {activeCount > 0 && (
                      <View style={[styles.statusPill, { backgroundColor: theme.accent + '20' }]}>
                        <Text style={[styles.statusPillText, { color: theme.accent }]}>
                          {activeCount} Active
                        </Text>
                      </View>
                    )}
                    {recurringCount > 0 && (
                      <View style={[styles.statusPill, { backgroundColor: '#F59E0B20' }]}>
                        <Text style={[styles.statusPillText, { color: '#F59E0B' }]}>
                          {recurringCount} Recurring
                        </Text>
                      </View>
                    )}
                  </View>
                )}

                {/* Pattern domain cards - with inline preview below selected card */}
                <View style={styles.landscapeDomainCards}>
                  {sortedDomains.slice(0, 7).map((domain) => {
                    const data = getIntroPatternData(domain.id);
                    const isHighlighted = data.status === 'Active' || data.status === 'Recurring';
                    const isSelected = selectedDomain === domain.id;
                    
                    return (
                      <React.Fragment key={domain.id}>
                        <TouchableOpacity 
                          style={[
                            styles.landscapeDomainCard,
                            { 
                              backgroundColor: theme.surface,
                              borderColor: isSelected ? theme.accent : (isHighlighted ? data.color + '40' : theme.border),
                              borderWidth: isSelected ? 2 : StyleSheet.hairlineWidth,
                              borderLeftWidth: isSelected ? 2 : (isHighlighted ? 3 : StyleSheet.hairlineWidth),
                              borderLeftColor: isSelected ? theme.accent : (isHighlighted ? data.color : theme.border),
                            }
                          ]}
                          onPress={() => handleIntroDomainSelect(domain.id, domain.name)}
                          activeOpacity={0.7}
                        >
                          <View style={styles.landscapeDomainHeader}>
                            <Text style={[styles.landscapeDomainName, { color: theme.text }]}>
                              {domain.name}
                            </Text>
                            <View style={styles.landscapeDomainHeaderRight}>
                              <View style={[styles.landscapeStatusBadge, { backgroundColor: data.color + '15' }]}>
                                <Text style={[styles.landscapeStatusText, { color: data.color }]}>
                                  {data.status}
                                </Text>
                              </View>
                              {isSelected && (
                                <Text style={[styles.selectedCheckmark, { color: theme.accent }]}>✓</Text>
                              )}
                            </View>
                          </View>
                          {/* Only show summary if NOT selected - interpretation replaces it */}
                          {!isSelected && data.summary && (
                            <Text 
                              style={[styles.landscapeDomainSummary, { color: theme.textSecondary }]}
                              numberOfLines={2}
                            >
                              {data.summary}
                            </Text>
                          )}
                        </TouchableOpacity>

                        {/* Interpretation Preview - renders directly below selected card */}
                        {isSelected && (
                          <View style={[styles.inlineInterpretationPreview, { backgroundColor: theme.surface, borderColor: theme.accent }]}>
                            {loadingInterpretation ? (
                              <View style={styles.interpretationLoading}>
                                <ActivityIndicator size="small" color={theme.accent} />
                                <Text style={[styles.interpretationLoadingText, { color: theme.textTertiary }]}>
                                  Loading pattern insights...
                                </Text>
                              </View>
                            ) : patternInterpretation?.interpretation ? (
                              <>
                                {/* Story Section */}
                                {patternInterpretation.interpretation.story && (
                                  <View style={styles.inlineInterpretationSection}>
                                    <Text style={[styles.inlineInterpretationTitle, { color: theme.text }]}>
                                      Story
                                    </Text>
                                    <Text style={[styles.inlineInterpretationText, { color: theme.textSecondary }]}>
                                      {patternInterpretation.interpretation.story}
                                    </Text>
                                  </View>
                                )}
                                
                                {/* Challenge Section */}
                                {patternInterpretation.interpretation.challenge && (
                                  <View style={[styles.inlineInterpretationSection, { borderTopColor: theme.border, borderTopWidth: StyleSheet.hairlineWidth, marginTop: 12, paddingTop: 12 }]}>
                                    <Text style={[styles.inlineInterpretationTitle, { color: theme.text }]}>
                                      Challenge
                                    </Text>
                                    <Text style={[styles.inlineInterpretationText, { color: theme.textSecondary }]}>
                                      {patternInterpretation.interpretation.challenge}
                                    </Text>
                                  </View>
                                )}
                                
                                {/* Genius Section */}
                                {patternInterpretation.interpretation.genius && (
                                  <View style={[styles.inlineInterpretationSection, { borderTopColor: theme.border, borderTopWidth: StyleSheet.hairlineWidth, marginTop: 12, paddingTop: 12 }]}>
                                    <Text style={[styles.inlineInterpretationTitle, { color: theme.text }]}>
                                      Genius
                                    </Text>
                                    <Text style={[styles.inlineInterpretationText, { color: theme.textSecondary }]}>
                                      {patternInterpretation.interpretation.genius}
                                    </Text>
                                  </View>
                                )}
                                
                                {/* Why This May Be Active */}
                                {patternInterpretation.signal_strength && (patternInterpretation.signal_strength === 'active' || patternInterpretation.signal_strength === 'recurring') && (
                                  <View style={[styles.inlineWhyActive, { backgroundColor: theme.accent + '10', marginTop: 12 }]}>
                                    <Text style={[styles.inlineWhyActiveText, { color: theme.accent }]}>
                                      This pattern has signals showing up across your reflections right now.
                                    </Text>
                                  </View>
                                )}

                                {/* Continue Button - inside the preview card */}
                                <TouchableOpacity
                                  style={[styles.inlineContinueButton, { backgroundColor: theme.buttonPrimaryBg, marginTop: 16 }]}
                                  onPress={() => {
                                    setStep('guidance');
                                  }}
                                >
                                  <Text style={[styles.inlineContinueButtonText, { color: theme.buttonPrimaryText }]}>
                                    Continue to Reflection
                                  </Text>
                                </TouchableOpacity>
                              </>
                            ) : (
                              <Text style={[styles.interpretationEmpty, { color: theme.textTertiary }]}>
                                Unable to load interpretation
                              </Text>
                            )}
                          </View>
                        )}
                      </React.Fragment>
                    );
                  })}
                </View>
              </>
            )}
          </View>

          {/* Mirror insights alternative - only show if no domain selected */}
          {!selectedDomain && (
            <TouchableOpacity
              style={styles.alternateOption}
              onPress={() => {
                setSourceType('mirror');
                setStep('mirror-lens');
              }}
            >
              <Text style={[styles.alternateOptionText, { color: theme.textTertiary }]}>
                Or reflect from Mirror insights instead →
              </Text>
            </TouchableOpacity>
          )}
        </ScrollView>
      </SafeAreaView>
    );
  }

  // SOURCE SELECTION STEP
  if (step === 'source') {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          {renderStepIndicator()}
          
          <Text style={[styles.stepTitle, { color: theme.textTertiary }]}>STEP 1</Text>
          <Text style={[styles.title, { color: theme.text }]}>Choose where your reflection comes from</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Select a source that feels relevant to what's active in your life right now.
          </Text>

          <View style={styles.sourceOptions}>
            <TouchableOpacity
              style={[
                styles.sourceCard,
                { 
                  backgroundColor: theme.surface, 
                  borderColor: sourceType === 'patterns' ? theme.accent : theme.border,
                  borderWidth: sourceType === 'patterns' ? 2 : StyleSheet.hairlineWidth,
                }
              ]}
              onPress={() => setSourceType('patterns')}
            >
              <Text style={[styles.sourceIcon, { color: theme.accent }]}>◆</Text>
              <Text style={[styles.sourceTitle, { color: theme.text }]}>Patterns</Text>
              <Text style={[styles.sourceDesc, { color: theme.textSecondary }]}>
                Reflect from life domains like energy, relationships, identity, or growth
              </Text>
              {sourceType === 'patterns' && (
                <Text style={[styles.checkmark, { color: theme.accent }]}>✓</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.sourceCard,
                { 
                  backgroundColor: theme.surface, 
                  borderColor: sourceType === 'mirror' ? theme.accent : theme.border,
                  borderWidth: sourceType === 'mirror' ? 2 : StyleSheet.hairlineWidth,
                }
              ]}
              onPress={() => setSourceType('mirror')}
            >
              <Text style={[styles.sourceIcon, { color: theme.accent }]}>◎</Text>
              <Text style={[styles.sourceTitle, { color: theme.text }]}>My Mirror</Text>
              <Text style={[styles.sourceDesc, { color: theme.textSecondary }]}>
                Reflect from your personal insights like Human Design, Enneagram, or Daily Insight
              </Text>
              {sourceType === 'mirror' && (
                <Text style={[styles.checkmark, { color: theme.accent }]}>✓</Text>
              )}
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[
              styles.primaryButton, 
              { backgroundColor: sourceType ? theme.buttonPrimaryBg : theme.border }
            ]}
            onPress={() => {
              if (sourceType === 'patterns') {
                setStep('domain');
              } else if (sourceType === 'mirror') {
                setStep('mirror-lens');
              }
            }}
            disabled={!sourceType}
          >
            <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>
              Continue
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // DOMAIN SELECTION STEP (for Patterns source)
  // Now shows live pattern status like the Patterns page
  if (step === 'domain') {
    // Helper to get pattern status from pattern graph
    const getPatternStatus = (domainId: string): { status: string; color: string; summary?: string } => {
      const category = patternCategories.find(c => c.category_id === domainId);
      if (!category) return { status: '', color: theme.textTertiary };
      
      const signalStrength = category.signal_strength;
      switch (signalStrength) {
        case 'active':
          return { status: 'Active', color: theme.accent, summary: category.summary };
        case 'emerging':
          return { status: 'Recurring', color: '#F59E0B', summary: category.summary };
        case 'quiet':
          return { status: 'Stable', color: theme.textTertiary, summary: category.summary };
        default:
          return { status: '', color: theme.textTertiary };
      }
    };

    // Fetch interpretation when domain is selected
    const handleDomainSelect = async (domainId: string, domainName: string) => {
      setSelectedDomain(domainId);
      setSelectedDomainName(domainName);
      setPatternInterpretation(null);
      
      if (user?.id) {
        setLoadingInterpretation(true);
        try {
          const interpretation = await getPatternInterpretation(user.id, domainId);
          setPatternInterpretation(interpretation);
        } catch (err) {
          console.error('[Exercise] Error fetching interpretation:', err);
        } finally {
          setLoadingInterpretation(false);
        }
      }
    };

    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          {renderStepIndicator()}
          
          <Text style={[styles.stepTitle, { color: theme.textTertiary }]}>STEP 2</Text>
          <Text style={[styles.title, { color: theme.text }]}>Your Pattern Landscape</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Choose the domain that feels most present for you right now. These are your live pattern signals.
          </Text>

          <View style={styles.domainsList}>
            {domains.map((domain) => {
              const patternStatus = getPatternStatus(domain.id);
              const isSelected = selectedDomain === domain.id;
              
              return (
                <TouchableOpacity
                  key={domain.id}
                  style={[
                    styles.domainCardLive,
                    { 
                      backgroundColor: theme.surface, 
                      borderColor: isSelected ? theme.accent : theme.border,
                      borderWidth: isSelected ? 2 : StyleSheet.hairlineWidth,
                    }
                  ]}
                  onPress={() => handleDomainSelect(domain.id, domain.name)}
                >
                  <View style={styles.domainCardHeader}>
                    <Text style={[styles.domainName, { color: theme.text }]}>
                      {domain.name}
                    </Text>
                    {patternStatus.status ? (
                      <View style={[styles.statusBadge, { backgroundColor: patternStatus.color + '20' }]}>
                        <Text style={[styles.statusText, { color: patternStatus.color }]}>
                          {patternStatus.status}
                        </Text>
                      </View>
                    ) : null}
                    {isSelected && (
                      <Text style={[styles.checkmark, { color: theme.accent }]}>✓</Text>
                    )}
                  </View>
                  {patternStatus.summary && (
                    <Text style={[styles.domainSummary, { color: theme.textSecondary }]} numberOfLines={2}>
                      {patternStatus.summary}
                    </Text>
                  )}
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Show interpretation preview when domain selected */}
          {selectedDomain && (
            <View style={[styles.interpretationPreview, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              {loadingInterpretation ? (
                <View style={styles.interpretationLoading}>
                  <ActivityIndicator size="small" color={theme.accent} />
                  <Text style={[styles.interpretationLoadingText, { color: theme.textTertiary }]}>
                    Loading pattern insights...
                  </Text>
                </View>
              ) : patternInterpretation?.interpretation ? (
                <>
                  <View style={styles.interpretationHeader}>
                    <Text style={[styles.interpretationLabel, { color: theme.textTertiary }]}>
                      ABOUT THIS PATTERN
                    </Text>
                    {patternInterpretation.signal_strength && (
                      <View style={[
                        styles.signalStrengthBadge, 
                        { backgroundColor: patternInterpretation.signal_strength === 'active' ? theme.accent + '20' : '#F59E0B20' }
                      ]}>
                        <Text style={[
                          styles.signalStrengthText, 
                          { color: patternInterpretation.signal_strength === 'active' ? theme.accent : '#F59E0B' }
                        ]}>
                          {patternInterpretation.signal_strength === 'active' ? 'Active' : 
                           patternInterpretation.signal_strength === 'emerging' ? 'Recurring' : 'Stable'}
                        </Text>
                      </View>
                    )}
                  </View>
                  
                  {/* Story Section */}
                  {patternInterpretation.interpretation.story && (
                    <View style={styles.interpretationSection}>
                      <Text style={[styles.interpretationSectionTitle, { color: theme.text }]}>
                        Story
                      </Text>
                      <Text style={[styles.interpretationSectionText, { color: theme.textSecondary }]}>
                        {patternInterpretation.interpretation.story}
                      </Text>
                    </View>
                  )}
                  
                  {/* Challenge Section */}
                  {patternInterpretation.interpretation.challenge && (
                    <View style={[styles.interpretationSection, { borderTopColor: theme.border, borderTopWidth: StyleSheet.hairlineWidth }]}>
                      <Text style={[styles.interpretationSectionTitle, { color: theme.text }]}>
                        Challenge
                      </Text>
                      <Text style={[styles.interpretationSectionText, { color: theme.textSecondary }]}>
                        {patternInterpretation.interpretation.challenge}
                      </Text>
                    </View>
                  )}
                  
                  {/* Genius Section */}
                  {patternInterpretation.interpretation.genius && (
                    <View style={[styles.interpretationSection, { borderTopColor: theme.border, borderTopWidth: StyleSheet.hairlineWidth }]}>
                      <Text style={[styles.interpretationSectionTitle, { color: theme.text }]}>
                        Genius
                      </Text>
                      <Text style={[styles.interpretationSectionText, { color: theme.textSecondary }]}>
                        {patternInterpretation.interpretation.genius}
                      </Text>
                    </View>
                  )}
                  
                  {/* Why This May Be Active - Signals hint */}
                  {patternInterpretation.signal_strength && (patternInterpretation.signal_strength === 'active' || patternInterpretation.signal_strength === 'recurring') && (
                    <View style={[styles.whyActiveHint, { backgroundColor: theme.accent + '10' }]}>
                      <Text style={[styles.whyActiveHintText, { color: theme.accent }]}>
                        This pattern has signals showing up across your reflections right now.
                      </Text>
                    </View>
                  )}
                </>
              ) : (
                <Text style={[styles.interpretationEmpty, { color: theme.textTertiary }]}>
                  Tap Continue to reflect on {selectedDomainName}
                </Text>
              )}
            </View>
          )}

          <TouchableOpacity
            style={[
              styles.primaryButton, 
              { backgroundColor: selectedDomain ? theme.buttonPrimaryBg : theme.border }
            ]}
            onPress={() => setStep('guidance')}
            disabled={!selectedDomain}
          >
            <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>
              Continue
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // MIRROR LENS SELECTION STEP
  if (step === 'mirror-lens') {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          {renderStepIndicator()}
          
          <Text style={[styles.stepTitle, { color: theme.textTertiary }]}>STEP 2</Text>
          <Text style={[styles.title, { color: theme.text }]}>Choose a Mirror insight</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Which lens do you want to reflect from?
          </Text>

          <View style={styles.lensOptions}>
            <TouchableOpacity
              style={[
                styles.lensCard,
                { 
                  backgroundColor: theme.surface, 
                  borderColor: mirrorLens === 'human-design' ? theme.accent : theme.border,
                  borderWidth: mirrorLens === 'human-design' ? 2 : StyleSheet.hairlineWidth,
                }
              ]}
              onPress={() => setMirrorLens('human-design')}
            >
              <Text style={[styles.lensTitle, { color: theme.text }]}>Human Design</Text>
              <Text style={[styles.lensDesc, { color: theme.textSecondary }]}>
                Type, Strategy, Authority, Profile
              </Text>
              {mirrorLens === 'human-design' && (
                <Text style={[styles.checkmark, { color: theme.accent }]}>✓</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.lensCard,
                { 
                  backgroundColor: theme.surface, 
                  borderColor: mirrorLens === 'enneagram' ? theme.accent : theme.border,
                  borderWidth: mirrorLens === 'enneagram' ? 2 : StyleSheet.hairlineWidth,
                  opacity: 0.5,
                }
              ]}
              disabled
            >
              <Text style={[styles.lensTitle, { color: theme.text }]}>Enneagram</Text>
              <Text style={[styles.lensDesc, { color: theme.textSecondary }]}>
                Coming soon
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.lensCard,
                { 
                  backgroundColor: theme.surface, 
                  borderColor: mirrorLens === 'daily-insight' ? theme.accent : theme.border,
                  borderWidth: mirrorLens === 'daily-insight' ? 2 : StyleSheet.hairlineWidth,
                  opacity: 0.5,
                }
              ]}
              disabled
            >
              <Text style={[styles.lensTitle, { color: theme.text }]}>Daily Insight</Text>
              <Text style={[styles.lensDesc, { color: theme.textSecondary }]}>
                Coming soon
              </Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[
              styles.primaryButton, 
              { backgroundColor: mirrorLens ? theme.buttonPrimaryBg : theme.border }
            ]}
            onPress={() => {
              if (mirrorLens === 'human-design') {
                fetchHDMechanics();
                setStep('mirror-insight');
              }
            }}
            disabled={!mirrorLens}
          >
            <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>
              Continue
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // MIRROR INSIGHT SELECTION (Human Design)
  if (step === 'mirror-insight') {
    if (loadingHD) {
      return (
        <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.accent} />
            <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
              Loading your Human Design...
            </Text>
          </View>
        </SafeAreaView>
      );
    }

    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          {renderStepIndicator()}
          
          <Text style={[styles.stepTitle, { color: theme.textTertiary }]}>STEP 3</Text>
          <Text style={[styles.title, { color: theme.text }]}>Choose a Human Design insight</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Which aspect feels most relevant to reflect on?
          </Text>

          <View style={styles.hdInsightsList}>
            {hdInsights.map((insight) => (
              <TouchableOpacity
                key={insight.id}
                style={[
                  styles.hdInsightCard,
                  { 
                    backgroundColor: theme.surface, 
                    borderColor: selectedHDInsight?.id === insight.id ? theme.accent : theme.border,
                    borderWidth: selectedHDInsight?.id === insight.id ? 2 : StyleSheet.hairlineWidth,
                  }
                ]}
                onPress={() => setSelectedHDInsight(insight)}
              >
                <View style={styles.hdInsightHeader}>
                  <Text style={[styles.hdInsightName, { color: theme.text }]}>
                    {insight.name}
                  </Text>
                  <Text style={[styles.hdInsightValue, { color: theme.accent }]}>
                    {insight.value}
                  </Text>
                </View>
                {selectedHDInsight?.id === insight.id && (
                  <Text style={[styles.checkmark, { color: theme.accent }]}>✓</Text>
                )}
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity
            style={[
              styles.primaryButton, 
              { backgroundColor: selectedHDInsight ? theme.buttonPrimaryBg : theme.border }
            ]}
            onPress={() => setStep('guidance')}
            disabled={!selectedHDInsight}
          >
            <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>
              Continue
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // GUIDANCE STEP
  if (step === 'guidance') {
    const isHDSource = sourceType === 'mirror' && selectedHDInsight;
    
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          {renderStepIndicator()}
          
          {isHDSource ? (
            <>
              <View style={[styles.guidanceBadge, { backgroundColor: theme.accent + '20' }]}>
                <Text style={[styles.guidanceBadgeText, { color: theme.accent }]}>
                  Human Design – {selectedHDInsight.name}
                </Text>
              </View>
              
              <Text style={[styles.guidanceValue, { color: theme.text }]}>
                {selectedHDInsight.value}
              </Text>
              
              <View style={[styles.guidanceCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                <View style={styles.guidanceSection}>
                  <Text style={[styles.guidanceLabel, { color: theme.textTertiary }]}>THEME</Text>
                  <Text style={[styles.guidanceText, { color: theme.textSecondary }]}>
                    {selectedHDInsight.theme}
                  </Text>
                </View>
                
                <View style={styles.guidanceSection}>
                  <Text style={[styles.guidanceLabel, { color: theme.textTertiary }]}>STRENGTH</Text>
                  <Text style={[styles.guidanceText, { color: theme.textSecondary }]}>
                    {selectedHDInsight.strength}
                  </Text>
                </View>
                
                <View style={styles.guidanceSection}>
                  <Text style={[styles.guidanceLabel, { color: theme.textTertiary }]}>COMMON CHALLENGE</Text>
                  <Text style={[styles.guidanceText, { color: theme.textSecondary }]}>
                    {selectedHDInsight.challenge}
                  </Text>
                </View>
                
                <View style={styles.guidanceSection}>
                  <Text style={[styles.guidanceLabel, { color: theme.textTertiary }]}>PRACTICAL GUIDANCE</Text>
                  <Text style={[styles.guidanceText, { color: theme.textSecondary }]}>
                    {selectedHDInsight.guidance}
                  </Text>
                </View>
              </View>
            </>
          ) : (
            <>
              <View style={[styles.guidanceBadge, { backgroundColor: theme.accent + '20' }]}>
                <Text style={[styles.guidanceBadgeText, { color: theme.accent }]}>
                  {selectedDomainName}
                </Text>
              </View>
              
              <View style={[styles.guidanceCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                <Text style={[styles.guidanceIntro, { color: theme.textSecondary }]}>
                  You'll reflect on how this pattern domain is showing up in your life right now.
                </Text>
              </View>
            </>
          )}

          <TouchableOpacity
            style={[styles.primaryButton, { backgroundColor: theme.buttonPrimaryBg }]}
            onPress={() => setStep('prompts')}
          >
            <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>
              Continue to Reflection
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // PROMPTS / WRITING STEP
  if (step === 'prompts') {
    const isHDSource = sourceType === 'mirror' && selectedHDInsight;
    
    const hdPrompts = [
      "Where is this showing up in your life right now?",
      "What relationship, leadership situation, or personal pattern does this bring to mind?",
      "What happens when you are in alignment with this?",
      "What happens when you override it?",
    ];
    
    const patternPrompts = exercise?.prompts || [
      "Where is this pattern showing up in your life right now?",
      "What situation from the last 30–60 days best represents it?",
      "How has this pattern helped you succeed?",
      "Where might this same pattern now be limiting you?",
      "If this pattern softened by 10%, what might change?"
    ];
    
    const prompts = isHDSource ? hdPrompts : patternPrompts;
    const sourceName = isHDSource 
      ? `Human Design – ${selectedHDInsight?.name}` 
      : selectedDomainName;

    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={{ flex: 1 }}
        >
          <View style={styles.header}>
            <TouchableOpacity onPress={handleBack} style={styles.backButton}>
              <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
            {renderStepIndicator()}
            
            <Text style={[styles.stepTitle, { color: theme.textTertiary }]}>FINAL STEP</Text>
            <Text style={[styles.title, { color: theme.text }]}>Reflect</Text>
            <View style={[styles.guidanceBadge, { backgroundColor: theme.accent + '20' }]}>
              <Text style={[styles.guidanceBadgeText, { color: theme.accent }]}>
                {sourceName}
              </Text>
            </View>

            <View style={[styles.promptsBox, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.promptsLabel, { color: theme.textTertiary }]}>REFLECTION PROMPTS</Text>
              {prompts.map((prompt: string, index: number) => (
                <Text key={index} style={[styles.promptItem, { color: theme.textSecondary }]}>
                  {index + 1}. {prompt}
                </Text>
              ))}
            </View>

            <Text style={[styles.label, { color: theme.text }]}>Your Reflection</Text>
            <TextInput
              style={[styles.textArea, { 
                backgroundColor: theme.inputBg, 
                borderColor: theme.inputBorder,
                color: theme.text 
              }]}
              placeholder="Write your reflection here... You can address any or all of the prompts above."
              placeholderTextColor={theme.inputPlaceholder}
              value={reflectionText}
              onChangeText={setReflectionText}
              multiline
              numberOfLines={8}
              textAlignVertical="top"
            />
            
            {reflectionText.trim().length > 0 && reflectionText.trim().length < 20 && (
              <Text style={[styles.hint, { color: theme.textTertiary }]}>
                Please write at least 20 characters
              </Text>
            )}

            {/* Destination Selection */}
            <Text style={[styles.label, { color: theme.text, marginTop: 24 }]}>Save To</Text>
            
            <View style={styles.destinationOptions}>
              {/* This Forum checkbox */}
              <TouchableOpacity
                style={[
                  styles.destinationOption,
                  { 
                    backgroundColor: theme.surface, 
                    borderColor: isShared ? theme.accent : theme.border,
                    borderWidth: isShared ? 2 : StyleSheet.hairlineWidth,
                  }
                ]}
                onPress={() => setIsShared(!isShared)}
                activeOpacity={0.7}
              >
                <View style={[
                  styles.checkbox,
                  { 
                    borderColor: isShared ? theme.accent : theme.border,
                    backgroundColor: isShared ? theme.accent : 'transparent'
                  }
                ]}>
                  {isShared && (
                    <Text style={styles.checkboxCheck}>✓</Text>
                  )}
                </View>
                <View style={styles.destinationTextContainer}>
                  <Text style={[styles.destinationOptionTitle, { color: theme.text }]}>
                    This Forum
                  </Text>
                  <Text style={[styles.destinationOptionDesc, { color: theme.textSecondary }]}>
                    Share with other forum members
                  </Text>
                </View>
              </TouchableOpacity>

              {/* My Journal checkbox */}
              <TouchableOpacity
                style={[
                  styles.destinationOption,
                  { 
                    backgroundColor: theme.surface, 
                    borderColor: saveToJournal ? theme.accent : theme.border,
                    borderWidth: saveToJournal ? 2 : StyleSheet.hairlineWidth,
                  }
                ]}
                onPress={() => setSaveToJournal(!saveToJournal)}
                activeOpacity={0.7}
              >
                <View style={[
                  styles.checkbox,
                  { 
                    borderColor: saveToJournal ? theme.accent : theme.border,
                    backgroundColor: saveToJournal ? theme.accent : 'transparent'
                  }
                ]}>
                  {saveToJournal && (
                    <Text style={styles.checkboxCheck}>✓</Text>
                  )}
                </View>
                <View style={styles.destinationTextContainer}>
                  <Text style={[styles.destinationOptionTitle, { color: theme.text }]}>
                    My Journal
                  </Text>
                  <Text style={[styles.destinationOptionDesc, { color: theme.textSecondary }]}>
                    Save privately for personal reflection
                  </Text>
                </View>
              </TouchableOpacity>
            </View>

            {!isShared && !saveToJournal && (
              <Text style={[styles.hint, { color: theme.warning || '#F59E0B' }]}>
                Please select at least one destination
              </Text>
            )}

            <TouchableOpacity
              style={[
                styles.primaryButton, 
                { backgroundColor: (reflectionText.trim().length >= 20 && (isShared || saveToJournal)) ? theme.buttonPrimaryBg : theme.border }
              ]}
              onPress={handleSubmit}
              disabled={reflectionText.trim().length < 20 || (!isShared && !saveToJournal) || submitting}
            >
              {submitting ? (
                <ActivityIndicator color={theme.buttonPrimaryText} />
              ) : (
                <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>
                  Submit Reflection
                </Text>
              )}
            </TouchableOpacity>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    );
  }

  // PRIVACY STEP - Kept for backwards compatibility but no longer used in main flow
  // PRIVACY STEP - Now uses checkboxes for destination selection
  if (step === 'privacy') {
    const canSubmit = (isShared || saveToJournal) && reflectionText.trim().length >= 20;
    
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          {renderStepIndicator()}
          
          <Text style={[styles.stepTitle, { color: theme.textTertiary }]}>FINAL STEP</Text>
          <Text style={[styles.title, { color: theme.text }]}>Save Your Reflection</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Choose where to save your reflection. You can select one or both.
          </Text>

          <View style={styles.destinationOptions}>
            {/* This Forum checkbox */}
            <TouchableOpacity
              style={[
                styles.destinationOption,
                { 
                  backgroundColor: theme.surface, 
                  borderColor: isShared ? theme.accent : theme.border,
                  borderWidth: isShared ? 2 : StyleSheet.hairlineWidth,
                }
              ]}
              onPress={() => setIsShared(!isShared)}
              activeOpacity={0.7}
            >
              <View style={[
                styles.checkbox,
                { 
                  borderColor: isShared ? theme.accent : theme.border,
                  backgroundColor: isShared ? theme.accent : 'transparent'
                }
              ]}>
                {isShared && (
                  <Text style={styles.checkboxCheck}>✓</Text>
                )}
              </View>
              <View style={styles.destinationTextContainer}>
                <Text style={[styles.destinationOptionTitle, { color: theme.text }]}>
                  This Forum
                </Text>
                <Text style={[styles.destinationOptionDesc, { color: theme.textSecondary }]}>
                  Share with other forum members. Builds trust and connection.
                </Text>
              </View>
            </TouchableOpacity>

            {/* My Journal checkbox */}
            <TouchableOpacity
              style={[
                styles.destinationOption,
                { 
                  backgroundColor: theme.surface, 
                  borderColor: saveToJournal ? theme.accent : theme.border,
                  borderWidth: saveToJournal ? 2 : StyleSheet.hairlineWidth,
                }
              ]}
              onPress={() => setSaveToJournal(!saveToJournal)}
              activeOpacity={0.7}
            >
              <View style={[
                styles.checkbox,
                { 
                  borderColor: saveToJournal ? theme.accent : theme.border,
                  backgroundColor: saveToJournal ? theme.accent : 'transparent'
                }
              ]}>
                {saveToJournal && (
                  <Text style={styles.checkboxCheck}>✓</Text>
                )}
              </View>
              <View style={styles.destinationTextContainer}>
                <Text style={[styles.destinationOptionTitle, { color: theme.text }]}>
                  My Journal
                </Text>
                <Text style={[styles.destinationOptionDesc, { color: theme.textSecondary }]}>
                  Save privately for personal reflection. Only you can see it.
                </Text>
              </View>
            </TouchableOpacity>
          </View>

          {!isShared && !saveToJournal && (
            <Text style={[styles.hint, { color: theme.warning || '#F59E0B' }]}>
              Please select at least one destination
            </Text>
          )}

          <TouchableOpacity
            style={[
              styles.primaryButton, 
              { backgroundColor: canSubmit ? theme.buttonPrimaryBg : theme.border }
            ]}
            onPress={handleSubmit}
            disabled={!canSubmit || submitting}
          >
            {submitting ? (
              <ActivityIndicator color={theme.buttonPrimaryText} />
            ) : (
              <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>
                Submit Reflection
              </Text>
            )}
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // COMPLETE STEP
  if (step === 'complete') {
    // Build completion message based on destinations
    let completionMessage = '';
    if (isShared && saveToJournal) {
      completionMessage = 'Your reflection has been shared with the forum and saved to your journal.';
    } else if (isShared) {
      completionMessage = 'Your reflection has been shared with the forum.';
    } else if (saveToJournal) {
      completionMessage = 'Your reflection has been saved to your journal.';
    }

    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.completeContent}>
          <Text style={styles.completeIcon}>✓</Text>
          <Text style={[styles.completeTitle, { color: theme.text }]}>
            Reflection Submitted
          </Text>
          <Text style={[styles.completeSubtitle, { color: theme.textSecondary }]}>
            {completionMessage}
          </Text>
          
          <TouchableOpacity
            style={[styles.primaryButton, { backgroundColor: theme.buttonPrimaryBg, marginTop: 32 }]}
            onPress={handleFinish}
          >
            <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>
              Return to Forum
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return null;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  backButton: {
    minWidth: 80,
  },
  backText: {
    fontSize: 16,
    fontWeight: '500',
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  stepIndicator: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 24,
  },
  stepDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  stepTitle: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 8,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 24,
  },
  introText: {
    fontSize: 16,
    lineHeight: 24,
    marginBottom: 24,
  },
  // Pattern Landscape Preview (Intro screen)
  patternLandscapePreview: {
    padding: 20,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 20,
  },
  landscapeTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 16,
  },
  landscapeLoading: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 12,
  },
  landscapeLoadingText: {
    fontSize: 14,
  },
  landscapeSummary: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  statusPill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  statusPillText: {
    fontSize: 13,
    fontWeight: '600',
  },
  landscapeQuiet: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  // New card-based pattern landscape styles
  patternLandscapeSection: {
    marginBottom: 20,
  },
  landscapeHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  landscapeSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  changeSelectionButton: {
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  changeSelectionText: {
    fontSize: 14,
    fontWeight: '500',
  },
  landscapeLoadingCard: {
    padding: 24,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  landscapeSummaryRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  landscapeDomainCards: {
    gap: 10,
  },
  landscapeDomainCard: {
    padding: 14,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  landscapeDomainHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  landscapeDomainHeaderRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  selectedCheckmark: {
    fontSize: 16,
    fontWeight: '600',
  },
  landscapeDomainSummary: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  // Intro screen interpretation preview (legacy - kept for compatibility)
  introInterpretationPreview: {
    marginTop: 20,
    padding: 20,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
  },
  interpretationDomainTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  // Inline interpretation preview - directly below selected card
  inlineInterpretationPreview: {
    marginTop: 4,
    marginBottom: 10,
    marginLeft: 8,
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderTopWidth: 0,
    borderTopLeftRadius: 0,
    borderTopRightRadius: 0,
  },
  inlineInterpretationSection: {
    marginBottom: 4,
  },
  inlineInterpretationTitle: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  inlineInterpretationText: {
    fontSize: 14,
    lineHeight: 20,
  },
  inlineWhyActive: {
    padding: 10,
    borderRadius: 8,
  },
  inlineWhyActiveText: {
    fontSize: 13,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  inlineContinueButton: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 10,
    alignItems: 'center',
  },
  inlineContinueButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  // Legacy styles (kept for compatibility)
  landscapeDomains: {
    gap: 8,
  },
  landscapeDomainRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  landscapeDomainName: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
  },
  landscapeStatusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  landscapeStatusText: {
    fontSize: 12,
    fontWeight: '500',
  },
  alternateOption: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  alternateOptionText: {
    fontSize: 14,
  },
  infoBox: {
    padding: 20,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 32,
  },
  infoTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 12,
  },
  infoItem: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 4,
  },
  primaryButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  // Source selection
  sourceOptions: {
    gap: 12,
    marginBottom: 24,
  },
  sourceCard: {
    padding: 20,
    borderRadius: 14,
    position: 'relative',
  },
  sourceIcon: {
    fontSize: 28,
    marginBottom: 12,
  },
  sourceTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 6,
  },
  sourceDesc: {
    fontSize: 14,
    lineHeight: 20,
    paddingRight: 24,
  },
  checkmark: {
    position: 'absolute',
    top: 16,
    right: 16,
    fontSize: 20,
    fontWeight: '600',
  },
  // Domain selection
  domainsList: {
    gap: 10,
    marginBottom: 24,
  },
  domainCard: {
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  domainCardLive: {
    padding: 16,
    borderRadius: 12,
  },
  domainCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  domainName: {
    fontSize: 16,
    fontWeight: '500',
    flex: 1,
  },
  domainSummary: {
    fontSize: 13,
    lineHeight: 18,
    marginTop: 8,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  // Interpretation Preview
  interpretationPreview: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 24,
  },
  interpretationLoading: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    paddingVertical: 8,
  },
  interpretationLoadingText: {
    fontSize: 13,
  },
  interpretationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  interpretationLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
  },
  signalStrengthBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
  },
  signalStrengthText: {
    fontSize: 11,
    fontWeight: '600',
  },
  interpretationText: {
    fontSize: 14,
    lineHeight: 21,
  },
  // Story/Challenge/Genius sections
  interpretationSection: {
    paddingTop: 14,
    marginTop: 14,
  },
  interpretationSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  interpretationSectionText: {
    fontSize: 14,
    lineHeight: 21,
  },
  whyActiveHint: {
    marginTop: 16,
    padding: 12,
    borderRadius: 8,
  },
  whyActiveHintText: {
    fontSize: 13,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  whyActiveSection: {
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  whyActiveLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
    textTransform: 'uppercase',
  },
  whyActiveText: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  interpretationSignal: {
    fontSize: 12,
    fontWeight: '500',
    marginTop: 10,
  },
  interpretationEmpty: {
    fontSize: 13,
    fontStyle: 'italic',
    textAlign: 'center',
    paddingVertical: 8,
  },
  // Lens selection
  lensOptions: {
    gap: 10,
    marginBottom: 24,
  },
  lensCard: {
    padding: 16,
    borderRadius: 12,
    position: 'relative',
  },
  lensTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  lensDesc: {
    fontSize: 13,
    paddingRight: 24,
  },
  // HD insights list
  hdInsightsList: {
    gap: 10,
    marginBottom: 24,
  },
  hdInsightCard: {
    padding: 16,
    borderRadius: 12,
    position: 'relative',
  },
  hdInsightHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingRight: 30,
  },
  hdInsightName: {
    fontSize: 15,
    fontWeight: '600',
  },
  hdInsightValue: {
    fontSize: 14,
    fontWeight: '500',
  },
  // Guidance
  guidanceBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginBottom: 16,
  },
  guidanceBadgeText: {
    fontSize: 13,
    fontWeight: '500',
  },
  guidanceValue: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 20,
  },
  guidanceCard: {
    padding: 20,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 24,
  },
  guidanceSection: {
    marginBottom: 16,
  },
  guidanceLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  guidanceText: {
    fontSize: 14,
    lineHeight: 21,
  },
  guidanceIntro: {
    fontSize: 15,
    lineHeight: 22,
  },
  // Prompts
  promptsBox: {
    padding: 16,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 24,
  },
  promptsLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  promptItem: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  textArea: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    fontSize: 16,
    minHeight: 180,
    lineHeight: 24,
    marginBottom: 16,
  },
  hint: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
  },
  // Privacy
  privacyOptions: {
    gap: 12,
    marginBottom: 24,
  },
  privacyOption: {
    padding: 20,
    borderRadius: 14,
    position: 'relative',
  },
  privacyOptionTitle: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 6,
  },
  privacyOptionDesc: {
    fontSize: 14,
    lineHeight: 20,
    paddingRight: 24,
  },
  // Destination checkboxes (new)
  destinationOptions: {
    gap: 12,
    marginBottom: 24,
  },
  destinationOption: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 16,
    borderRadius: 14,
    gap: 14,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 2,
  },
  checkboxCheck: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  destinationTextContainer: {
    flex: 1,
  },
  destinationOptionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  destinationOptionDesc: {
    fontSize: 14,
    lineHeight: 20,
  },
  // Complete
  completeContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  completeIcon: {
    fontSize: 72,
    color: '#66BB6A',
    marginBottom: 24,
  },
  completeTitle: {
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 12,
    textAlign: 'center',
  },
  completeSubtitle: {
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
  },
});
