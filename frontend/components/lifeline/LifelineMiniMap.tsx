/**
 * LifelineMiniMap V3
 * 
 * A true life-arc visualization with:
 * - Meaningful centerline (supported vs challenged periods)
 * - Arc moves above/below center based on life rhythm
 * - Large invisible touch targets for reliable tapping
 * - Elegant dark aesthetic preserved
 * 
 * Y-axis model:
 * - Center (5) = balanced / neutral
 * - Above center = more supported / expansive / resourced
 * - Below center = more difficult / challenging / tested
 */

import React, { useMemo, useState, useCallback } from 'react';
import {
  View,
  Text,
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
const GRAPH_HEIGHT = 140; // Taller for more expressive arc visibility
const GRAPH_WIDTH = SCREEN_WIDTH - (CONTAINER_PADDING * 2) - 32;
const VERTICAL_PADDING = 12;
const ARC_HEIGHT = GRAPH_HEIGHT - (VERTICAL_PADDING * 2); // More vertical space for ups and downs
const CENTER_Y = VERTICAL_PADDING + (ARC_HEIGHT / 2); // Midpoint line
const MIN_TOUCH_SIZE = 44; // Minimum touch target size for accessibility
const AMPLITUDE_MULTIPLIER = 1.8; // Increase vertical movement for more expressive arc

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
  score: number; // -1 to +1, where 0 is center
  amplitude: number; // How far from center (0-1)
  isGap?: boolean;
  gapData?: GapPromptData;
  x: number;
  y: number;
}

// Category valence mapping (heuristic when explicit data unavailable)
// Positive valence = tends toward supported/expansive
// Negative valence = tends toward challenged/difficult
const CATEGORY_VALENCE: Record<string, number> = {
  // Positive-leaning categories
  'achievement': 0.6,
  'joy': 0.7,
  'love': 0.5,
  'relationship': 0.3,
  'connection': 0.4,
  'growth': 0.5,
  'success': 0.6,
  'celebration': 0.7,
  'milestone': 0.4,
  'family': 0.2, // Neutral-positive
  'work': 0.1, // Slightly positive
  'education': 0.3,
  'travel': 0.4,
  'creative': 0.4,
  
  // Negative-leaning categories
  'loss': -0.7,
  'grief': -0.8,
  'health': -0.3,
  'challenge': -0.5,
  'crisis': -0.7,
  'trauma': -0.8,
  'conflict': -0.5,
  'difficulty': -0.6,
  'failure': -0.5,
  'fear': -0.4,
  'anxiety': -0.4,
  'depression': -0.6,
  'illness': -0.5,
  'accident': -0.6,
  'separation': -0.5,
  'divorce': -0.6,
  'death': -0.8,
  
  // Neutral categories
  'change': 0,
  'transition': 0,
  'move': 0.1,
  'self': 0,
  'reflection': 0.1,
  'other': 0,
};

/**
 * Calculate lifeline score for a year's events
 * Returns value from -1 (most challenged) to +1 (most supported)
 * 0 = center/balanced
 */
