import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet, Platform } from 'react-native';
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
 * WEB BUILD VERSION CHECK (Safari-Safe)
 * 
 * Checks the backend build version and forces a TRUE hard refresh if the
 * frontend's cached version doesn't match. Uses location.replace() with
 * cache-busting query params to bypass Safari's aggressive caching.
 * 
 * Features:
 * - Cache-busting via query param (r=timestamp)
 * - Loop guard via refreshed=1 param to prevent infinite reloads
 * - Only runs on web platform
 */
const BUILD_VERSION_KEY = 'mirror_build_id';
const REFRESH_GUARD_PARAM = 'refreshed';
const CACHE_BUST_PARAM = 'r';

async function checkBuildVersionAndRefresh(): Promise<void> {
  // Only run on web
  if (Platform.OS !== 'web') return;
  
  // Guard against SSR - ensure window is available
  if (typeof window === 'undefined') return;
  
  const urlParams = new URLSearchParams(window.location.search);
  
  // LOOP GUARD: If we already refreshed once, don't refresh again
  if (urlParams.get(REFRESH_GUARD_PARAM) === '1') {
    console.log('[BuildCheck] Already refreshed once (guard active), skipping');
    // Clean up the URL by removing refresh params (cosmetic)
    cleanupRefreshParams();
    return;
  }
  
  try {
    const response = await fetch('/api/build-version', {
      cache: 'no-store', // Bypass any HTTP caching
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
      },
    });
    
    if (!response.ok) {
      console.warn('[BuildCheck] Failed to fetch build version:', response.status);
      return;
    }
    
    const data = await response.json();
    const serverBuildId = data.build_id;
    
    if (!serverBuildId || serverBuildId === 'unknown') {
      console.log('[BuildCheck] Server build ID not set, skipping check');
      return;
    }
    
    const storedBuildId = localStorage.getItem(BUILD_VERSION_KEY);
    
    console.log('[BuildCheck] Server build:', serverBuildId, '| Stored build:', storedBuildId);
    
    if (storedBuildId && storedBuildId !== serverBuildId) {
      console.log('[BuildCheck] Build mismatch detected! Forcing TRUE hard refresh...');
      // Update stored version before refresh to prevent infinite loop
      localStorage.setItem(BUILD_VERSION_KEY, serverBuildId);
      
      // TRUE HARD REFRESH: Use location.replace with cache-busting params
      // This forces Safari to request fresh index.html and all assets
      const currentPath = window.location.pathname;
      const currentSearch = window.location.search;
      const separator = currentSearch ? '&' : '?';
      const newUrl = `${currentPath}${currentSearch}${separator}${REFRESH_GUARD_PARAM}=1&${CACHE_BUST_PARAM}=${Date.now()}`;
      
      console.log('[BuildCheck] Redirecting to:', newUrl);
      window.location.replace(newUrl);
      return;
    }
    
    // First visit or matching version - store the current build ID
    if (!storedBuildId) {
      console.log('[BuildCheck] First visit, storing build ID:', serverBuildId);
      localStorage.setItem(BUILD_VERSION_KEY, serverBuildId);
    }
  } catch (error) {
    console.warn('[BuildCheck] Error checking build version:', error);
    // Don't block the app if this fails
  }
}

/**
 * Clean up refresh params from URL after successful load (cosmetic)
 * Uses replaceState to avoid adding to browser history
 */
function cleanupRefreshParams(): void {
  if (typeof window === 'undefined') return;
  
  try {
    const url = new URL(window.location.href);
    const hadParams = url.searchParams.has(REFRESH_GUARD_PARAM) || url.searchParams.has(CACHE_BUST_PARAM);
    
    if (hadParams) {
      url.searchParams.delete(REFRESH_GUARD_PARAM);
      url.searchParams.delete(CACHE_BUST_PARAM);
      
      // Clean URL without the refresh params
      const cleanUrl = url.pathname + (url.searchParams.toString() ? '?' + url.searchParams.toString() : '') + url.hash;
      window.history.replaceState({}, '', cleanUrl);
      console.log('[BuildCheck] Cleaned up refresh params from URL');
    }
  } catch (e) {
    // Ignore errors - this is just cosmetic
  }
}

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
  
  // WEB BUILD VERSION CHECK - Ensures users get latest assets after deployment
  useEffect(() => {
    checkBuildVersionAndRefresh();
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
    return (
      <>
        <WelcomeGate />
        <StagingBuildFooter />
      </>
    );
  }

  // User exists - render app
  return (
    <>
      <Stack screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: Colors.background },
      }}>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="reflection-chat" options={{ presentation: 'modal' }} />
        <Stack.Screen name="welcome" options={{ headerShown: false }} />
      </Stack>
      <StagingBuildFooter />
    </>
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
