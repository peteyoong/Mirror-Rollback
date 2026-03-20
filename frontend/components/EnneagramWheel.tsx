/**
 * EnneagramWheel - Classic Enneagram Diagram Component
 * 
 * Renders a proper Enneagram wheel with:
 * - Outer circle
 * - 9 type positions (9 at top, clockwise)
 * - Classic inner line geometry (triangle 3-6-9, hexad 1-4-2-8-5-7)
 * - Type names and need descriptors
 * - User overlay for core, wing, growth, stress highlights
 */

import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import Svg, { Circle, Line, Path, G, Text as SvgText } from 'react-native-svg';
import { useTheme } from '../contexts/ThemeContext';

// ============================================
// ENNEAGRAM DATA (Single Source of Truth)
// ============================================

export interface EnneagramTypeData {
  id: number;
  name: string;
  shortName: string;
  need: string;
  angle: number; // degrees from top (0 = top, clockwise)
}

// Type positions: 9 at top (0°), then clockwise
// Each type is 40° apart (360/9 = 40)
export const ENNEAGRAM_TYPES: EnneagramTypeData[] = [
  { id: 9, name: "The Peacemaker", shortName: "Peacemaker", need: "to avoid conflict", angle: 0 },
  { id: 1, name: "The Reformer", shortName: "Reformer", need: "to be perfect", angle: 40 },
  { id: 2, name: "The Helper", shortName: "Helper", need: "to be needed", angle: 80 },
  { id: 3, name: "The Achiever", shortName: "Achiever", need: "to succeed", angle: 120 },
  { id: 4, name: "The Individualist", shortName: "Individualist", need: "to be special", angle: 160 },
  { id: 5, name: "The Observer", shortName: "Observer", need: "to perceive", angle: 200 },
  { id: 6, name: "The Loyalist", shortName: "Loyalist", need: "for security", angle: 240 },
  { id: 7, name: "The Epicure", shortName: "Epicure", need: "to avoid pain", angle: 280 },
  { id: 8, name: "The Challenger", shortName: "Challenger", need: "to control", angle: 320 },
];

// Growth and Stress connections
export const GROWTH_DIRECTIONS: { [key: number]: number } = {
  1: 7, 2: 4, 3: 6, 4: 1, 5: 8, 6: 9, 7: 5, 8: 2, 9: 3
};

export const STRESS_DIRECTIONS: { [key: number]: number } = {
  1: 4, 2: 8, 3: 9, 4: 2, 5: 7, 6: 3, 7: 1, 8: 5, 9: 6
};

// Classic Enneagram inner lines
// Triangle: 3-6-9
// Hexad: 1-4-2-8-5-7-1 (based on 1/7 = 0.142857...)
const TRIANGLE_CONNECTIONS = [
  [3, 6], [6, 9], [9, 3]
];

const HEXAD_CONNECTIONS = [
  [1, 4], [4, 2], [2, 8], [8, 5], [5, 7], [7, 1]
];

// ============================================
// HELPER FUNCTIONS
// ============================================

const getTypeById = (id: number): EnneagramTypeData | undefined => {
  return ENNEAGRAM_TYPES.find(t => t.id === id);
};

// Convert angle (0 = top, clockwise) to x,y coordinates
const polarToXY = (
  centerX: number,
  centerY: number,
  radius: number,
  angleDegrees: number
): { x: number; y: number } => {
  // Convert to radians, adjust so 0° is at top
  const angleRadians = (angleDegrees - 90) * (Math.PI / 180);
  return {
    x: centerX + radius * Math.cos(angleRadians),
    y: centerY + radius * Math.sin(angleRadians)
  };
};

// Get position for a type ID
const getTypePosition = (
  typeId: number,
  centerX: number,
  centerY: number,
  radius: number
): { x: number; y: number } => {
  const typeData = getTypeById(typeId);
  if (!typeData) return { x: centerX, y: centerY };
  return polarToXY(centerX, centerY, radius, typeData.angle);
};

// ============================================
// COMPONENT PROPS
// ============================================

interface EnneagramWheelProps {
  coreType: number;
  wing?: number | null;
  size?: number;
  showLabels?: boolean;
  compact?: boolean;
}

// ============================================
// TYPE NAMES FOR DISPLAY
// ============================================

const TYPE_DISPLAY_NAMES: { [key: number]: string } = {
  1: "Reformer",
  2: "Helper",
  3: "Achiever",
  4: "Individualist",
  5: "Observer",
  6: "Loyalist",
  7: "Epicure",
  8: "Challenger",
  9: "Peacemaker",
};

// ============================================
// MAIN COMPONENT
// ============================================

