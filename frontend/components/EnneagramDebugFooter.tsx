/**
 * Enneagram Debug Footer - Shows build version and leak warnings
 * Only visible when debug mode is enabled
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { APP_BUILD_ID, hasDetectedLeaks, getDetectedLeaks } from '../utils/enneagramTripwire';
import { Colors } from '../constants/colors';

interface Props {
  showDebug?: boolean;
}

export default function EnneagramDebugFooter({ showDebug = false }: Props) {
  if (!showDebug) return null;
  
  const leaks = getDetectedLeaks();
  const hasLeaks = hasDetectedLeaks();
  
  return (
    <View style={styles.container}>
      {/* Build Version */}
      <View style={styles.buildInfo}>
        <Text style={styles.buildLabel}>Build: {APP_BUILD_ID}</Text>
      </View>
      
      {/* Leak Warnings */}
      {hasLeaks && (
        <View style={styles.leakWarning}>
          <Text style={styles.leakTitle}>⚠️ ENNEAGRAM LABEL LEAK DETECTED ({leaks.length})</Text>
          {leaks.map((leak, index) => (
            <View key={index} style={styles.leakItem}>
              <Text style={styles.leakContext}>Context: {leak.context}</Text>
              <Text style={styles.leakValue}>Value: "{leak.value}"</Text>
              <Text style={styles.leakPattern}>Pattern: {leak.pattern}</Text>
            </View>
          ))}
        </View>
      )}
      
      {/* No leaks indicator */}
      {!hasLeaks && (
        <View style={styles.noLeaks}>
          <Text style={styles.noLeaksText}>✓ No label leaks detected</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 12,
    marginTop: 20,
    marginBottom: 20,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  buildInfo: {
    backgroundColor: '#1a1a2e',
    padding: 8,
    borderRadius: 4,
    marginBottom: 8,
  },
  buildLabel: {
    fontSize: 11,
    fontFamily: 'monospace',
    color: '#888',
    textAlign: 'center',
  },
  leakWarning: {
    backgroundColor: '#4a0000',
    padding: 12,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#ff4444',
  },
  leakTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#ff4444',
    marginBottom: 8,
  },
  leakItem: {
    backgroundColor: '#300000',
    padding: 8,
    borderRadius: 4,
    marginTop: 4,
  },
  leakContext: {
    fontSize: 11,
    color: '#ffaaaa',
    fontFamily: 'monospace',
  },
  leakValue: {
    fontSize: 11,
    color: '#ff8888',
    fontFamily: 'monospace',
  },
  leakPattern: {
    fontSize: 10,
    color: '#ff6666',
    fontFamily: 'monospace',
  },
  noLeaks: {
    backgroundColor: '#003300',
    padding: 8,
    borderRadius: 4,
  },
  noLeaksText: {
    fontSize: 11,
    color: '#44ff44',
    textAlign: 'center',
  },
});
