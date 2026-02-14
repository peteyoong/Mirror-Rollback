import React, { useState } from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';
import { loginUser } from '../services/api';

// Import the Onboarding component to render inline
import Onboarding from '../app/onboarding/index';

/**
 * BUILD TAG: 2026-02-14-onboarding-inline
 * 
 * WelcomeGate - The Authentication Gate Component
 * 
 * FIX: Instead of navigating to /onboarding (which requires Stack),
 * we render the Onboarding component inline using state.
 * 
 * This component handles:
 * 1. New User -> Shows Onboarding inline
 * 2. Existing User -> Shows login form
 */
export default function WelcomeGate() {
  const { setUser, setChart } = useAppStore();
  
  const [showLogin, setShowLogin] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleBeginReflection = () => {
    console.log('[WELCOME] NewUser onPress - showing onboarding inline');
    setShowOnboarding(true);
  };

  const handleShowLogin = () => {
    console.log('[WELCOME] ExistingUser onPress');
    setShowLogin(true);
  };

  const handleLogin = async () => {
    console.log('[WELCOME] SignIn onPress');
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
        
        console.log('[WelcomeGate] Login successful, user set - layout will update');
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Login failed. Please try again.';
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    console.log('[WELCOME] Back onPress');
    setShowLogin(false);
    setShowOnboarding(false);
    setEmail('');
    setError('');
  };

  // Show onboarding flow inline
  if (showOnboarding) {
    return <Onboarding />;
  }

  // Login form view
  if (showLogin) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <View style={styles.content}>
            <View style={styles.header}>
              <Text style={styles.title}>Project Mirror</Text>
            </View>
            
            <View style={styles.loginContainer}>
              <Text style={styles.loginTitle}>Welcome back</Text>
              <Text style={styles.loginSubtitle}>
                Enter the email you used to save your reflection space.
              </Text>
              
              <TextInput
                style={styles.input}
                value={email}
                onChangeText={(text) => {
                  setEmail(text);
                  setError('');
                }}
                placeholder="your@email.com"
                placeholderTextColor={Colors.textTertiary}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
                editable={!isLoading}
              />
              
              {error ? (
                <View style={styles.errorContainer}>
                  <Text style={styles.errorText}>{error}</Text>
                </View>
              ) : null}
              
              <Pressable 
                style={({ pressed }) => [
                  styles.primaryButton,
                  isLoading && styles.buttonDisabled,
                  pressed && styles.buttonPressed,
                ]}
                onPress={handleLogin}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator size="small" color={Colors.text} />
                ) : (
                  <Text style={styles.primaryButtonText}>Sign In</Text>
                )}
              </Pressable>
              
              <Pressable 
                style={({ pressed }) => [
                  styles.textButton,
                  pressed && styles.buttonPressed,
                ]}
                onPress={handleBack}
                disabled={isLoading}
              >
                <Text style={styles.textButtonText}>Back</Text>
              </Pressable>
            </View>
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    );
  }

  // Default welcome view with two options
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      
      <View style={styles.mainContent}>
        {/* Title */}
        <View style={styles.header}>
          <Text style={styles.title}>Project Mirror</Text>
        </View>
        
        {/* Core Message */}
        <View style={styles.messageContainer}>
          <Text style={styles.tagline}>A space for noticing.</Text>
          <View style={styles.permissionLines}>
            <Text style={styles.permissionText}>Nothing to fix.</Text>
            <Text style={styles.permissionText}>Nothing to decide.</Text>
          </View>
        </View>
        
        {/* Two Options */}
        <View style={styles.buttonContainer}>
          {/* New User */}
          <Pressable 
            style={({ pressed }) => [
              styles.primaryButton,
              pressed && styles.buttonPressed,
            ]}
            onPress={handleBeginReflection}
          >
            <Text style={styles.primaryButtonText}>New User</Text>
            <Text style={styles.buttonSubtext}>Begin your reflection journey</Text>
          </Pressable>
          
          {/* Existing User */}
          <Pressable 
            style={({ pressed }) => [
              styles.secondaryButton,
              pressed && styles.buttonPressed,
            ]}
            onPress={handleShowLogin}
          >
            <Text style={styles.secondaryButtonText}>Existing User</Text>
            <Text style={styles.secondaryButtonSubtext}>Sign in with email</Text>
          </Pressable>
        </View>
        
        {/* Exit Permission */}
        <Text style={styles.exitPermission}>You can leave at any time.</Text>
      </View>
      
      {/* Footer Philosophy Line */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          You don't have to do anything with what you notice.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  keyboardView: {
    flex: 1,
  },
  mainContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
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
    // Ensure buttons are above any decorative layers
    zIndex: 10,
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
  buttonPressed: {
    opacity: 0.7,
    transform: [{ scale: 0.98 }],
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
  // DEBUG: TAPPED overlay
  tappedOverlay: {
    position: 'absolute',
    top: 100,
    left: 20,
    right: 20,
    backgroundColor: '#00FF00',
    padding: 20,
    borderRadius: 12,
    zIndex: 9999,
    alignItems: 'center',
  },
  tappedText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000',
  },
  tappedSubtext: {
    fontSize: 14,
    color: '#333',
    marginTop: 4,
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
});
