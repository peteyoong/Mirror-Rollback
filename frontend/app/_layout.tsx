import React, { useEffect, useRef } from 'react';
import { Stack, Slot } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';

// ============================================================================
// globalThis guard survives Fast Refresh / HMR
// ============================================================================
const g: any = globalThis as any;
g.__mirror_layout_guard ??= { effectRan: false, renderCount: 0 };
const LAYOUT_GUARD = g.__mirror_layout_guard;

/**
 * ROOT LAYOUT - LOOP-PROOF VERSION
 * 
 * Key safety mechanisms:
 * 1. globalThis guard survives React StrictMode double effects and Fast Refresh
 * 2. restoreSession() in store has globalThis guards too
 * 3. Only stable primitives are selected from store (no objects/arrays that trigger re-renders)
 */
export default function RootLayout() {
  LAYOUT_GUARD.renderCount++;
  console.log(`[RootLayout] Render #${LAYOUT_GUARD.renderCount}`);
  
  // Select ONLY stable primitives - NOT objects/arrays
  const userId = useAppStore(s => s.user?.id);
  const restoreSession = useAppStore(s => s.restoreSession);
  const isRestoringSession = useAppStore(s => s.isRestoringSession);
  const hasTriedSessionRestore = useAppStore(s => s.hasTriedSessionRestore);

  // LOOP-PROOF: Call restoreSession ONCE using globalThis guard
  useEffect(() => {
    if (LAYOUT_GUARD.effectRan) {
      console.log('[RootLayout] useEffect: Already ran (globalThis guard), skipping');
      return;
    }
    LAYOUT_GUARD.effectRan = true;
    console.log('[RootLayout] useEffect: Calling restoreSession (one-shot via globalThis)');
    restoreSession();
  }, []); // EMPTY DEPS - runs only on mount

  // STATE 1: Still restoring session - show loading
  if (!hasTriedSessionRestore || isRestoringSession) {
    console.log(`[RootLayout] Showing loading (hasTriedSessionRestore=${hasTriedSessionRestore}, isRestoringSession=${isRestoringSession})`);
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.textSecondary} />
        <Text style={styles.loadingText}>Restoring...</Text>
      </View>
    );
  }

  // STATE 2: No user - show simple login prompt (WelcomeGate removed for isolation)
  if (!userId) {
    console.log('[RootLayout] No user, showing minimal login prompt');
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Please log in</Text>
        <Text style={{ color: '#888', fontSize: 12 }}>WelcomeGate disabled for loop isolation</Text>
      </View>
    );
  }

  // STATE 3: User exists - render app
  console.log(`[RootLayout] User exists (id=${userId}), rendering Stack`);
  return (
    <Stack screenOptions={{
      headerShown: false,
      contentStyle: { backgroundColor: Colors.background },
    }}>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="reflection-chat" options={{ presentation: 'modal' }} />
      <Stack.Screen name="welcome" options={{ headerShown: false }} />
    </Stack>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.background,
    gap: 16,
    padding: 20,
  },
  loadingText: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginTop: 12,
  },
});
