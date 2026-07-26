/**
 * PatternStorm Component & Detection Logic
 * 
 * Detects and visualizes clusters of major life events that occur
 * within a short time window (Intense Periods / Pattern Storms).
 * 
 * Detection Rules:
 * - 3+ events within a 3-year window
 * - 2 high-impact events (≥8) within 2 years
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { LifelineEvent } from './LifelineEventCard';

// =============================================================================
// TYPES
// =============================================================================

export interface PatternStorm {
  id: string;
  startYear: number;
  endYear: number;
  events: LifelineEvent[];
  intensity: 'high' | 'moderate';
  label: string;
}

interface StormBadgeProps {
  storm: PatternStorm;
  onPress?: () => void;
  compact?: boolean;
}

interface StormModalProps {
  storm: PatternStorm | null;
  visible: boolean;
  onClose: () => void;
}

interface StormHighlightProps {
  storm: PatternStorm;
  children: React.ReactNode;
  onPress?: () => void;
}

// =============================================================================
// STORM DETECTION LOGIC
// =============================================================================

/**
 * Detect pattern storms (intense periods) from a list of events
 */
export function detectPatternStorms(events: LifelineEvent[]): PatternStorm[] {
  if (events.length < 2) return [];
  
  // Sort events by year
  const sortedEvents = [...events]
    .filter(e => e.year)
    .sort((a, b) => (a.year || 0) - (b.year || 0));
  
  if (sortedEvents.length < 2) return [];
  
  const storms: PatternStorm[] = [];
  const usedEventIds = new Set<string>();
  
  // Rule 1: 3+ events within a 3-year window
  for (let i = 0; i < sortedEvents.length - 2; i++) {
    const startYear = sortedEvents[i].year || 0;
    const windowEnd = startYear + 3;
    
    const eventsInWindow = sortedEvents.filter(e => {
      const year = e.year || 0;
      return year >= startYear && year <= windowEnd && !usedEventIds.has(e.id);
    });
    
    if (eventsInWindow.length >= 3) {
      const endYear = Math.max(...eventsInWindow.map(e => e.year || 0));
      
      // Mark events as used
      eventsInWindow.forEach(e => usedEventIds.add(e.id));
      
      storms.push({
        id: `storm-${startYear}-${endYear}`,
        startYear,
        endYear,
        events: eventsInWindow,
        intensity: eventsInWindow.length >= 4 ? 'high' : 'moderate',
        label: `${startYear}–${endYear}`,
      });
    }
  }
  
  // Rule 2: 2 high-impact events (≥8) within 2 years
  const highImpactEvents = sortedEvents.filter(
    e => (e.impact_score || 0) >= 8 && !usedEventIds.has(e.id)
  );
  
  for (let i = 0; i < highImpactEvents.length - 1; i++) {
    const event1 = highImpactEvents[i];
    const event2 = highImpactEvents[i + 1];
    
    const year1 = event1.year || 0;
    const year2 = event2.year || 0;
    
    if (year2 - year1 <= 2 && !usedEventIds.has(event1.id) && !usedEventIds.has(event2.id)) {
      usedEventIds.add(event1.id);
      usedEventIds.add(event2.id);
      
      storms.push({
        id: `storm-${year1}-${year2}`,
        startYear: year1,
        endYear: year2,
        events: [event1, event2],
        intensity: 'high',
        label: year1 === year2 ? `${year1}` : `${year1}–${year2}`,
      });
    }
  }
  
  // Sort storms by start year
  return storms.sort((a, b) => a.startYear - b.startYear);
}

/**
 * Check if an event belongs to any storm
 */
export function getStormForEvent(
  event: LifelineEvent, 
  storms: PatternStorm[]
): PatternStorm | null {
  return storms.find(storm => 
    storm.events.some(e => e.id === event.id)
  ) || null;
}

/**
 * Check if an event is the first in its storm
 */
export function isFirstEventInStorm(
  event: LifelineEvent, 
  storms: PatternStorm[]
): boolean {
  const storm = getStormForEvent(event, storms);
  if (!storm) return false;
  
  const sortedStormEvents = [...storm.events].sort(
    (a, b) => (a.year || 0) - (b.year || 0)
  );
  return sortedStormEvents[0]?.id === event.id;
}

// =============================================================================
// STORM BADGE COMPONENT
// =============================================================================