export default function EnneagramWheel({
  coreType,
  wing = null,
  size = 280,
  showLabels = true,
  compact = false
}: EnneagramWheelProps) {
  const { theme } = useTheme();
  
  // Calculate dimensions
  const svgSize = size;
  const center = svgSize / 2;
  const outerRadius = (svgSize / 2) - 8; // Main circle radius
  const nodeRadius = outerRadius - 15; // Where nodes sit
  const innerLineRadius = nodeRadius - 8; // Inner geometry lines
  
  // Get growth and stress targets
  const growthTarget = GROWTH_DIRECTIONS[coreType] || 0;
  const stressTarget = STRESS_DIRECTIONS[coreType] || 0;
  
  // Node sizes
  const nodeSize = compact ? 24 : 28;
  const coreNodeSize = compact ? 30 : 34;
  
  // Colors
  const colors = {
    circle: theme.isDark ? 'rgba(201, 168, 108, 0.3)' : 'rgba(201, 168, 108, 0.4)',
    innerLines: theme.isDark ? 'rgba(201, 168, 108, 0.15)' : 'rgba(201, 168, 108, 0.25)',
    core: theme.accent || '#C9A86C',
    wing: theme.isDark ? 'rgba(201, 168, 108, 0.5)' : 'rgba(201, 168, 108, 0.6)',
    growth: '#2E7D32',
    stress: '#C62828',
    inactive: theme.isDark ? 'rgba(150, 150, 150, 0.25)' : 'rgba(100, 100, 100, 0.3)',
    inactiveText: theme.isDark ? 'rgba(150, 150, 150, 0.6)' : 'rgba(100, 100, 100, 0.7)',
    text: theme.text || '#E8E3DB',
    textSecondary: theme.textSecondary || '#9A9590',
  };
  
  // Get node style based on type
  const getNodeStyle = (typeId: number) => {
    const isCore = typeId === coreType;
    const isWing = typeId === wing;
    const isGrowth = typeId === growthTarget;
    const isStress = typeId === stressTarget;
    
    if (isCore) {
      return {
        fill: colors.core,
        stroke: colors.core,
        strokeWidth: 2,
        size: coreNodeSize,
        textColor: theme.isDark ? '#0B0B0C' : '#FFFFFF',
        fontWeight: '700' as const,
        opacity: 1,
      };
    }
    if (isWing) {
      return {
        fill: colors.wing,
        stroke: colors.core,
        strokeWidth: 2,
        size: nodeSize + 2,
        textColor: colors.core,
        fontWeight: '600' as const,
        opacity: 1,
      };
    }
    if (isGrowth) {
      return {
        fill: 'rgba(46, 125, 50, 0.2)',
        stroke: colors.growth,
        strokeWidth: 2,
        size: nodeSize,
        textColor: colors.growth,
        fontWeight: '600' as const,
        opacity: 1,
      };
    }
    if (isStress) {
      return {
        fill: 'rgba(198, 40, 40, 0.2)',
        stroke: colors.stress,
        strokeWidth: 2,
        size: nodeSize,
        textColor: colors.stress,
        fontWeight: '600' as const,
        opacity: 1,
      };
    }
    return {
      fill: theme.isDark ? 'rgba(40, 40, 40, 0.8)' : 'rgba(240, 237, 232, 0.9)',
      stroke: colors.inactive,
      strokeWidth: 1,
      size: nodeSize - 4,
      textColor: colors.inactiveText,
      fontWeight: '500' as const,
      opacity: 0.5,
    };
  };
  
  // Render inner enneagram lines
  const renderInnerLines = () => {
    const lines: JSX.Element[] = [];
    
    // Triangle (3-6-9)
    TRIANGLE_CONNECTIONS.forEach(([from, to], idx) => {
      const fromPos = getTypePosition(from, center, center, innerLineRadius);
      const toPos = getTypePosition(to, center, center, innerLineRadius);
      lines.push(
        <Line
          key={`tri-${idx}`}
          x1={fromPos.x}
          y1={fromPos.y}
          x2={toPos.x}
          y2={toPos.y}
          stroke={colors.innerLines}
          strokeWidth={1.5}
        />
      );
    });
    
    // Hexad (1-4-2-8-5-7)
    HEXAD_CONNECTIONS.forEach(([from, to], idx) => {
      const fromPos = getTypePosition(from, center, center, innerLineRadius);
      const toPos = getTypePosition(to, center, center, innerLineRadius);
      lines.push(
        <Line
          key={`hex-${idx}`}
          x1={fromPos.x}
          y1={fromPos.y}
          x2={toPos.x}
          y2={toPos.y}
          stroke={colors.innerLines}
          strokeWidth={1.5}
        />
      );
    });
    
    return lines;
  };
  
  // Render directional indicator (growth/stress)
  const renderDirectionalLine = (
    fromType: number,
    toType: number,
    color: string,
    isDashed: boolean = false
  ) => {
    const fromPos = getTypePosition(fromType, center, center, nodeRadius);
    const toPos = getTypePosition(toType, center, center, nodeRadius);
    
    // Shorten line to not overlap with nodes
    const dx = toPos.x - fromPos.x;
    const dy = toPos.y - fromPos.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    const shortenBy = coreNodeSize / 2 + 6;
    
    const startX = fromPos.x + (dx / length) * shortenBy;
    const startY = fromPos.y + (dy / length) * shortenBy;
    const endX = toPos.x - (dx / length) * (nodeSize / 2 + 4);
    const endY = toPos.y - (dy / length) * (nodeSize / 2 + 4);
    
    // Arrow head
    const arrowSize = 6;
    const angle = Math.atan2(endY - startY, endX - startX);
    const arrowX1 = endX - arrowSize * Math.cos(angle - Math.PI / 6);
    const arrowY1 = endY - arrowSize * Math.sin(angle - Math.PI / 6);
    const arrowX2 = endX - arrowSize * Math.cos(angle + Math.PI / 6);
    const arrowY2 = endY - arrowSize * Math.sin(angle + Math.PI / 6);
    
    return (
      <G key={`dir-${fromType}-${toType}`}>
        <Line
          x1={startX}
          y1={startY}
          x2={endX}
          y2={endY}
          stroke={color}
          strokeWidth={2}
          strokeDasharray={isDashed ? "4,3" : undefined}
          opacity={0.7}
        />
        <Path
          d={`M ${endX} ${endY} L ${arrowX1} ${arrowY1} L ${arrowX2} ${arrowY2} Z`}
          fill={color}
          opacity={0.7}
        />
      </G>
    );
  };
  
  // Render nodes (type circles)
  const renderNodes = () => {
    return ENNEAGRAM_TYPES.map(type => {
      const pos = polarToXY(center, center, nodeRadius, type.angle);
      const style = getNodeStyle(type.id);
      const halfSize = style.size / 2;
      
      return (
        <G key={`node-${type.id}`} opacity={style.opacity}>
          <Circle
            cx={pos.x}
            cy={pos.y}
            r={halfSize}
            fill={style.fill}
            stroke={style.stroke}
            strokeWidth={style.strokeWidth}
          />
          <SvgText
            x={pos.x}
            y={pos.y + 1}
            fontSize={style.size > 28 ? 14 : 12}
            fontWeight={style.fontWeight}
            fill={style.textColor}
            textAnchor="middle"
            alignmentBaseline="middle"
          >
            {type.id}
          </SvgText>
        </G>
      );
    });
  };
  
  return (
    <View style={styles.container}>
      {/* SVG Wheel */}
      <View style={styles.wheelContainer}>
        <Svg width={svgSize} height={svgSize}>
          {/* Outer circle */}
          <Circle
            cx={center}
            cy={center}
            r={outerRadius}
            fill="none"
            stroke={colors.circle}
            strokeWidth={2}
          />
          
          {/* Inner enneagram geometry */}
          {renderInnerLines()}
          
          {/* Directional arrows (growth and stress) */}
          {renderDirectionalLine(coreType, growthTarget, colors.growth, false)}
          {renderDirectionalLine(coreType, stressTarget, colors.stress, true)}
          
          {/* Type nodes */}
          {renderNodes()}
        </Svg>
      </View>
      
      {/* Labels around the wheel (mobile-friendly list below) */}
      {showLabels && (
        <View style={styles.labelsContainer}>
          {ENNEAGRAM_TYPES.map(type => {
            const isCore = type.id === coreType;
            const isWing = type.id === wing;
            const isGrowth = type.id === growthTarget;
            const isStress = type.id === stressTarget;
            const isHighlighted = isCore || isWing || isGrowth || isStress;
            
            return (
              <View key={`label-${type.id}`} style={styles.labelRow}>
                <View style={[
                  styles.labelNumber,
                  isCore && { backgroundColor: colors.core },
                  isWing && { backgroundColor: colors.wing, borderColor: colors.core, borderWidth: 1 },
                  isGrowth && { backgroundColor: 'rgba(46, 125, 50, 0.2)', borderColor: colors.growth, borderWidth: 1 },
                  isStress && { backgroundColor: 'rgba(198, 40, 40, 0.2)', borderColor: colors.stress, borderWidth: 1 },
                  !isHighlighted && { backgroundColor: theme.surfaceLight, opacity: 0.5 },
                ]}>
                  <Text style={[
                    styles.labelNumberText,
                    isCore && { color: theme.isDark ? '#0B0B0C' : '#FFFFFF' },
                    isWing && { color: colors.core },
                    isGrowth && { color: colors.growth },
                    isStress && { color: colors.stress },
                    !isHighlighted && { color: colors.inactiveText },
                  ]}>
                    {type.id}
                  </Text>
                </View>
                <View style={styles.labelTextContainer}>
                  <Text style={[
                    styles.labelName,
                    { color: isHighlighted ? colors.text : colors.inactiveText },
                    isCore && { fontWeight: '600' },
                  ]}>
                    {type.shortName}
                  </Text>
                  <Text style={[
                    styles.labelNeed,
                    { color: isHighlighted ? colors.textSecondary : colors.inactiveText },
                  ]}>
                    The need {type.need}
                  </Text>
                </View>
                {isCore && (
                  <View style={[styles.labelBadge, { backgroundColor: colors.core }]}>
                    <Text style={[styles.labelBadgeText, { color: theme.isDark ? '#0B0B0C' : '#FFFFFF' }]}>Core</Text>
                  </View>
                )}
                {isWing && (
                  <View style={[styles.labelBadge, { backgroundColor: colors.wing, borderColor: colors.core, borderWidth: 1 }]}>
                    <Text style={[styles.labelBadgeText, { color: colors.core }]}>Wing</Text>
                  </View>
                )}
                {isGrowth && (
                  <View style={[styles.labelBadge, { backgroundColor: 'rgba(46, 125, 50, 0.2)', borderColor: colors.growth, borderWidth: 1 }]}>
                    <Text style={[styles.labelBadgeText, { color: colors.growth }]}>Growth</Text>
                  </View>
                )}
                {isStress && (
                  <View style={[styles.labelBadge, { backgroundColor: 'rgba(198, 40, 40, 0.2)', borderColor: colors.stress, borderWidth: 1 }]}>
                    <Text style={[styles.labelBadgeText, { color: colors.stress }]}>Stress</Text>
                  </View>
                )}
              </View>
            );
          })}
        </View>
      )}
      
      {/* Legend */}
      <View style={styles.legend}>
        <View style={styles.legendRow}>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: colors.core }]} />
            <Text style={[styles.legendText, { color: colors.textSecondary }]}>Core</Text>
          </View>
          {wing && (
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: colors.wing, borderWidth: 1, borderColor: colors.core }]} />
              <Text style={[styles.legendText, { color: colors.textSecondary }]}>Wing</Text>
            </View>
          )}
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: colors.growth }]} />
            <Text style={[styles.legendText, { color: colors.textSecondary }]}>Growth → {growthTarget}</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: colors.stress }]} />
            <Text style={[styles.legendText, { color: colors.textSecondary }]}>Stress → {stressTarget}</Text>
          </View>
        </View>
      </View>
      
      {/* Result Label */}
      <View style={styles.resultLabel}>
        <Text style={[styles.resultText, { color: colors.text }]}>
          {wing ? `${coreType}w${wing}` : `Type ${coreType}`} — {TYPE_DISPLAY_NAMES[coreType] || 'Unknown'}
        </Text>
      </View>
    </View>
  );
}

