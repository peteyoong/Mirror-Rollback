/**
 * LifelineMiniMap V2
 * 
 * An expressive life-arc visualization showing the emotional rhythm of a life.
 * - Flowing curved path that rises/falls based on event intensity
 * - Nodes for recorded moments with size based on impact
 * - Visual distinction for quiet periods
 * - Tap-to-jump navigation preserved
 * 
 * Design: Emotionally legible, visually elegant, clean dark aesthetic
 */

import React, { useMemo, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Pressable,
} from 'react-native';
import Svg, { Path, Circle, Defs, LinearGradient, Stop, Line, G, Rect } from 'react-native-svg';
import { useTheme } from '../../contexts/ThemeContext';
import { LifelineEvent } from './LifelineEventCard';
import { GapPromptData } from './LifelineGapPrompt';

const SCREEN_WIDTH = Dimensions.get('window').width;
const CONTAINER_PADDING = 16;
const GRAPH_HEIGHT = 100;
const GRAPH_WIDTH = SCREEN_WIDTH - (CONTAINER_PADDING * 2) - 32; // Account for container padding
const VERTICAL_PADDING = 20; // Space above and below the arc
const ARC_HEIGHT = GRAPH_HEIGHT - (VERTICAL_PADDING * 2);
const BASELINE_Y = GRAPH_HEIGHT - VERTICAL_PADDING; // Bottom of the arc area

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
  intensity: number; // 0-1 normalized intensity
  isGap?: boolean;
  gapData?: GapPromptData;
  x: number; // X position on graph
  y: number; // Y position on graph (higher intensity = lower Y value)
}

// Life chapter definitions based on age
interface LifeChapter {
  label: string;
  startAge: number;
  endAge: number;
}

const LIFE_CHAPTERS: LifeChapter[] = [
  { label: 'Early Life', startAge: 0, endAge: 12 },
  { label: 'Formative', startAge: 13, endAge: 22 },
  { label: 'Building', startAge: 23, endAge: 40 },
  { label: 'Midlife', startAge: 41, endAge: 60 },
  { label: 'Later', startAge: 61, endAge: 100 },
];

/**
 * Calculate event intensity for a year
 * Uses: event count, impact level, category diversity
 */
function calculateIntensity(yearEvents: LifelineEvent[], maxEventsInYear: number): number {
  if (yearEvents.length === 0) return 0;
  
  // Base intensity from event count (normalized)
  const countIntensity = yearEvents.length / Math.max(maxEventsInYear, 1);
  
  // Boost from impact levels if available
  const impactBoost = yearEvents.reduce((sum, e) => {
    const impact = (e as any).impact || (e as any).significance || 0;
    return sum + (impact / 10); // Normalize impact to 0-1
  }, 0) / yearEvents.length;
  
  // Boost from category diversity
  const categories = new Set(yearEvents.map(e => e.category).filter(Boolean));
  const diversityBoost = Math.min(categories.size / 3, 0.3); // Max 0.3 boost for 3+ categories
  
  // Combine with weights
  const rawIntensity = (countIntensity * 0.6) + (impactBoost * 0.25) + (diversityBoost * 0.15);
  
  // Ensure minimum visibility for years with events
  return Math.max(0.15, Math.min(1, rawIntensity));
}

/**
 * Generate smooth SVG path through points using bezier curves
 */
function generateSmoothPath(points: { x: number; y: number }[]): string {
  if (points.length < 2) return '';
  
  let path = `M ${points[0].x} ${points[0].y}`;
  
  for (let i = 0; i < points.length - 1; i++) {
    const current = points[i];
    const next = points[i + 1];
    
    // Calculate control points for smooth curve
    const midX = (current.x + next.x) / 2;
    
    // Use quadratic bezier for smoother, more organic feel
    path += ` Q ${midX} ${current.y}, ${midX} ${(current.y + next.y) / 2}`;
    path += ` Q ${midX} ${next.y}, ${next.x} ${next.y}`;
  }
  
  return path;
}

/**
 * Generate path with closed area for gradient fill
 */
