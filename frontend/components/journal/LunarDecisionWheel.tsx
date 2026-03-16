/**
 * Lunar Decision Wheel - Task 53
 * 
 * Circular visualization of the 29.5-day lunar cycle for Reflector users.
 * Shows gate progression, journal entry markers, and current position.
 * Helps Reflectors visualize how their perspective evolves across the cycle.
 */

import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Modal,
  ScrollView,
} from 'react-native';
import Svg, { 
  Circle, 
  Path, 
  G, 
  Text as SvgText,
  Defs,
  LinearGradient,
  Stop,
} from 'react-native-svg';
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

interface LunarDecisionWheelProps {
  currentLunarDay: number;
  currentGate: number | null;
  currentGateTitle: string | null;
  cycleProgress: number;
  timeline: TimelineDay[];
  activeTopic: string | null;
  onDayPress?: (day: number, entries: LunarEntry[]) => void;
  onAddEntry?: () => void;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const LUNAR_COLORS = {
  moonlight: '#C0C8D4',
  silver: '#A8B2C0',
  glow: 'rgba(192, 200, 212, 0.15)',
  dimGlow: 'rgba(192, 200, 212, 0.08)',
  accent: 'rgba(192, 200, 212, 0.25)',
};

const SCREEN_WIDTH = Dimensions.get('window').width;
const WHEEL_SIZE = Math.min(SCREEN_WIDTH - 48, 340);
const CENTER = WHEEL_SIZE / 2;
const OUTER_RADIUS = (WHEEL_SIZE / 2) - 8;
const INNER_RADIUS = OUTER_RADIUS - 50;
const GATE_LABEL_RADIUS = OUTER_RADIUS - 25;
const TOTAL_DAYS = 29;

// Gate sequence for the lunar cycle (simplified mapping)
const GATE_SEQUENCE: { [key: number]: { gate: number; title: string } } = {
  1: { gate: 41, title: 'Contraction' },
  2: { gate: 19, title: 'Wanting' },
  3: { gate: 13, title: 'Listener' },
  4: { gate: 49, title: 'Principles' },
  5: { gate: 30, title: 'Feelings' },
  6: { gate: 55, title: 'Spirit' },
  7: { gate: 37, title: 'Friendship' },
  8: { gate: 63, title: 'Doubt' },
  9: { gate: 22, title: 'Openness' },
  10: { gate: 36, title: 'Crisis' },
  11: { gate: 25, title: 'Innocence' },
  12: { gate: 17, title: 'Opinions' },
  13: { gate: 21, title: 'Hunter' },
  14: { gate: 51, title: 'Shock' },
  15: { gate: 42, title: 'Growth' },
  16: { gate: 3, title: 'Ordering' },
  17: { gate: 27, title: 'Caring' },
  18: { gate: 24, title: 'Rational' },
  19: { gate: 2, title: 'Receptive' },
  20: { gate: 23, title: 'Assimilate' },
  21: { gate: 8, title: 'Contribute' },
  22: { gate: 20, title: 'The Now' },
  23: { gate: 16, title: 'Skills' },
  24: { gate: 35, title: 'Change' },
  25: { gate: 45, title: 'Gatherer' },
  26: { gate: 12, title: 'Caution' },
  27: { gate: 15, title: 'Extremes' },
  28: { gate: 52, title: 'Stillness' },
  29: { gate: 39, title: 'Provoke' },
};

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

const polarToCartesian = (
  centerX: number,
  centerY: number,
  radius: number,
  angleInDegrees: number
) => {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians),
  };
};

const describeArc = (
  x: number,
  y: number,
  outerRadius: number,
  innerRadius: number,
  startAngle: number,
  endAngle: number
) => {
  const start = polarToCartesian(x, y, outerRadius, endAngle);
  const end = polarToCartesian(x, y, outerRadius, startAngle);
  const innerStart = polarToCartesian(x, y, innerRadius, endAngle);
  const innerEnd = polarToCartesian(x, y, innerRadius, startAngle);
  
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';
  
  return [
    'M', start.x, start.y,
    'A', outerRadius, outerRadius, 0, largeArcFlag, 0, end.x, end.y,
    'L', innerEnd.x, innerEnd.y,
    'A', innerRadius, innerRadius, 0, largeArcFlag, 1, innerStart.x, innerStart.y,
    'Z',
  ].join(' ');
};

