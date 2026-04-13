import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { useAppStore } from '../store';
import { loginUser } from '../services/api';

// Forums redirect target type
type ForumsRedirect = 'create' | 'join' | null;

/**
 * Welcome Page - SINGLE SOURCE OF TRUTH
 * Clean typography-led design - same visual for ALL users
 * Only behavior differs (CTA actions), not UI
 * 
 * ALWAYS DARK MODE - Onboarding should feel calm, safe, intentional
 */
export default function Welcome() {
  const router = useRouter();
  const { setUser, setChart, user, hasCompletedOnboarding } = useAppStore();
  
  // User state for routing decisions
  const isAuthenticated = !!user?.id;
  // Legacy alias for backwards compatibility
  const hasExistingSession = isAuthenticated;
  
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

  // HEADLINE - experiential hook
  const headline = {
    main: "You almost did it again.",
    sub: "You were about to decide—then stopped.\nYou noticed it—then moved past it."
  };

  const handleBeginReflection = () => {
    router.push('/onboarding');
  };

  const handleContinue = () => {
    router.replace('/(tabs)');
  };

  /**
   * SHOW ME BUTTON LOGIC
   * - If authenticated AND onboarding complete → go to home
   * - Otherwise → go to onboarding
   */
  const handleShowMe = () => {
    if (isAuthenticated && hasCompletedOnboarding) {
      console.log('[Welcome] Show Me → authenticated + onboarding complete → going to home');
      router.replace('/(tabs)');
    } else {
      console.log('[Welcome] Show Me → needs onboarding → going to onboarding');
      router.push('/onboarding');
    }
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
    if (!email.trim()) {
      setError('Please enter your email');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      const result = await loginUser(email.trim());
      
      if (result.success && result.user) {
        await setUser(result.user);
        
        if (result.chart) {
          await setChart(result.chart);
        }
        
        // Navigate based on forums redirect or default to main app
        if (forumsRedirect === 'create') {
          router.replace('/forums/create');
        } else if (forumsRedirect === 'join') {
          router.replace('/forums/join');
        } else {
          router.replace('/(tabs)');
        }
      } else {
        setError('Login failed. Please try again.');
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Login failed. Please try again.';
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================
  // LOGIN FORM VIEW
  // ============================================================
  if (showLogin) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: darkTheme.background }]}>
        <StatusBar style="light" />
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

  // ============================================================
  // MAIN WELCOME VIEW - SINGLE UI FOR ALL USERS
  // Only behavior differs (CTA target), not visual design
  // ============================================================
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: darkTheme.background }]}>
      <StatusBar style="light" />
      
      <View style={styles.content}>
        {/* Brand - Framed wordmark with em-dash separators */}
        <View style={styles.brandContainer}>
          <Text style={styles.brandSeparator}>—</Text>
          <Text style={styles.brandText}>The Mirror</Text>
          <Text style={styles.brandSeparator}>—</Text>
        </View>
        
        {/* Headline */}
        <View style={styles.headlineContainer}>
          <Text style={[styles.headline, { color: darkTheme.text }]}>
            {headline.main}
          </Text>
        </View>
        
        {/* Subtext */}
        <View style={styles.subtextContainer}>
          <Text style={[styles.subtext, { color: darkTheme.textSecondary }]}>
            {headline.sub}
          </Text>
        </View>
        
        {/* Bridge line */}
        <View style={styles.bridgeContainer}>
          <Text style={[styles.bridgeLine, { color: darkTheme.textTertiary }]}>
            This isn't about who you are.{'\n'}
            It's about what's happening right now.
          </Text>
        </View>
        
        {/* Primary CTA - Same visual, smart routing */}
        <View style={styles.buttonContainer}>
          <TouchableOpacity 
            style={[styles.primaryButton, { 
              backgroundColor: 'rgba(255, 255, 255, 0.08)',
              borderColor: 'rgba(255, 255, 255, 0.15)' 
            }]}
            onPress={handleShowMe}
            activeOpacity={0.7}
          >
            <Text style={[styles.primaryButtonText, { color: 'rgba(255, 255, 255, 0.9)' }]}>
              Show me
            </Text>
          </TouchableOpacity>
          
          {/* Secondary actions row */}
          <View style={styles.secondaryActionsRow}>
            <TouchableOpacity onPress={handleBeginReflection} activeOpacity={0.6}>
              <Text style={styles.secondaryActionText}>I'm new here</Text>
            </TouchableOpacity>
            <Text style={styles.secondaryActionDivider}>·</Text>
            <TouchableOpacity onPress={() => setShowLogin(true)} activeOpacity={0.6}>
              <Text style={styles.secondaryActionText}>Sign in</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
      
      {/* Footer - Forums */}
      <View style={styles.footerArea}>
        <View style={styles.forumsFooter}>
          <TouchableOpacity style={styles.forumLink} onPress={handleCreateForum} activeOpacity={0.5}>
            <Text style={styles.forumLinkText}>Create Forum</Text>
          </TouchableOpacity>
          <Text style={styles.forumDivider}>·</Text>
          <TouchableOpacity style={styles.forumLink} onPress={handleJoinForum} activeOpacity={0.5}>
            <Text style={styles.forumLinkText}>Join Forum</Text>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
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
  
  // Brand container - framed wordmark
  brandContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 32,
    gap: 12,
  },
  brandText: {
    fontSize: 24,
    fontWeight: '400',
    letterSpacing: 2.5,
    color: 'rgba(255, 255, 255, 0.88)',
    textAlign: 'center',
  },
  brandSeparator: {
    fontSize: 24,
    fontWeight: '300',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  
  // Headline
  headlineContainer: {
    marginBottom: 24,
    paddingHorizontal: 8,
  },
  headline: {
    fontSize: 24,
    fontWeight: '500',
    textAlign: 'center',
    lineHeight: 32,
  },
  
  // Subtext
  subtextContainer: {
    marginBottom: 32,
  },
  subtext: {
    fontSize: 16,
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
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 28,
    fontStyle: 'italic',
  },
  
  // Buttons
  buttonContainer: {
    width: '100%',
    maxWidth: 300,
    gap: 16,
    marginBottom: 32,
    alignItems: 'center',
  },
  primaryButton: {
    borderWidth: 1,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 10,
    alignItems: 'center',
    width: '100%',
  },
  primaryButtonText: {
    fontSize: 17,
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  
  // Secondary actions row
  secondaryActionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 18,
    gap: 12,
  },
  secondaryActionText: {
    fontSize: 16,
    fontWeight: '400',
    color: 'rgba(255, 255, 255, 0.52)',
  },
  secondaryActionDivider: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.3)',
  },
  
  // Footer area
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
    fontSize: 16,
    fontWeight: '400',
    color: 'rgba(255, 255, 255, 0.4)',
  },
  forumDivider: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.25)',
  },
  
  // Login form styles
  header: {
    marginBottom: 48,
  },
  title: {
    fontSize: 28,
    fontWeight: '300',
    letterSpacing: 1,
  },
  loginContainer: {
    width: '100%',
    maxWidth: 320,
    alignItems: 'center',
  },
  loginTitle: {
    fontSize: 22,
    fontWeight: '500',
    marginBottom: 14,
  },
  loginSubtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 25,
  },
  input: {
    width: '100%',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    borderWidth: 1,
    marginBottom: 16,
  },
  errorContainer: {
    width: '100%',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
  },
  textButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  textButtonText: {
    fontSize: 16,
    fontWeight: '400',
  },
});
