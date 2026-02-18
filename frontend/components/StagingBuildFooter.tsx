/**
 * Staging Build Footer
 * ====================
 * 
 * Shows build info at the bottom of every screen in STAGING only.
 * HIDDEN by default - only visible when:
 *   1. URL contains ?debug=1
 *   OR
 *   2. EXPO_PUBLIC_DEBUG_MIRROR=true
 * 
 * Normal users never see this footer.
 */

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

// Environment variables
const APP_ENV = process.env.EXPO_PUBLIC_ENV || 'unknown';
const BUILD_VERSION = process.env.EXPO_PUBLIC_BUILD_VERSION || 'dev';
const BUILD_ID = process.env.EXPO_PUBLIC_BUILD_ID || 'unknown';
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'not-set';
const DEBUG_MIRROR = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

// Only show in staging
const IS_STAGING = APP_ENV === 'staging';

// Inference version - hardcoded since this is the unified version
const INFERENCE_VERSION = 'v2';

export const StagingBuildFooter: React.FC = () => {
  const insets = useSafeAreaInsets();
  const [showFooter, setShowFooter] = useState(false);
  
  // Check URL param on mount (client-side only)
  useEffect(() => {
    // Must be staging environment
    if (!IS_STAGING) {
      setShowFooter(false);
      return;
    }
    
    // Check if DEBUG_MIRROR env is true
    if (DEBUG_MIRROR) {
      setShowFooter(true);
      return;
    }
    
    // Check URL param (web only)
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      try {
        const urlParams = new URLSearchParams(window.location?.search || '');
        if (urlParams.get('debug') === '1') {
          setShowFooter(true);
          return;
        }
      } catch {
        // Ignore errors
      }
    }
    
    // Default: hidden
    setShowFooter(false);
  }, []);
  
  // Don't render if not showing - no layout shift
  if (!showFooter) {
    return null;
  }

  // Extract just the hostname from API_BASE_URL for brevity
  let apiHost = API_BASE_URL;
  try {
    const url = new URL(API_BASE_URL);
    apiHost = url.hostname;
  } catch {
    // Keep full value if not a valid URL
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
        BUILD: {BUILD_VERSION} | ID: {BUILD_ID.slice(-12)} | INF: {INFERENCE_VERSION}
      </Text>
      <Text style={styles.textSmall}>
        API: {apiHost}
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
  textSmall: {
    color: '#00ff00',
    fontSize: 8,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    textAlign: 'center',
    opacity: 0.8,
  },
});

export default StagingBuildFooter;
