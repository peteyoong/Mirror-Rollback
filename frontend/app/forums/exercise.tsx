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
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { getForumExercise, submitForumReflection, PatternDomain } from '../../services/api';

type Step = 'intro' | 'domain' | 'prompts' | 'privacy' | 'complete';

export default function ExerciseScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const { forumId } = useLocalSearchParams();
  
  const [step, setStep] = useState<Step>('intro');
  const [exercise, setExercise] = useState<any | null>(null);
  const [domains, setDomains] = useState<PatternDomain[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [reflectionText, setReflectionText] = useState('');
  const [isShared, setIsShared] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const fetchExercise = useCallback(async () => {
    if (!user?.id || !forumId) return;
    
    setLoading(true);
    try {
      const data = await getForumExercise(forumId as string, user.id);
      setExercise(data.exercise);
      setDomains(data.domains);
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

  const handleBack = () => {
    if (step === 'intro') {
      router.back();
    } else if (step === 'domain') {
      setStep('intro');
    } else if (step === 'prompts') {
      setStep('domain');
    } else if (step === 'privacy') {
      setStep('prompts');
    } else {
      router.back();
    }
  };

  const handleSubmit = async () => {
    if (!user?.id || !forumId || !selectedDomain) return;
    
    setSubmitting(true);
    try {
      await submitForumReflection(forumId as string, {
        user_id: user.id,
        selected_domain: selectedDomain,
        reflection_text: reflectionText,
        is_shared: isShared,
      });
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
    const steps = ['intro', 'domain', 'prompts', 'privacy'];
    const currentIndex = steps.indexOf(step);
    if (step === 'complete') return null;
    
    return (
      <View style={styles.stepIndicator}>
        {steps.map((s, i) => (
          <View
            key={s}
            style={[
              styles.stepDot,
              { backgroundColor: i <= currentIndex ? theme.accent : theme.border }
            ]}
          />
        ))}
      </View>
    );
  };

  // INTRO STEP
  if (step === 'intro') {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          {renderStepIndicator()}
          
          <Text style={[styles.title, { color: theme.text }]}>
            {exercise?.title || 'The Pattern Running Me'}
          </Text>
          
          <Text style={[styles.introText, { color: theme.textSecondary }]}>
            {exercise?.description || 'This exercise helps surface one pattern that may currently be shaping how you lead, relate, or respond to life.'}
          </Text>
          
          <View style={[styles.infoBox, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.infoTitle, { color: theme.text }]}>What you'll do</Text>
            <Text style={[styles.infoItem, { color: theme.textSecondary }]}>
              • Choose a pattern domain that's active for you
            </Text>
            <Text style={[styles.infoItem, { color: theme.textSecondary }]}>
              • Reflect on 5 prompts about this pattern
            </Text>
            <Text style={[styles.infoItem, { color: theme.textSecondary }]}>
              • Decide if you want to share with the group
            </Text>
          </View>

          <TouchableOpacity
            style={[styles.primaryButton, { backgroundColor: theme.buttonPrimaryBg }]}
            onPress={() => setStep('domain')}
          >
            <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>
              Begin Exercise
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // DOMAIN SELECTION STEP
  if (step === 'domain') {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          {renderStepIndicator()}
          
          <Text style={[styles.stepTitle, { color: theme.text }]}>Step 1</Text>
          <Text style={[styles.title, { color: theme.text }]}>Choose a Domain</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Which area of life feels most active or charged for you right now?
          </Text>

          <View style={styles.domainsList}>
            {domains.map((domain) => (
              <TouchableOpacity
                key={domain.id}
                style={[
                  styles.domainCard,
                  { 
                    backgroundColor: theme.surface, 
                    borderColor: selectedDomain === domain.id ? theme.accent : theme.border,
                    borderWidth: selectedDomain === domain.id ? 2 : StyleSheet.hairlineWidth,
                  }
                ]}
                onPress={() => setSelectedDomain(domain.id)}
              >
                <Text style={[styles.domainName, { color: theme.text }]}>
                  {domain.name}
                </Text>
                {selectedDomain === domain.id && (
                  <Text style={[styles.checkmark, { color: theme.accent }]}>✓</Text>
                )}
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity
            style={[
              styles.primaryButton, 
              { backgroundColor: selectedDomain ? theme.buttonPrimaryBg : theme.border }
            ]}
            onPress={() => setStep('prompts')}
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

  // PROMPTS STEP
  if (step === 'prompts') {
    const prompts = exercise?.prompts || [
      "Where is this pattern showing up in your life right now?",
      "What situation from the last 30–60 days best represents it?",
      "How has this pattern helped you succeed?",
      "Where might this same pattern now be limiting you?",
      "If this pattern softened by 10%, what might change?"
    ];
    
    const selectedDomainName = domains.find(d => d.id === selectedDomain)?.name || '';

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
            
            <Text style={[styles.stepTitle, { color: theme.text }]}>Step 2</Text>
            <Text style={[styles.title, { color: theme.text }]}>Reflect</Text>
            <View style={[styles.domainBadge, { backgroundColor: theme.accent + '20' }]}>
              <Text style={[styles.domainBadgeText, { color: theme.accent }]}>
                {selectedDomainName}
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

            <TouchableOpacity
              style={[
                styles.primaryButton, 
                { backgroundColor: reflectionText.trim().length > 20 ? theme.buttonPrimaryBg : theme.border }
              ]}
              onPress={() => setStep('privacy')}
              disabled={reflectionText.trim().length < 20}
            >
              <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>
                Continue
              </Text>
            </TouchableOpacity>
            
            {reflectionText.trim().length > 0 && reflectionText.trim().length < 20 && (
              <Text style={[styles.hint, { color: theme.textTertiary }]}>
                Please write at least 20 characters
              </Text>
            )}
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    );
  }

  // PRIVACY STEP
  if (step === 'privacy') {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          {renderStepIndicator()}
          
          <Text style={[styles.stepTitle, { color: theme.text }]}>Step 3</Text>
          <Text style={[styles.title, { color: theme.text }]}>Privacy Choice</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Would you like to share your reflection with the forum?
          </Text>

          <View style={styles.privacyOptions}>
            <TouchableOpacity
              style={[
                styles.privacyOption,
                { 
                  backgroundColor: theme.surface, 
                  borderColor: !isShared ? theme.accent : theme.border,
                  borderWidth: !isShared ? 2 : StyleSheet.hairlineWidth,
                }
              ]}
              onPress={() => setIsShared(false)}
            >
              <Text style={[styles.privacyOptionTitle, { color: theme.text }]}>
                Keep Private
              </Text>
              <Text style={[styles.privacyOptionDesc, { color: theme.textSecondary }]}>
                Only you can see your reflection. Perfect for personal processing.
              </Text>
              {!isShared && (
                <Text style={[styles.checkmark, { color: theme.accent }]}>✓</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.privacyOption,
                { 
                  backgroundColor: theme.surface, 
                  borderColor: isShared ? theme.accent : theme.border,
                  borderWidth: isShared ? 2 : StyleSheet.hairlineWidth,
                }
              ]}
              onPress={() => setIsShared(true)}
            >
              <Text style={[styles.privacyOptionTitle, { color: theme.text }]}>
                Share with Forum
              </Text>
              <Text style={[styles.privacyOptionDesc, { color: theme.textSecondary }]}>
                Other forum members can read your reflection. Builds trust and connection.
              </Text>
              {isShared && (
                <Text style={[styles.checkmark, { color: theme.accent }]}>✓</Text>
              )}
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[styles.primaryButton, { backgroundColor: theme.buttonPrimaryBg }]}
            onPress={handleSubmit}
            disabled={submitting}
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
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.completeContent}>
          <Text style={styles.completeIcon}>✓</Text>
          <Text style={[styles.completeTitle, { color: theme.text }]}>
            Reflection Submitted
          </Text>
          <Text style={[styles.completeSubtitle, { color: theme.textSecondary }]}>
            {isShared 
              ? 'Your reflection has been shared with the forum.' 
              : 'Your reflection has been saved privately.'}
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
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 8,
    opacity: 0.6,
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
  domainName: {
    fontSize: 16,
    fontWeight: '500',
  },
  checkmark: {
    fontSize: 18,
    fontWeight: '600',
  },
  // Prompts
  domainBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginBottom: 20,
  },
  domainBadgeText: {
    fontSize: 13,
    fontWeight: '500',
  },
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
