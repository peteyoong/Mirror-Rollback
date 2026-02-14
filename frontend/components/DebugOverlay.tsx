import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { API_BASE_URL, API_URL_MISSING } from '../services/api';

/**
 * BUILD TAG: 2026-02-14-overlay-touch-fix
 * 
 * DebugOverlay - Environment debug strip
 * 
 * CRITICAL FIX: All wrappers use pointerEvents="none" to ensure
 * this overlay NEVER intercepts touch events.
 * 
 * Set DEBUG_OVERLAY_ENABLED to true to see debug info.
 * Set to false to completely disable the overlay.
 */

// Toggle this to enable/disable the debug overlay
const DEBUG_OVERLAY_ENABLED = false;

interface DebugOverlayProps {
  extra?: Record<string, any>;
}

export default function DebugOverlay({ extra = {} }: DebugOverlayProps) {
  // Completely disable overlay when flag is false
  if (!DEBUG_OVERLAY_ENABLED) {
    return null;
  }
  
  const reflectionChatUrl = `${API_BASE_URL}/reflection/chat`;
  
  return (
    // CRITICAL: pointerEvents="none" on ALL wrappers
    // This ensures the overlay never blocks touch events
    <View style={styles.container} pointerEvents="none">
      <View style={styles.inner} pointerEvents="none">
        <Text style={styles.title}>🔧 DEBUG</Text>
        <Text style={styles.row}>
          API_URL_MISSING: <Text style={API_URL_MISSING ? styles.error : styles.ok}>{String(API_URL_MISSING)}</Text>
        </Text>
        <Text style={styles.row} numberOfLines={1}>
          API: {API_BASE_URL || '(none)'}
        </Text>
        <Text style={styles.row} numberOfLines={1}>
          Chat: {reflectionChatUrl}
        </Text>
        {Object.entries(extra).map(([key, value]) => (
          <Text key={key} style={styles.row} numberOfLines={1}>
            {key}: {typeof value === 'object' ? JSON.stringify(value) : String(value)}
          </Text>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 9999,
    // pointerEvents is set as prop, not style
  },
  inner: {
    backgroundColor: 'rgba(0,0,0,0.9)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    borderBottomWidth: 1,
    borderBottomColor: '#FF6B00',
  },
  title: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FF6B00',
    marginBottom: 2,
  },
  row: {
    fontSize: 9,
    color: '#AAA',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 1,
  },
  error: {
    color: '#FF4444',
    fontWeight: '700',
  },
  ok: {
    color: '#00FF88',
  },
});
