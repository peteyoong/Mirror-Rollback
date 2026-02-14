import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';

/**
 * BUILD TAG: 2026-02-14-nav-architecture-fix
 * 
 * Welcome Route - For "Start Fresh" scenario
 * 
 * This route is ONLY accessible when a user is already logged in
 * and wants to start fresh or switch accounts.
 * 
 * The initial welcome gate (for unauthenticated users) is handled
 * by WelcomeGate component in _layout.tsx.
 */
export default function Welcome() {
  const router = useRouter();
  const { user, clearUser } = useAppStore();

  const handleContinue = () => {
    // Go back to main app
    router.replace('/(tabs)');
  };

  const handleStartFresh = async () => {
    // Clear user session and go to onboarding
    await clearUser();
    // After clearing user, _layout.tsx will show WelcomeGate
    // which has the login/register options
  };

  const handleSwitchAccount = async () => {
    // Clear current session - WelcomeGate will show login form
    await clearUser();
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>Project Mirror</Text>
        </View>
        
        <View style={styles.messageContainer}>
          <Text style={styles.welcomeBack}>Welcome back{user?.name ? `, ${user.name}` : ''}.</Text>
          <Text style={styles.tagline}>Your reflection space awaits.</Text>
        </View>
        
        <View style={styles.buttonContainer}>
          <TouchableOpacity 
            style={styles.primaryButton}
            onPress={handleContinue}
            activeOpacity={0.8}
          >
            <Text style={styles.primaryButtonText}>Continue</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.secondaryButton}
            onPress={handleStartFresh}
            activeOpacity={0.8}
          >
            <Text style={styles.secondaryButtonText}>Start Fresh</Text>
            <Text style={styles.secondaryButtonSubtext}>Begin a new reflection journey</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.textButton}
            onPress={handleSwitchAccount}
            activeOpacity={0.8}
          >
            <Text style={styles.textButtonText}>Switch Account</Text>
          </TouchableOpacity>
        </View>
      </View>
      
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
    width: '100%',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
    width: '100%',
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
  textButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  textButtonText: {
    fontSize: 14,
    color: Colors.textTertiary,
    fontWeight: '400',
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
});
