/**
 * Mirror V2 - ULTRA MINIMAL ISOLATION VERSION
 * 
 * NO store imports, NO effects, NO nothing
 * Just static text to prove the tab can render
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function MirrorV2Screen() {
  // ZERO store access
  // ZERO useEffect
  // ZERO navigation
  // ZERO async code
  
  console.log('[MirrorV2] Render - ULTRA MINIMAL');
  
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>MIRROR - ULTRA MINIMAL</Text>
        <Text style={styles.subtitle}>No store, no effects, no hooks</Text>
      </View>
      <View style={styles.content}>
        <Text style={styles.text}>If you see this without crash,</Text>
        <Text style={styles.text}>the loop is NOT in mirror-v2.tsx</Text>
        <Text style={styles.hint}>Check browser console for [ZUSTAND set] logs</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  header: {
    padding: 40,
    paddingTop: 80,
    backgroundColor: '#006600',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 14,
    color: '#cfc',
    marginTop: 8,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  text: {
    fontSize: 18,
    color: '#fff',
    textAlign: 'center',
    marginBottom: 8,
  },
  hint: {
    fontSize: 14,
    color: '#888',
    marginTop: 20,
    textAlign: 'center',
  },
});
