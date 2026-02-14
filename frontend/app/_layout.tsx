import React, { useEffect, useRef } from 'react';
import { Stack, Slot } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';

// DEBUG: Track render count
let ROOT_RENDER_COUNT = 0;

/**
 * ROOT LAYOUT - LOOP-PROOF VERSION
 * 
 * Key safety mechanisms:
 * 1. didRestoreRef ensures restoreSession() is only called ONCE in this component
 * 2. restoreSession() in store has module-level guards
 * 3. Only stable primitives are selected from store (no objects/arrays that trigger re-renders)
 */
export default function RootLayout() {
  ROOT_RENDER_COUNT++;
  console.log(`[RootLayout] Render #${ROOT_RENDER_COUNT}`);
  
  // CRITICAL: This ref ensures we NEVER call restoreSession twice from this component
  const didRestoreRef = useRef(false);
  
  // Select ONLY stable primitives - NOT objects/arrays
  const userId = useAppStore(s => s.user?.id);
  const restoreSession = useAppStore(s => s.restoreSession);
  const isRestoringSession = useAppStore(s => s.isRestoringSession);
  const hasTriedSessionRestore = useAppStore(s => s.hasTriedSessionRestore);

  // LOOP-PROOF: Call restoreSession ONCE with empty deps []
  useEffect(() => {
    if (didRestoreRef.current) {
      console.log('[RootLayout] useEffect: Already called restore, skipping');
      return;
    }
    didRestoreRef.current = true;
    console.log('[RootLayout] useEffect: Calling restoreSession (one-shot)');
    restoreSession();
  }, []); // EMPTY DEPS - runs only on mount

  // STATE 1: Still restoring session - show loading
  if (!hasTriedSessionRestore || isRestoringSession) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.textSecondary} />
        <Text style={styles.loadingText}>Restoring...</Text>
      </View>
    );
  }

  // STATE 2: No user - show simple login prompt (WelcomeGate removed for isolation)
  if (!user) {
    console.log('[RootLayout] No user, showing minimal login prompt');
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Please log in</Text>
        <Text style={{ color: '#888', fontSize: 12 }}>WelcomeGate disabled for loop isolation</Text>
      </View>
    );
  }

  // STATE 3: User exists - show ONLY the Stack navigator (nothing else)
  console.log('[RootLayout] User exists, showing minimal Stack');
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
