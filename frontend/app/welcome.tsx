import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  useWindowDimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useAppStore } from '../store';
import { useTheme } from '../contexts/ThemeContext';
import { loginUser } from '../services/api';
import { Colors } from '../constants/colors';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Svg, { Circle, Line, Path } from 'react-native-svg';

// Forums redirect target type
type ForumsRedirect = 'create' | 'join' | null;

// Build info - bump this to force cache refresh
const BUILD_VERSION = '2.2.0';
const BUILD_ID = 'icon-fix-v4';
const BUILD_DATE = '2026-03-10';

// Debug mode - set to true to show debug panel
const SHOW_DEBUG_PANEL = false; // Disabled for production

/**
 * Welcome Page - The Psychological Orientation Layer
 * ALWAYS DARK MODE - Onboarding should feel calm, safe, intentional
 */
export default function Welcome() {
  const router = useRouter();
  const params = useLocalSearchParams();
  // Force dark theme for onboarding - ignore user preference
  const { setUser, setChart } = useAppStore();
  
  // Dark onboarding colors (hardcoded)
  const darkTheme = {
    background: '#0B0B0C',
    surface: '#1C1C1E',
    surfaceElevated: '#2C2C2E',
    text: '#F0EDE8',
    textSecondary: '#B5B2AD',
    textTertiary: '#8E8E93',
    border: '#2C2C2E',
    accent: '#EAE3D9',
    buttonPrimaryBg: '#EAE3D9',
    buttonPrimaryText: '#1C1C1E',
    error: '#EF5350',
  };
  
  const [showLogin, setShowLogin] = useState(false);
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [forumsRedirect, setForumsRedirect] = useState<ForumsRedirect>(null);
  const [debugInfo, setDebugInfo] = useState<{
    storedTheme: string | null;
    effectiveTheme: string;
    platform: string;
    userAgent: string;
  } | null>(null);
  
  const { user } = useAppStore();
  const hasExistingSession = !!user;

  // Load debug info on mount
  useEffect(() => {
    const loadDebugInfo = async () => {
      try {
        const storedTheme = await AsyncStorage.getItem('@mirror_theme_mode');
        setDebugInfo({
          storedTheme,
          effectiveTheme: 'dark', // Always dark for onboarding
          platform: Platform.OS,
          userAgent: Platform.OS === 'web' ? (typeof navigator !== 'undefined' ? navigator.userAgent.substring(0, 50) : 'N/A') : 'native',
        });
      } catch (e) {
        console.log('[Debug] Failed to load debug info');
      }
    };
    loadDebugInfo();
  }, []);

  // Debug panel component
  const renderDebugPanel = () => {
    if (!SHOW_DEBUG_PANEL || !debugInfo) return null;
    
    return (
      <View style={[styles.debugPanel, { backgroundColor: darkTheme.surfaceElevated, borderColor: darkTheme.border }]}>
        <Text style={[styles.debugTitle, { color: darkTheme.accent }]}>🔧 Theme Debug</Text>
        <Text style={[styles.debugText, { color: darkTheme.textSecondary }]}>
          Stored: {debugInfo.storedTheme || 'none'}
        </Text>
        <Text style={[styles.debugText, { color: darkTheme.textSecondary }]}>
          Mode: dark → {debugInfo.effectiveTheme}
        </Text>
        <Text style={[styles.debugText, { color: darkTheme.textSecondary }]}>
          Platform: {debugInfo.platform}
        </Text>
        <Text style={[styles.debugText, { color: darkTheme.textTertiary, fontSize: 10 }]}>
          {debugInfo.userAgent}
        </Text>
        <Text style={[styles.debugText, { color: darkTheme.accent, fontSize: 10 }]}>
          Build: {BUILD_VERSION} • {BUILD_ID}
        </Text>
      </View>
    );
  };

  const handleBeginReflection = () => {
    router.push('/onboarding');
  };

  const handleContinue = () => {
    router.replace('/(tabs)');
  };

  // Forums quick access handlers
  const handleCreateForum = () => {
    if (hasExistingSession) {
      router.push('/forums/create');
    } else {
      setForumsRedirect('create');
      setShowLogin(true);
    }
  };

  const handleJoinForum = () => {
    if (hasExistingSession) {
      router.push('/forums/join');
    } else {
      setForumsRedirect('join');
      setShowLogin(true);
    }
  };

  const handleLogin = async () => {
    console.log('[Login] handleLogin called with email:', email);
    if (!email.trim()) {
      setError('Please enter your email');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      console.log('[Login] Calling loginUser API...');
      const result = await loginUser(email.trim());
      console.log('[Login] API response:', result?.success, result?.user?.id);
      
      if (result.success && result.user) {
        // Set user in store
        console.log('[Login] Setting user in store...');
        await setUser(result.user);
        
        // Set chart if available
        if (result.chart) {
          console.log('[Login] Setting chart...');
          await setChart(result.chart);
        }
        
        // Navigate based on forums redirect or default to main app
        console.log('[Login] Navigating to main app...');
        if (forumsRedirect === 'create') {
          router.replace('/forums/create');
        } else if (forumsRedirect === 'join') {
          router.replace('/forums/join');
        } else {
          router.replace('/(tabs)');
        }
      } else {
        console.log('[Login] Login failed - no success or user:', result);
        setError('Login failed. Please try again.');
      }
    } catch (err: any) {
      console.error('[Login] Error:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Login failed. Please try again.';
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  // HEADLINE CONFIGURATION - Must be defined before hasExistingSession block
  // A: "You keep ending up in the same place."
  // B: "Something keeps repeating."
  // C: "You've felt this before."
  // D: "You almost did it again." (experiential hook)
  const HEADLINE_VERSION = 'D';
  
  const headlines = {
    'A': {
      main: "You keep ending up in the same place.",
      sub: "The loop you notice but can't name.\nThe pattern that runs before you catch it."
    },
    'B': {
      main: "Something keeps repeating.",
      sub: "A feeling. A reaction. A choice you've made before.\nYou've noticed—but it hasn't stopped."
    },
    'C': {
      main: "You've felt this before.",
      sub: "The hesitation. The pull. The thing you keep circling back to.\nIt's not random."
    },
    'D': {
      main: "You almost did it again.",
      sub: "You were about to decide—then stopped.\nYou noticed it—then moved past it."
    }
  };
  
  const currentHeadline = headlines[HEADLINE_VERSION];

  // If user is already logged in, show the same new entry screen
  // but with a simpler flow (tap goes directly to app)
  if (hasExistingSession) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: darkTheme.background }]}>
        <StatusBar style={'light'} />
        
        <View style={styles.content}>
          {/* The Mirror – Final Mark */}
          <View style={styles.apertureContainer}>
            {/* Extremely subtle glow */}
            <View style={styles.apertureGlow} />
            
            {/* Final Symbol: Circle + Vertical Line only */}
            <Svg width={88} height={88} viewBox="0 0 100 100" style={{ opacity: 0.9 }}>
              {/* Outer circle */}
              <Circle
                cx={50}
                cy={50}
                r={38}
                stroke="#EAE6DF"
                strokeWidth={1.5}
                fill="none"
              />
              {/* Vertical center line */}
              <Line
                x1={50}
                y1={12}
                x2={50}
                y2={88}
                stroke="#EAE6DF"
                strokeWidth={1.5}
              />
            </Svg>
          </View>
          
          {/* Wordmark - below logo, above headline */}
          <Text style={styles.apertureWordmark}>The Mirror</Text>
          
          {/* Headline */}
          <View style={styles.headlineContainer}>
            <Text style={[styles.headline, { color: darkTheme.text }]}>
              {currentHeadline.main}
            </Text>
          </View>
          
          {/* Subtext */}
          <View style={styles.subtextContainer}>
            <Text style={[styles.subtext, { color: darkTheme.textSecondary }]}>
              {currentHeadline.sub}
            </Text>
          </View>
          
          {/* Bridge line */}
          <View style={styles.bridgeContainer}>
            <Text style={[styles.bridgeLine, { color: darkTheme.textTertiary }]}>
              This isn't about who you are.{'\n'}
              It's about what's happening right now.
            </Text>
          </View>
          
          {/* Primary CTA */}
          <View style={styles.buttonContainer}>
            <TouchableOpacity 
              style={[styles.primaryButton, { 
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                borderColor: 'rgba(255, 255, 255, 0.15)' 
              }]}
              onPress={handleContinue}
              activeOpacity={0.7}
            >
              <Text style={[styles.primaryButtonText, { color: 'rgba(255, 255, 255, 0.9)' }]}>Show me</Text>
            </TouchableOpacity>
          </View>
        </View>
        
        {/* Footer - subtle, understated */}
        <View style={styles.footerArea}>
          <View style={styles.forumsFooter}>
            <TouchableOpacity style={styles.forumLink} onPress={handleCreateForum} activeOpacity={0.6}>
              <Text style={[styles.forumLinkText, { color: 'rgba(255, 255, 255, 0.35)' }]}>Create Forum</Text>
            </TouchableOpacity>
            <Text style={[styles.forumDivider, { color: 'rgba(255, 255, 255, 0.2)' }]}>·</Text>
            <TouchableOpacity style={styles.forumLink} onPress={handleJoinForum} activeOpacity={0.6}>
              <Text style={[styles.forumLinkText, { color: 'rgba(255, 255, 255, 0.35)' }]}>Join Forum</Text>
            </TouchableOpacity>
          </View>
          {/* Hidden verification marker */}
          <Text style={{ fontSize: 9, color: 'rgba(255, 255, 255, 0.15)', marginTop: 12 }}>
            welcome.tsx • existing-session • {BUILD_VERSION}
          </Text>
        </View>
        
        {renderDebugPanel()}
      </SafeAreaView>
    );
  }

  // Login form view
  if (showLogin) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: darkTheme.background }]}>
        <StatusBar style={'light'} />
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <View style={styles.content}>
            <View style={styles.header}>
              <Text style={[styles.title, { color: darkTheme.text }]}>Project Mirror</Text>
            </View>
            
            <View style={styles.loginContainer}>
              <Text style={[styles.loginTitle, { color: darkTheme.text }]}>Welcome back</Text>
              <Text style={[styles.loginSubtitle, { color: darkTheme.textSecondary }]}>
                Enter the email you used to save your reflection space.
              </Text>
              
              <TextInput
                style={[styles.input, { 
                  backgroundColor: darkTheme.surface,
                  borderColor: darkTheme.border,
                  color: darkTheme.text 
                }]}
                value={email}
                onChangeText={(text) => {
                  setEmail(text);
                  setError('');
                }}
                placeholder="your@email.com"
                placeholderTextColor={darkTheme.textTertiary}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
                editable={!isLoading}
              />
              
              {error ? (
                <View style={[styles.errorContainer, { backgroundColor: darkTheme.error + '20' }]}>
                  <Text style={[styles.errorText, { color: darkTheme.error }]}>{error}</Text>
                </View>
              ) : null}
              
              <TouchableOpacity 
                style={[
                  styles.primaryButton, 
                  { 
                    backgroundColor: darkTheme.buttonPrimaryBg,
                    borderColor: darkTheme.border 
                  },
                  isLoading && styles.buttonDisabled
                ]}
                onPress={handleLogin}
                disabled={isLoading}
                activeOpacity={0.8}
              >
                {isLoading ? (
                  <ActivityIndicator size="small" color={darkTheme.buttonPrimaryText} />
                ) : (
                  <Text style={[styles.primaryButtonText, { color: darkTheme.buttonPrimaryText }]}>Enter</Text>
                )}
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={styles.textButton}
                onPress={() => {
                  setShowLogin(false);
                  setEmail('');
                  setError('');
                }}
                disabled={isLoading}
                activeOpacity={0.8}
              >
                <Text style={[styles.textButtonText, { color: darkTheme.textTertiary }]}>Back</Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    );
  }

  // Default welcome view - High-conversion entry experience
  // Default welcome view - no session
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: darkTheme.background }]}>
      <StatusBar style={'light'} />
      
      {/* TEMP MARKER 1: Visible label at top */}
      <View style={{ position: 'absolute', top: 60, left: 0, right: 0, zIndex: 9999, alignItems: 'center', backgroundColor: '#FF0000', padding: 8 }}>
        <Text style={{ color: '#FFFFFF', fontSize: 16, fontWeight: 'bold' }}>WELCOME V2 LIVE</Text>
      </View>
      
      {/* TEMP MARKER 2: Bright pulse circle */}
      <View style={styles.pulseContainer}>
        <View style={[styles.pulseRing, { borderColor: '#00FF00', borderWidth: 3 }]} />
        <View style={[styles.pulseCore, { backgroundColor: '#00FF00' }]} />
      </View>
      
      <View style={styles.content}>
        {/* Logo / Wordmark - Premium minimal treatment */}
        <View style={styles.logoContainer}>
          {/* Single thin circle - minimal lens/portal motif */}
          <View style={[styles.logoCircle, { borderColor: darkTheme.textTertiary }]} />
          <Text style={[styles.logoText, { color: darkTheme.text }]}>The Mirror</Text>
        </View>
        
        {/* Headline - something already happening */}
        <View style={styles.headlineContainer}>
          <Text style={[styles.headline, { color: darkTheme.text }]}>
            {currentHeadline.main}
          </Text>
        </View>
        
        {/* Subtext - real behavior description */}
        <View style={styles.subtextContainer}>
          <Text style={[styles.subtext, { color: darkTheme.textSecondary }]}>
            {currentHeadline.sub}
          </Text>
        </View>
        
        {/* Bridge line - what Mirror does */}
        <View style={styles.bridgeContainer}>
          <Text style={[styles.bridgeLine, { color: darkTheme.textTertiary }]}>
            This isn't about who you are.{'\n'}
            It's about what's happening right now.
          </Text>
        </View>
        
        {/* CTA Buttons - Clear paths for new vs returning */}
        <View style={styles.buttonContainer}>
          {/* TEMP MARKER 3: Primary CTA with V2 */}
          <TouchableOpacity 
            style={[styles.primaryButton, { 
              backgroundColor: '#FF6B00',
              borderColor: '#FF6B00' 
            }]}
            onPress={handleBeginReflection}
            activeOpacity={0.8}
          >
            <Text style={[styles.primaryButtonText, { color: '#FFFFFF' }]}>SHOW ME V2</Text>
          </TouchableOpacity>
          
          {/* Secondary CTAs - Both visible for new users */}
          <View style={styles.secondaryCtaRow}>
            <TouchableOpacity 
              style={styles.secondaryCta}
              onPress={handleBeginReflection}
              activeOpacity={0.8}
            >
              <Text style={[styles.secondaryCtaText, { color: darkTheme.textSecondary }]}>I'm new here</Text>
            </TouchableOpacity>
            
            <Text style={[styles.ctaDivider, { color: darkTheme.textTertiary }]}>·</Text>
            
            <TouchableOpacity 
              style={styles.secondaryCta}
              onPress={() => setShowLogin(true)}
              activeOpacity={0.8}
            >
              <Text style={[styles.secondaryCtaText, { color: darkTheme.textSecondary }]}>Sign in</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
      
      {/* Footer area - Forums moved here, reduced prominence */}
      <View style={styles.footerArea}>
        {/* Forums - Secondary/Optional */}
        <View style={styles.forumsFooter}>
          <TouchableOpacity 
            style={styles.forumLink}
            onPress={handleCreateForum}
            activeOpacity={0.7}
          >
            <Text style={[styles.forumLinkText, { color: darkTheme.textTertiary }]}>Create Forum</Text>
          </TouchableOpacity>
          <Text style={[styles.forumDivider, { color: darkTheme.textTertiary }]}>·</Text>
          <TouchableOpacity 
            style={styles.forumLink}
            onPress={handleJoinForum}
            activeOpacity={0.7}
          >
            <Text style={[styles.forumLinkText, { color: darkTheme.textTertiary }]}>Join Forum</Text>
          </TouchableOpacity>
        </View>
        
        {/* TEMP MARKER 4: Build info with WELCOME-V2 */}
        <Text style={[styles.buildInfo, { color: '#FF6B00' }]}>WELCOME-V2 • v{BUILD_VERSION} • {BUILD_ID}</Text>
      </View>
      
      {/* Debug Panel */}
      {renderDebugPanel()}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    width: '100%',
  },
  keyboardView: {
    flex: 1,
    width: '100%',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 28,
    width: '100%',
  },
  
  // Pulse animation container
  pulseContainer: {
    position: 'absolute',
    top: '15%',
    left: '50%',
    transform: [{ translateX: -100 }],
    width: 200,
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
  },
  pulseRing: {
    position: 'absolute',
    width: 180,
    height: 180,
    borderRadius: 90,
    borderWidth: 1,
  },
  pulseCore: {
    width: 120,
    height: 120,
    borderRadius: 60,
  },
  
  // Aperture Mark - The Mirror logo
  apertureContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
    position: 'relative',
  },
  apertureGlow: {
    position: 'absolute',
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: 'rgba(234, 230, 223, 0.04)',
  },
  apertureWordmark: {
    fontSize: 14,
    fontWeight: '400',
    letterSpacing: 1.2,
    color: 'rgba(255, 255, 255, 0.6)',
    textAlign: 'center',
    marginBottom: 16,
  },
  
  // Legacy logo styles (for non-session view)
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logoCircle: {
    width: 24,
    height: 24,
    borderWidth: 1,
    borderRadius: 12,
    marginBottom: 14,
    opacity: 0.6,
  },
  logoText: {
    fontSize: 18,
    fontWeight: '300',
    letterSpacing: 2,
  },
  
  // Headline
  headlineContainer: {
    marginBottom: 24,
    paddingHorizontal: 8,
  },
  headline: {
    fontSize: 24,
    fontWeight: '500',
    color: Colors.text,
    textAlign: 'center',
    lineHeight: 32,
  },
  
  // Subtext
  subtextContainer: {
    marginBottom: 32,
  },
  subtext: {
    fontSize: 16,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 26,
    fontWeight: '400',
  },
  
  // Bridge line
  bridgeContainer: {
    marginBottom: 48,
    paddingHorizontal: 12,
  },
  bridgeLine: {
    fontSize: 14,
    color: Colors.textTertiary,
    textAlign: 'center',
    lineHeight: 24,
    fontStyle: 'italic',
  },
  
  // Legacy styles kept for login flow
  header: {
    marginBottom: 48,
  },
  title: {
    fontSize: 28,
    fontWeight: '300',
    color: Colors.text,
    letterSpacing: 1,
  },
  messageContainer: {
    alignItems: 'center',
    marginBottom: 48,
  },
  welcomeBack: {
    fontSize: 20,
    color: Colors.text,
    fontWeight: '500',
    marginBottom: 8,
  },
  tagline: {
    fontSize: 18,
    color: Colors.textSecondary,
    marginBottom: 24,
    fontWeight: '400',
  },
  permissionLines: {
    alignItems: 'center',
    gap: 8,
  },
  permissionText: {
    fontSize: 15,
    color: Colors.textTertiary,
    fontWeight: '400',
  },
  buttonContainer: {
    width: '100%',
    maxWidth: 300,
    gap: 16,
    marginBottom: 32,
    alignItems: 'center',
  },
  primaryButton: {
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 10,
    alignItems: 'center',
    width: '100%',
  },
  primaryButtonText: {
    fontSize: 17,
    color: Colors.text,
    fontWeight: '600',
  },
  secondaryCtaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  secondaryCta: {
    paddingVertical: 8,
    paddingHorizontal: 4,
  },
  secondaryCtaText: {
    fontSize: 14,
    fontWeight: '400',
  },
  ctaDivider: {
    fontSize: 14,
  },
  buttonSubtext: {
    fontSize: 13,
    color: Colors.textTertiary,
    marginTop: 4,
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 10,
    alignItems: 'center',
  },
  secondaryButtonText: {
    fontSize: 15,
    color: Colors.textSecondary,
    fontWeight: '400',
  },
  secondaryButtonSubtext: {
    fontSize: 13,
    color: Colors.textTertiary,
    marginTop: 4,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  textButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  textButtonText: {
    fontSize: 14,
    color: Colors.textTertiary,
    fontWeight: '400',
  },
  exitPermission: {
    fontSize: 13,
    color: Colors.textTertiary,
    opacity: 0.7,
  },
  // Footer area with forums
  footerArea: {
    paddingBottom: 24,
    paddingHorizontal: 32,
    alignItems: 'center',
    gap: 12,
  },
  forumsFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  forumLink: {
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  forumLinkText: {
    fontSize: 12,
    fontWeight: '400',
  },
  forumDivider: {
    fontSize: 12,
    opacity: 0.5,
  },
  footer: {
    paddingBottom: 32,
    paddingHorizontal: 32,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: Colors.textTertiary,
    opacity: 0.5,
    textAlign: 'center',
  },
  // Login form styles
  loginContainer: {
    width: '100%',
    maxWidth: 320,
    alignItems: 'center',
  },
  loginTitle: {
    fontSize: 22,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 8,
  },
  loginSubtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 20,
  },
  input: {
    width: '100%',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 16,
  },
  errorContainer: {
    width: '100%',
    backgroundColor: Colors.error + '20',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 14,
    color: Colors.error,
    textAlign: 'center',
  },
  buildInfo: {
    fontSize: 10,
    color: Colors.textTertiary,
    marginTop: 8,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  // Debug panel styles
  debugPanel: {
    position: 'absolute',
    bottom: 100,
    left: 16,
    right: 16,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  debugTitle: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
  },
  debugText: {
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 4,
  },
  // Forums quick access styles
  forumsSection: {
    width: '100%',
    maxWidth: 300,
    marginTop: 24,
    paddingTop: 24,
    borderTopWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  forumsSectionLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.5,
    marginBottom: 12,
  },
  forumsButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  forumButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
  },
  forumButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
});
