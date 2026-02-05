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
 * Welcome Page - The Psychological Orientation Layer
 * 
 * This is not onboarding. This is not marketing.
 * This is a threshold — a permission slip — a tone-setter.
 * 
 * The user should feel:
 * "I'm not being assessed. I'm not being guided. I can just be here."
 */
export default function Welcome() {
  const router = useRouter();
  const { user } = useAppStore();
  
  const hasExistingSession = !!user;

  const handleBeginReflection = () => {
    router.push('/onboarding');
  };

  const handleContinue = () => {
    router.replace('/(tabs)');
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      
      <View style={styles.content}>
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
        
        {/* Buttons */}
        <View style={styles.buttonContainer}>
          {!hasExistingSession && (
            <TouchableOpacity 
              style={styles.primaryButton}
              onPress={handleBeginReflection}
              activeOpacity={0.8}
            >
              <Text style={styles.primaryButtonText}>Begin Reflection</Text>
            </TouchableOpacity>
          )}
          
          {hasExistingSession && (
            <>
              <TouchableOpacity 
                style={styles.primaryButton}
                onPress={handleContinue}
                activeOpacity={0.8}
              >
                <Text style={styles.primaryButtonText}>Continue</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={styles.secondaryButton}
                onPress={handleBeginReflection}
                activeOpacity={0.8}
              >
                <Text style={styles.secondaryButtonText}>Begin New Reflection</Text>
              </TouchableOpacity>
            </>
          )}
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
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
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
    marginBottom: 64,
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
    maxWidth: 280,
    gap: 12,
    marginBottom: 32,
  },
  primaryButton: {
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryButtonText: {
    fontSize: 16,
    color: Colors.text,
    fontWeight: '500',
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    paddingVertical: 12,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  secondaryButtonText: {
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
});
