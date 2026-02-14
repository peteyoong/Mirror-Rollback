import React, { useEffect, useRef } from 'react';
import { Stack, Slot } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';

/**
 * ROOT LAYOUT - STRIPPED DOWN FOR LOOP ISOLATION
 * 
 * REMOVED: DebugOverlay, BuildBadge, AddToHomeScreenBanner, DebugViewportOverlay, WelcomeGate
 * 
 * Testing if the loop is caused by one of these components.
 */
export default function RootLayout() {
  // STEP 4: Ensure restoreSession only runs ONCE
  const didRestoreRef = useRef(false);
  
  const { 
    user,
    restoreSession, 
    isRestoringSession, 
    hasTriedSessionRestore,
  } = useAppStore();

  useEffect(() => {
    if (didRestoreRef.current) return;
    didRestoreRef.current = true;
    console.log('[RootLayout] Starting session restore (one-shot)...');
    restoreSession();
  }, []);

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
