import React, { useEffect, useState, Component, ErrorInfo, ReactNode } from 'react';
import { Stack } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet, Platform, useWindowDimensions, TouchableOpacity, ScrollView } from 'react-native';
import { useAppStore } from '../store';
import { ThemeProvider, useTheme, LightTheme, DarkTheme } from '../contexts/ThemeContext';
import { ForumContextProvider } from '../contexts/ForumContext';
import { DebugViewportOverlay } from '../components/DebugViewportOverlay';
import { AddToHomeScreenBanner } from '../components/AddToHomeScreenBanner';

// Build info from environment
const BUILD_VERSION = process.env.EXPO_PUBLIC_BUILD_VERSION || 'unknown';
const BUILD_ID = process.env.EXPO_PUBLIC_BUILD_ID || 'unknown';

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
    <ThemeProvider>
      <ThemedRootLayout />
    </ThemeProvider>
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
    setBootstrapStage('restoring_session');
    restoreSession().then(() => {
      setBootstrapStage('ready');
    }).catch((err) => {
      console.error('[RootLayout] Session restore failed:', err);
      setBootstrapStage('error');
    });
  }, []);

  // Block rendering until we've tried to restore the session
  // This is the AUTH HYDRATION GATE
  if (!hasTriedSessionRestore || isRestoringSession) {
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
        </View>
        {/* Debug viewport overlay for web */}
        {Platform.OS === 'web' && <DebugViewportOverlay />}
      </View>
    );
  }

  return (
    <AppErrorBoundary>
      <Stack screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: theme.background },
      }} />
      {/* iOS Add to Home Screen Banner (browser only) */}
      {Platform.OS === 'web' && <AddToHomeScreenBanner />}
      {/* Debug viewport overlay for web - always present when debug enabled */}
      {Platform.OS === 'web' && <DebugViewportOverlay />}
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
