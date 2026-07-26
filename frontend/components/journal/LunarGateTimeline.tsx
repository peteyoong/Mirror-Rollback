/**
 * Lunar Gate Timeline - Task 52
 * 
 * Visual horizontal timeline showing the Moon's movement through
 * Human Design gates across the lunar cycle for Reflector users.
 * 
 * Features:
 * - Gate progression across the cycle
 * - Journal entry markers
 * - Current position highlighting
 * - Interactive entry navigation
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Modal,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';

// =============================================================================
// TYPES
// =============================================================================

interface LunarEntry {
  id: string;
  content: string;
  created_at: string;
  lunar_day: number;
  moon_gate: number | null;
  gate_title: string | null;
  gate_theme: string | null;
}

interface TimelineDay {
  lunar_day: number;
  entries: LunarEntry[];
  entry_count: number;
  gates: number[];
}

interface LunarGateTimelineProps {
  currentLunarDay: number;
  currentGate: number | null;
  currentGateTitle: string | null;
  timeline: TimelineDay[];
  cycleProgress: number;
  onEntryPress?: (entry: LunarEntry) => void;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const LUNAR_COLORS = {
  moonlight: '#C0C8D4',
  silver: '#A8B2C0',
  glow: 'rgba(192, 200, 212, 0.15)',
  dimGlow: 'rgba(192, 200, 212, 0.08)',
};

const SCREEN_WIDTH = Dimensions.get('window').width;
const DAY_WIDTH = 56; // Width of each day marker
const TOTAL_DAYS = 30; // Approximate lunar cycle

// Generate approximate gate positions for the lunar cycle
// In reality, the Moon moves through all 64 gates in ~27.5 days
// This is a simplified representation
const GATE_SEQUENCE = [
  { day: 1, gate: 41, title: 'Contraction' },
  { day: 2, gate: 19, title: 'Wanting' },
  { day: 3, gate: 13, title: 'The Listener' },
  { day: 4, gate: 49, title: 'Principles' },
  { day: 5, gate: 30, title: 'Recognition of Feelings' },
  { day: 6, gate: 55, title: 'Spirit' },
  { day: 7, gate: 37, title: 'Friendship' },
  { day: 8, gate: 63, title: 'Doubt' },
  { day: 9, gate: 22, title: 'Openness' },
  { day: 10, gate: 36, title: 'Crisis' },
  { day: 11, gate: 25, title: 'Innocence' },
  { day: 12, gate: 17, title: 'Opinions' },
  { day: 13, gate: 21, title: 'The Hunter' },
  { day: 14, gate: 51, title: 'Shock' },
  { day: 15, gate: 42, title: 'Growth' },
  { day: 16, gate: 3, title: 'Ordering' },
  { day: 17, gate: 27, title: 'Caring' },
  { day: 18, gate: 24, title: 'Rationalization' },
  { day: 19, gate: 2, title: 'The Receptive' },
  { day: 20, gate: 23, title: 'Assimilation' },
  { day: 21, gate: 8, title: 'Contribution' },
  { day: 22, gate: 20, title: 'The Now' },
  { day: 23, gate: 16, title: 'Skills' },
  { day: 24, gate: 35, title: 'Change' },
  { day: 25, gate: 45, title: 'The Gatherer' },
  { day: 26, gate: 12, title: 'Caution' },
  { day: 27, gate: 15, title: 'Extremes' },
  { day: 28, gate: 52, title: 'Stillness' },
  { day: 29, gate: 39, title: 'Provocation' },
];

// =============================================================================
// COMPONENT
// =============================================================================

export default function LunarGateTimeline({
  currentLunarDay,
  currentGate,
  currentGateTitle,
  timeline,
  cycleProgress,
  onEntryPress,
}: LunarGateTimelineProps) {
  const { theme } = useTheme();
  const scrollViewRef = useRef<ScrollView>(null);
  const [selectedEntry, setSelectedEntry] = useState<LunarEntry | null>(null);
  const [entryModalVisible, setEntryModalVisible] = useState(false);

  // Create a map of days with entries for quick lookup
  const entriesByDay = new Map<number, LunarEntry[]>();
  timeline.forEach(day => {
    entriesByDay.set(day.lunar_day, day.entries);
  });

  // Scroll to current day on mount
  useEffect(() => {
    const timeout = setTimeout(() => {
      const scrollPosition = Math.max(0, (Math.round(currentLunarDay) - 3) * DAY_WIDTH);
      scrollViewRef.current?.scrollTo({ x: scrollPosition, animated: true });
    }, 300);
    return () => clearTimeout(timeout);
  }, [currentLunarDay]);

  const handleDayPress = (day: number) => {
    const entries = entriesByDay.get(day);
    if (entries && entries.length > 0) {
      if (entries.length === 1) {
        setSelectedEntry(entries[0]);
        setEntryModalVisible(true);
      } else {
        // Multiple entries - show the first one, user can navigate in modal
        setSelectedEntry(entries[0]);
        setEntryModalVisible(true);
      }
    }
  };

  const handleEntrySelect = (entry: LunarEntry) => {
    setEntryModalVisible(false);
    onEntryPress?.(entry);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const truncateContent = (content: string, maxLength: number = 80) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength).trim() + '...';
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.title, { color: LUNAR_COLORS.moonlight }]}>
          LUNAR GATE PROGRESSION
        </Text>
        <Text style={[styles.description, { color: theme.textSecondary }]}>
          The Moon moves through different gates across the lunar cycle.{'\n'}
          Reflectors may notice their perspective shifting as these gates activate.
        </Text>
      </View>

      {/* Current Position Highlight */}
      <View style={[styles.currentPosition, { backgroundColor: LUNAR_COLORS.glow }]}>
        <Text style={styles.currentIcon}>🌙</Text>
        <View style={styles.currentInfo}>
          <Text style={[styles.currentLabel, { color: LUNAR_COLORS.silver }]}>
            TODAY
          </Text>
          <Text style={[styles.currentDay, { color: theme.text }]}>
            Day {Math.round(currentLunarDay)}
          </Text>
          {currentGate && (
            <Text style={[styles.currentGate, { color: LUNAR_COLORS.moonlight }]}>
              Gate {currentGate} — {currentGateTitle}
            </Text>
          )}
        </View>
      </View>

      {/* Cycle Progress Bar */}
      <View style={styles.progressSection}>
        <View style={[styles.progressTrack, { backgroundColor: LUNAR_COLORS.dimGlow }]}>
          <View 
            style={[
              styles.progressFill,
              { width: `${cycleProgress * 100}%`, backgroundColor: LUNAR_COLORS.moonlight }
            ]} 
          />
          <View 
            style={[
              styles.progressMarker,
              { left: `${cycleProgress * 100}%` }
            ]}
          />
        </View>
        <View style={styles.progressLabels}>
          <Text style={[styles.progressLabel, { color: theme.textTertiary }]}>New Moon</Text>
          <Text style={[styles.progressLabel, { color: theme.textTertiary }]}>Full</Text>
          <Text style={[styles.progressLabel, { color: theme.textTertiary }]}>New Moon</Text>
        </View>
      </View>

      {/* Timeline Scroll */}
      <ScrollView
        ref={scrollViewRef}
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.timelineContent}
        style={styles.timeline}
      >
        {GATE_SEQUENCE.map((item) => {
          const isToday = Math.round(currentLunarDay) === item.day;
          const hasEntries = entriesByDay.has(item.day);
          const entryCount = entriesByDay.get(item.day)?.length || 0;
          const isPast = item.day < Math.round(currentLunarDay);
          
          return (
            <TouchableOpacity
              key={item.day}
              style={[
                styles.dayMarker,
                isToday && styles.dayMarkerToday,
                { borderColor: isToday ? LUNAR_COLORS.moonlight : theme.border }
              ]}
              onPress={() => hasEntries && handleDayPress(item.day)}
              activeOpacity={hasEntries ? 0.7 : 1}
              disabled={!hasEntries}
            >
              {/* Day Number */}
              <Text style={[
                styles.dayNumber,
                { color: isToday ? LUNAR_COLORS.moonlight : isPast ? theme.textTertiary : theme.textSecondary }
              ]}>
                {item.day}
              </Text>
              
              {/* Gate Info */}
              <View style={[
                styles.gateBox,
                { backgroundColor: isToday ? LUNAR_COLORS.glow : LUNAR_COLORS.dimGlow }
              ]}>
                <Text style={[
                  styles.gateNumber,
                  { color: isToday ? LUNAR_COLORS.moonlight : theme.textSecondary }
                ]}>
                  {item.gate}
                </Text>
              </View>
              
              {/* Gate Title (abbreviated) */}
              <Text 
                style={[styles.gateTitle, { color: theme.textTertiary }]}
                numberOfLines={1}
              >
                {item.title.length > 8 ? item.title.substring(0, 7) + '…' : item.title}
              </Text>
              
              {/* Entry Indicator */}
              {hasEntries && (
                <View style={[styles.entryIndicator, { backgroundColor: LUNAR_COLORS.moonlight }]}>
                  <Text style={styles.entryIndicatorText}>
                    {entryCount}
                  </Text>
                </View>
              )}
              
              {/* Today Marker */}
              {isToday && (
                <View style={[styles.todayMarker, { backgroundColor: LUNAR_COLORS.moonlight }]} />
              )}
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {/* Legend */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: LUNAR_COLORS.moonlight }]} />
          <Text style={[styles.legendText, { color: theme.textTertiary }]}>Today</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, styles.legendEntryDot, { backgroundColor: LUNAR_COLORS.moonlight }]} />
          <Text style={[styles.legendText, { color: theme.textTertiary }]}>Has entry</Text>
        </View>
      </View>

      {/* Entry Preview Modal */}
      <Modal
        visible={entryModalVisible}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setEntryModalVisible(false)}
      >
        <TouchableOpacity 
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setEntryModalVisible(false)}
        >
          <View style={[styles.modalContent, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            {selectedEntry && (
              <>
                <View style={styles.modalHeader}>
                  <Text style={[styles.modalDay, { color: LUNAR_COLORS.moonlight }]}>
                    Day {Math.round(selectedEntry.lunar_day)}
                  </Text>
                  {selectedEntry.gate_title && (
                    <Text style={[styles.modalGate, { color: theme.textSecondary }]}>
                      Gate {selectedEntry.moon_gate} — {selectedEntry.gate_title}
                    </Text>
                  )}
                  <Text style={[styles.modalDate, { color: theme.textTertiary }]}>
                    {formatDate(selectedEntry.created_at)}
                  </Text>
                </View>
                
                <Text style={[styles.modalContent, { color: theme.text }]}>
                  {truncateContent(selectedEntry.content, 200)}
                </Text>
                
                <TouchableOpacity
                  style={[styles.modalButton, { backgroundColor: LUNAR_COLORS.moonlight }]}
                  onPress={() => handleEntrySelect(selectedEntry)}
                >
                  <Text style={styles.modalButtonText}>View Full Entry</Text>
                </TouchableOpacity>
                
                {/* Show count if multiple entries on this day */}
                {entriesByDay.get(Math.round(selectedEntry.lunar_day))?.length! > 1 && (
                  <Text style={[styles.moreEntries, { color: theme.textTertiary }]}>
                    +{entriesByDay.get(Math.round(selectedEntry.lunar_day))!.length - 1} more {entriesByDay.get(Math.round(selectedEntry.lunar_day))!.length - 1 === 1 ? 'entry' : 'entries'} on this day
                  </Text>
                )}
              </>
            )}
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
    overflow: 'hidden',
  },
  header: {
    padding: 16,
    paddingBottom: 12,
  },
  title: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 1,
    marginBottom: 8,
  },
  description: {
    fontSize: 13,
    lineHeight: 19,
  },
  currentPosition: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginBottom: 12,
    padding: 12,
    borderRadius: 10,
    gap: 12,
  },
  currentIcon: {
    fontSize: 24,
  },
  currentInfo: {
    flex: 1,
  },
  currentLabel: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  currentDay: {
    fontSize: 16,
    fontWeight: '500',
  },
  currentGate: {
    fontSize: 13,
    marginTop: 2,
  },
  progressSection: {
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  progressTrack: {
    height: 4,
    borderRadius: 2,
    position: 'relative',
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
  },
  progressMarker: {
    position: 'absolute',
    top: -3,
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#fff',
    marginLeft: -5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.3,
    shadowRadius: 2,
    elevation: 2,
  },
  progressLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 6,
  },
  progressLabel: {
    fontSize: 10,
  },
  timeline: {
    paddingLeft: 16,
  },
  timelineContent: {
    paddingRight: 32,
    paddingBottom: 8,
  },
  dayMarker: {
    width: DAY_WIDTH,
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'transparent',
    marginRight: 4,
    position: 'relative',
  },
  dayMarkerToday: {
    borderWidth: 1,
  },
  dayNumber: {
    fontSize: 11,
    fontWeight: '500',
    marginBottom: 4,
  },
  gateBox: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  gateNumber: {
    fontSize: 13,
    fontWeight: '500',
  },
  gateTitle: {
    fontSize: 9,
    textAlign: 'center',
  },
  entryIndicator: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 16,
    height: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  entryIndicatorText: {
    fontSize: 9,
    fontWeight: '500',
    color: '#1A1D24',
  },
  todayMarker: {
    position: 'absolute',
    bottom: 2,
    width: 20,
    height: 3,
    borderRadius: 1.5,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 20,
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(192, 200, 212, 0.2)',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendEntryDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  legendText: {
    fontSize: 11,
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalContent: {
    width: '100%',
    maxWidth: 340,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
  },
  modalHeader: {
    marginBottom: 12,
  },
  modalDay: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  modalGate: {
    fontSize: 13,
    marginBottom: 2,
  },
  modalDate: {
    fontSize: 11,
  },
  modalButton: {
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16,
  },
  modalButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1A1D24',
  },
  moreEntries: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 10,
  },
});

export type { LunarGateTimelineProps, LunarEntry, TimelineDay };
