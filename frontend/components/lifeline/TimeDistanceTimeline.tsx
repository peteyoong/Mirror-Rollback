/**
 * TimeDistanceTimeline
 * 
 * Transforms the Lifeline timeline from evenly spaced events into a 
 * time-distance visualization that reflects real spacing between life events.
 * 
 * Features:
 * - Time-proportional spacing between events
 * - "Quiet years" markers for gaps > 5 years
 * - Memory Echo prompts for gap recall
 * - Pattern Storm detection (Intense Periods)
 * - Animated reveal on first load
 * - First event reinforcement messages
 */

import React, { useEffect, useRef, useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import LifelineEventCard, { LifelineEvent } from './LifelineEventCard';
import MemoryEchoPrompt, { 
  generateEchoData, 
  MemoryEchoData, 
  EarlierMomentPrefill,
  canShowEcho,
} from './MemoryEchoPrompt';
import {
  detectPatternStorms,
  getStormForEvent,
  isFirstEventInStorm,
  StormBadge,
  StormModal,
  PatternStorm,
} from './PatternStorm';
import { ChartResonance } from './ChartResonance';

// =============================================================================
// CONSTANTS
// =============================================================================

const MIN_SPACING = 40;   // Minimum gap between events (pixels)
const MAX_SPACING = 120;  // Maximum gap between events (pixels)
const QUIET_YEARS_THRESHOLD = 5; // Years gap to trigger "Quiet years" label
const PIXELS_PER_YEAR = 15; // Base scale for year-to-pixel conversion

interface Props {
  events: LifelineEvent[];
  onEditEvent?: (event: LifelineEvent) => void;
  onDeleteEvent?: (eventId: string) => Promise<void>;
  onAddEarlierMoment?: (prefill: EarlierMomentPrefill) => void;
  isCompact?: boolean;
  isFirstReveal?: boolean;
  showEarlyMessages?: boolean; // Show "Your life is becoming visible" for 1-3 events
  newEventAdded?: LifelineEvent | null; // Recently added event to trigger memory echo
  resonanceMap?: Record<string, ChartResonance[]>; // Resonance data keyed by event_id
}

interface TimelineNode {
  event: LifelineEvent;
  spacing: number; // Spacing above this event
  showQuietYears: boolean;
  quietYearsCount?: number;
  gapStartYear?: number;
  gapEndYear?: number;
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Calculate time-proportional spacing between events
 */
function calculateTimelineNodes(events: LifelineEvent[]): TimelineNode[] {
  if (events.length === 0) return [];
  
  // Sort events by year (oldest first)
  const sortedEvents = [...events].sort((a, b) => {
    const yearA = a.year || 0;
    const yearB = b.year || 0;
    return yearA - yearB;
  });
  
  return sortedEvents.map((event, index) => {
    if (index === 0) {
      // First event has no spacing above
      return {
        event,
        spacing: 0,
        showQuietYears: false,
      };
    }
    
    const prevEvent = sortedEvents[index - 1];
    const prevYear = prevEvent.year || 0;
    const currYear = event.year || 0;
    const yearGap = Math.max(0, currYear - prevYear);
    
    // Calculate spacing based on year gap
    let spacing = yearGap * PIXELS_PER_YEAR;
    
    // Clamp to min/max
    spacing = Math.max(MIN_SPACING, Math.min(MAX_SPACING, spacing));
    
    // Check for quiet years
    const showQuietYears = yearGap >= QUIET_YEARS_THRESHOLD;
    
    return {
      event,
      spacing,
      showQuietYears,
      quietYearsCount: yearGap,
      gapStartYear: prevYear,
      gapEndYear: currYear,
    };
  });
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function TimeDistanceTimeline({ 
  events, 
  onEditEvent,
  onDeleteEvent,
  onAddEarlierMoment,
  isCompact = false,
  isFirstReveal = false,
  showEarlyMessages = true,
  newEventAdded = null,
  resonanceMap = {},
}: Props) {
  const { theme } = useTheme();
  
  // Animation state
  const [isAnimating, setIsAnimating] = useState(isFirstReveal);
  const [visibleCount, setVisibleCount] = useState(isFirstReveal ? 0 : events.length);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  
  // Memory echo state
  const [activeEcho, setActiveEcho] = useState<MemoryEchoData | null>(null);
  const [echoGapIndex, setEchoGapIndex] = useState<number | null>(null);
  const [canShowNewEventEcho, setCanShowNewEventEcho] = useState(false);
  
  // Storm state
  const [selectedStorm, setSelectedStorm] = useState<PatternStorm | null>(null);
  
  // Calculate timeline nodes with spacing
  const timelineNodes = calculateTimelineNodes(events);
  
  // Detect pattern storms
  const storms = useMemo(() => detectPatternStorms(events), [events]);
  
  // Check if we can show echoes
  useEffect(() => {
    canShowEcho().then(setCanShowNewEventEcho);
  }, []);
  
  // Trigger memory echo when a new event is added
  useEffect(() => {
    if (newEventAdded && canShowNewEventEcho && !activeEcho) {
      const echo = generateEchoData('new_event', {
        category: newEventAdded.category,
        year: newEventAdded.year,
      });
      setActiveEcho(echo);
      setEchoGapIndex(null); // Show at top, not in gap
    }
  }, [newEventAdded, canShowNewEventEcho]);
  
  // Run reveal animation on first mount
  useEffect(() => {
    if (isFirstReveal && events.length > 0) {
      // Fade in the reveal message
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: false,
      }).start();
      
      // Sequentially reveal each event
      const revealInterval = setInterval(() => {
        setVisibleCount(prev => {
          if (prev >= events.length) {
            clearInterval(revealInterval);
            setIsAnimating(false);
            return prev;
          }
          return prev + 1;
        });
      }, 400);
      
      return () => clearInterval(revealInterval);
    }
  }, [isFirstReveal, events.length]);
  
  // Update visible count when not animating
  useEffect(() => {
    if (!isFirstReveal) {
      setVisibleCount(events.length);
    }
  }, [events.length, isFirstReveal]);
  
  // Handle memory echo dismissal
  const handleDismissEcho = () => {
    setActiveEcho(null);
    setEchoGapIndex(null);
  };
  
  // Handle add earlier moment from echo
  const handleAddEarlierMoment = (prefill: EarlierMomentPrefill) => {
    setActiveEcho(null);
    setEchoGapIndex(null);
    if (onAddEarlierMoment) {
      onAddEarlierMoment(prefill);
    }
  };
  
  // Handle showing gap echo
  const handleShowGapEcho = (index: number, gapStartYear?: number, gapEndYear?: number) => {
    if (!canShowNewEventEcho || activeEcho) return;
    
    const echo = generateEchoData('timeline_gap', {
      gapStartYear,
      gapEndYear,
    });
    setActiveEcho(echo);
    setEchoGapIndex(index);
  };
  
  if (events.length === 0) {
    return null;
  }
  
  return (
    <View style={styles.container}>
      {/* Reveal message for pattern unlock */}
      {isFirstReveal && (
        <Animated.View style={[styles.revealMessage, { opacity: fadeAnim }]}>
          <Text style={[styles.revealText, { color: theme.text }]}>
            Your life does not change evenly.
          </Text>
          <Text style={[styles.revealTextSecond, { color: theme.text }]}>
            It changes in moments.
          </Text>
        </Animated.View>
      )}
      
      {/* Memory Echo for new event (at top) */}
      {activeEcho && echoGapIndex === null && (
        <MemoryEchoPrompt
          echo={activeEcho}
          onAddEarlierMoment={handleAddEarlierMoment}
          onDismiss={handleDismissEcho}
          variant="card"
        />
      )}
      
      {/* Timeline */}
      <View style={styles.timeline}>
        {timelineNodes.slice(0, visibleCount).map((node, index) => {
          // Check if this event is part of a storm
          const eventStorm = getStormForEvent(node.event, storms);
          const isStormStart = isFirstEventInStorm(node.event, storms);
          
          return (
            <View key={node.event.id}>
              {/* Storm badge - show before first event in storm */}
              {isStormStart && eventStorm && (
                <View style={styles.stormBadgeContainer}>
                  <StormBadge 
                    storm={eventStorm} 
                    onPress={() => setSelectedStorm(eventStorm)}
                    compact={false}
                  />
                </View>
              )}
              
              {/* Spacing and quiet years marker */}
              {node.spacing > 0 && (
                <View style={[styles.spacer, { height: node.spacing }]}>
                  {/* Vertical line */}
                  <View style={[styles.verticalLine, { backgroundColor: theme.border }]} />
                  
                  {/* Quiet years label with clickable Memory Echo trigger */}
                  {node.showQuietYears && node.quietYearsCount && (
                    <View style={styles.quietYearsContainer}>
                      <Text style={[styles.quietYearsText, { color: theme.textTertiary }]}>
                        Quiet years
                      </Text>
                      <Text style={[styles.quietYearsCount, { color: theme.textTertiary }]}>
                        {node.quietYearsCount} years
                      </Text>
                    </View>
                  )}
                  
                  {/* Memory Echo prompt for this gap */}
                  {activeEcho && echoGapIndex === index && (
                    <View style={styles.gapEchoContainer}>
                      <MemoryEchoPrompt
                        echo={activeEcho}
                        onAddEarlierMoment={handleAddEarlierMoment}
                        onDismiss={handleDismissEcho}
                        variant="inline"
                      />
                    </View>
                  )}
                </View>
              )}
              
              {/* Event card - with storm highlight if part of storm */}
              {eventStorm ? (
                <View style={[styles.stormHighlight, { backgroundColor: `${theme.accent}05` }]}>
                  <LifelineEventCard
                    event={node.event}
                    onEdit={onEditEvent}
                    isCompact={isCompact}
                    resonances={resonanceMap[node.event.id] || []}
                  />
                </View>
              ) : (
                <LifelineEventCard
                  event={node.event}
                  onEdit={onEditEvent}
                  isCompact={isCompact}
                  resonances={resonanceMap[node.event.id] || []}
                />
              )}
            </View>
          );
        })}
      </View>
      
      {/* Storm Detail Modal */}
      <StormModal
        storm={selectedStorm}
        visible={!!selectedStorm}
        onClose={() => setSelectedStorm(null)}
      />
      
      {/* Early event reinforcement message */}
      {showEarlyMessages && events.length <= 3 && events.length > 0 && (
        <View style={styles.earlyMessageContainer}>
          <Text style={[styles.earlyMessage, { color: theme.textSecondary }]}>
            Your life is becoming visible.
          </Text>
        </View>
      )}
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  
  // Reveal message
  revealMessage: {
    paddingVertical: 24,
    paddingHorizontal: 4,
    marginBottom: 20,
  },
  revealText: {
    fontSize: 18,
    fontWeight: '500',
    textAlign: 'center',
    marginBottom: 4,
  },
  revealTextSecond: {
    fontSize: 18,
    fontWeight: '500',
    textAlign: 'center',
  },
  
  // Timeline
  timeline: {
    paddingLeft: 4,
  },
  
  // Spacing between events
  spacer: {
    position: 'relative',
    justifyContent: 'center',
    marginLeft: 30, // Align with timeline connector
  },
  verticalLine: {
    position: 'absolute',
    left: 9, // Center of timeline dot
    top: 0,
    bottom: 0,
    width: 2,
  },
  
  // Quiet years marker
  quietYearsContainer: {
    position: 'absolute',
    left: 24,
    right: 0,
    alignItems: 'flex-start',
    paddingLeft: 8,
  },
  quietYearsText: {
    fontSize: 12,
    fontStyle: 'italic',
  },
  quietYearsCount: {
    fontSize: 11,
    marginTop: 2,
  },
  
  // Gap echo container (inside spacer)
  gapEchoContainer: {
    position: 'absolute',
    left: 20,
    right: 0,
    top: '50%',
    transform: [{ translateY: -30 }],
  },
  
  // Early message
  earlyMessageContainer: {
    paddingTop: 20,
    paddingBottom: 10,
    alignItems: 'center',
  },
  earlyMessage: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  
  // Storm visualization
  stormBadgeContainer: {
    marginBottom: 12,
    marginLeft: 30,
    paddingLeft: 20,
  },
  stormHighlight: {
    borderRadius: 12,
    paddingHorizontal: 4,
    marginHorizontal: -4,
    paddingVertical: 2,
  },
});
