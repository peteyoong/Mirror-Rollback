import React, { useEffect, useState, Component, ErrorInfo, ReactNode } from 'react';
import { Stack, router } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet, Platform, useWindowDimensions, TouchableOpacity, ScrollView } from 'react-native';
import { useAppStore } from '../store';
import { ThemeProvider, useTheme, LightTheme, DarkTheme } from '../contexts/ThemeContext';
import { ForumContextProvider } from '../contexts/ForumContext';
import { KeyboardProvider } from 'react-native-keyboard-controller';
import { DebugViewportOverlay } from '../components/DebugViewportOverlay';
import { AddToHomeScreenBanner, BannerProvider } from '../components/AddToHomeScreenBanner';

import { BUILD_ID as HOTFIX_BUILD_ID } from '../constants/buildMarker';

// Build info from environment
const BUILD_VERSION = process.env.EXPO_PUBLIC_BUILD_VERSION || 'unknown';
const BUILD_ID = process.env.EXPO_PUBLIC_BUILD_ID || 'unknown';

// Bump this whenever we ship a change that could leave Safari/PWA
// users with stale cached forum / pulse / live-field state. On boot
// we compare it against the value stored in localStorage; on
// mismatch we wipe forum-scoped storage so the new bundle isn't
// reading old JSON shapes from an earlier deploy.
const APP_STORAGE_VERSION = '2026.05.13.safari-forum-recovery';

// Web-only: purge stale forum state when the app storage version
// changes. Safe to call on every boot — it's idempotent and only
// removes keys that match a tight allowlist of forum / pulse /
// live-field / member-summary prefixes. User/session keys are
// preserved so logout is never forced by a version bump.
function purgeStaleForumStorageIfNeeded() {
  if (Platform.OS !== 'web') return;
  if (typeof window === 'undefined' || !window.localStorage) return;
  try {
    const stored = window.localStorage.getItem('mirror_storage_version');
    if (stored === APP_STORAGE_VERSION) return;

    const PURGE_PREFIXES = [
      'forum_', 'mirror_forum_', 'forumContext_', 'pulse_', 'live_field_',
      'forum_member_', 'member_summary_', 'forum_pattern_',
    ];
    const toRemove: string[] = [];
    for (let i = 0; i < window.localStorage.length; i++) {
      const k = window.localStorage.key(i);
      if (!k) continue;
      if (PURGE_PREFIXES.some((p) => k.startsWith(p))) toRemove.push(k);
    }
    toRemove.forEach((k) => window.localStorage.removeItem(k));
    window.localStorage.setItem('mirror_storage_version', APP_STORAGE_VERSION);
    if (toRemove.length) {
      console.log(
        `[Storage] APP_STORAGE_VERSION changed (${stored || 'none'} → ${APP_STORAGE_VERSION}). ` +
        `Purged ${toRemove.length} stale forum-scoped key(s).`
      );
    }
  } catch (e) {
    console.warn('[Storage] version-guard purge failed (non-fatal):', e);
  }
}

// Error Boundary Component
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class AppErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary] Caught error:', error);
    console.error('[ErrorBoundary] Error info:', errorInfo);
    this.setState({ errorInfo });
  }

  handleReload = () => {
    if (Platform.OS === 'web') {
      // Force hard reload with cache bust
      const url = new URL(window.location.href);
      url.searchParams.set('_cb', Date.now().toString());
      window.location.href = url.toString();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <View style={errorStyles.container}>
          <ScrollView contentContainerStyle={errorStyles.scrollContent}>
            <Text style={errorStyles.title}>Something went wrong</Text>
            <Text style={errorStyles.subtitle}>The app encountered an error</Text>
            
            <View style={errorStyles.infoBox}>
              <Text style={errorStyles.infoLabel}>Build Version</Text>
              <Text style={errorStyles.infoValue}>{BUILD_VERSION}</Text>
              
              <Text style={errorStyles.infoLabel}>Build ID</Text>
              <Text style={errorStyles.infoValue}>{BUILD_ID}</Text>
              
              <Text style={errorStyles.infoLabel}>Error</Text>
              <Text style={errorStyles.errorText}>{this.state.error?.message || 'Unknown error'}</Text>
              
              {this.state.errorInfo && (
                <>
                  <Text style={errorStyles.infoLabel}>Component Stack</Text>
                  <Text style={errorStyles.errorText} numberOfLines={10}>
                    {this.state.errorInfo.componentStack}
                  </Text>
                </>
              )}
            </View>
            
            <TouchableOpacity style={errorStyles.reloadButton} onPress={this.handleReload}>
              <Text style={errorStyles.reloadButtonText}>Reload App (Clear Cache)</Text>
            </TouchableOpacity>
            
            <Text style={errorStyles.hint}>
              If this keeps happening, try: Settings → Safari → Clear History and Website Data
            </Text>
          </ScrollView>
        </View>
      );
    }

    return this.props.children;
  }
}

