import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';
import { getDailyFocus, DailyFocusResponse } from '../services/api';

/**
 * Today's Mirror - First-time transition screen
 * 
 * Shows after onboarding completes, before the main app.
 * Surfaces the daily context with the Mirror philosophy:
 * - Non-prescriptive
 * - Dismissible
 * - Optional
 */
export default function TodaysMirror() {
  const router = useRouter();
  const { user } = useAppStore();
  const [dailyFocus, setDailyFocus] = useState<DailyFocusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchDailyFocus = async () => {
      if (!user?.id) {
        setLoading(false);
        return;
      }
      
      try {
        const focus = await getDailyFocus(user.id);
        setDailyFocus(focus);
      } catch (err) {
        console.error('Failed to fetch daily focus:', err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };
    
    fetchDailyFocus();
  }, [user?.id]);

  const handleContinue = () => {
    router.replace('/(tabs)');
  };

  // If no user, redirect to welcome
  if (!user) {
    router.replace('/welcome');
    return null;
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      
      <View style={styles.content}>
        {/* Title */}
        <View style={styles.header}>
          <Text style={styles.title}>Today's Mirror</Text>
        </View>
        
        {/* Daily Focus Content */}
        <View style={styles.focusContainer}>
          {loading ? (
            <ActivityIndicator size="small" color={Colors.textTertiary} />
          ) : (
            <>
              {/* Ambient Line - Always shown */}
              <Text style={styles.ambientLine}>
                {dailyFocus?.ambient_line || "Something to notice today: where your attention naturally rests."}
              </Text>
              
              {/* Context Block - Only if context exists */}
              {dailyFocus?.context && (
                <View style={styles.contextBlock}>
                  <Text style={styles.contextLine}>
                    Today's mirror may relate more to {dailyFocus.context}.
                  </Text>
                  <Text style={styles.contextDismiss}>
                    Or it may not — see if this fits.
                  </Text>
                </View>
              )}
            </>
          )}
        </View>
        
        {/* Continue Button */}
        <View style={styles.buttonContainer}>
          <TouchableOpacity 
            style={styles.continueButton}
            onPress={handleContinue}
            activeOpacity={0.8}
          >
            <Text style={styles.continueButtonText}>Continue</Text>
          </TouchableOpacity>
        </View>
      </View>
      
      {/* Footer */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          You can return to this anytime.
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
    fontSize: 24,
    fontWeight: '300',
    color: Colors.text,
    letterSpacing: 0.5,
  },
  focusContainer: {
    alignItems: 'center',
    marginBottom: 64,
    paddingHorizontal: 16,
  },
  ambientLine: {
    fontSize: 17,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 26,
    fontWeight: '400',
  },
  contextBlock: {
    marginTop: 32,
    alignItems: 'center',
  },
  contextLine: {
    fontSize: 15,
    color: Colors.text,
    textAlign: 'center',
    lineHeight: 24,
    fontWeight: '400',
  },
  contextDismiss: {
    fontSize: 14,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },
  buttonContainer: {
    width: '100%',
    maxWidth: 280,
  },
  continueButton: {
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  continueButtonText: {
    fontSize: 16,
    color: Colors.text,
    fontWeight: '500',
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
