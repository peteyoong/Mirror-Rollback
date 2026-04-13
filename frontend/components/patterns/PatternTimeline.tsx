/**
 * PatternTimeline Component
 * 
 * A visual timeline showing where a detected life pattern appears
 * across the user's Lifeline. Makes repeating sequences visible at a glance.
 * 
 * Design: Calm, minimal, pattern-focused
 * 
 * Features:
 * - Visual timeline with tappable nodes
 * - Decision Replay: editable fields for decision reflections
 * - Pattern context display
 * - "When This Pattern Appeared" list section
 * 
 * Future extensions:
 * - Pattern cycles visualization
 * - Forum pattern maps
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  Dimensions,
  TextInput,
  ScrollView,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import api from '../../services/api';

// =============================================================================
// TYPES
// =============================================================================

export interface TimelineEvent {
  id: string;
  year: number;
  title: string;
  description?: string;
  category: string;
  decision_text?: string | null;
  decision_reflection?: string | null;
}

interface PatternTimelineProps {
  patternSequence: string[];
  events: TimelineEvent[];
  onViewMoment?: (eventId: string) => void;
  onEventUpdated?: (event: TimelineEvent) => void;
}

// =============================================================================
// CATEGORY COLORS
// =============================================================================

export const CATEGORY_COLORS: Record<string, string> = {
  'Career': '#8B5CF6',      // purple
  'Achievement': '#8B5CF6', // purple
  'Relationships': '#3B82F6', // blue
  'Family': '#3B82F6',       // blue
  'Identity': '#10B981',     // green
  'Turning Point': '#F59E0B', // orange
  'Move': '#F59E0B',         // orange
  'Loss': '#EF4444',         // red
  'Health': '#EC4899',       // pink
  'Other': '#6B7280',        // neutral gray
};

export const getCategoryColor = (category: string): string => {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS['Other'];
};

// =============================================================================
// DECISION REPLAY MODAL
// =============================================================================

export interface DecisionReplayModalProps {
  visible: boolean;
  event: TimelineEvent | null;
  patternSequence: string[];
  onClose: () => void;
  onSave: (eventId: string, decisionText: string, decisionReflection: string) => Promise<void>;
  onViewMoment?: (eventId: string) => void;
  theme: any;
}

export function DecisionReplayModal({ 
  visible, 
  event, 
  patternSequence,
  onClose, 
  onSave,
  onViewMoment, 
  theme 
}: DecisionReplayModalProps) {
  const [decisionText, setDecisionText] = useState(event?.decision_text || '');
  const [decisionReflection, setDecisionReflection] = useState(event?.decision_reflection || '');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  
  // Reset state when event changes
  React.useEffect(() => {
    if (event) {
      setDecisionText(event.decision_text || '');
      setDecisionReflection(event.decision_reflection || '');
      setSaved(false);
    }
  }, [event?.id]);
  
  if (!event) return null;
  
  const categoryColor = getCategoryColor(event.category);
  
  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(event.id, decisionText, decisionReflection);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('[DecisionReplay] Save error:', err);
    } finally {
      setSaving(false);
    }
  };
  
  const hasChanges = 
    decisionText !== (event.decision_text || '') || 
    decisionReflection !== (event.decision_reflection || '');
  
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView 
        style={styles.modalOverlay}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <TouchableOpacity 
          style={styles.modalBackdrop}
          activeOpacity={1}
          onPress={onClose}
        />
        <View 
          style={[styles.decisionModalContent, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}
        >
          <ScrollView showsVerticalScrollIndicator={false}>
            {/* Pattern Context */}
            <View style={[styles.patternContext, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.patternContextLabel, { color: theme.textTertiary }]}>PATTERN</Text>
              <View style={styles.patternSequenceRow}>
                {patternSequence.map((step, index) => (
                  <React.Fragment key={index}>
                    <Text style={[styles.patternStep, { color: theme.text }]}>{step}</Text>
                    {index < patternSequence.length - 1 && (
                      <Text style={[styles.patternArrow, { color: theme.textSecondary }]}> → </Text>
                    )}
                  </React.Fragment>
                ))}
              </View>
            </View>
            
            {/* Year & Title */}
            <Text style={[styles.modalYear, { color: theme.accent }]}>{event.year}</Text>
            <Text style={[styles.modalTitle, { color: theme.text }]}>
              {event.title}
            </Text>
            
            {/* Category Badge */}
            <View style={[styles.categoryBadge, { backgroundColor: `${categoryColor}20` }]}>
              <View style={[styles.categoryDot, { backgroundColor: categoryColor }]} />
              <Text style={[styles.categoryText, { color: categoryColor }]}>
                {event.category}
              </Text>
            </View>
            
            {/* Description (if available) */}
            {event.description && (
              <Text style={[styles.descriptionText, { color: theme.textSecondary }]}>
                {event.description}
              </Text>
            )}
            
            {/* Decision Replay Section */}
            <View style={styles.decisionSection}>
              <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>
                DECISION REPLAY
              </Text>
              
              {/* Decision Text Field */}
              <Text style={[styles.fieldLabel, { color: theme.text }]}>
                What decision did you make at this moment?
              </Text>
              <TextInput
                style={[
                  styles.textInput,
                  { 
                    backgroundColor: theme.background,
                    color: theme.text,
                    borderColor: theme.border,
                  }
                ]}
                placeholder="The choice I made was..."
                placeholderTextColor={theme.textTertiary}
                multiline
                numberOfLines={3}
                value={decisionText}
                onChangeText={setDecisionText}
                textAlignVertical="top"
              />
              
              {/* Decision Reflection Field */}
              <Text style={[styles.fieldLabel, { color: theme.text }]}>
                How did this change your direction?
              </Text>
              <TextInput
                style={[
                  styles.textInput,
                  { 
                    backgroundColor: theme.background,
                    color: theme.text,
                    borderColor: theme.border,
                  }
                ]}
                placeholder="After that decision, things shifted because..."
                placeholderTextColor={theme.textTertiary}
                multiline
                numberOfLines={3}
                value={decisionReflection}
                onChangeText={setDecisionReflection}
                textAlignVertical="top"
              />
            </View>
            
            {/* Actions */}
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={[
                  styles.saveButton,
                  { backgroundColor: theme.accent },
                  (!hasChanges || saving) && styles.disabledButton
                ]}
                onPress={handleSave}
                disabled={!hasChanges || saving}
              >
                {saving ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <Text style={styles.saveButtonText}>
                    {saved ? '✓ Saved' : 'Save Reflection'}
                  </Text>
                )}
              </TouchableOpacity>
              
              {onViewMoment && (
                <TouchableOpacity
                  style={[styles.viewMomentButton, { borderColor: theme.border }]}
                  onPress={() => {
                    onViewMoment(event.id);
                    onClose();
                  }}
                >
                  <Text style={[styles.viewMomentText, { color: theme.textSecondary }]}>
                    View full moment →
                  </Text>
                </TouchableOpacity>
              )}
              
              <TouchableOpacity
                style={styles.closeButton}
                onPress={onClose}
              >
                <Text style={[styles.closeButtonText, { color: theme.textSecondary }]}>
                  Close
                </Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// =============================================================================
