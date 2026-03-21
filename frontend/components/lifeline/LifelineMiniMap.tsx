/**
 * LifelineMiniMap
 * 
 * A compact visual "life arc" showing the user's story at a glance.
 * - Horizontal timeline from birth year to current year
 * - Dots/markers for recorded moments
 * - Denser markers for years with multiple events
 * - Tap to navigate to that year in the timeline below
 */

import React, { useMemo, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  ScrollView,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { LifelineEvent } from './LifelineEventCard';
import { GapPromptData } from './LifelineGapPrompt';

const SCREEN_WIDTH = Dimensions.get('window').width;
const MAP_PADDING = 20;
const MAP_WIDTH = SCREEN_WIDTH - (MAP_PADDING * 2);

interface Props {
  events: LifelineEvent[];
  birthYear: number;
  currentYear?: number;
  gaps?: GapPromptData[];
  onYearPress: (year: number) => void;
  onGapPress?: (gap: GapPromptData) => void;
}

interface YearData {
  year: number;
  eventCount: number;
  events: LifelineEvent[];
  isGap?: boolean;
  gap?: GapPromptData;
}

export default function LifelineMiniMap({
  events,
  birthYear,
  currentYear = new Date().getFullYear(),
  gaps = [],
  onYearPress,
  onGapPress,
}: Props) {
  const { theme, isDark } = useTheme();
  
  // Calculate year range
  const totalYears = currentYear - birthYear + 1;
  const yearWidth = (MAP_WIDTH - 40) / Math.max(totalYears, 1); // -40 for end labels
  
  // Group events by year
  const yearData = useMemo(() => {
    const data: Map<number, YearData> = new Map();
    
    // Initialize all years
    for (let year = birthYear; year <= currentYear; year++) {
      data.set(year, { year, eventCount: 0, events: [] });
    }
    
    // Count events per year
    events.forEach(event => {
      if (event.year) {
        const existing = data.get(event.year);
        if (existing) {
          existing.eventCount++;
          existing.events.push(event);
        }
      }
    });
    
    // Mark gaps
    gaps.forEach(gap => {
      for (let year = gap.start_year; year <= gap.end_year; year++) {
        const existing = data.get(year);
        if (existing && existing.eventCount === 0) {
          existing.isGap = true;
          existing.gap = gap;
        }
      }
    });
    
    return data;
  }, [events, gaps, birthYear, currentYear]);
  
  // Find max events in any year for scaling
  const maxEventsInYear = useMemo(() => {
    let max = 0;
    yearData.forEach(d => {
      if (d.eventCount > max) max = d.eventCount;
    });
    return Math.max(max, 1);
  }, [yearData]);
  
  // Calculate position for a year
  const getYearPosition = (year: number) => {
    const offset = year - birthYear;
    return 20 + (offset * yearWidth); // 20px for left label space
  };
  
  // Get marker size based on event count
  const getMarkerSize = (eventCount: number) => {
    if (eventCount === 0) return 0;
    if (eventCount === 1) return 6;
    if (eventCount === 2) return 8;
    if (eventCount <= 4) return 10;
    return 12;
  };
  
  // Render decade markers
  const decadeMarkers = useMemo(() => {
    const markers: number[] = [];
    for (let year = Math.ceil(birthYear / 10) * 10; year <= currentYear; year += 10) {
      if (year > birthYear) {
        markers.push(year);
      }
    }
    return markers;
  }, [birthYear, currentYear]);
  
  const handleYearPress = (year: number, data: YearData) => {
    if (data.isGap && data.gap && onGapPress) {
      onGapPress(data.gap);
    } else {
      onYearPress(year);
    }
  };
  
  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header */}
      <View style={styles.headerSection}>
        <Text style={[styles.headerLabel, { color: theme.textSecondary }]}>
          YOUR STORY AT A GLANCE
        </Text>
        <Text style={[styles.headerSubtext, { color: theme.textTertiary }]}>
          From your earliest memories to now.
          {events.length >= 5 && ' Tap anywhere to jump to that part of your timeline.'}
        </Text>
      </View>
      
      {/* Timeline visualization */}
      <View style={styles.timelineContainer}>
        {/* Base line */}
        <View style={[styles.baseLine, { backgroundColor: theme.border }]} />
        
        {/* Birth year label */}
        <View style={[styles.yearLabel, { left: 0 }]}>
          <Text style={[styles.yearLabelText, { color: theme.textTertiary }]}>
            {birthYear}
          </Text>
        </View>
        
        {/* Current year label */}
        <View style={[styles.yearLabel, { right: 0 }]}>
          <Text style={[styles.yearLabelText, { color: theme.textTertiary }]}>
            {currentYear}
          </Text>
        </View>
        
        {/* Decade markers */}
        {decadeMarkers.map(year => (
          <View 
            key={`decade-${year}`}
            style={[
              styles.decadeMarker,
              { left: getYearPosition(year), backgroundColor: theme.border }
            ]}
          >
            <Text style={[styles.decadeText, { color: theme.textTertiary }]}>
              {year}
            </Text>
          </View>
        ))}
        
        {/* Event markers and gap spans */}
        {Array.from(yearData.values()).map((data) => {
          const position = getYearPosition(data.year);
          const markerSize = getMarkerSize(data.eventCount);
          
          // Gap visualization (subtle underline)
          if (data.isGap && data.year === data.gap?.start_year) {
            const gapWidth = ((data.gap.end_year - data.gap.start_year + 1) * yearWidth);
            return (
              <TouchableOpacity
                key={`gap-${data.year}`}
                style={[
                  styles.gapSpan,
                  {
                    left: position,
                    width: gapWidth,
                    backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)',
                  }
                ]}
                onPress={() => data.gap && onGapPress?.(data.gap)}
                activeOpacity={0.6}
              >
                <View style={[styles.gapDot, { backgroundColor: theme.textTertiary }]} />
              </TouchableOpacity>
            );
          }
          
          // Event marker
          if (markerSize > 0) {
            // Calculate opacity based on density
            const intensity = Math.min(data.eventCount / maxEventsInYear, 1);
            const opacity = 0.4 + (intensity * 0.6);
            
            return (
              <TouchableOpacity
                key={`event-${data.year}`}
                style={[
                  styles.eventMarker,
                  {
                    left: position - (markerSize / 2),
                    width: markerSize,
                    height: markerSize,
                    borderRadius: markerSize / 2,
                    backgroundColor: theme.accent,
                    opacity,
                  }
                ]}
                onPress={() => handleYearPress(data.year, data)}
                activeOpacity={0.6}
              >
                {data.eventCount > 2 && (
                  <Text style={styles.markerCount}>{data.eventCount}</Text>
                )}
              </TouchableOpacity>
            );
          }
          
          return null;
        })}
        
        {/* Current year indicator */}
        <View 
          style={[
            styles.currentYearIndicator,
            { right: 20, backgroundColor: theme.accent }
          ]}
        />
      </View>
      
      {/* Legend for users with data */}
      {events.length > 0 && (
        <View style={styles.legend}>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: theme.accent }]} />
            <Text style={[styles.legendText, { color: theme.textTertiary }]}>Recorded moment</Text>
          </View>
          {gaps.length > 0 && (
            <View style={styles.legendItem}>
              <View style={[styles.legendGap, { backgroundColor: theme.textTertiary }]} />
              <Text style={[styles.legendText, { color: theme.textTertiary }]}>Quiet period</Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  headerSection: {
    marginBottom: 16,
  },
  headerLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  headerSubtext: {
    fontSize: 13,
    lineHeight: 18,
  },
  timelineContainer: {
    height: 50,
    position: 'relative',
    marginVertical: 8,
  },
  baseLine: {
    position: 'absolute',
    top: 20,
    left: 20,
    right: 20,
    height: 2,
    borderRadius: 1,
  },
  yearLabel: {
    position: 'absolute',
    top: 30,
  },
  yearLabelText: {
    fontSize: 10,
    fontWeight: '500',
  },
  decadeMarker: {
    position: 'absolute',
    top: 16,
    width: 1,
    height: 10,
  },
  decadeText: {
    position: 'absolute',
    top: 14,
    fontSize: 9,
    width: 30,
    textAlign: 'center',
    marginLeft: -15,
  },
  eventMarker: {
    position: 'absolute',
    top: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  markerCount: {
    fontSize: 7,
    color: '#FFFFFF',
    fontWeight: '700',
  },
  gapSpan: {
    position: 'absolute',
    top: 18,
    height: 6,
    borderRadius: 3,
    justifyContent: 'center',
    alignItems: 'center',
  },
  gapDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    opacity: 0.5,
  },
  currentYearIndicator: {
    position: 'absolute',
    top: 14,
    width: 3,
    height: 14,
    borderRadius: 1.5,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(128,128,128,0.2)',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  legendGap: {
    width: 16,
    height: 4,
    borderRadius: 2,
    opacity: 0.5,
  },
  legendText: {
    fontSize: 11,
  },
});
