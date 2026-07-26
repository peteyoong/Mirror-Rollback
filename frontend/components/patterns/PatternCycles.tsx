/**
 * PatternCycles Component
 * 
 * Displays pattern cycles - groupings of timeline events that show
 * how a detected life pattern tends to unfold in phases.
 * 
 * Design: Calm, structured, easy to scan
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { getCategoryColor, TimelineEvent } from './PatternTimeline';

// =============================================================================
// TYPES
// =============================================================================

export interface PatternCycle {
  label: string;
  years: number[];
  events: TimelineEvent[];
  summary: string;
  event_count?: number;
}

interface PatternCyclesProps {
  cycles: PatternCycle[];
  onEventPress: (event: TimelineEvent) => void;
}

// =============================================================================
// CYCLE CARD COMPONENT
// =============================================================================

interface CycleCardProps {
  cycle: PatternCycle;
  onEventPress: (event: TimelineEvent) => void;
  theme: any;
}

function CycleCard({ cycle, onEventPress, theme }: CycleCardProps) {
  // Format years as a range
  const yearsText = cycle.years.length > 1
    ? `${cycle.years[0]} → ${cycle.years[cycle.years.length - 1]}`
    : `${cycle.years[0]}`;
  
  return (
    <View style={[styles.cycleCard, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
      {/* Header */}
      <View style={styles.cycleHeader}>
        <View style={[styles.cycleLabelBadge, { backgroundColor: 'rgba(139, 92, 246, 0.1)' }]}>
          <Text style={[styles.cycleLabelText, { color: '#8B5CF6' }]}>{cycle.label}</Text>
        </View>
        <Text style={[styles.cycleYears, { color: theme.textSecondary }]}>{yearsText}</Text>
      </View>
      
      {/* Summary */}
      <Text style={[styles.cycleSummary, { color: theme.text }]}>
        {cycle.summary}
      </Text>
      
      {/* Events */}
      <View style={styles.cycleEvents}>
        {cycle.events.map((event, index) => {
          const categoryColor = getCategoryColor(event.category);
          const hasDecision = !!(event.decision_text || event.decision_reflection);
          
          return (
            <TouchableOpacity
              key={event.id || `${event.year}-${index}`}
              style={[styles.cycleEventItem, { borderColor: theme.border }]}
              onPress={() => onEventPress(event)}
              activeOpacity={0.7}
            >
              <View style={styles.cycleEventLeft}>
                <View style={[styles.cycleEventYearBadge, { backgroundColor: `${categoryColor}15` }]}>
                  <Text style={[styles.cycleEventYear, { color: categoryColor }]}>{event.year}</Text>
                </View>
                <View style={styles.cycleEventInfo}>
                  <Text style={[styles.cycleEventTitle, { color: theme.text }]} numberOfLines={1}>
                    {event.title}
                  </Text>
                  <View style={styles.cycleEventMeta}>
                    <View style={[styles.cycleEventCategoryDot, { backgroundColor: categoryColor }]} />
                    <Text style={[styles.cycleEventCategory, { color: theme.textSecondary }]}>
                      {event.category}
                    </Text>
                  </View>
                </View>
              </View>
              {hasDecision && (
                <View style={[styles.decisionIndicator, { backgroundColor: '#10B98115' }]}>
                  <Text style={styles.decisionIndicatorText}>✓</Text>
                </View>
              )}
            </TouchableOpacity>
          );
        })}
      </View>
      
      {/* More events indicator */}
      {cycle.event_count && cycle.event_count > cycle.events.length && (
        <Text style={[styles.moreEventsText, { color: theme.textTertiary }]}>
          +{cycle.event_count - cycle.events.length} more moment{cycle.event_count - cycle.events.length > 1 ? 's' : ''} in this cycle
        </Text>
      )}
    </View>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function PatternCycles({ cycles, onEventPress }: PatternCyclesProps) {
  const { theme } = useTheme();
  
  // Don't render if no cycles
  if (!cycles || cycles.length === 0) {
    return null;
  }
  
  return (
    <View style={styles.container}>
      {cycles.map((cycle, index) => (
        <CycleCard
          key={`cycle-${index}`}
          cycle={cycle}
          onEventPress={onEventPress}
          theme={theme}
        />
      ))}
    </View>
  );
}

// =============================================================================
// EMPTY STATE COMPONENT
// =============================================================================

export function PatternCyclesEmptyState() {
  const { theme } = useTheme();
  
  return (
    <View style={[styles.emptyState, { borderColor: theme.border }]}>
      <Text style={[styles.emptyStateText, { color: theme.textSecondary }]}>
        More moments may help reveal full cycles in this pattern.
      </Text>
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    gap: 12,
  },
  cycleCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
  },
  cycleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  cycleLabelBadge: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 6,
  },
  cycleLabelText: {
    fontSize: 12,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  cycleYears: {
    fontSize: 14,
    fontWeight: '500',
  },
  cycleSummary: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
    fontStyle: 'italic',
  },
  cycleEvents: {
    gap: 8,
  },
  cycleEventItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 10,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
  },
  cycleEventLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  cycleEventYearBadge: {
    paddingVertical: 3,
    paddingHorizontal: 6,
    borderRadius: 4,
    marginRight: 10,
  },
  cycleEventYear: {
    fontSize: 12,
    fontWeight: '500',
  },
  cycleEventInfo: {
    flex: 1,
  },
  cycleEventTitle: {
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 2,
  },
  cycleEventMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cycleEventCategoryDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    marginRight: 5,
  },
  cycleEventCategory: {
    fontSize: 11,
  },
  decisionIndicator: {
    width: 20,
    height: 20,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  decisionIndicatorText: {
    fontSize: 10,
    color: '#10B981',
    fontWeight: '500',
  },
  moreEventsText: {
    fontSize: 11,
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },
  emptyState: {
    borderWidth: 1,
    borderStyle: 'dashed',
    borderRadius: 10,
    padding: 16,
  },
  emptyStateText: {
    fontSize: 13,
    textAlign: 'center',
    fontStyle: 'italic',
  },
});
