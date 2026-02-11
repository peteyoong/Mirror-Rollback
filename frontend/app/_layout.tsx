import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet, Platform, useWindowDimensions } from 'react-native';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';
import { DebugViewportOverlay } from '../components/DebugViewportOverlay';
import { AddToHomeScreenBanner } from '../components/AddToHomeScreenBanner';
import { BuildBadge } from '../components/BuildBadge';
import { DebugOverlay } from '../components/DebugOverlay';

export default function RootLayout() {
  const { 
    restoreSession, 
    isRestoringSession, 
    hasTriedSessionRestore 
  } = useAppStore();
  
  const { width } = useWindowDimensions();
  const isMobile = width < 768;

  useEffect(() => {
    // Trigger session restore on app start
    console.log('[RootLayout] Starting session restore...');
    restoreSession();
  }, []);

  // Block rendering until we've tried to restore the session
  // This is the AUTH HYDRATION GATE
  if (!hasTriedSessionRestore || isRestoringSession) {
    return (
      <View style={styles.container}>
        <View style={[
          styles.loadingContainer,
          // Only apply maxWidth on desktop web
          Platform.OS === 'web' && !isMobile && styles.desktopMaxWidth
        ]}>
          <ActivityIndicator size="large" color={Colors.textSecondary} />
          <Text style={styles.loadingText}>Restoring your profile...</Text>
        </View>
        {/* Debug viewport overlay for web */}
        {Platform.OS === 'web' && <DebugViewportOverlay />}
      </View>
    );
  }

  return (
    <>
      <Stack screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: Colors.background },
      }} />
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
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.background,
    // Full width on all platforms - no maxWidth on mobile
    width: '100%',
  },
  loadingContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
    padding: 20,
  },
  desktopMaxWidth: {
    maxWidth: 400,
  },
  loadingText: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginTop: 12,
  },
});
