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
 * - Era/chapter markers for narrative orientation
 * - Year grouping for multi-event years
 * - Jump destination highlighting
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

// Era/Chapter definitions based on typical life stages
interface LifeEra {
  id: string;
  label: string;
  minAge: number;
  maxAge: number;
}

const LIFE_ERAS: LifeEra[] = [
  { id: 'early', label: 'Early Life', minAge: 0, maxAge: 12 },
  { id: 'formative', label: 'Formative Years', minAge: 13, maxAge: 22 },
  { id: 'building', label: 'Building', minAge: 23, maxAge: 35 },
  { id: 'establishing', label: 'Establishing', minAge: 36, maxAge: 50 },
  { id: 'midlife', label: 'Midlife', minAge: 51, maxAge: 65 },
  { id: 'later', label: 'Later Years', minAge: 66, maxAge: 150 },
];

interface Props {
  events: LifelineEvent[];
  onEditEvent?: (event: LifelineEvent) => void;
  onDeleteEvent?: (eventId: string) => Promise<void>;
  onAddEarlierMoment?: (prefill: EarlierMomentPrefill) => void;
  isCompact?: boolean;
  isFirstReveal?: boolean;
  showEarlyMessages?: boolean;
  newEventAdded?: LifelineEvent | null;
  resonanceMap?: Record<string, ChartResonance[]>;
  onEventLayout?: (year: number, y: number) => void;
  highlightedYear?: number | null;
  birthYear?: number;
}