function generateAreaPath(points: { x: number; y: number }[]): string {
  if (points.length < 2) return '';
  
  const linePath = generateSmoothPath(points);
  const lastPoint = points[points.length - 1];
  const firstPoint = points[0];
  
  // Close the path to baseline for area fill
  return `${linePath} L ${lastPoint.x} ${BASELINE_Y} L ${firstPoint.x} ${BASELINE_Y} Z`;
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
  const [hoveredYear, setHoveredYear] = useState<number | null>(null);
  
  const totalYears = currentYear - birthYear + 1;
  const yearWidth = GRAPH_WIDTH / Math.max(totalYears, 1);
  
  // Process year data with intensity calculations
  const { yearDataMap, maxEventsInYear, pathPoints, significantNodes, gapRegions } = useMemo(() => {
    const dataMap = new Map<number, YearData>();
    let maxEvents = 1;
    
    // First pass: count events per year
    const eventsByYear = new Map<number, LifelineEvent[]>();
    events.forEach(event => {
      if (event.year) {
        const existing = eventsByYear.get(event.year) || [];
        existing.push(event);
        eventsByYear.set(event.year, existing);
        maxEvents = Math.max(maxEvents, existing.length);
      }
    });
    
    // Second pass: build year data with positions
    const points: { x: number; y: number; year: number; intensity: number }[] = [];
    const nodes: YearData[] = [];
    const gapRegs: { startX: number; endX: number; gap: GapPromptData }[] = [];
    
    for (let year = birthYear; year <= currentYear; year++) {
      const yearEvents = eventsByYear.get(year) || [];
      const intensity = calculateIntensity(yearEvents, maxEvents);
      const x = (year - birthYear) * yearWidth;
      const y = BASELINE_Y - (intensity * ARC_HEIGHT);
      
      // Check if this year is in a gap
      const gapData = gaps.find(g => year >= g.start_year && year <= g.end_year);
      
      const yearData: YearData = {
        year,
        eventCount: yearEvents.length,
        events: yearEvents,
        intensity,
        isGap: !!gapData && yearEvents.length === 0,
        gapData,
        x,
        y,
      };
      
      dataMap.set(year, yearData);
      points.push({ x, y, year, intensity });
      
      // Track significant nodes (years with events)
      if (yearEvents.length > 0) {
        nodes.push(yearData);
      }
    }
    
    // Build gap regions
    gaps.forEach(gap => {
      const startX = (gap.start_year - birthYear) * yearWidth;
      const endX = (gap.end_year - birthYear + 1) * yearWidth;
      gapRegs.push({ startX, endX, gap });
    });
    
    return {
      yearDataMap: dataMap,
      maxEventsInYear: maxEvents,
      pathPoints: points,
      significantNodes: nodes,
      gapRegions: gapRegs,
    };
  }, [events, gaps, birthYear, currentYear, yearWidth]);
  
  // Generate SVG paths
  const arcPath = useMemo(() => generateSmoothPath(pathPoints), [pathPoints]);
  const areaPath = useMemo(() => generateAreaPath(pathPoints), [pathPoints]);
  
  // Calculate decade markers
  const decadeMarkers = useMemo(() => {
    const markers: number[] = [];
    for (let year = Math.ceil(birthYear / 10) * 10; year <= currentYear; year += 10) {
      if (year > birthYear && year < currentYear) {
        markers.push(year);
      }
    }
    return markers;
  }, [birthYear, currentYear]);
  
  // Calculate life chapters that apply to this user's age range
  const applicableChapters = useMemo(() => {
    const userAge = currentYear - birthYear;
    return LIFE_CHAPTERS.filter(ch => ch.startAge <= userAge).map(ch => ({
      ...ch,
      startYear: birthYear + ch.startAge,
      endYear: Math.min(birthYear + ch.endAge, currentYear),
    }));
  }, [birthYear, currentYear]);
  
  const handleYearPress = (year: number) => {
    const yearData = yearDataMap.get(year);
    if (yearData?.isGap && yearData.gapData && onGapPress) {
      onGapPress(yearData.gapData);
    } else {
      onYearPress(year);
    }
  };
  
  const handleNodePress = (yearData: YearData) => {
    if (yearData.gapData && onGapPress) {
      onGapPress(yearData.gapData);
    } else {
      onYearPress(yearData.year);
    }
  };
  
  // Get node size based on event count and intensity
  const getNodeSize = (eventCount: number, intensity: number): number => {
    const base = 4;
    const countBonus = Math.min(eventCount - 1, 3) * 2; // +2px per event, max +6
    const intensityBonus = intensity * 4; // Up to +4px for high intensity
    return base + countBonus + intensityBonus;
  };
  
  // Accent color with opacity variations
  const accentColor = theme.accent || '#6366F1';
  const accentLight = `${accentColor}40`;
  const accentVeryLight = `${accentColor}15`;
  const lineColor = isDark ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.4)';
  const gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
  
  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header */}
      <View style={styles.headerSection}>
        <Text style={[styles.headerLabel, { color: theme.textSecondary }]}>
          YOUR STORY AT A GLANCE
        </Text>
        <Text style={[styles.headerSubtext, { color: theme.textTertiary }]}>
          From your earliest memories to now.
          {events.length >= 3 && ' Tap anywhere to jump to that moment.'}
        </Text>
      </View>
      
      {/* Life Arc Graph */}
      <View style={styles.graphContainer}>
        <Svg width={GRAPH_WIDTH} height={GRAPH_HEIGHT} style={styles.svg}>
          <Defs>
            {/* Gradient for area fill */}
            <LinearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <Stop offset="0" stopColor={accentColor} stopOpacity="0.3" />
              <Stop offset="1" stopColor={accentColor} stopOpacity="0.02" />
            </LinearGradient>
            
            {/* Gradient for the line itself */}
            <LinearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
              <Stop offset="0" stopColor={accentColor} stopOpacity="0.5" />
              <Stop offset="0.5" stopColor={accentColor} stopOpacity="0.9" />
              <Stop offset="1" stopColor={accentColor} stopOpacity="0.7" />
            </LinearGradient>
          </Defs>
          
          {/* Baseline */}
          <Line
            x1={0}
            y1={BASELINE_Y}
            x2={GRAPH_WIDTH}
            y2={BASELINE_Y}
            stroke={gridColor}
            strokeWidth={1}
          />
          
          {/* Gap regions - subtle faded areas */}
          {gapRegions.map((region, idx) => (
            <G key={`gap-${idx}`}>
              <Rect
                x={region.startX}
                y={VERTICAL_PADDING}
                width={region.endX - region.startX}
                height={ARC_HEIGHT}
                fill={isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)'}
                rx={4}
              />
              {/* Dashed line through gap */}
              <Line
                x1={region.startX}
                y1={BASELINE_Y - 5}
                x2={region.endX}
                y2={BASELINE_Y - 5}
                stroke={theme.textTertiary}
                strokeWidth={1}
                strokeDasharray="4,4"
                opacity={0.3}
              />
            </G>
          ))}
          
          {/* Area fill under the curve */}
          <Path
            d={areaPath}
            fill="url(#areaGradient)"
          />
          
          {/* Main life arc line */}
          <Path
            d={arcPath}
            stroke="url(#lineGradient)"
            strokeWidth={2.5}
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          
          {/* Decade markers */}
          {decadeMarkers.map(year => {
            const x = (year - birthYear) * yearWidth;
            return (
              <G key={`decade-${year}`}>
                <Line
                  x1={x}
                  y1={BASELINE_Y}
                  x2={x}
                  y2={BASELINE_Y + 6}
                  stroke={theme.textTertiary}
                  strokeWidth={1}
                  opacity={0.5}
                />
              </G>
            );
          })}
          
          {/* Event nodes */}
          {significantNodes.map((node) => {
            const nodeSize = getNodeSize(node.eventCount, node.intensity);
            const isHovered = hoveredYear === node.year;
            
            return (
              <G key={`node-${node.year}`}>
                {/* Glow effect for higher intensity */}
                {node.intensity > 0.4 && (
                  <Circle
                    cx={node.x}
                    cy={node.y}
                    r={nodeSize + 4}
                    fill={accentColor}
                    opacity={0.15}
                  />
                )}
                
                {/* Main node */}
                <Circle
                  cx={node.x}
                  cy={node.y}
                  r={isHovered ? nodeSize + 2 : nodeSize}
                  fill={accentColor}
                  opacity={0.6 + (node.intensity * 0.4)}
                />
                
                {/* Inner highlight */}
                <Circle
                  cx={node.x}
                  cy={node.y}
                  r={nodeSize * 0.5}
                  fill="#FFFFFF"
                  opacity={0.3}
                />
                
                {/* Event count indicator for years with 3+ events */}
                {node.eventCount >= 3 && (
                  <Circle
                    cx={node.x}
                    cy={node.y - nodeSize - 6}
                    r={8}
                    fill={theme.surface}
                    stroke={accentColor}
                    strokeWidth={1}
                  />
                )}
              </G>
            );
          })}
        </Svg>
        
        {/* Touch layer for interaction */}
        <View style={styles.touchLayer}>
          {pathPoints.map((point) => (
            <Pressable
              key={`touch-${point.year}`}
              style={[
                styles.touchTarget,
                {
                  left: point.x - (yearWidth / 2),
                  width: yearWidth,
                }
              ]}
              onPress={() => handleYearPress(point.year)}
              onPressIn={() => setHoveredYear(point.year)}
              onPressOut={() => setHoveredYear(null)}
            />
          ))}
        </View>
        
        {/* Year labels */}
        <View style={styles.yearLabels}>
          <Text style={[styles.yearLabel, { color: theme.textTertiary }]}>
            {birthYear}
          </Text>
          {decadeMarkers.slice(0, 3).map(year => (
            <Text 
              key={year} 
              style={[
                styles.decadeLabel, 
                { color: theme.textTertiary, left: (year - birthYear) * yearWidth - 15 }
              ]}
            >
              {year}
            </Text>
          ))}
          <Text style={[styles.yearLabel, styles.yearLabelRight, { color: theme.textTertiary }]}>
            {currentYear}
          </Text>
        </View>
      </View>
      
      {/* Life chapters bar (subtle) */}
      {applicableChapters.length > 2 && (
        <View style={styles.chaptersContainer}>
          {applicableChapters.map((chapter, idx) => {
            const startX = (chapter.startYear - birthYear) / totalYears * 100;
            const width = (chapter.endYear - chapter.startYear + 1) / totalYears * 100;
            
            return (
              <View
                key={chapter.label}
                style={[
                  styles.chapterSegment,
                  {
                    left: `${startX}%`,
                    width: `${width}%`,
                    backgroundColor: idx % 2 === 0 ? gridColor : 'transparent',
                  }
                ]}
              >
                {width > 15 && (
                  <Text style={[styles.chapterLabel, { color: theme.textTertiary }]}>
                    {chapter.label}
                  </Text>
                )}
              </View>
            );
          })}
        </View>
      )}
      
      {/* Legend */}
      {events.length > 0 && (
        <View style={styles.legend}>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: accentColor }]} />
            <Text style={[styles.legendText, { color: theme.textTertiary }]}>Recorded moments</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.legendArc, { borderColor: accentColor }]} />
            <Text style={[styles.legendText, { color: theme.textTertiary }]}>Intensity of change</Text>
          </View>
          {gapRegions.length > 0 && (
            <View style={styles.legendItem}>
              <View style={[styles.legendGap, { backgroundColor: theme.textTertiary }]} />
              <Text style={[styles.legendText, { color: theme.textTertiary }]}>Quiet periods</Text>
            </View>
          )}
        </View>
      )}
      
      {/* Hovered year tooltip */}
      {hoveredYear && (
        <View style={[styles.tooltip, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.tooltipYear, { color: theme.text }]}>{hoveredYear}</Text>
          {yearDataMap.get(hoveredYear)?.eventCount ? (
            <Text style={[styles.tooltipCount, { color: theme.textSecondary }]}>
              {yearDataMap.get(hoveredYear)?.eventCount} moment{yearDataMap.get(hoveredYear)?.eventCount !== 1 ? 's' : ''}
            </Text>
          ) : yearDataMap.get(hoveredYear)?.isGap ? (
            <Text style={[styles.tooltipCount, { color: theme.textTertiary }]}>Quiet period</Text>
          ) : (
            <Text style={[styles.tooltipCount, { color: theme.textTertiary }]}>No moments recorded</Text>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  headerSection: {
    marginBottom: 12,
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
  graphContainer: {
    position: 'relative',
    height: GRAPH_HEIGHT + 20, // Extra space for labels
    marginBottom: 8,
  },
  svg: {
    marginLeft: 0,
  },
  touchLayer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 20,
    flexDirection: 'row',
  },
  touchTarget: {
    position: 'absolute',
    top: 0,
    bottom: 0,
  },
  yearLabels: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 0,
  },
  yearLabel: {
    fontSize: 10,
    fontWeight: '500',
  },
  yearLabelRight: {
    textAlign: 'right',
  },
  decadeLabel: {
    position: 'absolute',
    bottom: 0,
    fontSize: 9,
    width: 30,
    textAlign: 'center',
  },
  chaptersContainer: {
    height: 16,
    position: 'relative',
    marginTop: 4,
    marginBottom: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  chapterSegment: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  chapterLabel: {
    fontSize: 8,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  legend: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 12,
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
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendArc: {
    width: 16,
    height: 8,
    borderWidth: 2,
    borderRadius: 4,
    borderBottomWidth: 0,
  },
  legendGap: {
    width: 16,
    height: 3,
    borderRadius: 1.5,
    opacity: 0.3,
  },
  legendText: {
    fontSize: 11,
  },
  tooltip: {
    position: 'absolute',
    top: 45,
    left: '50%',
    transform: [{ translateX: -40 }],
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
    minWidth: 80,
  },
  tooltipYear: {
    fontSize: 14,
    fontWeight: '600',
  },
  tooltipCount: {
    fontSize: 11,
    marginTop: 2,
  },
});