const errorStyles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: LightTheme.background,
  },
  scrollContent: {
    padding: 24,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100%',
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    color: LightTheme.text,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: LightTheme.textSecondary,
    marginBottom: 24,
  },
  infoBox: {
    backgroundColor: LightTheme.surface,
    borderRadius: 12,
    padding: 16,
    width: '100%',
    maxWidth: 400,
    marginBottom: 24,
  },
  infoLabel: {
    fontSize: 12,
    color: LightTheme.textTertiary,
    marginTop: 12,
    marginBottom: 4,
  },
  infoValue: {
    fontSize: 14,
    color: LightTheme.text,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  errorText: {
    fontSize: 12,
    color: '#E57373',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  reloadButton: {
    backgroundColor: LightTheme.accent,
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 8,
    marginBottom: 16,
  },
  reloadButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: LightTheme.background,
  },
  hint: {
    fontSize: 12,
    color: LightTheme.textTertiary,
    textAlign: 'center',
    maxWidth: 300,
  },
});

export default function RootLayout() {
  return (
    <KeyboardProvider>
      <ThemeProvider>
        <ForumContextProvider>
          <ThemedRootLayout />
        </ForumContextProvider>
      </ThemeProvider>
    </KeyboardProvider>
  );
}

// Inner component that uses theme
function ThemedRootLayout() {
  const { theme, isDark } = useTheme();
  const { 
    restoreSession, 
    isRestoringSession, 
    hasTriedSessionRestore 
  } = useAppStore();
  
  const { width } = useWindowDimensions();
  const isMobile = width < 768;
  const [bootstrapStage, setBootstrapStage] = useState('initializing');

  useEffect(() => {
    // Trigger session restore on app start
    console.log('[RootLayout] Starting session restore...');
    console.log('[RootLayout] Build:', BUILD_VERSION, 'ID:', BUILD_ID);
    console.log('[RootLayout] Theme:', isDark ? 'DARK' : 'LIGHT');
    // Safari/PWA self-heal: drop forum-scoped storage whose shape no
    // longer matches the current bundle BEFORE restoring the session.
    // Idempotent and platform-gated; native is a no-op.
    purgeStaleForumStorageIfNeeded();
    setBootstrapStage('restoring_session');
    restoreSession().then(() => {
      setBootstrapStage('ready');
    }).catch((err) => {
      console.error('[RootLayout] Session restore failed:', err);
      setBootstrapStage('error');
    });
  }, []);

  // P0 hotfix v1 (May 14 2026): bootstrap safety timeout. If
  // `restoreSession()` hangs (Safari iOS localStorage lockdown,
  // backend slow, network drop), don't sit forever on the "Restoring
  // your profile..." screen. After 5 seconds of stuck bootstrap, drop
  // straight to /welcome with the loading gate released.
  const [bootstrapTimedOut, setBootstrapTimedOut] = useState(false);
  useEffect(() => {
    if (hasTriedSessionRestore && !isRestoringSession) return;
    const t = setTimeout(() => {
      try { console.warn('[Boot/Safari-debug] bootstrap timeout 5s — releasing gate'); } catch {}
      setBootstrapTimedOut(true);
      setBootstrapStage('timeout_5s');
      // Best-effort navigation to /welcome — falls through if router
      // not ready yet, in which case bootstrapTimedOut still gates
      // the loading screen out of the way and renders the app shell.
      try {
        // Use a setTimeout(0) to defer the navigation past the
        // current render and avoid update-during-render warnings.
        setTimeout(() => {
          try { router.replace('/welcome'); } catch (e) {
            try { console.warn('[Boot] /welcome navigation failed:', e); } catch {}
          }
        }, 0);
      } catch {}
    }, 5000);
    return () => clearTimeout(t);
  }, [hasTriedSessionRestore, isRestoringSession, router]);

  // Block rendering until we've tried to restore the session
  // This is the AUTH HYDRATION GATE
  if ((!hasTriedSessionRestore || isRestoringSession) && !bootstrapTimedOut) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={[
          styles.loadingContainer,
          // Only apply maxWidth on desktop web
          Platform.OS === 'web' && !isMobile && styles.desktopMaxWidth
        ]}>
          <ActivityIndicator size="large" color={theme.textSecondary} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>Restoring your profile...</Text>
          <Text style={[styles.buildInfo, { color: theme.textTertiary }]}>v{BUILD_VERSION} • {BUILD_ID}</Text>
          <Text style={[styles.stageInfo, { color: theme.textTertiary }]}>Stage: {bootstrapStage}</Text>
          {/* Hotfix build marker — visible BEFORE app hydration so we
              can verify bundle freshness without depending on routing
              or auth being healthy. */}
          <Text style={[styles.stageInfo, { color: theme.textTertiary }]}>build · {HOTFIX_BUILD_ID}</Text>
        </View>
        {/* Debug viewport overlay for web */}
        {Platform.OS === 'web' && <DebugViewportOverlay />}
      </View>
    );
  }

  return (
    <AppErrorBoundary>
      <BannerProvider>
        <Stack screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: theme.background },
        }} />
        {/* iOS Add to Home Screen Banner (browser only) */}
        {Platform.OS === 'web' && <AddToHomeScreenBanner />}
        {/* Debug viewport overlay for web - always present when debug enabled */}
        {Platform.OS === 'web' && <DebugViewportOverlay />}
      </BannerProvider>
    </AppErrorBoundary>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    // Background color is set dynamically via theme
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
    marginTop: 12,
  },
  buildInfo: {
    fontSize: 10,
    marginTop: 8,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  stageInfo: {
    fontSize: 10,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
});
