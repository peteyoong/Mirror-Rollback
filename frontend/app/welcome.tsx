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
import { useRouter } from 'expo-router';
import { useAppStore } from '../store';
import { useTheme } from '../contexts/ThemeContext';
import { loginUser } from '../services/api';
import { Colors } from '../constants/colors';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Build info - bump this to force cache refresh
const BUILD_VERSION = '2.1.0';
const BUILD_ID = 'theme-fix-v3';
const BUILD_DATE = '2026-03-10';

// Debug mode - set to true to show debug panel
const SHOW_DEBUG_PANEL = __DEV__ || true; // Always show for now to debug production

/**
 * Welcome Page - The Psychological Orientation Layer
 * Now with full dark mode support
 */
export default function Welcome() {
  const router = useRouter();
  const { theme, isDark } = useTheme();
  const { user, setUser, setChart } = useAppStore();
  
  const [showLogin, setShowLogin] = useState(false);
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const hasExistingSession = !!user;

  const handleBeginReflection = () => {
    router.push('/onboarding');
  };

  const handleContinue = () => {
    router.replace('/(tabs)');
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
        // Set user in store
        await setUser(result.user);
        
        // Set chart if available
        if (result.chart) {
          await setChart(result.chart);
        }
        
        // Navigate to main app
        router.replace('/(tabs)');
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Login failed. Please try again.';
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  // If user is already logged in, show continue option
  if (hasExistingSession) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        
        <View style={styles.content}>
          <View style={styles.header}>
            <Text style={[styles.title, { color: theme.text }]}>Project Mirror</Text>
          </View>
          
          <View style={styles.messageContainer}>
            <Text style={[styles.welcomeBack, { color: theme.text }]}>Welcome back{user?.name ? `, ${user.name}` : ''}.</Text>
            <Text style={[styles.tagline, { color: theme.textSecondary }]}>Your reflection space awaits.</Text>
          </View>
          
          <View style={styles.buttonContainer}>
            <TouchableOpacity 
              style={[styles.primaryButton, { 
                backgroundColor: theme.buttonPrimaryBg,
                borderColor: theme.border 
              }]}
              onPress={handleContinue}
              activeOpacity={0.8}
            >
              <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>Continue</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.textButton, { borderColor: theme.border }]}
              onPress={handleBeginReflection}
              activeOpacity={0.8}
            >
              <Text style={[styles.textButtonText, { color: theme.textTertiary }]}>Start Fresh</Text>
            </TouchableOpacity>
          </View>
        </View>
        
        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: theme.textTertiary }]}>
            You don't have to do anything with what you notice.
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  // Login form view
  if (showLogin) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <View style={styles.content}>
            <View style={styles.header}>
              <Text style={[styles.title, { color: theme.text }]}>Project Mirror</Text>
            </View>
            
            <View style={styles.loginContainer}>
              <Text style={[styles.loginTitle, { color: theme.text }]}>Welcome back</Text>
              <Text style={[styles.loginSubtitle, { color: theme.textSecondary }]}>
                Enter the email you used to save your reflection space.
              </Text>
              
              <TextInput
                style={[styles.input, { 
                  backgroundColor: theme.surface,
                  borderColor: theme.border,
                  color: theme.text 
                }]}
                value={email}
                onChangeText={(text) => {
                  setEmail(text);
                  setError('');
                }}
                placeholder="your@email.com"
                placeholderTextColor={theme.textTertiary}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
                editable={!isLoading}
              />
              
              {error ? (
                <View style={[styles.errorContainer, { backgroundColor: theme.error + '20' }]}>
                  <Text style={[styles.errorText, { color: theme.error }]}>{error}</Text>
                </View>
              ) : null}
              
              <TouchableOpacity 
                style={[
                  styles.primaryButton, 
                  { 
                    backgroundColor: theme.buttonPrimaryBg,
                    borderColor: theme.border 
                  },
                  isLoading && styles.buttonDisabled
                ]}
                onPress={handleLogin}
                disabled={isLoading}
                activeOpacity={0.8}
              >
                {isLoading ? (
                  <ActivityIndicator size="small" color={theme.buttonPrimaryText} />
                ) : (
                  <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>Sign In</Text>
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
                <Text style={[styles.textButtonText, { color: theme.textTertiary }]}>Back</Text>
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    );
  }

  // Default welcome view with two options
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      
      <View style={styles.content}>
        {/* Title */}
        <View style={styles.header}>
          <Text style={[styles.title, { color: theme.text }]}>Project Mirror</Text>
        </View>
        
        {/* Core Message */}
        <View style={styles.messageContainer}>
          <Text style={[styles.tagline, { color: theme.textSecondary }]}>A space for noticing.</Text>
          <View style={styles.permissionLines}>
            <Text style={[styles.permissionText, { color: theme.textTertiary }]}>Nothing to fix.</Text>
            <Text style={[styles.permissionText, { color: theme.textTertiary }]}>Nothing to decide.</Text>
          </View>
        </View>
        
        {/* Two Options */}
        <View style={styles.buttonContainer}>
          {/* New User */}
          <TouchableOpacity 
            style={[styles.primaryButton, { 
              backgroundColor: theme.buttonPrimaryBg,
              borderColor: theme.border 
            }]}
            onPress={handleBeginReflection}
            activeOpacity={0.8}
          >
            <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>New User</Text>
            <Text style={[styles.buttonSubtext, { color: theme.textTertiary }]}>Begin your reflection journey</Text>
          </TouchableOpacity>
          
          {/* Existing User */}
          <TouchableOpacity 
            style={[styles.secondaryButton, { borderColor: theme.border }]}
            onPress={() => setShowLogin(true)}
            activeOpacity={0.8}
          >
            <Text style={[styles.secondaryButtonText, { color: theme.textSecondary }]}>Existing User</Text>
            <Text style={[styles.secondaryButtonSubtext, { color: theme.textTertiary }]}>Sign in with email</Text>
          </TouchableOpacity>
        </View>
        
        {/* Exit Permission */}
        <Text style={[styles.exitPermission, { color: theme.textTertiary }]}>You can leave at any time.</Text>
      </View>
      
      {/* Footer Philosophy Line */}
      <View style={styles.footer}>
        <Text style={[styles.footerText, { color: theme.textTertiary }]}>
          You don't have to do anything with what you notice.
        </Text>
        <Text style={[styles.buildInfo, { color: theme.textTertiary }]}>v{BUILD_VERSION} • {BUILD_ID}</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    // Full width - no centering that causes overflow
    width: '100%',
  },
  keyboardView: {
    flex: 1,
    width: '100%',
    // Remove maxWidth - handled dynamically in component
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24, // Reduced from 32 to prevent overflow
    width: '100%',
    // Remove maxWidth - handled dynamically in component
  },
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
  },
  primaryButton: {
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingVertical: 18,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryButtonText: {
    fontSize: 17,
    color: Colors.text,
    fontWeight: '600',
  },
  buttonSubtext: {
    fontSize: 13,
    color: Colors.textTertiary,
    marginTop: 4,
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: Colors.border,
    paddingVertical: 18,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  secondaryButtonText: {
    fontSize: 17,
    color: Colors.textSecondary,
    fontWeight: '500',
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
});
