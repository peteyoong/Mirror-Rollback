/**
 * WitnessEye - Visual Symbol for Project Mirror
 * 
 * Design Philosophy: "Whale eye in deep water - present, ancient, gentle. 
 * Not watching. Being with."
 * 
 * A soft, companion-like eye - feels like a presence just entered the room.
 * Organic, slightly imperfect, contemplative gaze (down and right).
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
  LinearGradient,
  Stop,
  Filter,
  FeGaussianBlur,
} from 'react-native-svg';

// Animation timing
const BLINK_INTERVAL = 5000;      // Time between blinks
const BLINK_CLOSE_MS = 300;       // Lid closes
const BLINK_OPEN_MS = 400;        // Lid opens
const MICRO_MOVEMENT_MS = 3000;   // Pupil micro-movement cycle
const RING_PULSE_MS = 8000;       // Outer rings pulse
const HOVER_TRANSITION_MS = 400;

// Colors - whale eye aesthetic
const GOLD_DARK = '#B8860B';      // Darker gold for pupil center
const GOLD_MID = '#D4AF37';       // Primary gold
const GOLD_LIGHT = '#E6C65A';     // Lighter gold for edge
const SCLERA = '#F5F5DC';         // Warm off-white
const CATCHLIGHT = '#FFFFFF';     // Pure white for reflection

// Animated components
const AnimatedG = Animated.createAnimatedComponent(G);
const AnimatedPath = Animated.createAnimatedComponent(Path);

interface WitnessEyeProps {
  size?: number;
  isHovered?: boolean;
}

export default function WitnessEye({ size = 200, isHovered = false }: WitnessEyeProps) {
  // Animation refs
  const lidAnim = useRef(new Animated.Value(0)).current;  // 0 = open, 1 = closed
  const pupilX = useRef(new Animated.Value(0)).current;
  const pupilY = useRef(new Animated.Value(0)).current;
  const ringPulse = useRef(new Animated.Value(0)).current;
  const hoverGlow = useRef(new Animated.Value(0)).current;
  
  // Blink animation - lid descends, not opacity fade
  useEffect(() => {
    const blink = () => {
      Animated.sequence([
        // Wait before blink
        Animated.delay(BLINK_INTERVAL),
        // Close lid
        Animated.timing(lidAnim, {
          toValue: 1,
          duration: BLINK_CLOSE_MS,
          easing: Easing.out(Easing.quad),
          useNativeDriver: false,
        }),
        // Open lid
        Animated.timing(lidAnim, {
          toValue: 0,
          duration: BLINK_OPEN_MS,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: false,
        }),
      ]).start(() => blink());
    };
    blink();
  }, [lidAnim]);
  
  // Micro-movement - subtle pupil shift (breathing/aliveness)
  useEffect(() => {
    const microMove = () => {
      Animated.parallel([
        Animated.sequence([
          Animated.timing(pupilX, {
            toValue: 1,
            duration: MICRO_MOVEMENT_MS,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: false,
          }),
          Animated.timing(pupilX, {
            toValue: 0,
            duration: MICRO_MOVEMENT_MS,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: false,
          }),
        ]),
        Animated.sequence([
          Animated.timing(pupilY, {
            toValue: 1,
            duration: MICRO_MOVEMENT_MS * 1.3,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: false,
          }),
          Animated.timing(pupilY, {
            toValue: 0,
            duration: MICRO_MOVEMENT_MS * 1.3,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: false,
          }),
        ]),
      ]).start(() => microMove());
    };
    microMove();
  }, [pupilX, pupilY]);
  
  // Ring pulse animation
  useEffect(() => {
    const pulse = () => {
      Animated.sequence([
        Animated.timing(ringPulse, {
          toValue: 1,
          duration: RING_PULSE_MS / 2,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: false,
        }),
        Animated.timing(ringPulse, {
          toValue: 0,
          duration: RING_PULSE_MS / 2,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: false,
        }),
      ]).start(() => pulse());
    };
    pulse();
  }, [ringPulse]);
  
  // Hover effect - glow expands
  useEffect(() => {
    Animated.timing(hoverGlow, {
      toValue: isHovered ? 1 : 0,
      duration: HOVER_TRANSITION_MS,
      easing: Easing.inOut(Easing.ease),
      useNativeDriver: false,
    }).start();
  }, [isHovered, hoverGlow]);
  
  // Calculate dimensions
  const cx = size / 2;
  const cy = size / 2;
  
  // Eye shape dimensions - almond shape
  const eyeWidth = size * 0.38;
  const eyeHeight = size * 0.16;
  
  // Gaze offset - down and to the right 20 degrees
  const gazeOffsetX = size * 0.015;
  const gazeOffsetY = size * 0.012;
  
  // Iris and pupil
  const irisRadius = size * 0.055;
  const pupilRadius = size * 0.028;
  
  // Interpolated values
  const lidClose = lidAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, eyeHeight * 0.95],
  });
  
  const pupilShiftX = pupilX.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 1.5],
  });
  
  const pupilShiftY = pupilY.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 1],
  });
  
  const ringScale = ringPulse.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 1.03],
  });
  
  const ringOpacity = ringPulse.interpolate({
    inputRange: [0, 1],
    outputRange: [0.025, 0.04],
  });
  
  const glowScale = hoverGlow.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 1.1],
  });

  // Create almond eye path (soft curves, slightly irregular)
  const createAlmondPath = (w: number, h: number, offsetY: number = 0) => {
    const x = cx;
    const y = cy + offsetY;
    // Slightly irregular curves for organic feel
    const ctrlOffset = w * 0.02; // Subtle asymmetry
    return `
      M ${x - w} ${y}
      Q ${x - w * 0.5 + ctrlOffset} ${y - h * 1.1}, ${x} ${y - h}
      Q ${x + w * 0.5 - ctrlOffset} ${y - h * 1.05}, ${x + w} ${y}
      Q ${x + w * 0.5 + ctrlOffset} ${y + h * 0.9}, ${x} ${y + h * 0.95}
      Q ${x - w * 0.5 - ctrlOffset} ${y + h * 0.85}, ${x - w} ${y}
      Z
    `;
  };
  
  // Upper eyelid path - heavier curve
  const createUpperLid = (closeAmount: number) => {
    const x = cx;
    const y = cy;
    const w = eyeWidth * 1.05;
    const h = eyeHeight;
    const lidDrop = closeAmount;
    
    return `
      M ${x - w} ${y}
      Q ${x - w * 0.5} ${y - h * 1.15 + lidDrop}, ${x} ${y - h + lidDrop}
      Q ${x + w * 0.5} ${y - h * 1.1 + lidDrop}, ${x + w} ${y}
      L ${x + w} ${y - h * 2}
      L ${x - w} ${y - h * 2}
      Z
    `;
  };
  
  // Lower eyelid path - lighter curve
  const createLowerLid = () => {
    const x = cx;
    const y = cy;
    const w = eyeWidth * 1.05;
    const h = eyeHeight;
    
    return `
      M ${x - w} ${y}
      Q ${x - w * 0.5} ${y + h * 0.85}, ${x} ${y + h * 0.9}
      Q ${x + w * 0.5} ${y + h * 0.8}, ${x + w} ${y}
      L ${x + w} ${y + h * 2}
      L ${x - w} ${y + h * 2}
      Z
    `;
  };

  const isWeb = Platform.OS === 'web';
  
  // Pupil center with gaze offset
  const pupilCx = cx + gazeOffsetX;
  const pupilCy = cy + gazeOffsetY;

  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <Animated.View 
        style={[
          styles.svgWrapper,
          { transform: [{ scale: glowScale as any }] }
        ]}
      >
        <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <Defs>
            {/* Sclera gradient - warm off-white */}
            <RadialGradient id="scleraGrad" cx="50%" cy="50%" r="60%">
              <Stop offset="0%" stopColor={SCLERA} stopOpacity="0.1" />
              <Stop offset="70%" stopColor={SCLERA} stopOpacity="0.05" />
              <Stop offset="100%" stopColor={SCLERA} stopOpacity="0" />
            </RadialGradient>
            
            {/* Iris gradient - soft gold depth */}
            <RadialGradient id="irisGrad" cx="40%" cy="40%" r="70%">
              <Stop offset="0%" stopColor={GOLD_LIGHT} stopOpacity="0.18" />
              <Stop offset="50%" stopColor={GOLD_MID} stopOpacity="0.14" />
              <Stop offset="100%" stopColor={GOLD_DARK} stopOpacity="0.1" />
            </RadialGradient>
            
            {/* Pupil gradient - darker center to lighter edge */}
            <RadialGradient id="pupilGrad" cx="35%" cy="35%" r="65%">
              <Stop offset="0%" stopColor={GOLD_DARK} stopOpacity="0.25" />
              <Stop offset="60%" stopColor={GOLD_MID} stopOpacity="0.18" />
              <Stop offset="100%" stopColor={GOLD_LIGHT} stopOpacity="0.12" />
            </RadialGradient>
            
            {/* Soft outer glow */}
            <RadialGradient id="outerGlow" cx="50%" cy="50%" r="50%">
              <Stop offset="0%" stopColor={GOLD_MID} stopOpacity="0.08" />
              <Stop offset="50%" stopColor={GOLD_MID} stopOpacity="0.04" />
              <Stop offset="100%" stopColor={GOLD_MID} stopOpacity="0" />
            </RadialGradient>
            
            {/* Vignette shadow */}
            <RadialGradient id="vignette" cx="50%" cy="50%" r="50%">
              <Stop offset="0%" stopColor="#000" stopOpacity="0" />
              <Stop offset="60%" stopColor="#000" stopOpacity="0" />
              <Stop offset="85%" stopColor="#000" stopOpacity="0.15" />
              <Stop offset="100%" stopColor="#000" stopOpacity="0.35" />
            </RadialGradient>
            
            {/* Eye socket shadow */}
            <RadialGradient id="socketShadow" cx="50%" cy="45%" r="60%">
              <Stop offset="0%" stopColor="#000" stopOpacity="0" />
              <Stop offset="70%" stopColor="#000" stopOpacity="0.02" />
              <Stop offset="100%" stopColor="#000" stopOpacity="0.06" />
            </RadialGradient>
          </Defs>
          
          {/* Outer vignette - grounds the eye */}
          <Circle
            cx={cx}
            cy={cy}
            r={size * 0.48}
            fill="url(#vignette)"
          />
          
          {/* Outer attention rings - ripples */}
          {isWeb ? (
            <G opacity={0.03} style={{ 
              // @ts-ignore
              transformOrigin: `${cx}px ${cy}px`,
              animation: `ringPulse ${RING_PULSE_MS}ms ease-in-out infinite`,
            }}>
              <Circle cx={cx} cy={cy} r={size * 0.42} fill="none" stroke={GOLD_MID} strokeWidth={0.5} />
              <Circle cx={cx} cy={cy} r={size * 0.38} fill="none" stroke={GOLD_MID} strokeWidth={0.5} />
              <Circle cx={cx} cy={cy} r={size * 0.34} fill="none" stroke={GOLD_MID} strokeWidth={0.5} />
            </G>
          ) : (
            <AnimatedG 
              opacity={ringOpacity as any}
              style={{ transform: [{ scale: ringScale as any }] }}
            >
              <Circle cx={cx} cy={cy} r={size * 0.42} fill="none" stroke={GOLD_MID} strokeWidth={0.5} />
              <Circle cx={cx} cy={cy} r={size * 0.38} fill="none" stroke={GOLD_MID} strokeWidth={0.5} />
              <Circle cx={cx} cy={cy} r={size * 0.34} fill="none" stroke={GOLD_MID} strokeWidth={0.5} />
            </AnimatedG>
          )}
          
          {/* Soft diffuse outer glow */}
          <Ellipse
            cx={cx}
            cy={cy}
            rx={eyeWidth * 1.8}
            ry={eyeHeight * 3}
            fill="url(#outerGlow)"
            opacity={0.5}
          />
          
          {/* Eye socket shadow */}
          <Ellipse
            cx={cx}
            cy={cy}
            rx={eyeWidth * 1.3}
            ry={eyeHeight * 1.8}
            fill="url(#socketShadow)"
          />
          
          {/* Sclera - very faint warm off-white */}
          <Path
            d={createAlmondPath(eyeWidth, eyeHeight)}
            fill="url(#scleraGrad)"
            opacity={0.8}
          />
          
          {/* Iris */}
          {isWeb ? (
            <G style={{
              // @ts-ignore
              transformOrigin: `${pupilCx}px ${pupilCy}px`,
              animation: `microMove ${MICRO_MOVEMENT_MS * 2}ms ease-in-out infinite`,
            }}>
              <Circle
                cx={pupilCx}
                cy={pupilCy}
                r={irisRadius}
                fill="url(#irisGrad)"
              />
              {/* Iris ring */}
              <Circle
                cx={pupilCx}
                cy={pupilCy}
                r={irisRadius}
                fill="none"
                stroke={GOLD_MID}
                strokeWidth={0.5}
                strokeOpacity={0.08}
              />
            </G>
          ) : (
            <AnimatedG style={{
              transform: [
                { translateX: pupilShiftX as any },
                { translateY: pupilShiftY as any },
              ],
            }}>
              <Circle
                cx={pupilCx}
                cy={pupilCy}
                r={irisRadius}
                fill="url(#irisGrad)"
              />
              <Circle
                cx={pupilCx}
                cy={pupilCy}
                r={irisRadius}
                fill="none"
                stroke={GOLD_MID}
                strokeWidth={0.5}
                strokeOpacity={0.08}
              />
            </AnimatedG>
          )}
          
          {/* Pupil - gradient from dark center to lighter edge */}
          {isWeb ? (
            <G style={{
              // @ts-ignore
              transformOrigin: `${pupilCx}px ${pupilCy}px`,
              animation: `microMove ${MICRO_MOVEMENT_MS * 2}ms ease-in-out infinite`,
            }}>
              <Circle
                cx={pupilCx}
                cy={pupilCy}
                r={pupilRadius}
                fill="url(#pupilGrad)"
              />
            </G>
          ) : (
            <AnimatedG style={{
              transform: [
                { translateX: pupilShiftX as any },
                { translateY: pupilShiftY as any },
              ],
            }}>
              <Circle
                cx={pupilCx}
                cy={pupilCy}
                r={pupilRadius}
                fill="url(#pupilGrad)"
              />
            </AnimatedG>
          )}
          
          {/* Catchlight - tiny white dot for life/wetness */}
          <Circle
            cx={pupilCx - irisRadius * 0.35}
            cy={pupilCy - irisRadius * 0.35}
            r={size * 0.008}
            fill={CATCHLIGHT}
            opacity={0.25}
          />
          {/* Secondary smaller catchlight */}
          <Circle
            cx={pupilCx + irisRadius * 0.2}
            cy={pupilCy - irisRadius * 0.25}
            r={size * 0.004}
            fill={CATCHLIGHT}
            opacity={0.15}
          />
          
          {/* Upper eyelid - heavier curve, animates down on blink */}
          {isWeb ? (
            <Path
              d={createUpperLid(0)}
              fill="#111214"
              style={{
                // @ts-ignore
                transformOrigin: `${cx}px ${cy - eyeHeight}px`,
                animation: `blink ${BLINK_INTERVAL + BLINK_CLOSE_MS + BLINK_OPEN_MS}ms ease-in-out infinite`,
              }}
            />
          ) : (
            <AnimatedPath
              d={lidAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [createUpperLid(0), createUpperLid(eyeHeight * 0.95)],
              }) as any}
              fill="#111214"
            />
          )}
          
          {/* Lower eyelid - lighter curve, static */}
          <Path
            d={createLowerLid()}
            fill="#111214"
          />
          
          {/* Soft eyelid edge shadows */}
          <Path
            d={`
              M ${cx - eyeWidth * 1.05} ${cy}
              Q ${cx - eyeWidth * 0.5} ${cy - eyeHeight * 0.9}, ${cx} ${cy - eyeHeight * 0.85}
              Q ${cx + eyeWidth * 0.5} ${cy - eyeHeight * 0.9}, ${cx + eyeWidth * 1.05} ${cy}
            `}
            fill="none"
            stroke={GOLD_MID}
            strokeWidth={0.8}
            strokeOpacity={0.06}
          />
          <Path
            d={`
              M ${cx - eyeWidth * 1.05} ${cy}
              Q ${cx - eyeWidth * 0.5} ${cy + eyeHeight * 0.75}, ${cx} ${cy + eyeHeight * 0.8}
              Q ${cx + eyeWidth * 0.5} ${cy + eyeHeight * 0.7}, ${cx + eyeWidth * 1.05} ${cy}
            `}
            fill="none"
            stroke={GOLD_MID}
            strokeWidth={0.5}
            strokeOpacity={0.04}
          />
        </Svg>
      </Animated.View>
      
      {/* CSS keyframes for web */}
      {isWeb && (
        <style>
          {`
            @keyframes blink {
              0%, 88% { transform: translateY(0); }
              92% { transform: translateY(${eyeHeight * 0.8}px); }
              96% { transform: translateY(0); }
              100% { transform: translateY(0); }
            }
            @keyframes microMove {
              0%, 100% { transform: translate(0, 0); }
              25% { transform: translate(1.5px, 0.5px); }
              50% { transform: translate(0.5px, 1px); }
              75% { transform: translate(-0.5px, 0.5px); }
            }
            @keyframes ringPulse {
              0%, 100% { opacity: 0.025; transform: scale(1); }
              50% { opacity: 0.04; transform: scale(1.03); }
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
  svgWrapper: {
    width: '100%',
    height: '100%',
  },
});
