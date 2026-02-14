import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { API_BASE_URL, API_URL_MISSING } from '../services/api';

/**
 * BUILD TAG: 2026-02-14-p0-touch-fix
 * 
 * DebugOverlay - Environment debug strip
 * 
 * P0 FIX: All wrappers use pointerEvents="none" to ensure
 * this overlay NEVER intercepts touch events.
 * 
 * This component should ONLY be rendered in the root _layout.tsx,
 * NOT in individual screens.
 * 
 * Set DEBUG_OVERLAY_ENABLED to true to see debug info.
 */

// Toggle this to enable/disable the debug overlay globally
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
  
  // P0 FIX: Wrap everything in pointerEvents="none" container
  // The style.pointerEvents is preferred over the prop for web compatibility
  return (
    <View style={styles.container} pointerEvents="none">
      <View style={styles.inner} pointerEvents="none">
        <Text style={styles.title} pointerEvents="none">🔧 DEBUG</Text>
        <Text style={styles.row} pointerEvents="none">
          API_URL_MISSING: <Text style={API_URL_MISSING ? styles.error : styles.ok}>{String(API_URL_MISSING)}</Text>
        </Text>
        <Text style={styles.row} numberOfLines={1} pointerEvents="none">
          API: {API_BASE_URL || '(none)'}
        </Text>
        <Text style={styles.row} numberOfLines={1} pointerEvents="none">
          Chat: {reflectionChatUrl}
        </Text>
        {Object.entries(extra).map(([key, value]) => (
          <Text key={key} style={styles.row} numberOfLines={1} pointerEvents="none">
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
    // P0: Ensure pointer events pass through on web
    pointerEvents: 'none',
  },
  inner: {
    backgroundColor: 'rgba(0,0,0,0.9)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    borderBottomWidth: 1,
    borderBottomColor: '#FF6B00',
    // P0: Ensure pointer events pass through on web
    pointerEvents: 'none',
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