export function StormBadge({ storm, onPress, compact = false }: StormBadgeProps) {
  const { theme } = useTheme();
  
  if (compact) {
    return (
      <TouchableOpacity 
        style={[styles.compactBadge, { backgroundColor: `${theme.accent}15` }]}
        onPress={onPress}
        activeOpacity={0.7}
      >
        <Text style={[styles.compactIcon]}>⚡</Text>
        <Text style={[styles.compactText, { color: theme.accent }]}>
          Intense Period
        </Text>
      </TouchableOpacity>
    );
  }
  
  return (
    <TouchableOpacity 
      style={[styles.badge, { backgroundColor: `${theme.accent}10`, borderColor: `${theme.accent}30` }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.badgeHeader}>
        <Text style={styles.badgeIcon}>⚡</Text>
        <Text style={[styles.badgeLabel, { color: theme.accent }]}>
          Intense Period
        </Text>
      </View>
      <Text style={[styles.badgeYears, { color: theme.text }]}>
        {storm.label}
      </Text>
    </TouchableOpacity>
  );
}

// =============================================================================
// STORM HIGHLIGHT WRAPPER
// =============================================================================

export function StormHighlight({ storm, children, onPress }: StormHighlightProps) {
  const { theme } = useTheme();
  
  return (
    <View style={styles.highlightWrapper}>
      {/* Storm label at top */}
      <StormBadge storm={storm} onPress={onPress} compact />
      
      {/* Highlight background */}
      <View style={[styles.highlightBackground, { backgroundColor: `${theme.accent}05` }]}>
        {children}
      </View>
    </View>
  );
}

// =============================================================================
// STORM MODAL
// =============================================================================

export function StormModal({ storm, visible, onClose }: StormModalProps) {
  const { theme } = useTheme();
  
  if (!storm) return null;
  
  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={[styles.modalContainer, { backgroundColor: theme.background }]}>
        {/* Header */}
        <View style={[styles.modalHeader, { borderBottomColor: theme.border }]}>
          <View style={styles.modalHeaderLeft}>
            <Text style={styles.modalIcon}>⚡</Text>
            <View>
              <Text style={[styles.modalTitle, { color: theme.text }]}>
                {storm.label} Intense Period
              </Text>
              <Text style={[styles.modalSubtitle, { color: theme.textSecondary }]}>
                {storm.events.length} turning points
              </Text>
            </View>
          </View>
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <Ionicons name="close" size={24} color={theme.textSecondary} />
          </TouchableOpacity>
        </View>
        
        {/* Content */}
        <ScrollView 
          style={styles.modalContent}
          contentContainerStyle={styles.modalContentContainer}
        >
          {/* Description */}
          <View style={[styles.descriptionCard, { backgroundColor: theme.surface }]}>
            <Text style={[styles.descriptionText, { color: theme.textSecondary }]}>
              Several major turning points occurred in a short time.
              {storm.intensity === 'high' && ' This was a period of rapid change.'}
            </Text>
          </View>
          
          {/* Events list */}
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Events in this period
          </Text>
          
          {storm.events
            .sort((a, b) => (a.year || 0) - (b.year || 0))
            .map((event) => (
              <View 
                key={event.id} 
                style={[styles.eventItem, { borderLeftColor: theme.accent }]}
              >
                <View style={styles.eventHeader}>
                  <Text style={[styles.eventYear, { color: theme.textSecondary }]}>
                    {event.year}
                  </Text>
                  {event.impact_score && event.impact_score >= 8 && (
                    <View style={[styles.highImpactBadge, { backgroundColor: `${theme.accent}20` }]}>
                      <Text style={[styles.highImpactText, { color: theme.accent }]}>
                        High Impact
                      </Text>
                    </View>
                  )}
                </View>
                <Text style={[styles.eventTitle, { color: theme.text }]}>
                  {event.title}
                </Text>
                {event.category && (
                  <Text style={[styles.eventCategory, { color: theme.textTertiary }]}>
                    {event.category}
                  </Text>
                )}
              </View>
            ))}
          
          {/* Reflection prompt */}
          <View style={[styles.reflectionCard, { backgroundColor: `${theme.accent}08`, borderColor: `${theme.accent}25` }]}>
            <Text style={[styles.reflectionIcon]}>💭</Text>
            <Text style={[styles.reflectionTitle, { color: theme.text }]}>
              Reflection
            </Text>
            <Text style={[styles.reflectionText, { color: theme.textSecondary }]}>
              What decisions during this period changed your direction most?
            </Text>
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

// =============================================================================
// PATTERN LENS STORM SECTION
// =============================================================================

interface IntensePeriodsProps {
  storms: PatternStorm[];
}

export function IntensePeriods({ storms }: IntensePeriodsProps) {
  const { theme } = useTheme();
  const [selectedStorm, setSelectedStorm] = useState<PatternStorm | null>(null);
  
  if (storms.length === 0) return null;
  
  return (
    <View style={styles.intensePeriodsSection}>
      <Text style={[styles.sectionHeader, { color: theme.text }]}>
        INTENSE PERIODS
      </Text>
      
      {storms.map((storm) => (
        <TouchableOpacity
          key={storm.id}
          style={[styles.stormCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
          onPress={() => setSelectedStorm(storm)}
          activeOpacity={0.7}
        >
          <View style={styles.stormCardHeader}>
            <Text style={styles.stormCardIcon}>⚡</Text>
            <Text style={[styles.stormCardLabel, { color: theme.text }]}>
              {storm.label}
            </Text>
            {storm.intensity === 'high' && (
              <View style={[styles.intensityBadge, { backgroundColor: `${theme.accent}15` }]}>
                <Text style={[styles.intensityText, { color: theme.accent }]}>
                  Rapid change
                </Text>
              </View>
            )}
          </View>
          
          <Text style={[styles.stormCardDescription, { color: theme.textSecondary }]}>
            {storm.events.length} turning points occurred in a short time.
          </Text>
          
          <View style={styles.stormCardEvents}>
            {storm.events.slice(0, 3).map((event) => (
              <Text 
                key={event.id} 
                style={[styles.stormEventPreview, { color: theme.textTertiary }]}
                numberOfLines={1}
              >
                • {event.title}
              </Text>
            ))}
            {storm.events.length > 3 && (
              <Text style={[styles.stormEventMore, { color: theme.textTertiary }]}>
                +{storm.events.length - 3} more
              </Text>
            )}
          </View>
          
          <View style={styles.stormCardFooter}>
            <Ionicons name="chevron-forward" size={16} color={theme.textTertiary} />
          </View>
        </TouchableOpacity>
      ))}
      
      {/* Storm Detail Modal */}
      <StormModal
        storm={selectedStorm}
        visible={!!selectedStorm}
        onClose={() => setSelectedStorm(null)}
      />
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  // Badge styles
  badge: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    marginBottom: 8,
  },
  badgeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  badgeIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  badgeLabel: {
    fontSize: 12,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  badgeYears: {
    fontSize: 16,
    fontWeight: '500',
  },
  
  // Compact badge
  compactBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 14,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  compactIcon: {
    fontSize: 12,
    marginRight: 4,
  },
  compactText: {
    fontSize: 11,
    fontWeight: '500',
  },
  
  // Highlight wrapper
  highlightWrapper: {
    position: 'relative',
  },
  highlightBackground: {
    borderRadius: 12,
    paddingHorizontal: 8,
    marginHorizontal: -8,
  },
  
  // Modal styles
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  modalHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  modalIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '500',
  },
  modalSubtitle: {
    fontSize: 14,
    marginTop: 2,
  },
  closeButton: {
    padding: 4,
  },
  modalContent: {
    flex: 1,
  },
  modalContentContainer: {
    padding: 20,
  },
  
  // Description card
  descriptionCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  descriptionText: {
    fontSize: 15,
    lineHeight: 22,
  },
  
  // Section title
  sectionTitle: {
    fontSize: 14,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  
  // Event items
  eventItem: {
    borderLeftWidth: 3,
    paddingLeft: 12,
    marginBottom: 16,
  },
  eventHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  eventYear: {
    fontSize: 13,
    marginRight: 8,
  },
  highImpactBadge: {
    paddingVertical: 2,
    paddingHorizontal: 8,
    borderRadius: 10,
  },
  highImpactText: {
    fontSize: 10,
    fontWeight: '500',
  },
  eventTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  eventCategory: {
    fontSize: 13,
    marginTop: 2,
  },
  
  // Reflection card
  reflectionCard: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 16,
    marginTop: 24,
    alignItems: 'center',
  },
  reflectionIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  reflectionTitle: {
    fontSize: 15,
    fontWeight: '500',
    marginBottom: 8,
  },
  reflectionText: {
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
  
  // Intense Periods section
  intensePeriodsSection: {
    marginTop: 24,
  },
  sectionHeader: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  
  // Storm card
  stormCard: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 16,
    marginBottom: 12,
  },
  stormCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  stormCardIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  stormCardLabel: {
    fontSize: 17,
    fontWeight: '500',
    flex: 1,
  },
  intensityBadge: {
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 10,
  },
  intensityText: {
    fontSize: 11,
    fontWeight: '500',
  },
  stormCardDescription: {
    fontSize: 14,
    marginBottom: 12,
  },
  stormCardEvents: {
    marginBottom: 8,
  },
  stormEventPreview: {
    fontSize: 13,
    marginBottom: 4,
  },
  stormEventMore: {
    fontSize: 12,
    fontStyle: 'italic',
  },
  stormCardFooter: {
    alignItems: 'flex-end',
  },
});
