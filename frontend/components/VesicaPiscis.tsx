/**
 * VesicaPiscis - Sacred Geometry Symbol for Project Mirror
 * 
 * Trinity of overlapping circles - ancient alchemical symbol.
 * Asymmetric, organic, hand-drawn feel. Discovered in an old manuscript.
 * 
 * Design Philosophy:
 * - Three circles (not two) - breaks luxury logo association
 * - Vertical orientation (3:4 ratio) - lens/mirror shape
 * - Asymmetry - human, not corporate
 * - Center "noticing space" emphasized with glow
 */

import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Easing, Platform } from 'react-native';
import Svg, { 
  Circle, 
  G, 
  Defs, 
  RadialGradient, 
  Stop,
  Path,
} from 'react-native-svg';

// Bright gold color
const GOLD = '#F0D878';
const GOLD_GLOW = '#F0D878';

// Animation timing
const BREATH_DURATION = 12000;  // 12s breathing cycle
const GLOW_DURATION = 8000;     // 8s glow pulse

// Animated components
const AnimatedG = Animated.createAnimatedComponent(G);

interface VesicaPiscisProps {
  size?: number;  // Base width (height will be 1.33x for 3:4 ratio)
}

export default function VesicaPiscis({ size = 80 }: VesicaPiscisProps) {
  // Animation refs
  const breathAnim = useRef(new Animated.Value(0)).current;
  const glowAnim = useRef(new Animated.Value(0)).current;
  
  // Breathing animation - scale 100% → 102% → 100%
  useEffect(() => {
    const breathe = () => {
      Animated.sequence([
        Animated.timing(breathAnim, {
          toValue: 1,
          duration: BREATH_DURATION / 2,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: false,
        }),
        Animated.timing(breathAnim, {
          toValue: 0,
          duration: BREATH_DURATION / 2,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: false,
        }),
      ]).start(() => breathe());
    };
    breathe();
  }, [breathAnim]);
  
  // Center glow pulse - 20% → 30% → 20%
  useEffect(() => {
    const pulse = () => {
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 1,
          duration: GLOW_DURATION / 2,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: false,
        }),
        Animated.timing(glowAnim, {
          toValue: 0,
          duration: GLOW_DURATION / 2,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: false,
        }),
      ]).start(() => pulse());
    };
    pulse();
  }, [glowAnim]);
  
  // Interpolations
  const breathScale = breathAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 1.02],
  });
  
  const glowOpacity = glowAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.20, 0.30],
  });
  
  // Dimensions - 3:4 ratio (taller than wide)
  const width = size;
  const height = size * 1.33;
  
  const cx = width / 2;
  const cy = height / 2;
  
  // Circle sizes with asymmetry
  // Left circle 10% larger than right
  const baseRadius = size * 0.28;
  const leftRadius = baseRadius * 1.10;   // 10% larger
  const rightRadius = baseRadius;
  const topRadius = baseRadius * 1.05;    // Top circle slightly larger
  
  // Circle positions - asymmetric layout
  // Top intersection 15% higher creates vertical emphasis
  const circleSpread = size * 0.22;
  const verticalOffset = size * 0.08;     // Move center down slightly
  
  // Left circle - slightly outward and down
  const leftCx = cx - circleSpread * 0.9;
  const leftCy = cy + verticalOffset * 0.5;
  
  // Right circle - slightly inward and down
  const rightCx = cx + circleSpread * 1.0;
  const rightCy = cy + verticalOffset * 0.7;
  
  // Top circle - behind and above, larger
  const topCx = cx + circleSpread * 0.05;  // Slight offset for organic feel
  const topCy = cy - circleSpread * 0.85;
  
  // Center of triple intersection (the "noticing space")
  const noticeCx = cx - 2;  // Slight offset for imperfection
  const noticeCy = cy - 5;
  
  // Outer field circle
  const outerRadius = size * 0.52;
  
  const isWeb = Platform.OS === 'web';
  
  // Create slightly irregular circle paths for hand-drawn feel
  const createOrganicCircle = (
    centerX: number, 
    centerY: number, 
    radius: number, 
    variation: number = 0.02
  ): string => {
    // Create path with subtle variations
    const points = 36;
    const pathParts: string[] = [];
    
    for (let i = 0; i <= points; i++) {
      const angle = (i / points) * Math.PI * 2;
      // Add slight random-like variation (deterministic based on angle)
      const wobble = 1 + Math.sin(angle * 3) * variation + Math.cos(angle * 5) * variation * 0.5;
      const r = radius * wobble;
      const x = centerX + Math.cos(angle) * r;
      const y = centerY + Math.sin(angle) * r;
      
      if (i === 0) {
        pathParts.push(`M ${x.toFixed(2)} ${y.toFixed(2)}`);
      } else {
        pathParts.push(`L ${x.toFixed(2)} ${y.toFixed(2)}`);
      }
    }
    pathParts.push('Z');
    return pathParts.join(' ');
  };

  return (
    <View style={[
      styles.container, 
      { 
        width, 
        height,
        transform: [{ rotate: '5deg' }]  // Slight tilt for dynamism
      }
    ]}>
      {isWeb ? (
        <Svg 
          width={width} 
          height={height} 
          viewBox={`0 0 ${width} ${height}`}
          style={{
            // @ts-ignore
            animation: `breathe ${BREATH_DURATION}ms ease-in-out infinite`,
          }}
        >
          <Defs>
            {/* Center noticing space glow */}
            <RadialGradient id="noticeGlow" cx="50%" cy="45%" r="50%">
              <Stop offset="0%" stopColor={GOLD_GLOW} stopOpacity="0.35" />
              <Stop offset="50%" stopColor={GOLD_GLOW} stopOpacity="0.15" />
              <Stop offset="100%" stopColor={GOLD_GLOW} stopOpacity="0" />
            </RadialGradient>
            
            {/* Subtle texture gradient */}
            <RadialGradient id="lineGrad" cx="50%" cy="50%" r="50%">
              <Stop offset="0%" stopColor={GOLD} stopOpacity="0.65" />
              <Stop offset="100%" stopColor={GOLD} stopOpacity="0.55" />
            </RadialGradient>
          </Defs>
          
          {/* Outer field circle - suggests expansion */}
          <Circle
            cx={cx}
            cy={cy}
            r={outerRadius}
            fill="none"
            stroke={GOLD}
            strokeWidth={1}
            strokeOpacity={0.15}
            strokeDasharray="2,4"  // Dashed for ethereal feel
          />
          
          {/* Center noticing space glow */}
          <Circle
            cx={noticeCx}
            cy={noticeCy}
            r={baseRadius * 0.7}
            fill="url(#noticeGlow)"
            style={{
              // @ts-ignore
              animation: `glowPulse ${GLOW_DURATION}ms ease-in-out infinite`,
            }}
          />
          
          {/* Trinity of circles - main structure */}
          <G opacity={0.60}>
            {/* Top circle - behind, larger */}
            <Path
              d={createOrganicCircle(topCx, topCy, topRadius, 0.015)}
              fill="none"
              stroke={GOLD}
              strokeWidth={2.5}
            />
            
            {/* Left circle - 10% larger */}
            <Path
              d={createOrganicCircle(leftCx, leftCy, leftRadius, 0.02)}
              fill="none"
              stroke={GOLD}
              strokeWidth={2.8}
            />
            
            {/* Right circle */}
            <Path
              d={createOrganicCircle(rightCx, rightCy, rightRadius, 0.018)}
              fill="none"
              stroke={GOLD}
              strokeWidth={2.5}
            />
          </G>
          
          {/* Intersection emphasis - thicker lines where circles meet */}
          <G opacity={0.45}>
            {/* Top-left intersection */}
            <Circle
              cx={(topCx + leftCx) / 2}
              cy={(topCy + leftCy) / 2}
              r={4}
              fill={GOLD}
              fillOpacity={0.3}
            />
            {/* Top-right intersection */}
            <Circle
              cx={(topCx + rightCx) / 2}
              cy={(topCy + rightCy) / 2}
              r={3.5}
              fill={GOLD}
              fillOpacity={0.25}
            />
            {/* Bottom intersection */}
            <Circle
              cx={(leftCx + rightCx) / 2}
              cy={(leftCy + rightCy) / 2}
              r={3}
              fill={GOLD}
              fillOpacity={0.2}
            />
          </G>
        </Svg>
      ) : (
        <Animated.View style={{ transform: [{ scale: breathScale as any }] }}>
          <Svg 
            width={width} 
            height={height} 
            viewBox={`0 0 ${width} ${height}`}
          >
            <Defs>
              <RadialGradient id="noticeGlow" cx="50%" cy="45%" r="50%">
                <Stop offset="0%" stopColor={GOLD_GLOW} stopOpacity="0.35" />
                <Stop offset="50%" stopColor={GOLD_GLOW} stopOpacity="0.15" />
                <Stop offset="100%" stopColor={GOLD_GLOW} stopOpacity="0" />
              </RadialGradient>
            </Defs>
            
            {/* Outer field circle */}
            <Circle
              cx={cx}
              cy={cy}
              r={outerRadius}
              fill="none"
              stroke={GOLD}
              strokeWidth={1}
              strokeOpacity={0.15}
              strokeDasharray="2,4"
            />
            
            {/* Center glow */}
            <AnimatedG opacity={glowOpacity as any}>
              <Circle
                cx={noticeCx}
                cy={noticeCy}
                r={baseRadius * 0.7}
                fill="url(#noticeGlow)"
              />
            </AnimatedG>
            
            {/* Trinity of circles */}
            <G opacity={0.60}>
              <Path
                d={createOrganicCircle(topCx, topCy, topRadius, 0.015)}
                fill="none"
                stroke={GOLD}
                strokeWidth={2.5}
              />
              <Path
                d={createOrganicCircle(leftCx, leftCy, leftRadius, 0.02)}
                fill="none"
                stroke={GOLD}
                strokeWidth={2.8}
              />
              <Path
                d={createOrganicCircle(rightCx, rightCy, rightRadius, 0.018)}
                fill="none"
                stroke={GOLD}
                strokeWidth={2.5}
              />
            </G>
            
            {/* Intersection emphasis */}
            <G opacity={0.45}>
              <Circle
                cx={(topCx + leftCx) / 2}
                cy={(topCy + leftCy) / 2}
                r={4}
                fill={GOLD}
                fillOpacity={0.3}
              />
              <Circle
                cx={(topCx + rightCx) / 2}
                cy={(topCy + rightCy) / 2}
                r={3.5}
                fill={GOLD}
                fillOpacity={0.25}
              />
              <Circle
                cx={(leftCx + rightCx) / 2}
                cy={(leftCy + rightCy) / 2}
                r={3}
                fill={GOLD}
                fillOpacity={0.2}
              />
            </G>
          </Svg>
        </Animated.View>
      )}
      
      {/* CSS animations for web */}
      {isWeb && (
        <style>
          {`
            @keyframes breathe {
              0%, 100% { transform: scale(1); }
              50% { transform: scale(1.02); }
            }
            @keyframes glowPulse {
              0%, 100% { opacity: 0.20; }
              50% { opacity: 0.30; }
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
