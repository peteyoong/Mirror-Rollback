/**
 * EnneagramWheel - JSON-Driven Enneagram Wheel Component
 * 
 * This component renders an Enneagram wheel from a deterministic JSON structure.
 * All positions, connections, and visual states are derived from data, not hardcoded.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle, Line, Path, Defs, Marker } from 'react-native-svg';
import { useTheme } from '../contexts/ThemeContext';

// ============================================
// ENNEAGRAM JSON SCHEMA (Single Source of Truth)
// ============================================

export interface EnneagramType {
  id: number;
  name: string;
  core_need: string;
  angle: number; // degrees, 0 = right, clockwise
}

export interface EnneagramConnections {
  growth: { [key: string]: number };
  stress: { [key: string]: number };
}

export interface EnneagramSchema {
  types: EnneagramType[];
  connections: EnneagramConnections;
}

export interface UserEnneagramState {
  core_type: number;
  wing: number | null;
  growth_target: number;
  stress_target: number;
}

export interface EnneagramWheelData {
  enneagram: EnneagramSchema;
  user_state: UserEnneagramState;
}

// ============================================
// DEFAULT ENNEAGRAM DATA (Single Source of Truth)
// ============================================

export const ENNEAGRAM_SCHEMA: EnneagramSchema = {
  types: [
    { id: 1, name: "Reformer", core_need: "to be perfect", angle: 0 },
    { id: 2, name: "Helper", core_need: "to be needed", angle: 40 },
    { id: 3, name: "Achiever", core_need: "to succeed", angle: 80 },
    { id: 4, name: "Individualist", core_need: "to be special", angle: 120 },
    { id: 5, name: "Observer", core_need: "to perceive", angle: 160 },
    { id: 6, name: "Loyalist", core_need: "security", angle: 200 },
    { id: 7, name: "Enthusiast", core_need: "to avoid pain", angle: 240 },
    { id: 8, name: "Challenger", core_need: "to control", angle: 280 },
    { id: 9, name: "Peacemaker", core_need: "to avoid conflict", angle: 320 }
  ],
  connections: {
    growth: {
      "1": 7, "2": 4, "3": 6, "4": 1, "5": 8,
      "6": 9, "7": 5, "8": 2, "9": 3
    },
    stress: {
      "1": 4, "2": 8, "3": 9, "4": 2, "5": 7,
      "6": 3, "7": 1, "8": 5, "9": 6
    }
  }
};

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Convert polar coordinates (angle, radius) to Cartesian (x, y)
 * Angle is in degrees, 0 = top (12 o'clock), clockwise
 */
const polarToCartesian = (
  centerX: number,
  centerY: number,
  radius: number,
  angleInDegrees: number
): { x: number; y: number } => {
  // Adjust angle: 0° at top, clockwise
  // Standard math: 0° at right, counter-clockwise
  // So we rotate by -90° and negate for clockwise
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180;
  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians)
  };
};

/**
 * Get type data by ID from schema
 */
const getTypeById = (schema: EnneagramSchema, id: number): EnneagramType | undefined => {
  return schema.types.find(t => t.id === id);
};

/**
 * Generate user state from core type using the schema connections
 */
export const generateUserState = (
  coreType: number,
  wing: number | null,
  schema: EnneagramSchema = ENNEAGRAM_SCHEMA
): UserEnneagramState => {
  return {
    core_type: coreType,
    wing: wing,
    growth_target: schema.connections.growth[coreType.toString()] || 0,
    stress_target: schema.connections.stress[coreType.toString()] || 0
  };
};

// ============================================
// COMPONENT PROPS
// ============================================

interface EnneagramWheelProps {
  coreType: number;
  wing?: number | null;
  size?: number; // Container size in pixels
  showLabels?: boolean; // Show type names around the wheel
  showArrows?: boolean; // Show growth/stress arrows
  compact?: boolean; // Compact mode for smaller displays
}

