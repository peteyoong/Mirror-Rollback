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
 * BUILD TAG: 2026-02-14-nav-architecture-fix
 * 
 * Root Layout - The Navigation Architecture Gate
 * 
 * This layout handles the core navigation decision:
 * 1. Show loading spinner while restoring session
 * 2. If NO user after restore → Show WelcomeGate (login/register)
 * 3. If user EXISTS → Show Stack navigator (tabs, modals, etc.)
 * 
 * CRITICAL: WelcomeGate is rendered AT THIS LEVEL, not as a route.
 * This prevents the "Welcome overlay on top of tabs" bug.
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
  // STATE 2: No user - show WelcomeGate (login/register)
  // This is NOT a route - it's a component rendered directly here
  // =========================================================================
  if (!user) {
    console.log('[RootLayout] No user found, showing WelcomeGate');
    return (
      <>
        <WelcomeGate />
        {Platform.OS === 'web' && <DebugViewportOverlay />}
        <BuildBadge />
      </>
    );
  }

  // =========================================================================
  // STATE 3: User exists - show the main app Stack
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
        
        {/* Onboarding flow - only accessible if user needs to complete setup */}
        <Stack.Screen name="onboarding" options={{ headerShown: false }} />
        <Stack.Screen name="questionnaire" options={{ headerShown: false }} />
        
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
        
        {/* Welcome screen - for "Start Fresh" or re-login scenarios */}
        <Stack.Screen name="welcome" options={{ headerShown: false }} />
        
        {/* Index route - redirects to tabs */}
        <Stack.Screen name="index" options={{ headerShown: false }} />
      </Stack>
      
      {/* iOS Add to Home Screen Banner (browser only) */}
      {Platform.OS === 'web' && <AddToHomeScreenBanner />}
      
      {/* Debug viewport overlay for web - always present when debug enabled */}
      {Platform.OS === 'web' && <DebugViewportOverlay />}
      
      {/* BUILD_ID Badge - shows in debug mode to verify deployed bundle */}
      <BuildBadge />
      
      {/* Debug Overlay - shows environment info when ?debug=1 */}
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
