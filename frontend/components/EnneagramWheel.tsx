/**
 * EnneagramWheel - Classic Enneagram Diagram with Annotations Around Wheel
 * 
 * Renders a proper Enneagram wheel with:
 * - Outer circle
 * - 9 type positions (9 at top, clockwise)
 * - Classic inner line geometry (triangle 3-6-9, hexad 1-4-2-8-5-7)
 * - Type labels positioned AROUND the wheel (not in a list below)
 * - User overlay for core, wing, growth, stress highlights
 * - Subtle radial gradient for depth
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle, Line, Path, G, Text as SvgText, Defs, RadialGradient, Stop } from 'react-native-svg';
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
const TRIANGLE_CONNECTIONS = [[3, 6], [6, 9], [9, 3]];
const HEXAD_CONNECTIONS = [[1, 4], [4, 2], [2, 8], [8, 5], [5, 7], [7, 1]];

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
  const angleRadians = (angleDegrees - 90) * (Math.PI / 180);
  return {
    x: centerX + radius * Math.cos(angleRadians),
    y: centerY + radius * Math.sin(angleRadians)
  };
};

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

// Type display names
const TYPE_DISPLAY_NAMES: { [key: number]: string } = {
  1: "Reformer", 2: "Helper", 3: "Achiever", 4: "Individualist",
  5: "Observer", 6: "Loyalist", 7: "Epicure", 8: "Challenger", 9: "Peacemaker",
};

// ============================================
// MAIN COMPONENT
// ============================================

export default function EnneagramWheel({
  coreType,
  wing = null,
  size = 300,
  showLabels = true,
  compact = false
}: EnneagramWheelProps) {
  const { theme } = useTheme();
  
  // Calculate dimensions for labels around the wheel
  const containerSize = showLabels ? size + 140 : size;
  const svgSize = size;
  const center = svgSize / 2;
  const outerRadius = (svgSize / 2) - 12;
  const nodeRadius = outerRadius - 18;
  const innerLineRadius = nodeRadius - 10;
  
  // Get growth and stress targets
  const growthTarget = GROWTH_DIRECTIONS[coreType] || 0;
  const stressTarget = STRESS_DIRECTIONS[coreType] || 0;
  
  // Node sizes
  const nodeSize = compact ? 26 : 30;
  const coreNodeSize = compact ? 32 : 36;
  
  // Colors - POLISHED for better mobile readability
  // Increased contrast for muted elements while keeping hierarchy
  const colors = {
    // Outer circle - more visible
    circle: theme.isDark ? 'rgba(201, 168, 108, 0.50)' : 'rgba(201, 168, 108, 0.6)',
    // Inner geometry lines - clearer but still subtle
    innerLines: theme.isDark ? 'rgba(201, 168, 108, 0.30)' : 'rgba(201, 168, 108, 0.4)',
    // Active highlights
    core: theme.accent || '#C9A86C',
    wing: theme.isDark ? 'rgba(201, 168, 108, 0.55)' : 'rgba(201, 168, 108, 0.65)',
    growth: '#2E7D32',
    stress: '#C62828',
    // Inactive elements - improved contrast
    inactive: theme.isDark ? 'rgba(160, 155, 145, 0.45)' : 'rgba(100, 100, 100, 0.45)',
    inactiveText: theme.isDark ? 'rgba(180, 175, 165, 0.70)' : 'rgba(90, 90, 90, 0.75)',
    inactiveNeed: theme.isDark ? 'rgba(160, 155, 145, 0.60)' : 'rgba(100, 100, 100, 0.65)',
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
        strokeWidth: 2.5,
        size: coreNodeSize,
        textColor: theme.isDark ? '#0B0B0C' : '#FFFFFF',
        fontWeight: '700' as const,
        opacity: 1,
        labelColor: colors.core,
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
        labelColor: colors.core,
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
        labelColor: colors.growth,
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
        labelColor: colors.stress,
      };
    }
    return {
      fill: theme.isDark ? 'rgba(50, 48, 45, 0.9)' : 'rgba(240, 237, 232, 0.9)',
      stroke: colors.inactive,
      strokeWidth: 1.5,
      size: nodeSize - 2,
      textColor: colors.inactiveText,
      fontWeight: '500' as const,
      opacity: 0.65,
      labelColor: colors.inactiveText,
    };
  };
  
  // Render inner enneagram lines - improved visibility
  const renderInnerLines = () => {
    const lines: JSX.Element[] = [];
    
    // Triangle (3-6-9) - slightly thicker for visibility
    TRIANGLE_CONNECTIONS.forEach(([from, to], idx) => {
      const fromPos = getTypePosition(from, center, center, innerLineRadius);
      const toPos = getTypePosition(to, center, center, innerLineRadius);
      lines.push(
        <Line key={`tri-${idx}`} x1={fromPos.x} y1={fromPos.y} x2={toPos.x} y2={toPos.y}
          stroke={colors.innerLines} strokeWidth={1.8} />
      );
    });
    
    // Hexad (1-4-2-8-5-7) - slightly thicker for visibility
    HEXAD_CONNECTIONS.forEach(([from, to], idx) => {
      const fromPos = getTypePosition(from, center, center, innerLineRadius);
      const toPos = getTypePosition(to, center, center, innerLineRadius);
      lines.push(
        <Line key={`hex-${idx}`} x1={fromPos.x} y1={fromPos.y} x2={toPos.x} y2={toPos.y}
          stroke={colors.innerLines} strokeWidth={1.8} />
      );
    });
    
    return lines;
  };
  
  // Render directional arrows
  const renderDirectionalLine = (fromType: number, toType: number, color: string, isDashed: boolean = false) => {
    const fromPos = getTypePosition(fromType, center, center, nodeRadius);
    const toPos = getTypePosition(toType, center, center, nodeRadius);
    
    const dx = toPos.x - fromPos.x;
    const dy = toPos.y - fromPos.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    const shortenBy = coreNodeSize / 2 + 8;
    
    const startX = fromPos.x + (dx / length) * shortenBy;
    const startY = fromPos.y + (dy / length) * shortenBy;
    const endX = toPos.x - (dx / length) * (nodeSize / 2 + 6);
    const endY = toPos.y - (dy / length) * (nodeSize / 2 + 6);
    
    const arrowSize = 7;
    const angle = Math.atan2(endY - startY, endX - startX);
    const arrowX1 = endX - arrowSize * Math.cos(angle - Math.PI / 6);
    const arrowY1 = endY - arrowSize * Math.sin(angle - Math.PI / 6);
    const arrowX2 = endX - arrowSize * Math.cos(angle + Math.PI / 6);
    const arrowY2 = endY - arrowSize * Math.sin(angle + Math.PI / 6);
    
    return (
      <G key={`dir-${fromType}-${toType}`}>
        <Line x1={startX} y1={startY} x2={endX} y2={endY}
          stroke={color} strokeWidth={2} strokeDasharray={isDashed ? "5,3" : undefined} opacity={0.75} />
        <Path d={`M ${endX} ${endY} L ${arrowX1} ${arrowY1} L ${arrowX2} ${arrowY2} Z`}
          fill={color} opacity={0.75} />
      </G>
    );
  };
  
  // Render nodes
  const renderNodes = () => {
    return ENNEAGRAM_TYPES.map(type => {
      const pos = polarToXY(center, center, nodeRadius, type.angle);
      const style = getNodeStyle(type.id);
      const halfSize = style.size / 2;
      
      return (
        <G key={`node-${type.id}`} opacity={style.opacity}>
          <Circle cx={pos.x} cy={pos.y} r={halfSize}
            fill={style.fill} stroke={style.stroke} strokeWidth={style.strokeWidth} />
          <SvgText x={pos.x} y={pos.y + 1} fontSize={style.size > 30 ? 14 : 12}
            fontWeight={style.fontWeight} fill={style.textColor}
            textAnchor="middle" alignmentBaseline="middle">
            {type.id}
          </SvgText>
        </G>
      );
    });
  };
  
  // Get label position adjustment based on angle
  const getLabelPosition = (angle: number) => {
    // Determine which quadrant/position for better label placement
    if (angle === 0) return { align: 'center', vAlign: 'bottom', offsetX: 0, offsetY: -8 }; // top
    if (angle === 40) return { align: 'left', vAlign: 'bottom', offsetX: 8, offsetY: -4 }; // top-right
    if (angle === 80) return { align: 'left', vAlign: 'center', offsetX: 10, offsetY: 0 }; // right-top
    if (angle === 120) return { align: 'left', vAlign: 'center', offsetX: 10, offsetY: 0 }; // right-bottom
    if (angle === 160) return { align: 'left', vAlign: 'top', offsetX: 8, offsetY: 4 }; // bottom-right
    if (angle === 200) return { align: 'right', vAlign: 'top', offsetX: -8, offsetY: 4 }; // bottom-left
    if (angle === 240) return { align: 'right', vAlign: 'center', offsetX: -10, offsetY: 0 }; // left-bottom
    if (angle === 280) return { align: 'right', vAlign: 'center', offsetX: -10, offsetY: 0 }; // left-top
    if (angle === 320) return { align: 'right', vAlign: 'bottom', offsetX: -8, offsetY: -4 }; // top-left
    return { align: 'center', vAlign: 'center', offsetX: 0, offsetY: 0 };
  };
  
  return (
    <View style={styles.container}>
      {/* Wheel with labels around it */}
      <View style={[styles.wheelWrapper, { width: containerSize, height: containerSize }]}>
        {/* SVG Wheel in center */}
        <View style={[styles.svgContainer, { 
          width: svgSize, 
          height: svgSize,
          left: showLabels ? 70 : 0,
          top: showLabels ? 70 : 0,
        }]}>
          <Svg width={svgSize} height={svgSize}>
            {/* Radial gradient definition for subtle depth */}
            <Defs>
              <RadialGradient
                id="wheelDepthGradient"
                cx="50%"
                cy="50%"
                rx="55%"
                ry="55%"
                fx="50%"
                fy="50%"
              >
                <Stop offset="0%" stopColor="rgba(255, 245, 220, 0.06)" />
                <Stop offset="50%" stopColor="rgba(255, 245, 220, 0.03)" />
                <Stop offset="100%" stopColor="rgba(255, 245, 220, 0)" />
              </RadialGradient>
            </Defs>
            
            {/* Subtle depth gradient behind wheel */}
            <Circle
              cx={center}
              cy={center}
              r={outerRadius + 12}
              fill="url(#wheelDepthGradient)"
            />
            
            {/* Outer circle - slightly thicker */}
            <Circle cx={center} cy={center} r={outerRadius}
              fill="none" stroke={colors.circle} strokeWidth={2.5} />
            
            {/* Inner geometry */}
            {renderInnerLines()}
            
            {/* Directional arrows */}
            {renderDirectionalLine(coreType, growthTarget, colors.growth, false)}
            {renderDirectionalLine(coreType, stressTarget, colors.stress, true)}
            
            {/* Nodes */}
            {renderNodes()}
          </Svg>
        </View>
        
        {/* Labels positioned around the wheel */}
        {showLabels && ENNEAGRAM_TYPES.map(type => {
          const labelRadius = (svgSize / 2) + 52;
          const labelPos = polarToXY(containerSize / 2, containerSize / 2, labelRadius, type.angle);
          const posInfo = getLabelPosition(type.angle);
          const style = getNodeStyle(type.id);
          const isHighlighted = type.id === coreType || type.id === wing || type.id === growthTarget || type.id === stressTarget;
          
          return (
            <View
              key={`label-${type.id}`}
              style={[
                styles.labelContainer,
                {
                  left: labelPos.x + posInfo.offsetX - 55,
                  top: labelPos.y + posInfo.offsetY - 18,
                  alignItems: posInfo.align === 'right' ? 'flex-end' : posInfo.align === 'left' ? 'flex-start' : 'center',
                  opacity: isHighlighted ? 1 : 0.7, // Increased from 0.5 for better readability
                }
              ]}
            >
              <Text style={[
                styles.labelTitle,
                { 
                  color: style.labelColor,
                  fontWeight: isHighlighted ? '600' : '500',
                }
              ]}>
                {type.id} {type.shortName}
              </Text>
              <Text style={[
                styles.labelNeed,
                { color: isHighlighted ? colors.textSecondary : colors.inactiveNeed }
              ]}>
                {type.need}
              </Text>
            </View>
          );
        })}
      </View>
      
      {/* Compact Legend */}
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
          {wing ? `${coreType}w${wing}` : `Type ${coreType}`} — {TYPE_DISPLAY_NAMES[coreType]}
        </Text>
      </View>
    </View>
  );
}

// Backward compatibility exports
export const ENNEAGRAM_SCHEMA = {
  types: ENNEAGRAM_TYPES.map(t => ({ id: t.id, name: t.shortName, core_need: t.need, angle: t.angle })),
  connections: { growth: GROWTH_DIRECTIONS, stress: STRESS_DIRECTIONS }
};

export const generateUserState = (coreType: number, wing: number | null) => ({
  core_type: coreType, wing: wing,
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
  wheelWrapper: {
    position: 'relative',
  },
  svgContainer: {
    position: 'absolute',
  },
  labelContainer: {
    position: 'absolute',
    width: 110,
  },
  labelTitle: {
    fontSize: 11,
    fontWeight: '500',
    lineHeight: 14,
  },
  labelNeed: {
    fontSize: 9,
    lineHeight: 12,
    marginTop: 1,
  },
  legend: {
    width: '100%',
    paddingHorizontal: 8,
    marginTop: 12,
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
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(150, 150, 150, 0.2)',
    width: '100%',
  },
  resultText: {
    fontSize: 15,
    fontWeight: '600',
  },
});