// For backward compatibility
export const ENNEAGRAM_SCHEMA = {
  types: ENNEAGRAM_TYPES.map(t => ({
    id: t.id,
    name: t.shortName,
    core_need: t.need,
    angle: t.angle
  })),
  connections: {
    growth: GROWTH_DIRECTIONS,
    stress: STRESS_DIRECTIONS
  }
};

export const generateUserState = (coreType: number, wing: number | null) => ({
  core_type: coreType,
  wing: wing,
  growth_target: GROWTH_DIRECTIONS[coreType] || 0,
  stress_target: STRESS_DIRECTIONS[coreType] || 0
});

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
  },
  wheelContainer: {
    marginBottom: 16,
  },
  labelsContainer: {
    width: '100%',
    paddingHorizontal: 4,
    marginBottom: 16,
  },
  labelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderRadius: 8,
    marginBottom: 4,
  },
  labelNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  labelNumberText: {
    fontSize: 12,
    fontWeight: '600',
  },
  labelTextContainer: {
    flex: 1,
  },
  labelName: {
    fontSize: 13,
    fontWeight: '500',
  },
  labelNeed: {
    fontSize: 11,
    marginTop: 1,
  },
  labelBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    marginLeft: 8,
  },
  labelBadgeText: {
    fontSize: 10,
    fontWeight: '600',
  },
  legend: {
    width: '100%',
    paddingHorizontal: 8,
    marginBottom: 12,
  },
  legendRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 12,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  legendText: {
    fontSize: 11,
  },
  resultLabel: {
    alignItems: 'center',
    paddingTop: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(150, 150, 150, 0.2)',
    width: '100%',
  },
  resultText: {
    fontSize: 15,
    fontWeight: '600',
  },
});
