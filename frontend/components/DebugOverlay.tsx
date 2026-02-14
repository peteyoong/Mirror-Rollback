import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { API_BASE_URL, API_URL_MISSING } from '../services/api';

// TEMPORARY: Set to false to completely disable overlay for debugging touch issues
const DEBUG_OVERLAY_ENABLED = false;

interface DebugOverlayProps {
  extra?: Record<string, any>;
}

/**
 * DebugOverlay - TEMPORARY visible debug strip for preview diagnosis
 * Shows on ALL screens to help diagnose issues
 * REMOVE after debugging is complete
 * 
 * CRITICAL: Must never intercept touches
 */
export default function DebugOverlay({ extra = {} }: DebugOverlayProps) {
  // Completely disable overlay to test if it's blocking touches
  if (!DEBUG_OVERLAY_ENABLED) {
    return null;
  }
  
  const reflectionChatUrl = `${API_BASE_URL}/reflection/chat`;
  
  return (
    <View pointerEvents="none" style={styles.container}>
      <View pointerEvents="none" style={styles.inner}>
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