// =============================================================================
// COMPONENT
// =============================================================================

export default function LunarDecisionWheel({
  currentLunarDay,
  currentGate,
  currentGateTitle,
  cycleProgress,
  timeline,
  activeTopic,
  onDayPress,
  onAddEntry,
}: LunarDecisionWheelProps) {
  const { theme } = useTheme();
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedEntries, setSelectedEntries] = useState<LunarEntry[]>([]);

  // Create a map of days with entries
  const entriesByDay = useMemo(() => {
    const map = new Map<number, LunarEntry[]>();
    timeline.forEach(day => {
      map.set(day.lunar_day, day.entries);
    });
    return map;
  }, [timeline]);

  // Handle day segment press
  const handleDayPress = (day: number) => {
    const entries = entriesByDay.get(day) || [];
    setSelectedDay(day);
    setSelectedEntries(entries);
    setModalVisible(true);
    onDayPress?.(day, entries);
  };

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Truncate content
  const truncateContent = (content: string, maxLength: number = 100) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength).trim() + '...';
  };

  // Render wheel segments
  const renderSegments = () => {
    const segments = [];
    const anglePerDay = 360 / TOTAL_DAYS;
    const currentDayRounded = Math.round(currentLunarDay);

    for (let day = 1; day <= TOTAL_DAYS; day++) {
      const startAngle = (day - 1) * anglePerDay;
      const endAngle = day * anglePerDay;
      const isCurrentDay = day === currentDayRounded;
      const hasEntries = entriesByDay.has(day);
      const entryCount = entriesByDay.get(day)?.length || 0;
      const isPast = day < currentDayRounded;
      
      const gateInfo = GATE_SEQUENCE[day] || { gate: 0, title: '' };
      
      // TASK 70 FIX: Highlight today's segment based on currentGate prop, not just day
      // The wheel shows GATE numbers - so highlight segment where gateInfo.gate matches currentGate
      const isCurrentGateSegment = currentGate !== null && gateInfo.gate === currentGate;
      
      // Segment fill color - prioritize current gate highlight
      let fillColor = theme.surface;
      if (isCurrentDay || isCurrentGateSegment) {
        fillColor = LUNAR_COLORS.glow;
      } else if (hasEntries) {
        fillColor = LUNAR_COLORS.dimGlow;
      } else if (isPast) {
        fillColor = 'rgba(255,255,255,0.02)';
      }

      // Calculate label position
      const midAngle = startAngle + anglePerDay / 2;
      const labelPos = polarToCartesian(CENTER, CENTER, GATE_LABEL_RADIUS, midAngle);

      // Highlight stroke if current gate
      const isHighlighted = isCurrentDay || isCurrentGateSegment;

      segments.push(
        <G key={day}>
          {/* Segment Path */}
          <Path
            d={describeArc(CENTER, CENTER, OUTER_RADIUS, INNER_RADIUS, startAngle, endAngle)}
            fill={fillColor}
            stroke={isHighlighted ? LUNAR_COLORS.moonlight : theme.border}
            strokeWidth={isHighlighted ? 2 : 0.5}
            onPress={() => handleDayPress(day)}
          />
          
          {/* Gate Number */}
          <SvgText
            x={labelPos.x}
            y={labelPos.y - 6}
            fill={isHighlighted ? LUNAR_COLORS.moonlight : theme.textTertiary}
            fontSize={9}
            fontWeight={isHighlighted ? '700' : '500'}
            textAnchor="middle"
          >
            {gateInfo.gate}
          </SvgText>
          
          {/* Entry Marker */}
          {hasEntries && (
            <Circle
              cx={labelPos.x}
              cy={labelPos.y + 10}
              r={entryCount > 1 ? 8 : 5}
              fill={LUNAR_COLORS.moonlight}
            />
          )}
          
          {/* Entry Count Badge */}
          {entryCount > 1 && (
            <SvgText
              x={labelPos.x}
              y={labelPos.y + 13}
              fill="#1A1D24"
              fontSize={8}
              fontWeight="700"
              textAnchor="middle"
            >
              {entryCount}
            </SvgText>
          )}
        </G>
      );
    }

    return segments;
  };

  // Render progress arc
  const renderProgressArc = () => {
    const progressAngle = cycleProgress * 360;
    const progressRadius = OUTER_RADIUS + 4;
    
    const start = polarToCartesian(CENTER, CENTER, progressRadius, 0);
    const end = polarToCartesian(CENTER, CENTER, progressRadius, progressAngle);
    
    const largeArcFlag = progressAngle > 180 ? 1 : 0;
    
    const d = [
      'M', start.x, start.y,
      'A', progressRadius, progressRadius, 0, largeArcFlag, 1, end.x, end.y,
    ].join(' ');

    return (
      <Path
        d={d}
        fill="none"
        stroke={LUNAR_COLORS.moonlight}
        strokeWidth={3}
        strokeLinecap="round"
        opacity={0.6}
      />
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Wheel */}
      <View style={styles.wheelContainer}>
        <Svg width={WHEEL_SIZE} height={WHEEL_SIZE}>
          <Defs>
            <LinearGradient id="moonGlow" x1="0%" y1="0%" x2="100%" y2="100%">
              <Stop offset="0%" stopColor={LUNAR_COLORS.moonlight} stopOpacity={0.3} />
              <Stop offset="100%" stopColor={LUNAR_COLORS.moonlight} stopOpacity={0.1} />
            </LinearGradient>
          </Defs>
          
          {/* Background Circle */}
          <Circle
            cx={CENTER}
            cy={CENTER}
            r={INNER_RADIUS - 2}
            fill={theme.background}
          />
          
          {/* Segments */}
          {renderSegments()}
          
          {/* Progress Arc */}
          {renderProgressArc()}
          
          {/* Inner Circle (for center content) */}
          <Circle
            cx={CENTER}
            cy={CENTER}
            r={INNER_RADIUS - 4}
            fill={theme.background}
            stroke={theme.border}
            strokeWidth={1}
          />
        </Svg>

        {/* Center Content */}
        <View style={[styles.centerContent, { width: INNER_RADIUS * 2 - 20, height: INNER_RADIUS * 2 - 20 }]}>
          {/* Current Position */}
          <Text style={styles.centerIcon}>🌙</Text>
          <Text style={[styles.centerLabel, { color: LUNAR_COLORS.silver }]}>TODAY</Text>
          <Text style={[styles.centerDay, { color: theme.text }]}>
            Day {Math.round(currentLunarDay)}
          </Text>
          {currentGate && (
            <Text style={[styles.centerGate, { color: LUNAR_COLORS.moonlight }]}>
              Gate {currentGate}
            </Text>
          )}
          
          {/* Active Consideration */}
          <View style={[styles.considerationDivider, { backgroundColor: theme.border }]} />
          {activeTopic ? (
            <View style={styles.considerationContainer}>
              <Text style={[styles.considerationLabel, { color: LUNAR_COLORS.silver }]}>
                OBSERVING
              </Text>
              <Text style={[styles.considerationText, { color: theme.textSecondary }]} numberOfLines={2}>
                "{truncateContent(activeTopic, 40)}"
              </Text>
            </View>
          ) : (
            <TouchableOpacity style={styles.addConsideration} onPress={onAddEntry}>
              <Text style={[styles.addConsiderationText, { color: theme.textTertiary }]}>
                What are you{'\n'}considering?
              </Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Day Info Footer */}
      <View style={[styles.footer, { borderTopColor: theme.border }]}>
        <Text style={[styles.footerProgress, { color: theme.textSecondary }]}>
          Day {Math.round(currentLunarDay)} of 29.5 • {Math.round(cycleProgress * 100)}% complete
        </Text>
        <Text style={[styles.footerDescription, { color: theme.textTertiary }]}>
          Tap any segment to view or add entries
        </Text>
      </View>

      {/* Day Detail Modal */}
      <Modal
        visible={modalVisible}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <TouchableOpacity 
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setModalVisible(false)}
        >
          <View style={[styles.modalContent, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            {selectedDay && (
              <>
                {/* Modal Header */}
                <View style={styles.modalHeader}>
                  <View style={styles.modalDayInfo}>
                    <Text style={[styles.modalDayNumber, { color: LUNAR_COLORS.moonlight }]}>
                      Day {selectedDay}
                    </Text>
                    {GATE_SEQUENCE[selectedDay] && (
                      <>
                        <Text style={[styles.modalGate, { color: theme.text }]}>
                          Gate {GATE_SEQUENCE[selectedDay].gate}
                        </Text>
                        <Text style={[styles.modalGateTitle, { color: theme.textSecondary }]}>
                          {GATE_SEQUENCE[selectedDay].title}
                        </Text>
                      </>
                    )}
                  </View>
                  {selectedDay === Math.round(currentLunarDay) && (
                    <View style={[styles.todayBadge, { backgroundColor: LUNAR_COLORS.glow }]}>
                      <Text style={[styles.todayBadgeText, { color: LUNAR_COLORS.moonlight }]}>
                        Today
                      </Text>
                    </View>
                  )}
                </View>

                {/* Entries List */}
                {selectedEntries.length > 0 ? (
                  <ScrollView style={styles.entriesList} showsVerticalScrollIndicator={false}>
                    {selectedEntries.map((entry, index) => (
                      <View 
                        key={entry.id}
                        style={[
                          styles.entryItem,
                          { borderBottomColor: theme.border },
                          index === selectedEntries.length - 1 && { borderBottomWidth: 0 }
                        ]}
                      >
                        <Text style={[styles.entryDate, { color: theme.textTertiary }]}>
                          {formatDate(entry.created_at)}
                        </Text>
                        <Text style={[styles.entryContent, { color: theme.text }]}>
                          {truncateContent(entry.content, 150)}
                        </Text>
                      </View>
                    ))}
                  </ScrollView>
                ) : (
                  <View style={styles.noEntries}>
                    <Text style={[styles.noEntriesText, { color: theme.textTertiary }]}>
                      No entries for this day
                    </Text>
                  </View>
                )}

                {/* Actions */}
                <View style={[styles.modalActions, { borderTopColor: theme.border }]}>
                  <TouchableOpacity
                    style={styles.closeButton}
                    onPress={() => setModalVisible(false)}
                  >
                    <Text style={[styles.closeButtonText, { color: theme.textSecondary }]}>
                      Close
                    </Text>
                  </TouchableOpacity>
                </View>
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
  wheelContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    position: 'relative',
  },
  centerContent: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 8,
  },
  centerIcon: {
    fontSize: 20,
    marginBottom: 4,
  },
  centerLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 1,
  },
  centerDay: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 2,
  },
  centerGate: {
    fontSize: 12,
    fontWeight: '500',
  },
  considerationDivider: {
    width: 40,
    height: 1,
    marginVertical: 10,
  },
  considerationContainer: {
    alignItems: 'center',
  },
  considerationLabel: {
    fontSize: 8,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  considerationText: {
    fontSize: 11,
    fontStyle: 'italic',
    textAlign: 'center',
    lineHeight: 15,
  },
  addConsideration: {
    alignItems: 'center',
  },
  addConsiderationText: {
    fontSize: 11,
    textAlign: 'center',
    lineHeight: 15,
  },
  footer: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  footerProgress: {
    fontSize: 13,
    marginBottom: 4,
  },
  footerDescription: {
    fontSize: 11,
  },
  // Modal Styles
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
    maxHeight: '70%',
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    overflow: 'hidden',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    padding: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(192, 200, 212, 0.2)',
  },
  modalDayInfo: {
    flex: 1,
  },
  modalDayNumber: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  modalGate: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 2,
  },
  modalGateTitle: {
    fontSize: 13,
  },
  todayBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  todayBadgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  entriesList: {
    maxHeight: 250,
    paddingHorizontal: 16,
  },
  entryItem: {
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  entryDate: {
    fontSize: 11,
    marginBottom: 4,
  },
  entryContent: {
    fontSize: 14,
    lineHeight: 20,
  },
  noEntries: {
    padding: 32,
    alignItems: 'center',
  },
  noEntriesText: {
    fontSize: 14,
  },
  modalActions: {
    padding: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  closeButton: {
    paddingVertical: 8,
    paddingHorizontal: 24,
  },
  closeButtonText: {
    fontSize: 15,
  },
});

export type { LunarDecisionWheelProps, LunarEntry, TimelineDay };
