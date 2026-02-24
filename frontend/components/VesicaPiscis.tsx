/**
 * VesicaPiscis - Sacred Geometry Symbol for Project Mirror
 * 
 * "The space for noticing" - the intersection of two worlds.
 * Clean, mathematical, precise. A reflective surface, not a watching entity.
 * 
 * Design: Two overlapping circles forming the vesica piscis (lens shape)
 * No fill, no glow, no animation - just the pure geometric form.
 */

import React from 'react';
import { View, StyleSheet } from 'react-native';
import Svg, { Circle, G } from 'react-native-svg';

// Gold color at specified opacities
const GOLD = '#D4AF37';

interface VesicaPiscisProps {
  size?: number;  // Width of the entire symbol (default 80px)
}

export default function VesicaPiscis({ size = 80 }: VesicaPiscisProps) {
  // Calculate dimensions
  // Vesica piscis: two circles where each passes through the other's center
  const circleRadius = size * 0.4;
  const circleOffset = circleRadius * 0.5;  // Distance from center to each circle center
  
  const viewBoxSize = size;
  const cx = viewBoxSize / 2;
  const cy = viewBoxSize / 2;
  
  // Outer ripple circle (optional enhancement)
  const outerRadius = size * 0.48;
  
  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <Svg 
        width={size} 
        height={size} 
        viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
      >
        {/* Outer ripple circle - very faint, suggesting field */}
        <Circle
          cx={cx}
          cy={cy}
          r={outerRadius}
          fill="none"
          stroke={GOLD}
          strokeWidth={1}
          strokeOpacity={0.08}
        />
        
        {/* Vesica Piscis - two overlapping circles */}
        <G>
          {/* Left circle */}
          <Circle
            cx={cx - circleOffset}
            cy={cy}
            r={circleRadius}
            fill="none"
            stroke={GOLD}
            strokeWidth={1}
            strokeOpacity={0.20}
          />
          
          {/* Right circle */}
          <Circle
            cx={cx + circleOffset}
            cy={cy}
            r={circleRadius}
            fill="none"
            stroke={GOLD}
            strokeWidth={1}
            strokeOpacity={0.20}
          />
        </G>
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