// PATTERN MOMENTS LIST COMPONENT
// =============================================================================

interface PatternMomentsListProps {
  events: TimelineEvent[];
  onEventPress: (event: TimelineEvent) => void;
  theme: any;
}

export function PatternMomentsList({ events, onEventPress, theme }: PatternMomentsListProps) {
  if (!events || events.length === 0) return null;
  
  return (
    <View style={styles.momentsList}>
      {events.map((event) => {
        const categoryColor = getCategoryColor(event.category);
        const hasDecision = !!(event.decision_text || event.decision_reflection);
        
        return (
          <TouchableOpacity
            key={event.id}
            style={[styles.momentItem, { borderColor: theme.border }]}
            onPress={() => onEventPress(event)}
            activeOpacity={0.7}
          >
            <View style={styles.momentLeft}>
              <View style={[styles.momentYearBadge, { backgroundColor: `${categoryColor}20` }]}>
                <Text style={[styles.momentYear, { color: categoryColor }]}>{event.year}</Text>
              </View>
              <View style={styles.momentInfo}>
                <Text style={[styles.momentTitle, { color: theme.text }]} numberOfLines={1}>
                  {event.title}
                </Text>
                <View style={styles.momentMeta}>
                  <View style={[styles.momentCategoryDot, { backgroundColor: categoryColor }]} />
                  <Text style={[styles.momentCategory, { color: theme.textSecondary }]}>
                    {event.category}
                  </Text>
                </View>
              </View>
            </View>
            <View style={styles.momentRight}>
              {hasDecision ? (
                <View style={[styles.decisionStatus, { backgroundColor: '#10B98120' }]}>
                  <Text style={[styles.decisionStatusText, { color: '#10B981' }]}>
                    ✓ Decision captured
                  </Text>
                </View>
              ) : (
                <Text style={[styles.noDecisionText, { color: theme.textTertiary }]}>
                  Add reflection →
                </Text>
              )}
            </View>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function PatternTimeline({ 
  patternSequence, 
  events,
  onViewMoment,
  onEventUpdated,
}: PatternTimelineProps) {
  const { theme } = useTheme();
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [localEvents, setLocalEvents] = useState(events);
  
  // Sync local events when props change
  React.useEffect(() => {
    setLocalEvents(events);
  }, [events]);
  
  // Hide if fewer than 2 events
  if (!localEvents || localEvents.length < 2) {
    return null;
  }
  
  const handleNodePress = (event: TimelineEvent) => {
    setSelectedEvent(event);
    setModalVisible(true);
  };
  
  const handleCloseModal = () => {
    setModalVisible(false);
    setSelectedEvent(null);
  };
  
  const handleSaveDecision = async (eventId: string, decisionText: string, decisionReflection: string) => {
    try {
      await api.put(`/lifeline/event/${eventId}`, {
        decision_text: decisionText || null,
        decision_reflection: decisionReflection || null,
      });
      
      // Update local state
      const updatedEvents = localEvents.map(e => 
        e.id === eventId 
          ? { ...e, decision_text: decisionText, decision_reflection: decisionReflection }
          : e
      );
      setLocalEvents(updatedEvents);
      
      // Update selected event
      if (selectedEvent?.id === eventId) {
        setSelectedEvent({
          ...selectedEvent,
          decision_text: decisionText,
          decision_reflection: decisionReflection,
        });
      }
      
      // Notify parent
      const updatedEvent = updatedEvents.find(e => e.id === eventId);
      if (updatedEvent && onEventUpdated) {
        onEventUpdated(updatedEvent);
      }
    } catch (err) {
      console.error('[PatternTimeline] Save decision error:', err);
      throw err;
    }
  };
  
  // Calculate node positions
  const screenWidth = Dimensions.get('window').width;
  const containerPadding = 40; // 20px on each side
  const availableWidth = screenWidth - containerPadding - 60; // Extra padding for edges
  const nodeSpacing = localEvents.length > 1 ? availableWidth / (localEvents.length - 1) : 0;
  
  return (
    <View style={styles.container}>
      {/* Pattern Sequence Header */}
      <View style={styles.sequenceHeader}>
        {patternSequence.map((step, index) => (
          <React.Fragment key={index}>
            <Text style={[styles.sequenceStep, { color: theme.text }]}>{step}</Text>
            {index < patternSequence.length - 1 && (
              <Text style={[styles.sequenceArrow, { color: theme.textSecondary }]}> → </Text>
            )}
          </React.Fragment>
        ))}
      </View>
      
      {/* Timeline Visual */}
      <View style={styles.timelineContainer}>
        {/* Connecting Line */}
        <View style={[styles.timelineLine, { backgroundColor: theme.border }]} />
        
        {/* Nodes */}
        <View style={styles.nodesContainer}>
          {localEvents.map((event, index) => {
            const categoryColor = getCategoryColor(event.category);
            const isFirst = index === 0;
            const hasDecision = !!(event.decision_text || event.decision_reflection);
            
            return (
              <View 
                key={event.id || `${event.year}-${index}`}
                style={[
                  styles.nodeWrapper,
                  {
                    marginLeft: isFirst ? 0 : nodeSpacing - 44,
                  }
                ]}
              >
                <TouchableOpacity
                  style={[
                    styles.node,
                    { 
                      backgroundColor: categoryColor,
                      borderColor: hasDecision ? '#10B981' : `${categoryColor}50`,
                      borderWidth: hasDecision ? 4 : 3,
                    }
                  ]}
                  onPress={() => handleNodePress(event)}
                  activeOpacity={0.7}
                >
                  <View style={styles.nodeInner}>
                    {hasDecision && (
                      <Text style={styles.nodeCheck}>✓</Text>
                    )}
                  </View>
                </TouchableOpacity>
                <Text style={[styles.nodeYear, { color: theme.textSecondary }]}>
                  {event.year}
                </Text>
              </View>
            );
          })}
        </View>
      </View>
      
      {/* Tap hint */}
      <Text style={[styles.tapHint, { color: theme.textTertiary }]}>
        Tap a node to replay the decision
      </Text>
      
      {/* Decision Replay Modal */}
      <DecisionReplayModal
        visible={modalVisible}
        event={selectedEvent}
        patternSequence={patternSequence}
        onClose={handleCloseModal}
        onSave={handleSaveDecision}
        onViewMoment={onViewMoment}
        theme={theme}
      />
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    paddingVertical: 8,
  },
  sequenceHeader: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  sequenceStep: {
    fontSize: 15,
    fontWeight: '600',
  },
  sequenceArrow: {
    fontSize: 14,
  },
  timelineContainer: {
    position: 'relative',
    height: 80,
    marginHorizontal: 10,
  },
  timelineLine: {
    position: 'absolute',
    top: 18,
    left: 18,
    right: 18,
    height: 2,
    borderRadius: 1,
  },
  nodesContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  nodeWrapper: {
    alignItems: 'center',
    width: 44,
  },
  node: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  nodeInner: {
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: 'rgba(255, 255, 255, 0.4)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  nodeCheck: {
    fontSize: 8,
    color: '#FFFFFF',
    fontWeight: '700',
  },
  nodeYear: {
    marginTop: 8,
    fontSize: 12,
    fontWeight: '600',
  },
  tapHint: {
    textAlign: 'center',
    fontSize: 11,
    marginTop: 8,
    fontStyle: 'italic',
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalBackdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  decisionModalContent: {
    width: '90%',
    maxWidth: 380,
    maxHeight: '85%',
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
  },
  patternContext: {
    borderRadius: 8,
    borderWidth: 1,
    padding: 12,
    marginBottom: 16,
  },
  patternContextLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  patternSequenceRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
  },
  patternStep: {
    fontSize: 13,
    fontWeight: '600',
  },
  patternArrow: {
    fontSize: 12,
  },
  modalYear: {
    fontSize: 36,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 4,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 12,
    lineHeight: 24,
  },
  categoryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'center',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    marginBottom: 12,
  },
  categoryDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  categoryText: {
    fontSize: 13,
    fontWeight: '600',
  },
  descriptionText: {
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
    marginBottom: 16,
    fontStyle: 'italic',
  },
  decisionSection: {
    marginTop: 8,
    marginBottom: 16,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    fontSize: 14,
    lineHeight: 20,
    minHeight: 80,
    marginBottom: 16,
  },
  modalActions: {
    gap: 10,
  },
  saveButton: {
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 48,
  },
  saveButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  disabledButton: {
    opacity: 0.6,
  },
  viewMomentButton: {
    paddingVertical: 12,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: 'center',
  },
  viewMomentText: {
    fontSize: 14,
    fontWeight: '500',
  },
  closeButton: {
    paddingVertical: 10,
    alignItems: 'center',
  },
  closeButtonText: {
    fontSize: 14,
  },
  // Pattern Moments List styles
  momentsList: {
    gap: 8,
  },
  momentItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  momentLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  momentYearBadge: {
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 6,
    marginRight: 12,
  },
  momentYear: {
    fontSize: 13,
    fontWeight: '700',
  },
  momentInfo: {
    flex: 1,
  },
  momentTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 2,
  },
  momentMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  momentCategoryDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  momentCategory: {
    fontSize: 12,
  },
  momentRight: {
    marginLeft: 12,
  },
  decisionStatus: {
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 6,
  },
  decisionStatusText: {
    fontSize: 11,
    fontWeight: '600',
  },
  noDecisionText: {
    fontSize: 12,
    fontStyle: 'italic',
  },
});
