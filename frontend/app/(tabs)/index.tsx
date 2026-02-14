import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
  Pressable,
  ActionSheetIOS,
  Platform,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../../constants/colors';
import { Typography } from '../../constants/typography';
import { useAppStore } from '../../store';
import api, { API_BASE_URL } from '../../services/api';
import { storage } from '../../store';
import DailyFocusCard, { DailyFocusState } from '../../components/DailyFocusCard';
import ReflectionEntry from '../../components/ReflectionEntry';
import DebugComputeInputs from '../../components/DebugComputeInputs';
import SectionLabel from '../../components/SectionLabel';

// =========================================
// DEBUG CONFIG - Collapsed by default, muted styling
// =========================================
const DEBUG_MODE = true;
const BUILD_ID = '2026-02-14-typography-v1';
const APP_HOST = Platform.OS === 'web' && typeof window !== 'undefined' 
  ? window.location?.origin || 'unknown'
  : 'native-app';
// =========================================

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
  const { user, hasTriedSessionRestore, isRestoringSession, clearUser } = useAppStore();
  const router = useRouter();
  const [keystone, setKeystone] = useState<DailyKeystone | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentDate, setCurrentDate] = useState<string>(getLocalDateString());
  const lastLoadedDateRef = useRef<string | null>(null);
  
  // Debug panel state - collapsed by default
  const [debugExpanded, setDebugExpanded] = useState(false);
  
  // Track journal count for conditional intelligence signal
  const [journalCount, setJournalCount] = useState<number>(0);
  
  // Track daily focus state for reflection entry
  const [focusState, setFocusState] = useState<DailyFocusState>({
    isLoading: true,
    isDismissed: false,
    hasContext: false,
    context: null,
    ambientLine: null,
  });
  
  // Conditional intelligence signal text
  const intelligenceText = journalCount >= 2 || focusState.hasContext
    ? "Based on recent reflections"
    : "Based on what's present today";

  // Handle focus state changes from DailyFocusCard
  const handleFocusStateChange = useCallback((state: DailyFocusState) => {
    setFocusState(state);
  }, []);

  // Handle reflection entry tap
  const handleReflect = useCallback(() => {
    // Navigate to reflection chat with context state
    const params = new URLSearchParams();
    if (focusState.context) {
      params.set('context', focusState.context);
    }
    if (focusState.isDismissed) {
      params.set('dismissed', 'true');
    }
    router.push(`/reflection-chat?${params.toString()}`);
  }, [router, focusState.context, focusState.isDismissed]);

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

  // Handler for logout action sheet
  const handleUserPress = () => {
    if (Platform.OS === 'ios') {
      ActionSheetIOS.showActionSheetWithOptions(
        {
          options: ['Cancel', 'Log out'],
          destructiveButtonIndex: 1,
          cancelButtonIndex: 0,
          title: user?.name || 'Account',
        },
        async (buttonIndex) => {
          if (buttonIndex === 1) {
            await clearUser();
            router.replace('/welcome');
          }
        }
      );
    } else {
      // Android/Web fallback using Alert
      Alert.alert(
        user?.name || 'Account',
        'What would you like to do?',
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Log out', 
            style: 'destructive',
            onPress: async () => {
              await clearUser();
              router.replace('/welcome');
            }
          },
        ]
      );
    }
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
      // Fetch journal count for conditional intelligence signal
      fetchJournalCount();
    }
  }, [user, hasTriedSessionRestore, isRestoringSession, currentDate]);
  
  const fetchJournalCount = async () => {
    if (!user?.id) return;
    try {
      const response = await api.get(`/journal/${user.id}`);
      setJournalCount(response.data?.length || 0);
    } catch (err) {
      // Silently fail - default to 0
      setJournalCount(0);
    }
  };

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
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar style="light" />
      
      {/* Compact Header with muted debug toggle */}
      <View style={styles.header}>
        <Pressable onPress={handleUserPress} style={styles.userCluster}>
          <Text style={styles.userName} numberOfLines={1} ellipsizeMode="tail">
            {user?.name || 'Account'}
          </Text>
          <Ionicons name="chevron-forward" size={14} color={Colors.textTertiary} />
        </Pressable>
        
        {/* Muted Debug Toggle - top right */}
        {DEBUG_MODE && (
          <TouchableOpacity 
            style={styles.debugToggle}
            onPress={() => setDebugExpanded(!debugExpanded)}
            activeOpacity={0.6}
          >
            <Text style={styles.debugToggleText}>Debug</Text>
          </TouchableOpacity>
        )}
      </View>
      
      {/* Collapsible Debug Panel - muted styling */}
      {DEBUG_MODE && debugExpanded && (
        <View style={styles.debugPanel}>
          <Text style={styles.debugText}>BUILD: {BUILD_ID}</Text>
          <Text style={styles.debugText}>API: {API_BASE_URL || '(none)'}</Text>
          <Text style={styles.debugText}>HOST: {APP_HOST}</Text>
        </View>
      )}
      
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
        {/* A. Section Label */}
        <SectionLabel marginBottom={28}>THE MIRROR</SectionLabel>
        
        {/* Loading State */}
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color={Colors.textTertiary} />
          </View>
        )}

        {/* B. Main Body - Primary Mirror Text (Serif, Large) */}
        {keystone && !isLoading && (
          <>
            <Text style={styles.mainBody}>
              {keystone.keystone}
            </Text>

            {/* C. Subtext - Supportive Line (Italic, Softer) */}
            <Text style={styles.subtext}>
              {keystone.micro_affirmation}
            </Text>

            {/* D. Divider - Subtle */}
            <View style={styles.divider} />

            {/* E. TODAY Section with conditional intelligence */}
            <View style={styles.todaySection}>
              <SectionLabel marginBottom={4}>TODAY</SectionLabel>
              <Text style={styles.intelligenceSignal}>{intelligenceText}</Text>
            </View>
            
            {/* Today's Focus Card - Embedded feel */}
            <DailyFocusCard 
              userId={user.id} 
              onStateChange={handleFocusStateChange}
            />

            {/* F. Reflect Prompt */}
            <View style={styles.reflectSection}>
              <SectionLabel marginBottom={14}>REFLECT</SectionLabel>
              <Text style={styles.reflectQuestion}>
                {keystone.reflect_question}
              </Text>
            </View>
            
            {/* Reflection Entry */}
            {!focusState.isLoading && (
              <ReflectionEntry onPress={handleReflect} />
            )}

            {/* Continue with Mirror button */}
            <TouchableOpacity
              style={styles.continueButton}
              onPress={handleContinueWithMirror}
              activeOpacity={0.7}
            >
              <Text style={styles.continueButtonText}>Continue with Mirror</Text>
              <Text style={styles.continueButtonSubtext}>Stay with this for a moment.</Text>
            </TouchableOpacity>
          </>
        )}

        {/* Show Daily Focus Card when loading or no keystone */}
        {!keystone && !isLoading && (
          <DailyFocusCard 
            userId={user.id} 
            onStateChange={handleFocusStateChange}
          />
        )}

        {/* Gentle footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Your reflection for today
          </Text>
        </View>

        {/* Debug: Compute Inputs Panel - only visible when DEBUG_MIRROR=true */}
        {user?.id && <DebugComputeInputs userId={user.id} />}

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
  // Header - minimal with debug toggle
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
    height: 48,
  },
  userCluster: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  userName: {
    fontSize: 14,
    color: Colors.textTertiary,
    maxWidth: 140,
  },
  // Debug - muted, collapsed by default
  debugToggle: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  debugToggleText: {
    ...Typography.debugText,
    opacity: 0.3,
  },
  debugPanel: {
    backgroundColor: 'rgba(0,0,0,0.85)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
    paddingHorizontal: 20,
    paddingVertical: 8,
  },
  debugText: {
    ...Typography.debugText,
    marginBottom: 2,
  },
  // Scroll content
  scrollContent: {
    flexGrow: 1,
    paddingTop: 8,
    paddingHorizontal: 24,
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
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  // A. Section Label
  sectionLabel: {
    fontSize: 10,
    fontWeight: '500',
    color: Colors.textTertiary,
    letterSpacing: 2,
    marginBottom: 28,
    opacity: 0.6,
  },
  // B. Main Body - Uses Typography.heroSerif
  mainBody: {
    ...Typography.heroSerif,
    marginBottom: 20,
  },
  // C. Subtext - Supportive (italic, softer)
  subtext: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    marginBottom: 36,
    opacity: 0.8,
  },
  // D. Divider - subtle
  divider: {
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.08)',
    marginBottom: 28,
  },
  // E. TODAY section
  todaySection: {
    marginBottom: 16,
  },
  todayLabel: {
    fontSize: 9,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.5,
    marginBottom: 4,
  },
  intelligenceSignal: {
    fontSize: 11,
    color: Colors.textTertiary,
    opacity: 0.4,
    fontStyle: 'italic',
  },
  // F. Reflect section
  reflectSection: {
    paddingTop: 28,
    paddingBottom: 20,
    marginTop: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.08)',
  },
  reflectLabel: {
    fontSize: 9,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.5,
    marginBottom: 14,
  },
  reflectQuestion: {
    fontSize: 17,
    lineHeight: 28,
    color: Colors.text,
    fontWeight: '400',
  },
  // Continue button
  continueButton: {
    marginTop: 32,
    paddingVertical: 16,
    paddingHorizontal: 20,
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
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
  // Footer
  footer: {
    marginTop: 'auto',
    paddingTop: 40,
    paddingBottom: 12,
  },
  footerText: {
    fontSize: 11,
    color: Colors.textTertiary,
    opacity: 0.3,
  },
  bottomSpacer: {
    height: 24,
  },
});
