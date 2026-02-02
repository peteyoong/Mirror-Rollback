import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import api from '../../services/api';
import { storage } from '../../store';

interface DailyKeystone {
  date: string;
  title: string;
  keystone: string;
  reflect_question: string;
  micro_affirmation: string;
  source_signals: {
    used: string[];
    tone: string;
  };
  daily_seed: string;
  is_first_visit: boolean;
}

// Get local date in YYYY-MM-DD format
const getLocalDateString = (): string => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export default function MirrorScreen() {
  const { user, hasTriedSessionRestore, isRestoringSession } = useAppStore();
  const router = useRouter();
  const [keystone, setKeystone] = useState<DailyKeystone | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentDate, setCurrentDate] = useState<string>(getLocalDateString());
  const lastLoadedDateRef = useRef<string | null>(null);

  // Handler to continue with Mirror chat
  const handleContinueWithMirror = async () => {
    if (!keystone) return;
    
    // Store the keystone context in async storage for the journal tab to pick up
    const keystoneContextForChat = {
      date: keystone.date,
      title: keystone.title,
      keystone: keystone.keystone,
      reflect_question: keystone.reflect_question,
      micro_affirmation: keystone.micro_affirmation,
      tone: keystone.source_signals?.tone || 'unclear',
      daily_seed: keystone.daily_seed,
    };
    
    try {
      await storage.setItem('pending_keystone_context', JSON.stringify(keystoneContextForChat));
      console.log('[MirrorHome] Stored keystone context for chat');
    } catch (e) {
      console.error('[MirrorHome] Failed to store keystone context:', e);
    }
    
    // Navigate to Journal tab with Mirror Chat view
    router.push('/(tabs)/journal?view=mirror&fromKeystone=true');
  };

  // Check for date change on focus/visibility
  useEffect(() => {
    const checkDateChange = () => {
      const newDate = getLocalDateString();
      if (newDate !== currentDate) {
        console.log(`[MirrorHome] Date changed: ${currentDate} -> ${newDate}`);
        setCurrentDate(newDate);
        lastLoadedDateRef.current = null; // Force reload
      }
    };

    // Check every minute for date change
    const interval = setInterval(checkDateChange, 60000);
    return () => clearInterval(interval);
  }, [currentDate]);

  useEffect(() => {
    // Only fetch after session restore is complete AND we have a user
    if (hasTriedSessionRestore && !isRestoringSession && user?.id) {
      // Only load if we haven't loaded for this date yet
      if (lastLoadedDateRef.current !== currentDate) {
        loadKeystone();
      }
    }
  }, [user, hasTriedSessionRestore, isRestoringSession, currentDate]);

  const loadKeystone = async (forceRefresh = false) => {
    if (!user?.id) return;

    const dateToLoad = getLocalDateString();

    if (forceRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }

    try {
      const response = await api.get(`/mirror/home/${user.id}`, {
        params: { date: dateToLoad }
      });
      setKeystone(response.data);
      lastLoadedDateRef.current = dateToLoad;
      setCurrentDate(dateToLoad);
    } catch (err: any) {
      console.error('Load keystone error:', err);
      // Use fallback
      setKeystone({
        date: dateToLoad,
        title: "A Quiet Arrival",
        keystone: "Something in you brought you here today. That's worth noticing.",
        reflect_question: "What feels most present right now?",
        micro_affirmation: "You don't have to have it figured out to be here.",
        source_signals: { used: ["fallback"], tone: "grounding" },
        daily_seed: "fallback",
        is_first_visit: false,
      });
      lastLoadedDateRef.current = dateToLoad;
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleRefresh = () => {
    // Pull-to-refresh re-fetches same date (cached, so same content)
    loadKeystone(true);
  };

  // Show loading while session is being restored
  if (!hasTriedSessionRestore || isRestoringSession) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={Colors.textTertiary} />
          <Text style={styles.restoringText}>Restoring your profile...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Show loading if no user
  if (!user) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={Colors.textTertiary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.textTertiary}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Spacer for breathing room */}
        <View style={styles.topSpacer} />

        {/* User greeting */}
        <View style={styles.greetingContainer}>
          <Text style={styles.greeting}>
            {user.name || 'Welcome'}
          </Text>
        </View>

        {/* Loading State */}
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color={Colors.textTertiary} />
          </View>
        )}

        {/* The Daily Keystone */}
        {keystone && !isLoading && (
          <View style={styles.keystoneContainer}>
            {/* Title as section header */}
            <Text style={styles.keystoneTitle}>
              {keystone.title.toUpperCase()}
            </Text>

            {/* Main keystone text - the emotional center */}
            <Text style={styles.keystoneText}>
              {keystone.keystone}
            </Text>

            {/* Micro-affirmation - soft grounding line */}
            <Text style={styles.microAffirmation}>
              {keystone.micro_affirmation}
            </Text>

            {/* Reflective question - separate section */}
            <View style={styles.reflectContainer}>
              <Text style={styles.reflectLabel}>Reflect</Text>
              <Text style={styles.reflectQuestion}>
                {keystone.reflect_question}
              </Text>
            </View>

            {/* Continue with Mirror button */}
            <TouchableOpacity
              style={styles.continueButton}
              onPress={handleContinueWithMirror}
              activeOpacity={0.7}
            >
              <Text style={styles.continueButtonText}>Continue with Mirror</Text>
              <Text style={styles.continueButtonSubtext}>Stay with this for a moment.</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Gentle footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Your reflection for today
          </Text>
        </View>

        <View style={styles.bottomSpacer} />
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
    paddingHorizontal: 32,
    // Constrain text width for readability
    maxWidth: 440,
    alignSelf: 'center',
    width: '100%',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  restoringText: {
    fontSize: 14,
    color: Colors.textTertiary,
    marginTop: 8,
  },
  topSpacer: {
    // More breathing room at top
    height: 80,
  },
  greetingContainer: {
    marginBottom: 40,
  },
  greeting: {
    // Visually lighter - anchor, not headline
    fontSize: 18,
    fontWeight: '400',
    color: Colors.textSecondary,
    letterSpacing: 0.2,
  },
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  keystoneContainer: {
    paddingVertical: 8,
  },
  keystoneTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.5,
    marginBottom: 24,
  },
  keystoneText: {
    fontSize: 20,
    // Increased line-height for breathing
    lineHeight: 36,
    color: Colors.text,
    fontWeight: '400',
    letterSpacing: 0.2,
    marginBottom: 28,
  },
  microAffirmation: {
    fontSize: 15,
    // Increased line-height
    lineHeight: 26,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    marginBottom: 48,
  },
  reflectContainer: {
    paddingTop: 28,
    paddingBottom: 20,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  reflectLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 14,
  },
  reflectQuestion: {
    fontSize: 17,
    // Increased line-height
    lineHeight: 30,
    color: Colors.text,
    fontWeight: '400',
  },
  continueButton: {
    marginTop: 36,
    paddingVertical: 18,
    paddingHorizontal: 24,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
    alignItems: 'center',
  },
  continueButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 4,
  },
  continueButtonSubtext: {
    fontSize: 12,
    color: Colors.textTertiary,
    fontStyle: 'italic',
  },
  footer: {
    marginTop: 'auto',
    paddingTop: 48,
    paddingBottom: 24,
  },
  footerText: {
    fontSize: 12,
    color: Colors.textTertiary,
    textAlign: 'center',
    opacity: 0.4,
  },
  bottomSpacer: {
    height: 48,
  },
});
