import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useLocalSearchParams } from 'expo-router';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';
import { API_BASE_URL, joinUrl } from '../utils/apiBase';
import { parseApiError, GATEWAY_ERROR_CODES } from '../utils/safeErrorParser';

// Import the Onboarding component to render inline
import Onboarding from '../app/onboarding/index';

// Debug mode check
const DEBUG_MIRROR_ENV = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

/**
 * WelcomeGate - Clean Authentication Component
 * With safe error handling and API base visibility
 */
export default function WelcomeGate() {
  const { setUser, setChart } = useAppStore();
  const searchParams = useLocalSearchParams<{ debug?: string }>();
  
  const [showLogin, setShowLogin] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isRetryable, setIsRetryable] = useState(false);
  
  // Debug mode
  const isDebugMode = DEBUG_MIRROR_ENV || searchParams.debug === '1';
  
  // Log API base URL once on mount
  useEffect(() => {
    console.log(`[API_BASE] ${API_BASE_URL}`);
  }, []);

  const handleBeginReflection = () => {
    setShowOnboarding(true);
  };

  const handleShowLogin = () => {
    setShowLogin(true);
  };

  const handleLogin = async () => {
    if (!email.trim()) {
      setError('Please enter your email');
      setIsRetryable(false);
      return;
    }
    
    setIsLoading(true);
    setError('');
    setIsRetryable(false);
    
    try {
      const loginUrl = joinUrl(API_BASE_URL, '/api/users/login');
      
      const res = await fetch(loginUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'omit',
        mode: 'cors',
        body: JSON.stringify({ email: email.trim() }),
      });
      
      const responseText = await res.text();
      
      if (!res.ok) {
        // Use safe error parser
        const parsed = parseApiError({
          response: {
            status: res.status,
            data: responseText,
          }
        });
        
        setError(parsed.message);
        setIsRetryable(parsed.isRetryable);
        return;
      }
      
      const result = JSON.parse(responseText);
      
      if (result.success && result.user) {
        await setUser(result.user);
        if (result.chart) {
          await setChart(result.chart);
        }
      } else {
        throw new Error('Invalid response format');
      }
      
    } catch (err: any) {
      // Use safe error parser for all errors
      const parsed = parseApiError(err);
      setError(parsed.message);
      setIsRetryable(parsed.isRetryable);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    setShowLogin(false);
    setShowOnboarding(false);
    setEmail('');
    setError('');
    setIsRetryable(false);
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
        <ScrollView contentContainerStyle={styles.scrollContent}>
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
                    setIsRetryable(false);
                  }}
                  placeholder="your@email.com"
                  placeholderTextColor={Colors.textTertiary}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                  editable={!isLoading}
                />
                
                {/* Debug: Show API base URL */}
                {isDebugMode && (
                  <Text style={styles.apiDebugText}>
                    API: {API_BASE_URL}
                  </Text>
                )}
                
                {error ? (
                  <View style={styles.errorContainer}>
                    <Text style={styles.errorText}>{error}</Text>
                    {isRetryable && (
                      <Pressable 
                        style={styles.retryButton}
                        onPress={handleLogin}
                        disabled={isLoading}
                      >
                        <Text style={styles.retryButtonText}>Try again</Text>
                      </Pressable>
                    )}
                    {error.includes('No space found') && (
                      <Pressable 
                        style={styles.newUserCTAButton}
                        onPress={() => {
                          setShowLogin(false);
                          setShowOnboarding(true);
                          setError('');
                        }}
                        disabled={isLoading}
                      >
                        <Text style={styles.newUserCTAText}>Start as New User</Text>
                      </Pressable>
                    )}
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
        </ScrollView>
      </SafeAreaView>
    );
  }

  // Default welcome view
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      
      <View style={styles.mainContent}>
        <View style={styles.header}>
          <Text style={styles.title}>Project Mirror</Text>
        </View>
        
        <View style={styles.messageContainer}>
          <Text style={styles.tagline}>A space for noticing.</Text>
          <View style={styles.permissionLines}>
            <Text style={styles.permissionText}>Nothing to fix.</Text>
            <Text style={styles.permissionText}>Nothing to decide.</Text>
          </View>
        </View>
        
        <View style={styles.buttonContainer}>
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
          
          <Pressable 
            style={({ pressed }) => [
              styles.secondaryButton,
              pressed && styles.buttonPressed,
            ]}
            onPress={handleShowLogin}
          >
            <Text style={styles.secondaryButtonText}>Existing User</Text>
            <Text style={styles.secondarySubtext}>Return to your space</Text>
          </Pressable>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    flexGrow: 1,
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
  },
  mainContent: {
    flex: 1,
    paddingHorizontal: 24,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginTop: 40,
    marginBottom: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: '300',
    color: Colors.text,
    letterSpacing: 1,
  },
  messageContainer: {
    alignItems: 'center',
    marginVertical: 30,
  },
  tagline: {
    fontSize: 20,
    fontWeight: '300',
    color: Colors.text,
    fontStyle: 'italic',
    marginBottom: 20,
  },
  permissionLines: {
    alignItems: 'center',
    gap: 4,
  },
  permissionText: {
    fontSize: 15,
    color: Colors.textSecondary,
    fontWeight: '300',
  },
  buttonContainer: {
    gap: 16,
    marginTop: 20,
  },
  primaryButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: Colors.surface,
    fontSize: 17,
    fontWeight: '600',
  },
  buttonSubtext: {
    color: Colors.surface,
    fontSize: 13,
    opacity: 0.8,
    marginTop: 4,
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: Colors.text,
    fontSize: 17,
    fontWeight: '500',
  },
  secondarySubtext: {
    color: Colors.textSecondary,
    fontSize: 13,
    marginTop: 4,
  },
  buttonPressed: {
    opacity: 0.7,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  loginContainer: {
    marginTop: 20,
  },
  loginTitle: {
    fontSize: 24,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 8,
    textAlign: 'center',
  },
  loginSubtitle: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 22,
  },
  input: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 16,
  },
  errorContainer: {
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    color: '#ff6b6b',
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 12,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(255, 107, 107, 0.2)',
    borderRadius: 6,
    alignSelf: 'center',
  },
  retryButtonText: {
    color: '#ff6b6b',
    fontSize: 14,
    fontWeight: '600',
  },
  newUserCTAButton: {
    marginTop: 12,
    paddingVertical: 10,
    paddingHorizontal: 20,
    backgroundColor: Colors.accent,
    borderRadius: 8,
    alignSelf: 'center',
  },
  newUserCTAText: {
    color: Colors.surface,
    fontSize: 14,
    fontWeight: '600',
  },
  apiDebugText: {
    fontSize: 11,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginBottom: 12,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  textButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  textButtonText: {
    color: Colors.textSecondary,
    fontSize: 15,
  },
});
