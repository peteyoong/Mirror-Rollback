/**
 * VesicaPiscis - Sacred Geometry Symbol for Project Mirror
 * 
 * "The space for noticing" - the intersection of two worlds.
 * Clean, mathematical, precise. A reflective surface, not a watching entity.
 * 
 * Design: Two overlapping circles forming the vesica piscis (lens shape)
 * With subtle breathing pulse animation for presence.
 */

import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Easing, Platform } from 'react-native';
import Svg, { Circle, G, Defs, RadialGradient, Stop } from 'react-native-svg';

// Brighter, more luminous gold
const GOLD = '#F0D878';

// Animation timing
const PULSE_DURATION = 8000;  // 8 second breathing cycle

// Animated components
const AnimatedG = Animated.createAnimatedComponent(G);

interface VesicaPiscisProps {
  size?: number;  // Width of the entire symbol (default 80px)
}

export default function VesicaPiscis({ size = 80 }: VesicaPiscisProps) {
  // Pulse animation ref
  const pulseAnim = useRef(new Animated.Value(0)).current;
  
  // Breathing pulse animation
  useEffect(() => {
    const pulse = () => {
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: PULSE_DURATION / 2,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: false,
        }),
        Animated.timing(pulseAnim, {
          toValue: 0,
          duration: PULSE_DURATION / 2,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: false,
        }),
      ]).start(() => pulse());
    };
    pulse();
  }, [pulseAnim]);
  
  // Interpolate opacity for breathing effect
  const mainOpacity = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.55, 0.65],
  });
  
  const outerOpacity = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.35, 0.45],
  });
  
  // Calculate dimensions
  // Vesica piscis: two circles where each passes through the other's center
  const circleRadius = size * 0.4;
  const circleOffset = circleRadius * 0.5;  // Distance from center to each circle center
  
  const viewBoxSize = size;
  const cx = viewBoxSize / 2;
  const cy = viewBoxSize / 2;
  
  // Outer ripple circle
  const outerRadius = size * 0.48;
  
  const isWeb = Platform.OS === 'web';
  
  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <Svg 
        width={size} 
        height={size} 
        viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
      >
        <Defs>
          {/* Inner glow gradient */}
          <RadialGradient id="innerGlow" cx="50%" cy="50%" r="50%">
            <Stop offset="0%" stopColor={GOLD} stopOpacity="0.20" />
            <Stop offset="60%" stopColor={GOLD} stopOpacity="0.08" />
            <Stop offset="100%" stopColor={GOLD} stopOpacity="0" />
          </RadialGradient>
        </Defs>
        
        {/* Inner glow - subtle 8px blur effect via gradient */}
        <Circle
          cx={cx}
          cy={cy}
          r={circleRadius * 1.2}
          fill="url(#innerGlow)"
        />
        
        {/* Outer ripple circle - more visible */}
        {isWeb ? (
          <Circle
            cx={cx}
            cy={cy}
            r={outerRadius}
            fill="none"
            stroke={GOLD}
            strokeWidth={1.5}
            strokeOpacity={0.35}
            style={{
              // @ts-ignore
              animation: `vesicaPulse ${PULSE_DURATION}ms ease-in-out infinite`,
            }}
          />
        ) : (
          <AnimatedG>
            <Circle
              cx={cx}
              cy={cy}
              r={outerRadius}
              fill="none"
              stroke={GOLD}
              strokeWidth={1.5}
              strokeOpacity={outerOpacity as any}
            />
          </AnimatedG>
        )}
        
        {/* Vesica Piscis - two overlapping circles */}
        {isWeb ? (
          <G 
            opacity={0.55}
            style={{
              // @ts-ignore
              animation: `vesicaPulse ${PULSE_DURATION}ms ease-in-out infinite`,
            }}
          >
            {/* Left circle */}
            <Circle
              cx={cx - circleOffset}
              cy={cy}
              r={circleRadius}
              fill="none"
              stroke={GOLD}
              strokeWidth={2.5}
            />
            
            {/* Right circle */}
            <Circle
              cx={cx + circleOffset}
              cy={cy}
              r={circleRadius}
              fill="none"
              stroke={GOLD}
              strokeWidth={2.5}
            />
          </G>
        ) : (
          <AnimatedG opacity={mainOpacity as any}>
            {/* Left circle */}
            <Circle
              cx={cx - circleOffset}
              cy={cy}
              r={circleRadius}
              fill="none"
              stroke={GOLD}
              strokeWidth={2.5}
            />
            
            {/* Right circle */}
            <Circle
              cx={cx + circleOffset}
              cy={cy}
              r={circleRadius}
              fill="none"
              stroke={GOLD}
              strokeWidth={2.5}
            />
          </AnimatedG>
        )}
      </Svg>
      
      {/* CSS animation for web */}
      {isWeb && (
        <style>
          {`
            @keyframes vesicaPulse {
              0%, 100% { opacity: 0.55; }
              50% { opacity: 0.65; }
            }
          `}
        </style>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