function calculateLifelineScore(yearEvents: LifelineEvent[]): { score: number; amplitude: number } {
  if (yearEvents.length === 0) {
    return { score: 0, amplitude: 0.05 }; // Quiet years hover near center with minimal amplitude
  }
  
  let totalValence = 0;
  let totalWeight = 0;
  let hasExplicitValence = false;
  
  yearEvents.forEach(event => {
    // Weight based on impact/significance if available
    const impact = (event as any).impact || (event as any).significance || 5;
    const weight = Math.max(1, impact / 5); // Normalize to 1-2 range
    
    // Try to get explicit emotional valence first
    const explicitValence = (event as any).valence || (event as any).emotional_valence;
    if (explicitValence !== undefined && explicitValence !== null) {
      hasExplicitValence = true;
      // Normalize explicit valence to -1 to +1
      const normalizedValence = (explicitValence - 5) / 5; // Assuming 0-10 scale
      totalValence += normalizedValence * weight;
      totalWeight += weight;
      return;
    }
    
    // Fall back to category-based heuristic
    const category = (event.category || '').toLowerCase();
    const categoryValence = CATEGORY_VALENCE[category] ?? 0;
    
    // Also check title/description for emotional keywords
    const title = (event.title || '').toLowerCase();
    const description = (event.description || '').toLowerCase();
    const text = `${title} ${description}`;
    
    let textValence = 0;
    let textSignals = 0;
    
    // Positive signals
    if (/\b(joy|happy|excit|wonderful|amazing|love|success|achiev|proud|celebrat|blessed|grateful)\b/.test(text)) {
      textValence += 0.4;
      textSignals++;
    }
    if (/\b(birth|married|wedding|promotion|graduat|award|won)\b/.test(text)) {
      textValence += 0.5;
      textSignals++;
    }
    
    // Negative signals
    if (/\b(loss|lost|grief|death|died|passed|tragic|trauma|crisis|difficult|hard|struggle)\b/.test(text)) {
      textValence -= 0.5;
      textSignals++;
    }
    if (/\b(divorce|separat|illness|sick|hospital|accident|fired|failed|fear|anxiety|depress)\b/.test(text)) {
      textValence -= 0.4;
      textSignals++;
    }
    
    // Combine category and text signals
    let eventValence = categoryValence;
    if (textSignals > 0) {
      eventValence = (categoryValence + textValence) / 2;
    }
    
    // Clamp to -1 to +1
    eventValence = Math.max(-1, Math.min(1, eventValence));
    
    totalValence += eventValence * weight;
    totalWeight += weight;
  });
  
  // Calculate final score
  const rawScore = totalWeight > 0 ? totalValence / totalWeight : 0;
  
  // Less dampening for more expressive movement
  const score = rawScore * 0.95;
  
  // Amplitude based on event count and clarity of signal - increased for more visible variation
  const eventCountAmplitude = Math.min(yearEvents.length / 2, 1); // Max at 2 events (was 3)
  const signalClarity = hasExplicitValence ? 1 : 0.85; // Higher baseline for heuristic data
  const amplitude = 0.35 + (eventCountAmplitude * signalClarity * 0.55); // Base 0.35 (was 0.15)
  
  return { score, amplitude };
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
    
    // Control points for smooth curve
    const tension = 0.3;
    const dx = next.x - current.x;
    
    const cp1x = current.x + dx * tension;
    const cp1y = current.y;
    const cp2x = next.x - dx * tension;
    const cp2y = next.y;
    
    path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${next.x} ${next.y}`;
  }
  
  return path;
}

/**
 * Generate closed area path for gradient fill
 */
function generateAreaPath(points: { x: number; y: number }[], fillToY: number): string {
  if (points.length < 2) return '';
  
  const linePath = generateSmoothPath(points);
  const lastPoint = points[points.length - 1];
  const firstPoint = points[0];
  
  return `${linePath} L ${lastPoint.x} ${fillToY} L ${firstPoint.x} ${fillToY} Z`;
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
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  
  const totalYears = currentYear - birthYear + 1;
  const yearWidth = GRAPH_WIDTH / Math.max(totalYears, 1);
  
  // Process year data with lifeline scores
  const { yearDataMap, pathPoints, significantNodes, gapRegions, abovePoints, belowPoints } = useMemo(() => {
    const dataMap = new Map<number, YearData>();
    
    // Group events by year
    const eventsByYear = new Map<number, LifelineEvent[]>();
    events.forEach(event => {
      if (event.year) {
        const existing = eventsByYear.get(event.year) || [];
        existing.push(event);
        eventsByYear.set(event.year, existing);
      }
    });
    
    // Build year data with lifeline scores
    const points: { x: number; y: number; year: number; score: number }[] = [];
    const nodes: YearData[] = [];
    const above: { x: number; y: number }[] = [];
    const below: { x: number; y: number }[] = [];
    
    for (let year = birthYear; year <= currentYear; year++) {
      const yearEvents = eventsByYear.get(year) || [];
      const { score, amplitude } = calculateLifelineScore(yearEvents);
      
      const x = (year - birthYear) * yearWidth;
      // Y position: score moves us above (positive) or below (negative) center
      // amplitude determines how far from center
      // Apply AMPLITUDE_MULTIPLIER for more expressive vertical movement
      const yOffset = score * amplitude * (ARC_HEIGHT / 2) * AMPLITUDE_MULTIPLIER;
      const y = Math.max(VERTICAL_PADDING, Math.min(GRAPH_HEIGHT - VERTICAL_PADDING, CENTER_Y - yOffset));
      
      const gapData = gaps.find(g => year >= g.start_year && year <= g.end_year);
      
      const yearData: YearData = {
        year,
        eventCount: yearEvents.length,
        events: yearEvents,
        score,
        amplitude,
        isGap: !!gapData && yearEvents.length === 0,
        gapData,
        x,
        y,
      };
      
      dataMap.set(year, yearData);
      points.push({ x, y, year, score });
      
      // Track points for above/below gradient fills
      if (y < CENTER_Y) {
        above.push({ x, y });
      } else {
        below.push({ x, y });
      }
      
      if (yearEvents.length > 0) {
        nodes.push(yearData);
      }
    }
    
    // Build gap regions
    const gapRegs: { startX: number; endX: number; gap: GapPromptData }[] = [];
    gaps.forEach(gap => {
      const startX = (gap.start_year - birthYear) * yearWidth;
      const endX = (gap.end_year - birthYear + 1) * yearWidth;
      gapRegs.push({ startX, endX, gap });
    });
    
    return {
      yearDataMap: dataMap,
      pathPoints: points,
      significantNodes: nodes,
      gapRegions: gapRegs,
      abovePoints: above,
      belowPoints: below,
    };
  }, [events, gaps, birthYear, currentYear, yearWidth]);
  
  // Generate SVG paths
  const arcPath = useMemo(() => generateSmoothPath(pathPoints), [pathPoints]);
  
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
  
  // Handle node/year tap with larger hit area
  const handleTap = useCallback((year: number) => {
    console.log('==== MINIMAP TAP DEBUG ====');
    console.log('[MiniMap] handleTap called with year:', year, 'type:', typeof year);
    console.log('[MiniMap] yearDataMap has this year:', yearDataMap.has(year));
    const yearData = yearDataMap.get(year);
    console.log('[MiniMap] yearData for', year, ':', yearData ? { eventCount: yearData.eventCount, isGap: yearData.isGap } : 'undefined');
    
    setSelectedYear(year);
    
    if (yearData?.isGap && yearData.gapData && onGapPress) {
      console.log('[MiniMap] Calling onGapPress for gap');
      onGapPress(yearData.gapData);
    } else {
      console.log('[MiniMap] Calling onYearPress with year:', year);
      onYearPress(year);
    }
    
    // Clear selection after animation
    setTimeout(() => setSelectedYear(null), 300);
    console.log('==== END MINIMAP TAP DEBUG ====');
  }, [yearDataMap, onYearPress, onGapPress]);
  
  // Find nearest node to a touch position
  const findNearestNode = useCallback((touchX: number): number => {
    const touchYear = birthYear + Math.round(touchX / yearWidth);
    
    // Find nearest year with events
    let nearestYear = touchYear;
    let minDistance = Infinity;
    
    significantNodes.forEach(node => {
      const distance = Math.abs(node.year - touchYear);
      if (distance < minDistance) {
        minDistance = distance;
        nearestYear = node.year;
      }
    });
    
    // If no nodes nearby, use the touched year
    if (minDistance > 3) {
      return Math.max(birthYear, Math.min(currentYear, touchYear));
    }
    
    return nearestYear;
  }, [birthYear, currentYear, yearWidth, significantNodes]);
  
  // Get visual node size (smaller for elegance)
  const getVisualNodeSize = (eventCount: number, amplitude: number): number => {
    const base = 5;
    const countBonus = Math.min(eventCount - 1, 2) * 2;
    const amplitudeBonus = amplitude * 3;
    return base + countBonus + amplitudeBonus;
  };
  
  // Colors
  const accentColor = theme.accent || '#6366F1';
  const supportedColor = isDark ? '#4ADE80' : '#22C55E'; // Soft green for above center
  const challengedColor = isDark ? '#FB923C' : '#F97316'; // Soft orange for below center
  const centerLineColor = isDark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.15)';
  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)';
  
  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header */}
      <View style={styles.headerSection}>
        <Text style={[styles.headerLabel, { color: theme.textSecondary }]}>
          YOUR STORY AT A GLANCE
        </Text>
        <Text style={[styles.headerSubtext, { color: theme.textTertiary }]}>
          The rhythm of your life — supported periods, challenging stretches, and turning points.
        </Text>
        {events.length >= 3 && (
          <Text style={[styles.tapHint, { color: theme.accent }]}>
            Tap a moment to jump into that part of your story
          </Text>
        )}
      </View>
      
      {/* Life Arc Graph */}
      <View style={styles.graphContainer}>
        {/* Simple Y-axis indicator - removed colored labels */}
        <View style={styles.yAxisLabels}>
          <Text style={[styles.yAxisLabel, { color: theme.textTertiary }]}>+</Text>
          <Text style={[styles.yAxisLabel, styles.yAxisLabelBottom, { color: theme.textTertiary }]}>−</Text>
        </View>
        
        <View style={styles.svgContainer}>
          <Svg width={GRAPH_WIDTH} height={GRAPH_HEIGHT}>
            <Defs>
              {/* Gradient for area above center (supported) - very subtle */}
              <LinearGradient id="supportedGradient" x1="0" y1="1" x2="0" y2="0">
                <Stop offset="0" stopColor={supportedColor} stopOpacity="0" />
                <Stop offset="1" stopColor={supportedColor} stopOpacity="0.06" />
              </LinearGradient>
              
              {/* Gradient for area below center (challenged) - very subtle */}
              <LinearGradient id="challengedGradient" x1="0" y1="0" x2="0" y2="1">
                <Stop offset="0" stopColor={challengedColor} stopOpacity="0" />
                <Stop offset="1" stopColor={challengedColor} stopOpacity="0.05" />
              </LinearGradient>
              
              {/* Line gradient */}
              <LinearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
                <Stop offset="0" stopColor={accentColor} stopOpacity="0.6" />
                <Stop offset="0.5" stopColor={accentColor} stopOpacity="0.95" />
                <Stop offset="1" stopColor={accentColor} stopOpacity="0.7" />
              </LinearGradient>
            </Defs>
            
            {/* Very subtle zone backgrounds - let the arc tell the story */}
            <Rect
              x={0}
              y={VERTICAL_PADDING}
              width={GRAPH_WIDTH}
              height={ARC_HEIGHT / 2}
              fill="url(#supportedGradient)"
            />
            <Rect
              x={0}
              y={CENTER_Y}
              width={GRAPH_WIDTH}
              height={ARC_HEIGHT / 2}
              fill="url(#challengedGradient)"
            />
            
            {/* Center line (the midpoint) - subtle but visible */}
            <Line
              x1={0}
              y1={CENTER_Y}
              x2={GRAPH_WIDTH}
              y2={CENTER_Y}
              stroke={centerLineColor}
              strokeWidth={1}
              strokeDasharray="8,6"
            />
            
            {/* Gap regions */}
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
              </G>
            ))}
            
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
                <Line
                  key={`decade-${year}`}
                  x1={x}
                  y1={CENTER_Y - 4}
                  x2={x}
                  y2={CENTER_Y + 4}
                  stroke={theme.textTertiary}
                  strokeWidth={1}
                  opacity={0.4}
                />
              );
            })}
            
            {/* Event nodes */}
            {significantNodes.map((node) => {
              const visualSize = getVisualNodeSize(node.eventCount, node.amplitude);
              const isSelected = selectedYear === node.year;
              const nodeColor = node.score > 0.1 ? supportedColor : node.score < -0.1 ? challengedColor : accentColor;
              
              return (
                <G key={`node-${node.year}`}>
                  {/* Glow for higher amplitude */}
                  {node.amplitude > 0.3 && (
                    <Circle
                      cx={node.x}
                      cy={node.y}
                      r={visualSize + 6}
                      fill={nodeColor}
                      opacity={0.15}
                    />
                  )}
                  
                  {/* Selection ring */}
                  {isSelected && (
                    <Circle
                      cx={node.x}
                      cy={node.y}
                      r={visualSize + 4}
                      fill="none"
                      stroke={theme.text}
                      strokeWidth={2}
                      opacity={0.5}
                    />
                  )}
                  
                  {/* Main node */}
                  <Circle
                    cx={node.x}
                    cy={node.y}
                    r={isSelected ? visualSize + 1 : visualSize}
                    fill={nodeColor}
                    opacity={0.7 + (node.amplitude * 0.3)}
                  />
                  
                  {/* Inner highlight */}
                  <Circle
                    cx={node.x}
                    cy={node.y}
                    r={visualSize * 0.4}
                    fill="#FFFFFF"
                    opacity={0.35}
                  />
                </G>
              );
            })}
          </Svg>
          
          {/* Large invisible touch targets */}
          <View style={styles.touchLayer}>
            {/* Fallback touch layer for years without events - RENDERED FIRST (underneath) */}
            <Pressable
              style={styles.fallbackTouchLayer}
              onPress={(e) => {
                console.log('[MiniMap] Fallback layer touched at X:', e.nativeEvent.locationX);
                const touchX = e.nativeEvent.locationX;
                const nearestYear = findNearestNode(touchX);
                console.log('[MiniMap] Fallback resolving to nearest year:', nearestYear);
                handleTap(nearestYear);
              }}
            />
            
            {/* Gap touch targets - rendered second */}
            {gapRegions.map((region, idx) => (
              <Pressable
                key={`touch-gap-${idx}`}
                style={[
                  styles.gapTouchTarget,
                  {
                    left: region.startX,
                    width: region.endX - region.startX,
                  }
                ]}
                onPress={() => {
                  console.log('[MiniMap] Gap region touched, gap:', region.gap?.start_year, '-', region.gap?.end_year);
                  region.gap && onGapPress?.(region.gap);
                }}
              />
            ))}
            
            {/* Node-specific touch targets (larger than visible nodes) - rendered last (on top) */}
            {significantNodes.map((node) => {
              const touchSize = Math.max(MIN_TOUCH_SIZE, yearWidth * 2);
              return (
                <Pressable
                  key={`touch-node-${node.year}`}
                  style={[
                    styles.nodeTouchTarget,
                    {
                      left: node.x - (touchSize / 2),
                      top: node.y - (touchSize / 2),
                      width: touchSize,
                      height: touchSize,
                    }
                  ]}
                  onPress={() => {
                    console.log('[MiniMap] Node touch target pressed for year:', node.year);
                    handleTap(node.year);
                  }}
                  hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                />
              );
            })}
          </View>
        </View>
        
        {/* Year labels */}
        <View style={styles.yearLabels}>
          <Text style={[styles.yearLabel, { color: theme.textTertiary }]}>
            {birthYear}
          </Text>
          {decadeMarkers.slice(0, 4).map(year => (
            <Text 
              key={year} 
              style={[
                styles.decadeLabel, 
                { color: theme.textTertiary, left: (year - birthYear) * yearWidth - 12 }
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
      
      {/* Legend */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: accentColor }]} />
          <Text style={[styles.legendText, { color: theme.textTertiary }]}>Moments</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendLine, { borderColor: centerLineColor }]} />
          <Text style={[styles.legendText, { color: theme.textTertiary }]}>Balance point</Text>
        </View>
        {gapRegions.length > 0 && (
          <View style={styles.legendItem}>
            <View style={[styles.legendGap, { backgroundColor: theme.textTertiary }]} />
            <Text style={[styles.legendText, { color: theme.textTertiary }]}>Quiet periods</Text>
          </View>
        )}
      </View>
      
      {/* Selected year indicator */}
      {selectedYear && (
        <View style={[styles.selectionIndicator, { backgroundColor: `${accentColor}15`, borderColor: accentColor }]}>
          <Text style={[styles.selectionYear, { color: theme.text }]}>{selectedYear}</Text>
          {yearDataMap.get(selectedYear)?.eventCount ? (
            <Text style={[styles.selectionDetail, { color: theme.textSecondary }]}>
              {yearDataMap.get(selectedYear)?.eventCount} moment{yearDataMap.get(selectedYear)?.eventCount !== 1 ? 's' : ''}
              {' · Jumping...'}
            </Text>
          ) : yearDataMap.get(selectedYear)?.isGap ? (
            <Text style={[styles.selectionDetail, { color: theme.textTertiary }]}>Quiet period · Jumping...</Text>
          ) : (
            <Text style={[styles.selectionDetail, { color: theme.textTertiary }]}>Jumping...</Text>
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
  tapHint: {
    fontSize: 12,
    marginTop: 6,
    fontStyle: 'italic',
  },
  graphContainer: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  yAxisLabels: {
    width: 28,
    justifyContent: 'space-between',
    paddingVertical: VERTICAL_PADDING,
    marginRight: 4,
  },
  yAxisLabel: {
    fontSize: 8,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.3,
    transform: [{ rotate: '-90deg' }],
    width: 50,
    marginLeft: -11,
  },
  yAxisLabelBottom: {
    marginTop: 'auto',
  },
  svgContainer: {
    flex: 1,
    position: 'relative',
  },
  touchLayer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  nodeTouchTarget: {
    position: 'absolute',
    zIndex: 10,
  },
  gapTouchTarget: {
    position: 'absolute',
    top: VERTICAL_PADDING,
    height: ARC_HEIGHT,
    zIndex: 5,
  },
  fallbackTouchLayer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1,
  },
  yearLabels: {
    position: 'absolute',
    bottom: -18,
    left: 32,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
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
    fontSize: 9,
    width: 26,
    textAlign: 'center',
  },
  legend: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 14,
    marginTop: 20,
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
  legendLine: {
    width: 16,
    height: 0,
    borderWidth: 1,
    borderStyle: 'dashed',
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
  selectionIndicator: {
    position: 'absolute',
    top: 50,
    alignSelf: 'center',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: 'center',
  },
  selectionYear: {
    fontSize: 16,
    fontWeight: '600',
  },
  selectionDetail: {
    fontSize: 11,
    marginTop: 2,
  },
});
