import React, { useEffect } from 'react';
import { Stack, useLocalSearchParams } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet, Platform } from 'react-native';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';
import { DebugViewportOverlay } from '../components/DebugViewportOverlay';
import { AddToHomeScreenBanner } from '../components/AddToHomeScreenBanner';
import { BuildBadge } from '../components/BuildBadge';
import DebugOverlay from '../components/DebugOverlay';
import WelcomeGate from '../components/WelcomeGate';

/**
 * BUILD TAG: 2026-02-14-logout-fix
 * 
 * Root Layout - The Navigation Architecture Gate
 * 
 * Features:
 * 1. WelcomeGate renders EXCLUSIVELY when no user - never overlays tabs
 * 2. DebugOverlay rendered ONLY here at root - not in individual screens
 * 3. Session state is deterministic via hasTriedSessionRestore flag
 * 4. Supports reset=1 URL param for forced logout
 * 
 * Navigation Logic:
 * - STATE 1: Restoring session -> Show loading spinner
 * - STATE 2: No user after restore -> Show WelcomeGate (REPLACES everything)
 * - STATE 3: User exists -> Show Stack navigator
 */
export default function RootLayout() {
  const params = useLocalSearchParams<{ reset?: string }>();
  const { 
    user,
    restoreSession, 
    isRestoringSession, 
    hasTriedSessionRestore,
    resetLocalSession,
  } = useAppStore();

  // Handle reset=1 URL param - clears all local data
  useEffect(() => {
    if (params.reset === '1') {
      console.log('[RootLayout] reset=1 param detected - clearing local session');
      // Reset without forcing reload (we're already in a fresh load)
      resetLocalSession(false);
    }
  }, [params.reset]);

  useEffect(() => {
    // Trigger session restore on app start (unless reset=1)
    if (params.reset !== '1') {
      console.log('[RootLayout] Starting session restore...');
      restoreSession();
    }
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
  // STATE 2: No user - show WelcomeGate OR onboarding flow
  // The Stack IS mounted to allow navigation to /onboarding
  // WelcomeGate will be the initial screen, but user can navigate to onboarding
  // =========================================================================
  if (!user) {
    console.log('[RootLayout] No user found, showing Stack with WelcomeGate as initial');
    return (
      <View style={{ flex: 1 }}>
        <Stack 
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: Colors.background },
          }}
          initialRouteName="welcome-gate"
        >
          {/* WelcomeGate as initial screen for unauthenticated users */}
          <Stack.Screen 
            name="welcome-gate" 
            options={{ headerShown: false }}
            // Use getId to ensure it's treated as the root
            getId={() => 'welcome-gate'}
          />
          
          {/* Onboarding flow - accessible without auth */}
          <Stack.Screen name="onboarding/index" options={{ headerShown: false }} />
          <Stack.Screen name="questionnaire/index" options={{ headerShown: false }} />
          
          {/* Index redirects */}
          <Stack.Screen name="index" options={{ headerShown: false }} />
        </Stack>
        
        {/* These overlays must have pointerEvents="none" and are positioned absolute */}
        {Platform.OS === 'web' && <DebugViewportOverlay />}
        <BuildBadge />
        <DebugOverlay />
      </View>
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
