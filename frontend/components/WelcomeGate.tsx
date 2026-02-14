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
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';
import { API_BASE_URL, joinUrl } from '../services/api';

// Import the Onboarding component to render inline
import Onboarding from '../app/onboarding/index';

/**
 * BUILD TAG: 2026-02-14-login-debug
 * 
 * WelcomeGate - Authentication Gate with FULL DEBUG INSTRUMENTATION
 * 
 * Features:
 * - Direct fetch() instead of axios for better error messages
 * - Full debug panel showing API URLs, status, response
 * - Ping API button for connectivity testing
 */

// Debug state type
interface DebugInfo {
  apiBaseUrl: string;
  loginUrl: string;
  lastAttemptAt: string;
  lastFetchUrl: string;
  lastHttpStatus: number | null;
  lastResponseText: string;
  lastError: string;
  pingResult: string;
}

export default function WelcomeGate() {
  const { setUser, setChart } = useAppStore();
  
  const [showLogin, setShowLogin] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showDebug, setShowDebug] = useState(true); // Show debug by default for troubleshooting
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Debug state
  const [debug, setDebug] = useState<DebugInfo>({
    apiBaseUrl: API_BASE_URL,
    loginUrl: joinUrl(API_BASE_URL, '/users/login'),
    lastAttemptAt: 'never',
    lastFetchUrl: '',
    lastHttpStatus: null,
    lastResponseText: '',
    lastError: '',
    pingResult: 'not tested',
  });

  const handleBeginReflection = () => {
    console.log('[WELCOME] NewUser onPress - showing onboarding inline');
    setShowOnboarding(true);
  };

  const handleShowLogin = () => {
    console.log('[WELCOME] ExistingUser onPress');
    setShowLogin(true);
  };

  // Ping API for connectivity test
  const handlePingApi = async () => {
    const pingUrl = joinUrl(API_BASE_URL, '/debug/ping');
    console.log('[WelcomeGate] Pinging:', pingUrl);
    
    setDebug(prev => ({ ...prev, pingResult: 'pinging...' }));
    
    try {
      const res = await fetch(pingUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'bypass-tunnel-reminder': 'true',
        },
        credentials: 'omit',
        mode: 'cors',
      });
      
      const text = await res.text();
      setDebug(prev => ({ 
        ...prev, 
        pingResult: `${res.status}: ${text.slice(0, 100)}` 
      }));
    } catch (err: any) {
      setDebug(prev => ({ 
        ...prev, 
        pingResult: `ERROR: ${err.message}` 
      }));
    }
  };

  // Login with full debugging
  const handleLogin = async () => {
    console.log('[WELCOME] SignIn onPress');
    if (!email.trim()) {
      setError('Please enter your email');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    const loginUrl = joinUrl(API_BASE_URL, '/users/login');
    const timestamp = new Date().toLocaleTimeString();
    
    // Update debug info before request
    setDebug(prev => ({
      ...prev,
      lastAttemptAt: timestamp,
      lastFetchUrl: loginUrl,
      lastHttpStatus: null,
      lastResponseText: '',
      lastError: '',
    }));
    
    console.log('[WelcomeGate] Login URL:', loginUrl);
    console.log('[WelcomeGate] Email:', email.trim());
    
    try {
      const res = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'bypass-tunnel-reminder': 'true',
        },
        credentials: 'omit',
        mode: 'cors',
        body: JSON.stringify({ email: email.trim() }),
      });
      
      const responseText = await res.text();
      console.log('[WelcomeGate] Response status:', res.status);
      console.log('[WelcomeGate] Response text:', responseText.slice(0, 500));
      
      // Update debug with response
      setDebug(prev => ({
        ...prev,
        lastHttpStatus: res.status,
        lastResponseText: responseText.slice(0, 300),
      }));
      
      if (!res.ok) {
        // Try to parse error message
        let errorMsg = `HTTP ${res.status}`;
        try {
          const errorData = JSON.parse(responseText);
          errorMsg = errorData.detail || errorMsg;
        } catch {
          errorMsg = responseText.slice(0, 100) || errorMsg;
        }
        throw new Error(errorMsg);
      }
      
      // Parse successful response
      const result = JSON.parse(responseText);
      
      if (result.success && result.user) {
        await setUser(result.user);
        
        if (result.chart) {
          await setChart(result.chart);
        }
        
        console.log('[WelcomeGate] Login successful, user set');
      } else {
        throw new Error('Invalid response format');
      }
      
    } catch (err: any) {
      console.error('[WelcomeGate] Login error:', err);
      
      // Update debug with error
      setDebug(prev => ({
        ...prev,
        lastError: err.message || String(err),
      }));
      
      setError(err.message || 'Login failed. Please try again.');
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

  // Debug panel component
  const DebugPanel = () => (
    <View style={styles.debugPanel}>
      <Pressable 
        style={styles.debugToggle}
        onPress={() => setShowDebug(!showDebug)}
      >
        <Text style={styles.debugToggleText}>
          {showDebug ? '▼ Hide Debug' : '▶ Show Debug'}
        </Text>
      </Pressable>
      
      {showDebug && (
        <View style={styles.debugContent}>
          <Text style={styles.debugLabel}>API_BASE_URL:</Text>
          <Text style={styles.debugValue}>{debug.apiBaseUrl}</Text>
          
          <Text style={styles.debugLabel}>LOGIN_URL:</Text>
          <Text style={styles.debugValue}>{debug.loginUrl}</Text>
          
          <Pressable style={styles.pingButton} onPress={handlePingApi}>
            <Text style={styles.pingButtonText}>🔍 Ping API</Text>
          </Pressable>
          <Text style={styles.debugValue}>Ping: {debug.pingResult}</Text>
          
          <Text style={styles.debugLabel}>Last Attempt:</Text>
          <Text style={styles.debugValue}>{debug.lastAttemptAt}</Text>
          
          <Text style={styles.debugLabel}>Last Fetch URL:</Text>
          <Text style={styles.debugValue}>{debug.lastFetchUrl || 'none'}</Text>
          
          <Text style={styles.debugLabel}>Last HTTP Status:</Text>
          <Text style={styles.debugValue}>{debug.lastHttpStatus ?? 'none'}</Text>
          
          <Text style={styles.debugLabel}>Last Response (300 chars):</Text>
          <Text style={styles.debugValue}>{debug.lastResponseText || 'none'}</Text>
          
          <Text style={styles.debugLabel}>Last Error:</Text>
          <Text style={[styles.debugValue, { color: '#ff6b6b' }]}>
            {debug.lastError || 'none'}
          </Text>
        </View>
      )}
    </View>
  );

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
              
              {/* Debug Panel */}
              <DebugPanel />
              
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
        </ScrollView>
      </SafeAreaView>
    );
  }

  // Default welcome view with two options
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.mainContent}>
          {/* Title */}
          <View style={styles.header}>
            <Text style={styles.title}>Project Mirror</Text>
          </View>
          
          {/* Debug Panel on Welcome Screen too */}
          <DebugPanel />
          
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
              <Text style={styles.secondarySubtext}>Return to your space</Text>
            </Pressable>
          </View>
        </View>
      </ScrollView>
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
  // Debug Panel Styles
  debugPanel: {
    backgroundColor: '#1a1a1a',
    borderRadius: 8,
    marginBottom: 16,
    overflow: 'hidden',
  },
  debugToggle: {
    padding: 10,
    backgroundColor: '#333',
  },
  debugToggleText: {
    color: '#0f0',
    fontSize: 12,
    fontWeight: '600',
  },
  debugContent: {
    padding: 10,
  },
  debugLabel: {
    color: '#888',
    fontSize: 10,
    marginTop: 6,
  },
  debugValue: {
    color: '#0f0',
    fontSize: 10,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 4,
  },
  pingButton: {
    backgroundColor: '#444',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 4,
    alignSelf: 'flex-start',
    marginVertical: 6,
  },
  pingButtonText: {
    color: '#fff',
    fontSize: 12,
  },
  // Message styles
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
  // Button styles
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
  // Login form styles
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
  textButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  textButtonText: {
    color: Colors.textSecondary,
    fontSize: 15,
  },
});
