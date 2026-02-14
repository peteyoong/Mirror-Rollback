import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { API_BASE_URL, API_URL_MISSING } from '../services/api';

interface DebugOverlayProps {
  extra?: Record<string, any>;
}

/**
 * DebugOverlay - TEMPORARY visible debug strip for preview diagnosis
 * Shows on ALL screens to help diagnose issues
 * REMOVE after debugging is complete
 */
export default function DebugOverlay({ extra = {} }: DebugOverlayProps) {
  const reflectionChatUrl = `${API_BASE_URL}/reflection/chat`;
  
  return (
    <View style={styles.container}>
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
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'rgba(0,0,0,0.95)',
    paddingHorizontal: 12,
    paddingVertical: 6,
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
