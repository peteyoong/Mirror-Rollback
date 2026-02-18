/**
 * Staging Build Footer
 * ====================
 * 
 * Shows build info at the bottom of every screen in STAGING only.
 * Hidden in production (EXPO_PUBLIC_ENV !== 'staging').
 */

import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

// Environment variables
const APP_ENV = process.env.EXPO_PUBLIC_ENV || 'unknown';
const BUILD_VERSION = process.env.EXPO_PUBLIC_BUILD_VERSION || 'dev';
const BUILD_ID = process.env.EXPO_PUBLIC_BUILD_ID || 'unknown';

// Only show in staging
const IS_STAGING = APP_ENV === 'staging';

// Inference version - hardcoded since this is the unified version
const INFERENCE_VERSION = 'v2';

export const StagingBuildFooter: React.FC = () => {
  const insets = useSafeAreaInsets();
  
  // Only render in staging
  if (!IS_STAGING) {
    return null;
  }

  return (
    <View 
      style={[
        styles.container, 
        { paddingBottom: Math.max(insets.bottom, 4) }
      ]}
      pointerEvents="none"
    >
      <Text style={styles.text}>
        BUILD: {BUILD_VERSION} | ID: {BUILD_ID.slice(-12)} | INFERENCE: {INFERENCE_VERSION}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingVertical: 4,
    paddingHorizontal: 8,
    zIndex: 9999,
  },
  text: {
    color: '#00ff00',
    fontSize: 9,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    textAlign: 'center',
  },
});

export default StagingBuildFooter;
