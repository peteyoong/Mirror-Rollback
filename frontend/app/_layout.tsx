import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';
import WelcomeGate from '../components/WelcomeGate';
import { StagingBuildFooter } from '../components/StagingBuildFooter';

// Keep splash screen visible while fonts load
SplashScreen.preventAutoHideAsync().catch(() => {
  // Ignore errors - splash screen may already be hidden
});

/**
 * ROOT LAYOUT - With Local Font Loading
 * 
 * Loads Ionicons.ttf from local assets to eliminate CDN dependency.
 * The font is registered with the exact family name that @expo/vector-icons expects.
 */
export default function RootLayout() {
  
  // Load fonts from local assets
  // IMPORTANT: 'ionicons' (lowercase) is the font family name used by @expo/vector-icons
  const [fontsLoaded, fontError] = useFonts({
    // Register with the exact name @expo/vector-icons uses internally
    'ionicons': require('../assets/fonts/Ionicons.ttf'),
    // Also register capitalized version for compatibility
    'Ionicons': require('../assets/fonts/Ionicons.ttf'),
    // SpaceMono for any text that needs it
    'SpaceMono': require('../assets/fonts/SpaceMono-Regular.ttf'),
  });
  
  // Select stable primitives only
  const userId = useAppStore(s => s.user?.id);
  const isRestoringSession = useAppStore(s => s.isRestoringSession);
  const hasTriedSessionRestore = useAppStore(s => s.hasTriedSessionRestore);

  // STEP 1: DISABLED restoreSession - DO NOT CALL
  // useEffect(() => {
  //   useAppStore.getState().restoreSession();
  // }, []);
  
  // TEMP: Mark session restore as "tried" immediately so UI doesn't block
  useEffect(() => {
    console.log("[RootLayout] Setting hasTriedSessionRestore=true (NO restore call)");
    useAppStore.setState({ hasTriedSessionRestore: true, isRestoringSession: false });
  }, []);

  // Hide splash screen when fonts are loaded
  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync().catch(() => {
        // Ignore errors
      });
    }
  }, [fontsLoaded, fontError]);

  // Log font loading status
  useEffect(() => {
    if (fontsLoaded) {
      console.log('[RootLayout] ✅ Fonts loaded successfully (Ionicons bundled locally)');
    }
    if (fontError) {
      console.error('[RootLayout] ❌ Font loading error:', fontError);
    }
  }, [fontsLoaded, fontError]);

  // Show loading while fonts load OR session restore
  if (!fontsLoaded || !hasTriedSessionRestore || isRestoringSession) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.textSecondary} />
        <Text style={styles.loadingText}>
          {!fontsLoaded ? 'Loading fonts...' : 'Loading...'}
        </Text>
      </View>
    );
  }

  // No user - show WelcomeGate
  if (!userId) {
    return <WelcomeGate />;
  }

  // User exists - render app
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
  },
  loadingText: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginTop: 12,
  },
});
