/**
 * WitnessEye - Visual Symbol for Project Mirror
 * 
 * A soft, companion-like eye within vesica piscis geometry.
 * Represents gentle witnessing presence - "I'm here with you"
 * 
 * Design Philosophy:
 * - Defocused, not piercing or all-knowing
 * - Gold accent matching brand colors
 * - Breath-rhythm animations (slow blink, gentle pulse)
 */

import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Easing, Platform } from 'react-native';
import Svg, { 
  Defs, 
  Circle, 
  Ellipse, 
  Path, 
  G, 
  RadialGradient, 
  Stop,
  ClipPath,
  Mask,
} from 'react-native-svg';

// Animation constants - breath rhythm
const BLINK_DURATION = 4500;    // 4.5 second cycle
const PULSE_DURATION = 7000;    // 7 second cycle for vesica piscis
const BLINK_CLOSE_DURATION = 300; // Quick close

// Gold color matching #D4AF37 at various opacities
const GOLD_PRIMARY = '#D4AF37';
const GOLD_OPACITY_15 = 'rgba(212, 175, 55, 0.15)';
const GOLD_OPACITY_20 = 'rgba(212, 175, 55, 0.20)';
const GOLD_OPACITY_25 = 'rgba(212, 175, 55, 0.25)';
const GOLD_OPACITY_08 = 'rgba(212, 175, 55, 0.08)';
const GOLD_OPACITY_12 = 'rgba(212, 175, 55, 0.12)';

// Animated SVG components
const AnimatedG = Animated.createAnimatedComponent(G);
const AnimatedEllipse = Animated.createAnimatedComponent(Ellipse);
const AnimatedCircle = Animated.createAnimatedComponent(Circle);

interface WitnessEyeProps {
  size?: number;
  isHovered?: boolean;  // For hover effect on New User button
}

