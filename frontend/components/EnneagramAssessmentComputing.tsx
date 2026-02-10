/**
 * EnneagramAssessmentComputing
 * ============================
 * Interstitial screen shown while computing results.
 * Creates a reflective pause before showing results.
 */

import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Animated, Easing } from 'react-native';
import { Colors } from '../constants/colors';

interface Props {
  onComplete: () => void;
  minDuration?: number; // Minimum time to show (ms)
}

const LOADING_MESSAGES = [
  'Looking for the strongest recurring pattern…',
  'Noticing what shows up most consistently…',
  'Bringing the signals together…',
];

export const EnneagramAssessmentComputing: React.FC<Props> = ({
  onComplete,
  minDuration = 2000,
}) => {
  const [messageIndex, setMessageIndex] = useState(0);
  const fadeAnim = React.useRef(new Animated.Value(0)).current;
  const dotAnim = React.useRef(new Animated.Value(0)).current;

  // Fade in animation
  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 400,
      useNativeDriver: true,
    }).start();
  }, []);

  // Dot animation loop
  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(dotAnim, {
          toValue: 1,
          duration: 600,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(dotAnim, {
          toValue: 0,
          duration: 600,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );
    animation.start();
    return () => animation.stop();
  }, []);

  // Cycle through messages
  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  // Timer to call onComplete after minimum duration
  useEffect(() => {
    const timer = setTimeout(() => {
      onComplete();
    }, minDuration);
    return () => clearTimeout(timer);
  }, [minDuration, onComplete]);

  const dot1Opacity = dotAnim.interpolate({
    inputRange: [0, 0.33, 0.66, 1],
    outputRange: [0.3, 1, 0.3, 0.3],
  });
  const dot2Opacity = dotAnim.interpolate({
    inputRange: [0, 0.33, 0.66, 1],
    outputRange: [0.3, 0.3, 1, 0.3],
  });
  const dot3Opacity = dotAnim.interpolate({
    inputRange: [0, 0.33, 0.66, 1],
    outputRange: [0.3, 0.3, 0.3, 1],
  });

  return (
    <Animated.View style={[styles.container, { opacity: fadeAnim }]}>
      {/* Animated Dots */}
      <View style={styles.dotsContainer}>
        <Animated.View style={[styles.dot, { opacity: dot1Opacity }]} />
        <Animated.View style={[styles.dot, { opacity: dot2Opacity }]} />
        <Animated.View style={[styles.dot, { opacity: dot3Opacity }]} />
      </View>

      {/* Loading Message */}
      <Text style={styles.message}>{LOADING_MESSAGES[messageIndex]}</Text>

      {/* Subtext */}
      <Text style={styles.subtext}>
        This takes just a moment
      </Text>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  dotsContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 32,
  },
  dot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: Colors.accent,
  },
  message: {
    fontSize: 18,
    fontWeight: '500',
    color: Colors.text,
    textAlign: 'center',
    marginBottom: 12,
    minHeight: 50,
  },
  subtext: {
    fontSize: 14,
    color: Colors.textTertiary,
    textAlign: 'center',
  },
});

export default EnneagramAssessmentComputing;
