/**
 * Pattern Lens Reflection Screen
 * 
 * A dedicated screen where users can explore a detected life pattern
 * and reflect on it deeply. Connects insights from the Pattern Engine
 * to reflection and timeline updates.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useTheme } from '../contexts/ThemeContext';
import { useAppStore } from '../store';
import api from '../services/api';
import PatternTimeline, { TimelineEvent, PatternMomentsList, getCategoryColor, DecisionReplayModal } from '../components/patterns/PatternTimeline';
import PatternCycles, { PatternCyclesEmptyState } from '../components/patterns/PatternCycles';
import PatternPhase, { PatternPhaseData } from '../components/patterns/PatternPhase';
import DecisionAwareness, { DecisionAwarenessData } from '../components/patterns/DecisionAwareness';

// Colors for consistent styling
const Colors = {
  accent: '#8B5CF6',
  accentLight: 'rgba(139, 92, 246, 0.1)',
  accentMedium: 'rgba(139, 92, 246, 0.2)',
  border: '#E5E5E5',
  success: '#10B981',
  warning: '#F59E0B',
};

// Cycle data structure from API
interface PatternCycle {
  label: string;
  years: number[];
  events: TimelineEvent[];
  summary: string;
  event_count?: number;
}

interface PatternLensData {
  has_pattern: boolean;
  pattern_sequence: string[];
  years: number[];
  timeline_events: TimelineEvent[];
  cycles: PatternCycle[];
  pattern_phase: PatternPhaseData | null;
  decision_awareness: DecisionAwarenessData | null;
  challenge: string;
  genius: string;
  tips: string[];
  reflection_prompt: string;
}

export default function PatternLensScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const { user } = useAppStore();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [data, setData] = useState<PatternLensData | null>(null);
  const [reflectionText, setReflectionText] = useState('');
  const [saved, setSaved] = useState(false);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [selectedMomentEvent, setSelectedMomentEvent] = useState<TimelineEvent | null>(null);
  const [momentModalVisible, setMomentModalVisible] = useState(false);
  
  useEffect(() => {
    loadPatternLensData();
  }, [user?.id]);
  
  // Sync timeline events when data changes
  useEffect(() => {
    if (data?.timeline_events) {
      setTimelineEvents(data.timeline_events);
    }
  }, [data?.timeline_events]);
  
  const loadPatternLensData = async () => {
    if (!user?.id) return;
    
    setLoading(true);
    try {
      const response = await api.get(`/synthesis/${user.id}/pattern-lens`);
      if (response.data) {
        setData(response.data);
      }
    } catch (err) {
      console.error('[PatternLens] Failed to load:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle timeline event updates from Decision Replay
  const handleEventUpdated = (updatedEvent: TimelineEvent) => {
    setTimelineEvents(prev => 
      prev.map(e => e.id === updatedEvent.id ? updatedEvent : e)
    );
    // Also update in the main data object
    if (data) {
      setData({
        ...data,
        timeline_events: data.timeline_events.map(e => 
          e.id === updatedEvent.id ? updatedEvent : e
        ),
      });
    }
  };
  
  // Handle saving decision from standalone modal
  const handleSaveDecision = async (eventId: string, decisionText: string, decisionReflection: string) => {
    try {
      await api.put(`/lifeline/event/${eventId}`, {
        decision_text: decisionText || null,
        decision_reflection: decisionReflection || null,
      });
      
      // Update local state
      const updatedEvents = timelineEvents.map(e => 
        e.id === eventId 
          ? { ...e, decision_text: decisionText, decision_reflection: decisionReflection }
          : e
      );
      setTimelineEvents(updatedEvents);
      
      // Update selected event
      if (selectedMomentEvent?.id === eventId) {
        setSelectedMomentEvent({
          ...selectedMomentEvent,
          decision_text: decisionText,
          decision_reflection: decisionReflection,
        });
      }
      
      // Update data too
      if (data) {
        setData({
          ...data,
          timeline_events: data.timeline_events.map(e => 
            e.id === eventId ? { ...e, decision_text: decisionText, decision_reflection: decisionReflection } : e
          ),
        });
      }
    } catch (err) {
      console.error('[PatternLens] Save decision error:', err);
      throw err;
    }
  };
  
  const handleSaveReflection = async () => {
    if (!user?.id || !reflectionText.trim()) {
      Alert.alert('Reflection Empty', 'Please write something before saving.');
      return;
    }
    
    setSaving(true);
    try {
      await api.post('/journal', {
        user_id: user.id,
        entry_type: 'reflection',
        content: reflectionText,
        metadata: {
          source: 'pattern_lens',
          pattern_sequence: data?.pattern_sequence,
          years: data?.years,
        }
      });
      
      setSaved(true);
      Alert.alert('Saved', 'Your reflection has been saved to your journal.');
    } catch (err) {
      console.error('[PatternLens] Failed to save reflection:', err);
      Alert.alert('Error', 'Failed to save reflection. Please try again.');
    } finally {
      setSaving(false);
    }
  };
  
  const handleAddTimelineMoment = () => {
    // Navigate to lifeline with pre-filled data
    router.push({
      pathname: '/(tabs)/life',
      params: {
        action: 'add_event',
        prefill_description: reflectionText || `Reflection on pattern: ${data?.pattern_sequence?.join(' → ')}`,
        prefill_category: 'Turning Point',
      }
    });
  };
  
  const handleReturnToPatterns = () => {
    router.push('/(tabs)/patterns');
  };
  
  // Render pattern sequence with arrows
  const renderPatternSequence = () => {
    if (!data?.pattern_sequence || data.pattern_sequence.length === 0) {
      return null;
    }
    
    return (
      <View style={styles.sequenceContainer}>
        {data.pattern_sequence.map((step, index) => (
          <View key={index} style={styles.sequenceItem}>
            <View style={[styles.sequenceBox, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
              <Text style={[styles.sequenceText, { color: theme.text }]}>{step}</Text>
            </View>
            {index < data.pattern_sequence.length - 1 && (
              <Text style={[styles.sequenceArrow, { color: theme.accent }]}>↓</Text>
            )}
          </View>
        ))}
      </View>
    );
  };
  
  // Render years badges
  const renderYears = () => {
    if (!data?.years || data.years.length === 0) {
      return null;
    }
    
    return (
      <View style={styles.yearsContainer}>
        <Text style={[styles.yearsLabel, { color: theme.textSecondary }]}>
          Seen in your timeline:
        </Text>
        <View style={styles.yearsBadges}>
          {data.years.map((year, index) => (
            <React.Fragment key={year}>
              <Text style={[styles.yearBadge, { color: theme.accent }]}>{year}</Text>
              {index < data.years.length - 1 && (
                <Text style={[styles.yearDot, { color: theme.textSecondary }]}>•</Text>
              )}
            </React.Fragment>
          ))}
        </View>
      </View>
    );
  };
  
  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Loading pattern insights...
          </Text>
        </View>
      </SafeAreaView>
    );
  }
  
  if (!data || !data.has_pattern) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.emptyContainer}>
          <Text style={[styles.emptyTitle, { color: theme.text }]}>No Pattern Detected Yet</Text>
          <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
            Add more moments to your lifeline and continue reflecting to reveal patterns.
          </Text>
          <TouchableOpacity
            style={[styles.emptyButton, { backgroundColor: theme.accent }]}
            onPress={() => router.push('/(tabs)/life')}
          >
            <Text style={styles.emptyButtonText}>Add Lifeline Moments</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <KeyboardAvoidingView 
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView 
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity onPress={handleReturnToPatterns} style={styles.backButton}>
              <Text style={[styles.backButtonText, { color: theme.accent }]}>← Back</Text>
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: theme.text }]}>Pattern Lens</Text>
          </View>
          
          {/* SECTION 1: Pattern Sequence */}
          <View style={[styles.card, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
            <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>PATTERN</Text>
            {renderPatternSequence()}
            {renderYears()}
          </View>
          
          {/* SECTION 1.5: Pattern Timeline */}
          {timelineEvents && timelineEvents.length >= 2 && (
            <View style={[styles.card, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
              <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>PATTERN TIMELINE</Text>
              <PatternTimeline
                patternSequence={data.pattern_sequence}
                events={timelineEvents}
                onViewMoment={(eventId) => {
                  // Navigate to lifeline to view the specific moment
                  router.push({
                    pathname: '/(tabs)/life',
                    params: { highlightEventId: eventId }
                  });
                }}
                onEventUpdated={handleEventUpdated}
              />
            </View>
          )}
          
          {/* SECTION 1.75: When This Pattern Appeared */}
          {timelineEvents && timelineEvents.length >= 2 && (
            <View style={[styles.card, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
              <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>WHEN THIS PATTERN APPEARED</Text>
              <Text style={[styles.momentsIntro, { color: theme.textSecondary }]}>
                These are moments from your lifeline where this pattern showed up. Tap to revisit and reflect on the decisions you made.
              </Text>
              <PatternMomentsList
                events={timelineEvents}
                onEventPress={(event) => {
                  setSelectedMomentEvent(event);
                  setMomentModalVisible(true);
                }}
                theme={theme}
              />
            </View>
          )}
          
          {/* Decision Replay Modal for Moments List */}
          <DecisionReplayModal
            visible={momentModalVisible}
            event={selectedMomentEvent}
            patternSequence={data?.pattern_sequence || []}
            onClose={() => {
              setMomentModalVisible(false);
              setSelectedMomentEvent(null);
            }}
            onSave={handleSaveDecision}
            onViewMoment={(eventId) => {
              router.push({
                pathname: '/(tabs)/life',
                params: { highlightEventId: eventId }
              });
            }}
            theme={theme}
          />
          
          {/* SECTION 1.9: Pattern Cycles */}
          {data.cycles && data.cycles.length > 0 ? (
            <View style={[styles.card, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
              <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>PATTERN CYCLES</Text>
              <Text style={[styles.cyclesIntro, { color: theme.textSecondary }]}>
                Your life tends to move through recognizable cycles. Each cycle has a beginning, pressure point, and turning point.
              </Text>
              <PatternCycles
                cycles={data.cycles}
                onEventPress={(event) => {
                  setSelectedMomentEvent(event);
                  setMomentModalVisible(true);
                }}
              />
            </View>
          ) : timelineEvents && timelineEvents.length >= 2 && timelineEvents.length < 4 ? (
            <View style={[styles.card, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
              <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>PATTERN CYCLES</Text>
              <PatternCyclesEmptyState />
            </View>
          ) : null}
          
          {/* SECTION 1.95: Pattern Phase */}
          {data.pattern_phase && (
            <View style={[styles.card, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
              <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>PATTERN PHASE</Text>
              <PatternPhase phase={data.pattern_phase} />
            </View>
          )}
          
          {/* SECTION 1.97: Decision Awareness */}
          {data.decision_awareness && (
            <View style={[styles.card, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
              <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>DECISION AWARENESS</Text>
              <DecisionAwareness awareness={data.decision_awareness} />
            </View>
          )}
          
          {/* SECTION 2: The Challenge */}
          <View style={[styles.card, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
            <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>THE CHALLENGE</Text>
            <Text style={[styles.challengeText, { color: theme.text }]}>
              {data.challenge}
            </Text>
          </View>
          
          {/* SECTION 3: The Genius */}
          <View style={[styles.card, styles.geniusCard, { backgroundColor: Colors.accentLight, borderColor: theme.accent }]}>
            <Text style={[styles.sectionLabel, { color: theme.accent }]}>THE GENIUS</Text>
            <Text style={[styles.geniusText, { color: theme.text }]}>
              {data.genius}
            </Text>
          </View>
          
          {/* SECTION 4: Practical Moves */}
          <View style={[styles.card, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
            <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>PRACTICAL MOVES</Text>
            <View style={styles.tipsList}>
              {data.tips.map((tip, index) => (
                <View key={index} style={styles.tipItem}>
                  <Text style={[styles.tipBullet, { color: theme.accent }]}>•</Text>
                  <Text style={[styles.tipText, { color: theme.text }]}>{tip}</Text>
                </View>
              ))}
            </View>
          </View>
          
          {/* SECTION 5: Reflection */}
          <View style={[styles.card, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
            <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>REFLECTION</Text>
            <Text style={[styles.reflectionPrompt, { color: theme.text }]}>
              {data.reflection_prompt}
            </Text>
            <TextInput
              style={[
                styles.reflectionInput,
                { 
                  backgroundColor: theme.background,
                  color: theme.text,
                  borderColor: theme.border,
                }
              ]}
              placeholder="Write your reflection here..."
              placeholderTextColor={theme.textSecondary}
              multiline
              numberOfLines={6}
              value={reflectionText}
              onChangeText={setReflectionText}
              textAlignVertical="top"
            />
          </View>
          
          {/* SECTION 6: Actions */}
          <View style={styles.actionsContainer}>
            <TouchableOpacity
              style={[
                styles.actionButton,
                styles.primaryButton,
                { backgroundColor: theme.accent },
                (saving || saved) && styles.disabledButton
              ]}
              onPress={handleSaveReflection}
              disabled={saving || saved}
            >
              {saving ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <Text style={styles.primaryButtonText}>
                  {saved ? '✓ Saved' : 'Save Reflection'}
                </Text>
              )}
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.actionButton, styles.secondaryButton, { borderColor: theme.border }]}
              onPress={handleAddTimelineMoment}
            >
              <Text style={[styles.secondaryButtonText, { color: theme.text }]}>
                Add Timeline Moment
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.actionButton, styles.tertiaryButton]}
              onPress={handleReturnToPatterns}
            >
              <Text style={[styles.tertiaryButtonText, { color: theme.textSecondary }]}>
                Return to Patterns
              </Text>
            </TouchableOpacity>
          </View>
          
          {/* Disclaimer */}
          <Text style={[styles.disclaimer, { color: theme.textSecondary }]}>
            These patterns are observations for reflection, not fixed predictions. 
            You are always free to respond differently.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 120, // Extra padding for PWA banner overlay
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 15,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 12,
  },
  emptyText: {
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
  },
  emptyButton: {
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 12,
  },
  emptyButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
  },
  backButton: {
    paddingVertical: 8,
    paddingRight: 16,
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '600',
    flex: 1,
  },
  card: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 20,
    marginBottom: 16,
  },
  geniusCard: {
    borderWidth: 2,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 12,
  },
  sequenceContainer: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  sequenceItem: {
    alignItems: 'center',
  },
  sequenceBox: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    borderWidth: 1,
    minWidth: 140,
    alignItems: 'center',
  },
  sequenceText: {
    fontSize: 16,
    fontWeight: '600',
  },
  sequenceArrow: {
    fontSize: 24,
    marginVertical: 4,
  },
  yearsContainer: {
    marginTop: 20,
    alignItems: 'center',
  },
  yearsLabel: {
    fontSize: 13,
    marginBottom: 8,
  },
  yearsBadges: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  yearBadge: {
    fontSize: 15,
    fontWeight: '600',
  },
  yearDot: {
    fontSize: 12,
    marginHorizontal: 8,
  },
  challengeText: {
    fontSize: 15,
    lineHeight: 24,
  },
  momentsIntro: {
    fontSize: 13,
    lineHeight: 20,
    marginBottom: 16,
  },
  cyclesIntro: {
    fontSize: 13,
    lineHeight: 20,
    marginBottom: 16,
  },
  geniusText: {
    fontSize: 15,
    lineHeight: 24,
    fontWeight: '500',
  },
  tipsList: {
    gap: 12,
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  tipBullet: {
    fontSize: 22,
    marginRight: 10,
    marginTop: -2,
  },
  tipText: {
    fontSize: 15,
    lineHeight: 22,
    flex: 1,
  },
  reflectionPrompt: {
    fontSize: 15,
    lineHeight: 24,
    fontStyle: 'italic',
    marginBottom: 16,
  },
  reflectionInput: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
    fontSize: 15,
    lineHeight: 22,
    minHeight: 120,
  },
  actionsContainer: {
    gap: 12,
    marginTop: 8,
    marginBottom: 16,
  },
  actionButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButton: {
    minHeight: 52,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    borderWidth: 1,
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  tertiaryButton: {
    backgroundColor: 'transparent',
  },
  tertiaryButtonText: {
    fontSize: 15,
  },
  disabledButton: {
    opacity: 0.7,
  },
  disclaimer: {
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
    fontStyle: 'italic',
    paddingHorizontal: 20,
  },
});