export default function WitnessEye({ size = 280, isHovered = false }: WitnessEyeProps) {
  // Animation values
  const blinkAnim = useRef(new Animated.Value(1)).current;
  const pulseAnim = useRef(new Animated.Value(0)).current;
  const hoverAnim = useRef(new Animated.Value(0)).current;
  
  // Blink animation - breath rhythm
  useEffect(() => {
    const runBlinkCycle = () => {
      Animated.sequence([
        // Eye open (hold)
        Animated.delay(BLINK_DURATION - BLINK_CLOSE_DURATION * 2),
        // Close eyelid
        Animated.timing(blinkAnim, {
          toValue: 0.1,
          duration: BLINK_CLOSE_DURATION,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        // Open eyelid
        Animated.timing(blinkAnim, {
          toValue: 1,
          duration: BLINK_CLOSE_DURATION,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ]).start(() => runBlinkCycle());
    };
    
    runBlinkCycle();
  }, [blinkAnim]);
  
  // Pulse animation for vesica piscis intersection
  useEffect(() => {
    const runPulseCycle = () => {
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: PULSE_DURATION / 2,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 0,
          duration: PULSE_DURATION / 2,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ]).start(() => runPulseCycle());
    };
    
    runPulseCycle();
  }, [pulseAnim]);
  
  // Hover animation
  useEffect(() => {
    Animated.timing(hoverAnim, {
      toValue: isHovered ? 1 : 0,
      duration: 400,
      easing: Easing.inOut(Easing.ease),
      useNativeDriver: true,
    }).start();
  }, [isHovered, hoverAnim]);
  
  // Calculate eye scale from blink
  const eyeScaleY = blinkAnim.interpolate({
    inputRange: [0.1, 1],
    outputRange: [0.1, 1],
  });
  
  // Pulse opacity
  const pulseOpacity = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.08, 0.18],
  });
  
  // Hover opacity boost
  const hoverOpacity = hoverAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 1.3],
  });
  
  const viewBox = `0 0 ${size} ${size}`;
  const center = size / 2;
  const circleRadius = size * 0.35;
  const circleOffset = size * 0.18; // How far circles are from center
  
  // Eye dimensions
  const eyeWidth = size * 0.22;
  const eyeHeight = size * 0.10;
  const irisRadius = size * 0.045;
  const pupilRadius = size * 0.022;
  
  // For web platform, we need to handle animations differently
  const isWeb = Platform.OS === 'web';
  
  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <Animated.View style={[styles.svgWrapper, { opacity: hoverOpacity }]}>
        <Svg
          width={size}
          height={size}
          viewBox={viewBox}
          style={styles.svg}
        >
          <Defs>
            {/* Radial gradient for center glow */}
            <RadialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
              <Stop offset="0%" stopColor={GOLD_PRIMARY} stopOpacity="0.15" />
              <Stop offset="50%" stopColor={GOLD_PRIMARY} stopOpacity="0.08" />
              <Stop offset="100%" stopColor={GOLD_PRIMARY} stopOpacity="0" />
            </RadialGradient>
            
            {/* Gradient for eye depth */}
            <RadialGradient id="eyeGlow" cx="50%" cy="50%" r="50%">
              <Stop offset="0%" stopColor={GOLD_PRIMARY} stopOpacity="0.25" />
              <Stop offset="70%" stopColor={GOLD_PRIMARY} stopOpacity="0.12" />
              <Stop offset="100%" stopColor={GOLD_PRIMARY} stopOpacity="0.05" />
            </RadialGradient>
            
            {/* Iris gradient */}
            <RadialGradient id="irisGradient" cx="40%" cy="40%" r="60%">
              <Stop offset="0%" stopColor={GOLD_PRIMARY} stopOpacity="0.35" />
              <Stop offset="100%" stopColor={GOLD_PRIMARY} stopOpacity="0.18" />
            </RadialGradient>
            
            {/* Vignette gradient */}
            <RadialGradient id="vignette" cx="50%" cy="50%" r="50%">
              <Stop offset="0%" stopColor="#000" stopOpacity="0" />
              <Stop offset="70%" stopColor="#000" stopOpacity="0" />
              <Stop offset="100%" stopColor="#000" stopOpacity="0.4" />
            </RadialGradient>
          </Defs>
          
          {/* Vignette overlay */}
          <Circle
            cx={center}
            cy={center}
            r={size * 0.48}
            fill="url(#vignette)"
          />
          
          {/* Vesica Piscis - Two overlapping circles */}
          <G opacity={0.15}>
            {/* Left circle */}
            <Circle
              cx={center - circleOffset}
              cy={center}
              r={circleRadius}
              fill="none"
              stroke={GOLD_PRIMARY}
              strokeWidth={1}
            />
            
            {/* Right circle */}
            <Circle
              cx={center + circleOffset}
              cy={center}
              r={circleRadius}
              fill="none"
              stroke={GOLD_PRIMARY}
              strokeWidth={1}
            />
          </G>
          
          {/* Center intersection glow - pulsing */}
          {isWeb ? (
            <Ellipse
              cx={center}
              cy={center}
              rx={size * 0.12}
              ry={size * 0.22}
              fill="url(#centerGlow)"
              opacity={0.12}
              style={{
                // @ts-ignore - web-specific animation
                animation: `pulse ${PULSE_DURATION}ms ease-in-out infinite`,
              }}
            />
          ) : (
            <AnimatedEllipse
              cx={center}
              cy={center}
              rx={size * 0.12}
              ry={size * 0.22}
              fill="url(#centerGlow)"
              opacity={pulseOpacity as any}
            />
          )}
          
          {/* The Eye */}
          <G>
            {/* Eye socket glow */}
            <Ellipse
              cx={center}
              cy={center}
              rx={eyeWidth * 1.2}
              ry={eyeHeight * 1.5}
              fill="url(#eyeGlow)"
              opacity={0.3}
            />
            
            {/* Eye shape - soft almond */}
            {isWeb ? (
              <G
                style={{
                  // @ts-ignore - web-specific animation
                  transformOrigin: `${center}px ${center}px`,
                  animation: `blink ${BLINK_DURATION}ms ease-in-out infinite`,
                }}
              >
                <Ellipse
                  cx={center}
                  cy={center}
                  rx={eyeWidth}
                  ry={eyeHeight}
                  fill={GOLD_OPACITY_08}
                  stroke={GOLD_PRIMARY}
                  strokeWidth={1}
                  strokeOpacity={0.2}
                />
                
                {/* Iris */}
                <Circle
                  cx={center}
                  cy={center}
                  r={irisRadius}
                  fill="url(#irisGradient)"
                  stroke={GOLD_PRIMARY}
                  strokeWidth={0.5}
                  strokeOpacity={0.3}
                />
                
                {/* Pupil - soft, not harsh */}
                <Circle
                  cx={center}
                  cy={center}
                  r={pupilRadius}
                  fill={GOLD_OPACITY_25}
                />
                
                {/* Subtle light reflection */}
                <Circle
                  cx={center - irisRadius * 0.3}
                  cy={center - irisRadius * 0.3}
                  r={pupilRadius * 0.4}
                  fill={GOLD_PRIMARY}
                  opacity={0.15}
                />
              </G>
            ) : (
              <AnimatedG
                style={{
                  transform: [{ scaleY: eyeScaleY as any }],
                }}
              >
                <Ellipse
                  cx={center}
                  cy={center}
                  rx={eyeWidth}
                  ry={eyeHeight}
                  fill={GOLD_OPACITY_08}
                  stroke={GOLD_PRIMARY}
                  strokeWidth={1}
                  strokeOpacity={0.2}
                />
                
                {/* Iris */}
                <Circle
                  cx={center}
                  cy={center}
                  r={irisRadius}
                  fill="url(#irisGradient)"
                  stroke={GOLD_PRIMARY}
                  strokeWidth={0.5}
                  strokeOpacity={0.3}
                />
                
                {/* Pupil */}
                <Circle
                  cx={center}
                  cy={center}
                  r={pupilRadius}
                  fill={GOLD_OPACITY_25}
                />
                
                {/* Light reflection */}
                <Circle
                  cx={center - irisRadius * 0.3}
                  cy={center - irisRadius * 0.3}
                  r={pupilRadius * 0.4}
                  fill={GOLD_PRIMARY}
                  opacity={0.15}
                />
              </AnimatedG>
            )}
          </G>
          
          {/* Subtle inner vesica piscis lines for depth */}
          <G opacity={0.08}>
            {/* Inner left arc */}
            <Path
              d={`M ${center} ${center - circleRadius * 0.8}
                  A ${circleRadius * 0.6} ${circleRadius * 0.6} 0 0 1 ${center} ${center + circleRadius * 0.8}`}
              fill="none"
              stroke={GOLD_PRIMARY}
              strokeWidth={0.5}
            />
            {/* Inner right arc */}
            <Path
              d={`M ${center} ${center - circleRadius * 0.8}
                  A ${circleRadius * 0.6} ${circleRadius * 0.6} 0 0 0 ${center} ${center + circleRadius * 0.8}`}
              fill="none"
              stroke={GOLD_PRIMARY}
              strokeWidth={0.5}
            />
          </G>
        </Svg>
      </Animated.View>
      
      {/* CSS animations for web */}
      {isWeb && (
        <style>
          {`
            @keyframes blink {
              0%, 92% { transform: scaleY(1); }
              95% { transform: scaleY(0.1); }
              98% { transform: scaleY(1); }
              100% { transform: scaleY(1); }
            }
            @keyframes pulse {
              0%, 100% { opacity: 0.08; }
              50% { opacity: 0.18; }
            }
          `}
        </style>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: -1,
  },
  svgWrapper: {
    width: '100%',
    height: '100%',
  },
  svg: {
    // Ensure SVG renders properly
  },
});
