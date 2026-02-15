/**
 * Build Badge Component
 * =====================
 * 
 * ALWAYS-VISIBLE watermark showing BUILD_ID and BUILD_VERSION.
 * This is NOT debug-only - it's always shown to verify deploys.
 */

import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { BUILD_ID, BUILD_VERSION } from '../utils/buildInfo';

export function BuildBadge() {
  // ALWAYS visible - no conditions
  return (
    <View style={styles.badge} pointerEvents="none">
      <Text style={styles.badgeText}>
        BUILD {BUILD_ID} • {BUILD_VERSION}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    position: 'absolute',
    bottom: 70, // Above tab bar
    right: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 3,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    zIndex: 99999,
  },
  badgeText: {
    fontSize: 7,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontWeight: '500',
    color: 'rgba(255, 255, 255, 0.6)',
    letterSpacing: 0.2,
  },
});

export default BuildBadge;
