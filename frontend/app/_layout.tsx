import React, { useEffect, useRef } from 'react';
import { Stack, Slot } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';
import WelcomeGate from '../components/WelcomeGate';

// ============================================================================
// globalThis guard survives Fast Refresh / HMR
// ============================================================================
const g: any = globalThis as any;
g.__mirror_layout_guard ??= { effectRan: false, renderCount: 0 };
const LAYOUT_GUARD = g.__mirror_layout_guard;

/**
 * ROOT LAYOUT - LOOP-PROOF VERSION with WelcomeGate RESTORED
 * 
 * Key safety mechanisms:
 * 1. globalThis guard survives React StrictMode double effects and Fast Refresh
 * 2. restoreSession() in store has globalThis guards too
 * 3. Only stable primitives are selected from store (no objects/arrays that trigger re-renders)
 * 4. WelcomeGate is ALWAYS rendered when no user - users can always login
 */
export default function RootLayout() {
  LAYOUT_GUARD.renderCount++;
  console.log(`[RootLayout] Render #${LAYOUT_GUARD.renderCount}`);
  
  // Select ONLY stable primitives - NOT objects/arrays
  const userId = useAppStore(s => s.user?.id);
  const isRestoringSession = useAppStore(s => s.isRestoringSession);
  const hasTriedSessionRestore = useAppStore(s => s.hasTriedSessionRestore);

  // LOOP-PROOF: Fire-and-forget restoreSession - NO subscriptions in deps
  // Uses getState() to avoid any selector coupling
  useEffect(() => {
    if (LAYOUT_GUARD.effectRan) {
      console.log('[RootLayout] useEffect: Already ran (globalThis guard), skipping');
      return;
    }
    LAYOUT_GUARD.effectRan = true;
    console.log('[RootLayout] useEffect: Firing restoreSession (one-shot, fire-and-forget)');
    
    // Fire-and-forget - no await, no blocking
    Promise.resolve()
      .then(() => useAppStore.getState().restoreSession())
      .catch((err) => console.warn('[RootLayout] restoreSession error:', err));
  }, []); // EMPTY DEPS - runs only on mount

  // STATE 1: Still restoring session - show loading but don't block forever
  // After 3 seconds, we'll show WelcomeGate anyway (handled by hasTriedSessionRestore)
  if (!hasTriedSessionRestore || isRestoringSession) {
    console.log(`[RootLayout] Showing loading (hasTriedSessionRestore=${hasTriedSessionRestore}, isRestoringSession=${isRestoringSession})`);
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.textSecondary} />
        <Text style={styles.loadingText}>Restoring session...</Text>
      </View>
    );
  }

  // STATE 2: No user - show WelcomeGate (RESTORED!)
  if (!userId) {
    console.log('[RootLayout] No user, showing WelcomeGate');
    return <WelcomeGate />;
  }

  // STATE 3: User exists - render app
  console.log(`[RootLayout] User exists (id=${userId}), rendering Stack`);
  return (
    <Stack screenOptions={{
      headerShown: false,
      contentStyle: { backgroundColor: Colors.background },
      // Keep screens mounted when navigating away (preserves chat state)
      detachInactiveScreens: false,
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
