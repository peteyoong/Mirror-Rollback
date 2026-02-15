/**
 * Build Badge Component
 * =====================
 * 
 * Displays BUILD_ID as a small watermark for deploy verification.
 * ALWAYS visible to confirm which bundle is running.
 */

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform } from 'react-native';
import { BUILD_ID, BUILD_VERSION } from '../utils/buildInfo';

// Check for debug mode
const DEBUG_MIRROR_ENV = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

const getUrlDebugParam = (): boolean => {
  if (typeof window === 'undefined') return false;
  return new URLSearchParams(window.location?.search || '').get('debug') === '1';
};

export function BuildBadge() {
  const [isDebugMode, setIsDebugMode] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    // Check debug mode on mount and URL changes
    const checkDebug = () => {
      setIsDebugMode(DEBUG_MIRROR_ENV || getUrlDebugParam());
    };
    
    checkDebug();
    
    // Listen for URL changes (web only)
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      window.addEventListener('popstate', checkDebug);
      return () => window.removeEventListener('popstate', checkDebug);
    }
  }, []);

  // ALWAYS show build badge as watermark
  return (
    <TouchableOpacity 
      style={[
        styles.badge, 
        isDebugMode ? styles.badgeDebug : styles.badgeSubtle,
      ]}
      onPress={() => setExpanded(!expanded)}
      activeOpacity={0.8}
    >
      <Text style={[styles.badgeText, !isDebugMode && styles.badgeTextSubtle]}>
        {expanded 
          ? `${BUILD_VERSION}\n${BUILD_ID}` 
          : `BUILD ${BUILD_ID}`
        }
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  badge: {
    position: 'absolute',
    bottom: 70, // Above tab bar
    right: 8,
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 3,
    zIndex: 9999,
  },
  badgeDebug: {
    backgroundColor: 'rgba(0, 255, 0, 0.95)',
  },
  badgeSubtle: {
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
  },
  badgeText: {
    fontSize: 8,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontWeight: '600',
    color: '#000',
  },
  badgeTextSubtle: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: 7,
  },
});

export default BuildBadge;
