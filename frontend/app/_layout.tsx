import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet, Platform } from 'react-native';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';
import { DebugViewportOverlay } from '../components/DebugViewportOverlay';
import { AddToHomeScreenBanner } from '../components/AddToHomeScreenBanner';
import { BuildBadge } from '../components/BuildBadge';
import DebugOverlay from '../components/DebugOverlay';
import WelcomeGate from '../components/WelcomeGate';

/**
 * BUILD TAG: 2026-02-14-p0-p1-stability
 * 
 * Root Layout - The Navigation Architecture Gate
 * 
 * P0/P1 FIXES:
 * 1. WelcomeGate renders EXCLUSIVELY when no user - never overlays tabs
 * 2. DebugOverlay rendered ONLY here at root - not in individual screens
 * 3. Session state is deterministic via hasTriedSessionRestore flag
 * 
 * Navigation Logic:
 * - STATE 1: Restoring session -> Show loading spinner
 * - STATE 2: No user after restore -> Show WelcomeGate (REPLACES everything)
 * - STATE 3: User exists -> Show Stack navigator
 */
export default function RootLayout() {
  const { 
    user,
    restoreSession, 
    isRestoringSession, 
    hasTriedSessionRestore 
  } = useAppStore();

  useEffect(() => {
    // Trigger session restore on app start
    console.log('[RootLayout] Starting session restore...');
    restoreSession();
  }, []);

  // =========================================================================
  // STATE 1: Still restoring session - show loading
  // =========================================================================
  if (!hasTriedSessionRestore || isRestoringSession) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.textSecondary} />
        <Text style={styles.loadingText}>Restoring your profile...</Text>
        {Platform.OS === 'web' && <DebugViewportOverlay />}
      </View>
    );
  }

  // =========================================================================
  // STATE 2: No user - show WelcomeGate EXCLUSIVELY
  // P1 FIX: WelcomeGate is the ONLY thing rendered - no Stack, no tabs behind
  // =========================================================================
  if (!user) {
    console.log('[RootLayout] No user found, showing WelcomeGate (exclusive)');
    return (
      <>
        <WelcomeGate />
        {Platform.OS === 'web' && <DebugViewportOverlay />}
        <BuildBadge />
        {/* P0: DebugOverlay with pointerEvents="none" */}
        <DebugOverlay />
      </>
    );
  }

  // =========================================================================
  // STATE 3: User exists - show the main app Stack
  // P0: DebugOverlay rendered ONLY once here at root level
  // =========================================================================
  console.log('[RootLayout] User exists, showing main app');
  return (
    <>
      <Stack screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: Colors.background },
      }}>
        {/* Main tabs - this is the default route */}
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        
        {/* Modal screens */}
        <Stack.Screen name="reflection-chat" options={{ presentation: 'modal' }} />
        <Stack.Screen name="todays-mirror" options={{ presentation: 'modal' }} />
        
        {/* Onboarding flow */}
        <Stack.Screen name="onboarding/index" options={{ headerShown: false }} />
        <Stack.Screen name="questionnaire/index" options={{ headerShown: false }} />
        
        {/* Lens detail screens */}
        <Stack.Screen name="lenses/[lens]" options={{ headerShown: false }} />
        
        {/* Enneagram screens */}
        <Stack.Screen name="enneagram/index" options={{ headerShown: false }} />
        <Stack.Screen name="enneagram/assessment" options={{ headerShown: false }} />
        <Stack.Screen name="enneagram/quick-assessment" options={{ headerShown: false }} />
        <Stack.Screen name="enneagram/deep-assessment" options={{ headerShown: false }} />
        <Stack.Screen name="enneagram/p2-assessment" options={{ headerShown: false }} />
        <Stack.Screen name="enneagram/results" options={{ headerShown: false }} />
        
        {/* Debug screens */}
        <Stack.Screen name="debug/wing-states" options={{ headerShown: false }} />
        
        {/* Welcome screen - for "Start Fresh" scenarios */}
        <Stack.Screen name="welcome" options={{ headerShown: false }} />
        
        {/* Index route - redirects to tabs */}
        <Stack.Screen name="index" options={{ headerShown: false }} />
      </Stack>
      
      {/* iOS Add to Home Screen Banner (browser only) */}
      {Platform.OS === 'web' && <AddToHomeScreenBanner />}
      
      {/* Debug viewport overlay for web */}
      {Platform.OS === 'web' && <DebugViewportOverlay />}
      
      {/* BUILD_ID Badge */}
      <BuildBadge />
      
      {/* P0: DebugOverlay with pointerEvents="none" - ONLY rendered here */}
      <DebugOverlay />
    </>
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