// ============================================
// COLORS
// ============================================

const COLORS = {
  core: '#C9A86C', // Beige/warm accent
  coreDark: '#A68B4B',
  wing: 'rgba(201, 168, 108, 0.4)', // 40% opacity core color
  wingBorder: '#C9A86C',
  growth: '#2E7D32', // Green
  growthLight: 'rgba(46, 125, 50, 0.15)',
  stress: '#C62828', // Red
  stressLight: 'rgba(198, 40, 40, 0.15)',
  inactive: 'rgba(150, 150, 150, 0.35)',
  line: 'rgba(150, 150, 150, 0.3)',
  text: '#E8E3DB',
  textSecondary: '#9A9590',
};

// ============================================
// MAIN COMPONENT
// ============================================

export default function EnneagramWheel({
  coreType,
  wing = null,
  size = 240,
  showLabels = false,
  showArrows = true,
  compact = true
}: EnneagramWheelProps) {
  const { theme } = useTheme();
  
  // Generate user state from props
  const userState = generateUserState(coreType, wing);
  const schema = ENNEAGRAM_SCHEMA;
  
  // Layout calculations
  const center = size / 2;
  const nodeRadius = compact ? size * 0.35 : size * 0.38; // Radius for node positions
  const nodeSize = compact ? 40 : 48; // Node circle size
  const nodeSizeCore = compact ? 46 : 54; // Larger node for core type
  const svgSize = size;
  
  // Get positions for all types
  const typePositions = schema.types.map(type => {
    const pos = polarToCartesian(center, center, nodeRadius, type.angle);
    return { ...type, ...pos };
  });
  
  // Get core, wing, growth, stress types
  const coreTypeData = getTypeById(schema, userState.core_type);
  const wingTypeData = wing ? getTypeById(schema, wing) : null;
  const growthTypeData = getTypeById(schema, userState.growth_target);
  const stressTypeData = getTypeById(schema, userState.stress_target);
  
  // Calculate positions for arrows
  const corePos = coreTypeData 
    ? polarToCartesian(center, center, nodeRadius, coreTypeData.angle)
    : { x: center, y: center };
  const growthPos = growthTypeData
    ? polarToCartesian(center, center, nodeRadius, growthTypeData.angle)
    : null;
  const stressPos = stressTypeData
    ? polarToCartesian(center, center, nodeRadius, stressTypeData.angle)
    : null;
  
  // Determine node visual state
  const getNodeState = (typeId: number) => {
    if (typeId === userState.core_type) return 'core';
    if (typeId === userState.wing) return 'wing';
    if (typeId === userState.growth_target) return 'growth';
    if (typeId === userState.stress_target) return 'stress';
    return 'inactive';
  };
  
  // Get node styles based on state
  const getNodeStyles = (state: string) => {
    switch (state) {
      case 'core':
        return {
          backgroundColor: theme.accent || COLORS.core,
          borderColor: theme.accent || COLORS.core,
          borderWidth: 2.5,
          size: nodeSizeCore,
          textColor: theme.isDark ? '#0B0B0C' : '#F0EDE8',
          fontWeight: '700' as const,
          opacity: 1,
        };
      case 'wing':
        return {
          backgroundColor: `${theme.accent || COLORS.core}40`,
          borderColor: theme.accent || COLORS.wingBorder,
          borderWidth: 2,
          size: nodeSize,
          textColor: theme.accent || COLORS.core,
          fontWeight: '600' as const,
          opacity: 1,
        };
      case 'growth':
        return {
          backgroundColor: COLORS.growthLight,
          borderColor: COLORS.growth,
          borderWidth: 1.5,
          size: nodeSize,
          textColor: COLORS.growth,
          fontWeight: '600' as const,
          opacity: 1,
        };
      case 'stress':
        return {
          backgroundColor: COLORS.stressLight,
          borderColor: COLORS.stress,
          borderWidth: 1.5,
          size: nodeSize,
          textColor: COLORS.stress,
          fontWeight: '600' as const,
          opacity: 1,
        };
      default:
        return {
          backgroundColor: theme.surface || '#1A1A1B',
          borderColor: theme.border || '#333',
          borderWidth: 1,
          size: nodeSize,
          textColor: theme.textSecondary || COLORS.textSecondary,
          fontWeight: '500' as const,
          opacity: 0.35,
        };
    }
  };
  
  // Render arrow path for growth/stress lines
  const renderArrowLine = (
    fromX: number,
    fromY: number,
    toX: number,
    toY: number,
    color: string,
    isDashed: boolean = false
  ) => {
    // Calculate shortened line (to not overlap with nodes)
    const dx = toX - fromX;
    const dy = toY - fromY;
    const length = Math.sqrt(dx * dx + dy * dy);
    const shortening = nodeSize / 2 + 8; // Shorten by half node size + margin
    
    const startX = fromX + (dx / length) * shortening;
    const startY = fromY + (dy / length) * shortening;
    const endX = toX - (dx / length) * shortening;
    const endY = toY - (dy / length) * shortening;
    
    // Arrow head size
    const arrowSize = 8;
    const angle = Math.atan2(endY - startY, endX - startX);
    const arrowX1 = endX - arrowSize * Math.cos(angle - Math.PI / 6);
    const arrowY1 = endY - arrowSize * Math.sin(angle - Math.PI / 6);
    const arrowX2 = endX - arrowSize * Math.cos(angle + Math.PI / 6);
    const arrowY2 = endY - arrowSize * Math.sin(angle + Math.PI / 6);
    
    return (
      <>
        <Line
          x1={startX}
          y1={startY}
          x2={endX}
          y2={endY}
          stroke={color}
          strokeWidth={2}
          strokeDasharray={isDashed ? "6,4" : undefined}
          opacity={0.8}
        />
        {/* Arrow head */}
        <Path
          d={`M ${endX} ${endY} L ${arrowX1} ${arrowY1} L ${arrowX2} ${arrowY2} Z`}
          fill={color}
          opacity={0.8}
        />
      </>
    );
  };
  
  return (
    <View style={styles.container}>
      {/* SVG Layer for connections/arrows */}
      <Svg
        width={svgSize}
        height={svgSize}
        style={styles.svgLayer}
      >
        {/* Growth arrow (green, solid) */}
        {showArrows && growthPos && (
          renderArrowLine(
            corePos.x,
            corePos.y,
            growthPos.x,
            growthPos.y,
            COLORS.growth,
            false
          )
        )}
        
        {/* Stress arrow (red, dashed) */}
        {showArrows && stressPos && (
          renderArrowLine(
            corePos.x,
            corePos.y,
            stressPos.x,
            stressPos.y,
            COLORS.stress,
            true
          )
        )}
      </Svg>
      
      {/* Node Layer */}
      <View style={[styles.nodeLayer, { width: svgSize, height: svgSize }]}>
        {typePositions.map(type => {
          const state = getNodeState(type.id);
          const nodeStyles = getNodeStyles(state);
          const halfSize = nodeStyles.size / 2;
          
          return (
            <View
              key={type.id}
              style={[
                styles.node,
                {
                  left: type.x - halfSize,
                  top: type.y - halfSize,
                  width: nodeStyles.size,
                  height: nodeStyles.size,
                  borderRadius: nodeStyles.size / 2,
                  backgroundColor: nodeStyles.backgroundColor,
                  borderColor: nodeStyles.borderColor,
                  borderWidth: nodeStyles.borderWidth,
                  opacity: nodeStyles.opacity,
                }
              ]}
            >
              <Text
                style={[
                  styles.nodeNumber,
                  {
                    color: nodeStyles.textColor,
                    fontWeight: nodeStyles.fontWeight,
                    fontSize: state === 'core' ? 18 : 16,
                  }
                ]}
              >
                {type.id}
              </Text>
            </View>
          );
        })}
        
        {/* Center display */}
        <View style={[styles.centerDisplay, { left: center - 30, top: center - 18 }]}>
          <Text style={[styles.centerText, { color: theme.text || COLORS.text }]}>
            {wing ? `${coreType}w${wing}` : `${coreType}`}
          </Text>
        </View>
      </View>
      
      {/* Labels around the wheel (optional) */}
      {showLabels && (
        <View style={[styles.labelLayer, { width: svgSize + 120, height: svgSize + 60 }]}>
          {typePositions.map(type => {
            const state = getNodeState(type.id);
            const labelRadius = nodeRadius + 45;
            const labelPos = polarToCartesian(center + 60, center + 30, labelRadius, type.angle);
            
            // Adjust label position based on angle for readability
            const isLeft = type.angle > 135 && type.angle < 270;
            const isTop = type.angle <= 45 || type.angle >= 315;
            const isBottom = type.angle >= 135 && type.angle <= 225;
            
            return (
              <View
                key={`label-${type.id}`}
                style={[
                  styles.labelContainer,
                  {
                    left: labelPos.x - (isLeft ? 90 : 10),
                    top: labelPos.y - 10,
                  }
                ]}
              >
                <Text style={[
                  styles.labelName,
                  { 
                    color: state === 'core' ? (theme.accent || COLORS.core) 
                         : state === 'inactive' ? (theme.textTertiary || '#666')
                         : (theme.text || COLORS.text),
                    fontWeight: state === 'core' ? '600' : '400',
                    textAlign: isLeft ? 'right' : 'left',
                  }
                ]}>
                  {type.name}
                </Text>
              </View>
            );
          })}
        </View>
      )}
      
      {/* Legend */}
      <View style={styles.legend}>
        <View style={styles.legendRow}>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: theme.accent || COLORS.core }]} />
            <Text style={[styles.legendText, { color: theme.textTertiary || COLORS.textSecondary }]}>
              Core
            </Text>
          </View>
          {wing && (
            <View style={styles.legendItem}>
              <View style={[
                styles.legendDot, 
                { 
                  backgroundColor: `${theme.accent || COLORS.core}60`,
                  borderWidth: 1,
                  borderColor: theme.accent || COLORS.wingBorder,
                }
              ]} />
              <Text style={[styles.legendText, { color: theme.textTertiary || COLORS.textSecondary }]}>
                Wing
              </Text>
            </View>
          )}
        </View>
        <View style={styles.legendRow}>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: COLORS.growth }]} />
            <Text style={[styles.legendText, { color: theme.textTertiary || COLORS.textSecondary }]}>
              Growth → {userState.growth_target} when resourced
            </Text>
          </View>
        </View>
        <View style={styles.legendRow}>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: COLORS.stress }]} />
            <Text style={[styles.legendText, { color: theme.textTertiary || COLORS.textSecondary }]}>
              Stress → {userState.stress_target} under pressure
            </Text>
          </View>
        </View>
      </View>
    </View>
  );
}

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  svgLayer: {
    position: 'absolute',
  },
  nodeLayer: {
    position: 'relative',
  },
  node: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  nodeNumber: {
    fontSize: 16,
    fontWeight: '600',
  },
  centerDisplay: {
    position: 'absolute',
    width: 60,
    alignItems: 'center',
    justifyContent: 'center',
  },
  centerText: {
    fontSize: 18,
    fontWeight: '700',
  },
  labelLayer: {
    position: 'absolute',
  },
  labelContainer: {
    position: 'absolute',
    width: 100,
  },
  labelName: {
    fontSize: 11,
  },
  legend: {
    marginTop: 16,
    gap: 6,
    width: '100%',
    paddingHorizontal: 8,
  },
  legendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    flexWrap: 'wrap',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  legendText: {
    fontSize: 12,
  },
});
