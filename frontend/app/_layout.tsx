import React, { useEffect, useState } from 'react';
import { Stack } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet, Platform } from 'react-native';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';
import WelcomeGate from '../components/WelcomeGate';
import { StagingBuildFooter } from '../components/StagingBuildFooter';
import { startStagingKeepAlive, stopStagingKeepAlive } from '../utils/stagingKeepAlive';
import { validateStoredSession, clearStoredSession } from '../utils/sessionValidator';

// Keep splash screen visible while fonts load
SplashScreen.preventAutoHideAsync().catch(() => {
  // Ignore errors - splash screen may already be hidden
});

/**
 * WEB BUILD VERSION CHECK (Safari-Safe, Production-Hardened)
 * 
 * Checks the backend build version and forces a TRUE hard refresh if the
 * frontend's cached version doesn't match. Uses location.replace() with
 * cache-busting query params to bypass Safari's aggressive caching.
 * 
 * Features:
 * - Cache-busting via query param (r=timestamp)
 * - Loop guard via refreshed=1 param to prevent infinite reloads
 * - Fetch timeout (3s) - fails open on timeout/error
 * - Cooldown period (60s) - prevents repeated refreshes during rolling deploys
 * - Only runs on web platform
 */
const BUILD_VERSION_KEY = 'mirror_build_id';
const REFRESH_GUARD_PARAM = 'refreshed';
const CACHE_BUST_PARAM = 'r';
const LAST_REFRESH_TS_KEY = 'mirror_last_refresh_ts';
const FETCH_TIMEOUT_MS = 3000; // 3 second timeout
const REFRESH_COOLDOWN_MS = 60000; // 60 second cooldown

/**
 * Fetch with timeout - fails open (returns null) on timeout
 */
async function fetchWithTimeout(url: string, options: RequestInit, timeoutMs: number): Promise<Response | null> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      console.warn('[BuildCheck] Fetch timeout after', timeoutMs, 'ms - failing open');
    } else {
      console.warn('[BuildCheck] Fetch error - failing open:', error.message);
    }
    return null; // Fail open
  }
}

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
  
  // COOLDOWN GUARD: Don't refresh if we refreshed recently (rolling deploy protection)
  const lastRefreshTs = localStorage.getItem(LAST_REFRESH_TS_KEY);
  if (lastRefreshTs) {
    const timeSinceLastRefresh = Date.now() - parseInt(lastRefreshTs, 10);
    if (timeSinceLastRefresh < REFRESH_COOLDOWN_MS) {
      console.log('[BuildCheck] Cooldown active, last refresh was', Math.round(timeSinceLastRefresh / 1000), 's ago - skipping');
      return;
    }
  }
  
  // Fetch with timeout - fail open on timeout/error
  const response = await fetchWithTimeout('/api/build-version', {
    cache: 'no-store',
    headers: {
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
    },
  }, FETCH_TIMEOUT_MS);
  
  // Fail open: if fetch failed or timed out, continue app load
  if (!response) {
    console.log('[BuildCheck] No response - continuing app load');
    return;
  }
  
  if (!response.ok) {
    console.warn('[BuildCheck] Failed to fetch build version:', response.status);
    return;
  }
  
  try {
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
      // Record refresh timestamp for cooldown
      localStorage.setItem(LAST_REFRESH_TS_KEY, Date.now().toString());
      
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
    console.warn('[BuildCheck] Error parsing build version:', error);
    // Fail open - don't block the app
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
  
  // Track session validation state
  const [isValidatingSession, setIsValidatingSession] = useState(true);
  const [sessionError, setSessionError] = useState<string | null>(null);

  // SESSION VALIDATION - Check if stored userId exists in current database
  // This prevents hang when user has cached session from different environment
  useEffect(() => {
    const validateSession = async () => {
      console.log("[RootLayout] Starting session validation...");
      setIsValidatingSession(true);
      
      try {
        const result = await validateStoredSession();
        
        if (!result.isValid && result.error) {
          console.log(`[AUTH] Session invalid: ${result.error}`);
          setSessionError(result.error);
          
          // Clear the store's user state if session is invalid
          useAppStore.setState({ 
            user: null, 
            chart: null,
            hasTriedSessionRestore: true, 
            isRestoringSession: false 
          });
        } else {
          // Session is valid or no session exists
          useAppStore.setState({ hasTriedSessionRestore: true, isRestoringSession: false });
        }
      } catch (error: any) {
        console.error("[AUTH] Session validation error:", error);
        // On error, still allow app to proceed (fail open)
        useAppStore.setState({ hasTriedSessionRestore: true, isRestoringSession: false });
      } finally {
        setIsValidatingSession(false);
      }
    };
    
    validateSession();
  }, []);
  
  // WEB BUILD VERSION CHECK - Ensures users get latest assets after deployment
  useEffect(() => {
    checkBuildVersionAndRefresh();
  }, []);

  // STAGING KEEPALIVE - Prevents staging backend from sleeping
  // Only runs in staging environment, pings /api/health every 4 minutes
  useEffect(() => {
    startStagingKeepAlive();
    return () => stopStagingKeepAlive();
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

  // Show loading while fonts load OR session validation
  if (!fontsLoaded || isValidatingSession) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.textSecondary} />
        <Text style={styles.loadingText}>
          {!fontsLoaded ? 'Loading fonts...' : 'Validating session...'}
        </Text>
        {sessionError && (
          <Text style={styles.sessionErrorText}>
            Session expired — please sign in again
          </Text>
        )}
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