interface TimelineNode {
  event: LifelineEvent;
  spacing: number; // Spacing above this event
  showQuietYears: boolean;
  quietYearsCount?: number;
  gapStartYear?: number;
  gapEndYear?: number;
  isFirstInYear: boolean; // First event in this year (for year markers)
  eventsInYear: number; // Total events in this year
  showEraMarker: boolean; // Should show era transition marker
  eraLabel?: string; // Era label to show
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Get era label for a given age
 */
function getEraForAge(age: number): LifeEra | undefined {
  return LIFE_ERAS.find(era => age >= era.minAge && age <= era.maxAge);
}

/**
 * Calculate time-proportional spacing between events with era markers
 */
function calculateTimelineNodes(events: LifelineEvent[], birthYear?: number): TimelineNode[] {
  if (events.length === 0) return [];
  
  // Sort events by year (oldest first)
  const sortedEvents = [...events].sort((a, b) => {
    const yearA = a.year || 0;
    const yearB = b.year || 0;
    return yearA - yearB;
  });
  
  // Count events per year
  const eventsPerYear = new Map<number, number>();
  sortedEvents.forEach(e => {
    const year = e.year || 0;
    eventsPerYear.set(year, (eventsPerYear.get(year) || 0) + 1);
  });
  
  // Track first event per year and current era
  const seenYears = new Set<number>();
  let lastEra: string | undefined;
  
  return sortedEvents.map((event, index) => {
    const eventYear = event.year || 0;
    const isFirstInYear = !seenYears.has(eventYear);
    seenYears.add(eventYear);
    
    // Calculate era
    let showEraMarker = false;
    let eraLabel: string | undefined;
    
    if (birthYear && isFirstInYear) {
      const age = eventYear - birthYear;
      const currentEra = getEraForAge(age);
      if (currentEra && currentEra.id !== lastEra) {
        showEraMarker = true;
        eraLabel = currentEra.label;
        lastEra = currentEra.id;
      }
    }
    
    if (index === 0) {
      return {
        event,
        spacing: 0,
        showQuietYears: false,
        isFirstInYear,
        eventsInYear: eventsPerYear.get(eventYear) || 1,
        showEraMarker,
        eraLabel,
      };
    }
    
    const prevEvent = sortedEvents[index - 1];
    const prevYear = prevEvent.year || 0;
    const yearGap = Math.max(0, eventYear - prevYear);
    
    // Calculate spacing based on year gap
    let spacing = yearGap * PIXELS_PER_YEAR;
    spacing = Math.max(MIN_SPACING, Math.min(MAX_SPACING, spacing));
    
    // Reduce spacing for events in the same year (cluster them)
    if (eventYear === prevYear) {
      spacing = 16; // Tight clustering for same-year events
    }
    
    const showQuietYears = yearGap >= QUIET_YEARS_THRESHOLD;
    
    return {
      event,
      spacing,
      showQuietYears,
      quietYearsCount: yearGap,
      gapStartYear: prevYear,
      gapEndYear: eventYear,
      isFirstInYear,
      eventsInYear: eventsPerYear.get(eventYear) || 1,
      showEraMarker,
      eraLabel,
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
  onEventLayout,
  highlightedYear,
  birthYear,
}: Props) {
  const { theme } = useTheme();
  
  // Highlight animation
  const highlightAnim = useRef(new Animated.Value(0)).current;
  
  // Animate highlight when year changes
  useEffect(() => {
    if (highlightedYear) {
      Animated.sequence([
        Animated.timing(highlightAnim, { toValue: 1, duration: 300, useNativeDriver: false }),
        Animated.delay(2000),
        Animated.timing(highlightAnim, { toValue: 0, duration: 500, useNativeDriver: false }),
      ]).start();
    }
  }, [highlightedYear]);
  
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
  const timelineNodes = useMemo(() => calculateTimelineNodes(events, birthYear), [events, birthYear]);
  
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
              
              {/* Era marker - when entering a new life chapter */}
              {node.showEraMarker && node.eraLabel && (
                <View style={[styles.eraMarker, { borderColor: theme.border }]}>
                  <View style={[styles.eraLine, { backgroundColor: theme.border }]} />
                  <Text style={[styles.eraLabel, { color: theme.textTertiary, backgroundColor: theme.background }]}>
                    {node.eraLabel}
                  </Text>
                  <View style={[styles.eraLine, { backgroundColor: theme.border }]} />
                </View>
              )}
              
              {/* Year marker for first event in a year with multiple events */}
              {node.isFirstInYear && node.eventsInYear > 1 && (
                <View style={[styles.yearMarker, { backgroundColor: theme.surfaceAlt || theme.surface }]}>
                  <Text style={[styles.yearMarkerYear, { color: theme.textSecondary }]}>
                    {node.event.year}
                  </Text>
                  <Text style={[styles.yearMarkerCount, { color: theme.textTertiary }]}>
                    {node.eventsInYear} moments
                  </Text>
                </View>
              )}
              
              {/* Event card - with enhanced highlight for jump destination */}
              <Animated.View 
                style={[
                  eventStorm && styles.stormHighlight,
                  eventStorm && { backgroundColor: `${theme.accent}05` },
                  highlightedYear === node.event.year && styles.highlightedCard,
                  highlightedYear === node.event.year && { 
                    borderColor: theme.accent,
                    backgroundColor: highlightAnim.interpolate({
                      inputRange: [0, 1],
                      outputRange: ['transparent', `${theme.accent}10`],
                    }),
                  },
                ]}
                onLayout={(e) => onEventLayout?.(node.event.year || 0, e.nativeEvent.layout.y)}
              >
                {/* Jump indicator badge */}
                {highlightedYear === node.event.year && (
                  <Animated.View style={[
                    styles.jumpBadge, 
                    { 
                      backgroundColor: theme.accent,
                      opacity: highlightAnim,
                    }
                  ]}>
                    <Text style={styles.jumpBadgeText}>Jumped here</Text>
                  </Animated.View>
                )}
                
                <LifelineEventCard
                  event={node.event}
                  onEdit={onEditEvent}
                  onDelete={onDeleteEvent}
                  isCompact={isCompact}
                  resonances={resonanceMap[node.event.id] || []}
                />
              </Animated.View>
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
  highlightedCard: {
    borderWidth: 2,
    borderRadius: 14,
    padding: 4,
    overflow: 'hidden',
  },
  
  // Jump badge
  jumpBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    zIndex: 10,
  },
  jumpBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  
  // Era markers
  eraMarker: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 20,
    marginLeft: 20,
    paddingRight: 20,
  },
  eraLine: {
    flex: 1,
    height: 1,
  },
  eraLabel: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  
  // Year markers
  yearMarker: {
    marginLeft: 30,
    marginBottom: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  yearMarkerYear: {
    fontSize: 14,
    fontWeight: '600',
  },
  yearMarkerCount: {
    fontSize: 11,
    marginTop: 1,
  },
});
