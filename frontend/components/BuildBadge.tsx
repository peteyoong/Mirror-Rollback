/**
 * Build Badge Component
 * =====================
 * 
 * Displays BUILD_ID in a small corner badge for deploy verification.
 * Shows only when:
 * - URL has ?debug=1, OR
 * - EXPO_PUBLIC_DEBUG_MIRROR=true
 * 
 * This allows instant verification of which bundle is running.
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
  const [showDebug, setShowDebug] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    // Check debug mode on mount and URL changes
    const checkDebug = () => {
      setShowDebug(DEBUG_MIRROR_ENV || getUrlDebugParam());
    };
    
    checkDebug();
    
    // Listen for URL changes (web only)
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      window.addEventListener('popstate', checkDebug);
      return () => window.removeEventListener('popstate', checkDebug);
    }
  }, []);

  if (!showDebug) return null;

  return (
    <TouchableOpacity 
      style={styles.badge}
      onPress={() => setExpanded(!expanded)}
      activeOpacity={0.8}
      pointerEvents="auto"
    >
      <Text style={styles.badgeText}>
        {expanded ? `${BUILD_VERSION}\n${BUILD_ID}` : `🔧 ${BUILD_VERSION.slice(0, 12)}`}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  badge: {
    position: 'absolute',
    bottom: 70, // Above tab bar
    right: 8,
    backgroundColor: 'rgba(0, 255, 0, 0.9)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    zIndex: 9999,
  },
  badgeText: {
    fontSize: 10,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: '#000',
    fontWeight: 'bold',
  },
});

export default BuildBadge;
