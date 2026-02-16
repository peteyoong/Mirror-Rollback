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
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Colors } from '../../constants/colors';
import { Typography } from '../../constants/typography';
import { Spacing } from '../../constants/spacing';
import { useAppStore } from '../../store';
import api, { API_BASE_URL, API_URL_MISSING } from '../../services/api';
import { storage } from '../../store';
import DailyFocusCard, { DailyFocusState } from '../../components/DailyFocusCard';
import ReflectionEntry from '../../components/ReflectionEntry';
import DebugComputeInputs from '../../components/DebugComputeInputs';
import SectionLabel from '../../components/SectionLabel';
import ApiOfflineBanner, { InlineRetry } from '../../components/ApiOfflineBanner';
import { BUILD_ID as CANONICAL_BUILD_ID } from '../../utils/buildInfo';
import { SafeIcon } from '../../components/SafeIcon';

// =========================================
// BUILD ID - Use canonical source
// =========================================
const BUILD_ID = CANONICAL_BUILD_ID;
const APP_HOST = Platform.OS === 'web' && typeof window !== 'undefined' 
  ? window.location?.origin || 'unknown'
  : 'native-app';
// =========================================

// Default fallback content when API is unavailable
const DEFAULT_KEYSTONE = {
  date: new Date().toISOString().split('T')[0],
  title: 'Today',
  keystone: 'Take a moment to notice how you feel right now. What\'s present for you today?',
  reflect_question: 'What would you like to bring more attention to?',
  micro_affirmation: 'You\'re here, and that\'s enough.',
  source_signals: { used: [], tone: 'gentle' },
  daily_seed: 'default',
  is_first_visit: true,
};

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

// ===== ISOLATION TEST COMPLETE =====
// Phase 1: Store hooks - PASSED ✓
// Phase 2: useState hooks - PASSED ✓
// Phase 3: Debug useEffect - PASSED ✓
// Phase 4: Data loading useEffect - PASSED ✓
// Phase 99: Full original render
const ISOLATION_PHASE = 99;  // Restore full page

export default function MirrorScreen() {
  // ===== PHASE 1: Just store hooks =====
  if (ISOLATION_PHASE === 1) {
    const user = useAppStore(s => s.user);
    const hasTriedSessionRestore = useAppStore(s => s.hasTriedSessionRestore);
    const isRestoringSession = useAppStore(s => s.isRestoringSession);
    
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1a2e' }}>
        <Text style={{ color: 'white', fontSize: 18 }}>Mirror tab - Phase 1</Text>
        <Text style={{ color: '#888', fontSize: 12, marginTop: 10 }}>Store hooks only (no effects)</Text>
        <Text style={{ color: '#666', fontSize: 10, marginTop: 5 }}>
          user: {user?.name || 'null'} | restore: {String(hasTriedSessionRestore)} | restoring: {String(isRestoringSession)}
        </Text>
      </View>
    );
  }

  // ===== PHASE 2: Store hooks + useState (no useEffect) =====
  if (ISOLATION_PHASE === 2) {
    const user = useAppStore(s => s.user);
    const hasTriedSessionRestore = useAppStore(s => s.hasTriedSessionRestore);
    const isRestoringSession = useAppStore(s => s.isRestoringSession);
    const router = useRouter();
    
    const [keystone, setKeystone] = useState<DailyKeystone | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [currentDate, setCurrentDate] = useState<string>(getLocalDateString());
    const [debugVisible, setDebugVisible] = useState(false);
    const [debugExpanded, setDebugExpanded] = useState(false);
    const [journalCount, setJournalCount] = useState<number>(0);
    const [dailyFocusState, setDailyFocusState] = useState<DailyFocusState | null>(null);
    
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1a2e' }}>
        <Text style={{ color: 'white', fontSize: 18 }}>Mirror tab - Phase 2</Text>
        <Text style={{ color: '#888', fontSize: 12, marginTop: 10 }}>Store hooks + useState (no effects)</Text>
        <Text style={{ color: '#666', fontSize: 10, marginTop: 5 }}>
          user: {user?.name || 'null'} | date: {currentDate}
        </Text>
      </View>
    );
  }

  // ===== PHASE 3: Add first useEffect (debug param) =====
  if (ISOLATION_PHASE === 3) {
    const user = useAppStore(s => s.user);
    const hasTriedSessionRestore = useAppStore(s => s.hasTriedSessionRestore);
    const isRestoringSession = useAppStore(s => s.isRestoringSession);
    const router = useRouter();
    const params = useLocalSearchParams<{ debug?: string }>();
    
    const [keystone, setKeystone] = useState<DailyKeystone | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [currentDate, setCurrentDate] = useState<string>(getLocalDateString());
    const [debugVisible, setDebugVisible] = useState(false);
    const [debugExpanded, setDebugExpanded] = useState(false);
    const [journalCount, setJournalCount] = useState<number>(0);
    const [dailyFocusState, setDailyFocusState] = useState<DailyFocusState | null>(null);
    const lastLoadedDateRef = useRef<string | null>(null);
    
    // EFFECT 1: Debug param check
    useEffect(() => {
      if (params.debug === '1') {
        setDebugVisible(true);
      }
    }, [params.debug]);
    
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1a2e' }}>
        <Text style={{ color: 'white', fontSize: 18 }}>Mirror tab - Phase 3</Text>
        <Text style={{ color: '#888', fontSize: 12, marginTop: 10 }}>+ useEffect (debug param)</Text>
        <Text style={{ color: '#666', fontSize: 10, marginTop: 5 }}>
          user: {user?.name || 'null'} | date: {currentDate}
        </Text>
      </View>
    );
  }

  // ===== PHASE 4: Add main data loading useEffect =====
  if (ISOLATION_PHASE === 4) {
    const user = useAppStore(s => s.user);
    const hasTriedSessionRestore = useAppStore(s => s.hasTriedSessionRestore);
    const isRestoringSession = useAppStore(s => s.isRestoringSession);
    const router = useRouter();
    const params = useLocalSearchParams<{ debug?: string }>();
    
    const [keystone, setKeystone] = useState<DailyKeystone | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [currentDate, setCurrentDate] = useState<string>(getLocalDateString());
    const [debugVisible, setDebugVisible] = useState(false);
    const [debugExpanded, setDebugExpanded] = useState(false);
    const [journalCount, setJournalCount] = useState<number>(0);
    const lastLoadedDateRef = useRef<string | null>(null);
    const didInitRef = useRef(false);
    
    // EFFECT 1: Debug param check
    useEffect(() => {
      if (params.debug === '1') {
        setDebugVisible(true);
      }
    }, [params.debug]);
    
    // EFFECT 2: Main data loading (idempotent)
    useEffect(() => {
      // Only load once per mount
      if (didInitRef.current) return;
      if (!hasTriedSessionRestore || isRestoringSession || !user?.id) return;
      
      didInitRef.current = true;
      console.log('[Phase4] Loading keystone data...');
      
      // Load keystone
      const loadKeystone = async () => {
        try {
          const dateToLoad = getLocalDateString();
          const response = await api.get(`/mirror/home/${user.id}`, {
            params: { date: dateToLoad }
          });
          setKeystone(response.data);
          lastLoadedDateRef.current = dateToLoad;
        } catch (err: any) {
          console.error('[Phase4] Load keystone error:', err);
          setKeystone({
            date: getLocalDateString(),
            title: "A Quiet Arrival",
            keystone: "Something in you brought you here today.",
            reflect_question: "What feels most present right now?",
            micro_affirmation: "You don't have to have it figured out.",
            source_signals: { used: ["fallback"], tone: "grounding" },
            daily_seed: "fallback",
            is_first_visit: false,
          });
        } finally {
          setIsLoading(false);
        }
      };
      
      loadKeystone();
    }, [hasTriedSessionRestore, isRestoringSession, user?.id]);
    
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1a2e' }}>
        <Text style={{ color: 'white', fontSize: 18 }}>Mirror tab - Phase 4</Text>
        <Text style={{ color: '#888', fontSize: 12, marginTop: 10 }}>+ useEffect (data loading)</Text>
        <Text style={{ color: '#666', fontSize: 10, marginTop: 5 }}>
          user: {user?.name || 'null'} | loading: {String(isLoading)}
        </Text>
        <Text style={{ color: '#666', fontSize: 10, marginTop: 3 }}>
          keystone: {keystone?.title || 'null'}
        </Text>
      </View>
    );
  }

  const { user, hasTriedSessionRestore, isRestoringSession, clearUser } = useAppStore();
  const router = useRouter();
  const params = useLocalSearchParams<{ debug?: string }>();
  const [keystone, setKeystone] = useState<DailyKeystone | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentDate, setCurrentDate] = useState<string>(getLocalDateString());
  const lastLoadedDateRef = useRef<string | null>(null);
  
  // Debug panel - hidden by default, only visible with ?debug=1 or 5-tap
  const [debugVisible, setDebugVisible] = useState(false);
  const [debugExpanded, setDebugExpanded] = useState(false);
  const tapCountRef = useRef(0);
  const tapTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Check for ?debug=1 URL param
  useEffect(() => {
    if (params.debug === '1') {
      setDebugVisible(true);
    }
  }, [params.debug]);
  
  // 5-tap gesture to reveal debug panel
  const handleDebugTap = useCallback(() => {
    tapCountRef.current += 1;
    
    if (tapTimeoutRef.current) {
      clearTimeout(tapTimeoutRef.current);
    }
    
    if (tapCountRef.current >= 5) {
      setDebugVisible(true);
      setDebugExpanded(true);
      tapCountRef.current = 0;
    } else {
      tapTimeoutRef.current = setTimeout(() => {
        tapCountRef.current = 0;
      }, 1000);
    }
  }, []);
  
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
    const navParams = new URLSearchParams();
    if (focusState.context) {
      navParams.set('context', focusState.context);
    }
    if (focusState.isDismissed) {
      navParams.set('dismissed', 'true');
    }
    router.push(`/reflection-chat?${navParams.toString()}`);
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
    const { resetLocalSession } = useAppStore.getState();
    
    if (Platform.OS === 'ios') {
      ActionSheetIOS.showActionSheetWithOptions(
        {
          options: ['Cancel', 'Sign out', 'Start fresh (clear all data)'],
          destructiveButtonIndex: 2,
          cancelButtonIndex: 0,
          title: user?.name || 'Account',
        },
        async (buttonIndex) => {
          if (buttonIndex === 1) {
            // Sign out - keeps data but navigates to welcome
            await clearUser();
            router.replace('/welcome');
          } else if (buttonIndex === 2) {
            // Start fresh - clears ALL local data
            await resetLocalSession(true);
          }
        }
      );
    } else if (Platform.OS === 'web' && typeof window !== 'undefined') {
      // Web: Use window.confirm for better visibility
      const choice = window.confirm(
        `${user?.name || 'Account'}\n\nClick OK to Sign out, or Cancel to stay.\n\nTo clear all local data, add ?reset=1 to the URL.`
      );
      if (choice) {
        clearUser().then(() => {
          router.replace('/welcome');
        });
      }
    } else {
      // Android fallback using Alert
      Alert.alert(
        user?.name || 'Account',
        'What would you like to do?',
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Sign out', 
            onPress: async () => {
              await clearUser();
              router.replace('/welcome');
            }
          },
          { 
            text: 'Start fresh (clear all)', 
            style: 'destructive',
            onPress: async () => {
              await resetLocalSession(true);
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
  
  // Track if fetch failed for retry UI
  const [fetchFailed, setFetchFailed] = useState(false);

  // Show loading while session is being restored
  if (!hasTriedSessionRestore || isRestoringSession) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={Colors.textTertiary} />
          <Text style={styles.restoringText}>Restoring your profile...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Show loading if no user - but still render static UI
  if (!user) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <ApiOfflineBanner />
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={Colors.textTertiary} />
          <Text style={styles.restoringText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Use keystone or default fallback - ALWAYS render content
  const displayKeystone = keystone || DEFAULT_KEYSTONE;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar style="light" />
      
      {/* API Offline Banner - non-blocking */}
      <ApiOfflineBanner onRetry={() => loadKeystone(true)} />
      
      {/* Compact Header */}
      <View style={styles.header}>
        <Pressable onPress={handleUserPress} style={styles.userCluster}>
          <Text style={styles.userName} numberOfLines={1} ellipsizeMode="tail">
            {user?.name || 'Account'}
          </Text>
          <SafeIcon name="chevron-forward" size={14} color={Colors.textTertiary} />
        </Pressable>
      </View>
      
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
        <SectionLabel marginBottom={Spacing.lg}>THE MIRROR</SectionLabel>

        {/* B. Main Body - Primary Mirror Text (Serif, Large) - ALWAYS RENDER */}
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color={Colors.textTertiary} />
          </View>
        ) : (
          <>
            <Text style={styles.mainBody}>
              {displayKeystone.keystone}
            </Text>

            {/* C. Subtext - Supportive Line (Italic, Softer) */}
            <Text style={styles.subtext}>
              {displayKeystone.micro_affirmation}
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
                {displayKeystone.reflect_question}
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
              disabled={API_URL_MISSING}
            >
              <Text style={styles.continueButtonText}>Continue with Mirror</Text>
              <Text style={styles.continueButtonSubtext}>Stay with this for a moment.</Text>
            </TouchableOpacity>
          </>
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
  // Header - minimal with hidden debug trigger
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    height: 48,
  },
  userCluster: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xxs,
  },
  userName: {
    fontSize: 14,
    color: Colors.textTertiary,
    maxWidth: 140,
  },
  // Debug - hidden by default
  debugTrigger: {
    width: 44,
    height: 44,
    // Invisible touch target for 5-tap reveal
  },
  debugToggle: {
    paddingHorizontal: Spacing.xs,
    paddingVertical: Spacing.xxs,
  },
  debugToggleText: {
    ...Typography.debugText,
    opacity: 0.3,
  },
  debugPanel: {
    backgroundColor: 'rgba(0,0,0,0.85)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.xs,
  },
  debugText: {
    ...Typography.debugText,
    marginBottom: 2,
  },
  // Scroll content
  scrollContent: {
    flexGrow: 1,
    paddingTop: Spacing.xs,
    paddingHorizontal: Spacing.lg,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  restoringText: {
    fontSize: 14,
    color: Colors.textTertiary,
    marginTop: Spacing.xs,
  },
  loadingContainer: {
    paddingVertical: Spacing.xxl + Spacing.lg,
    alignItems: 'center',
  },
  // B. Main Body - Uses Typography.heroSerif
  mainBody: {
    ...Typography.heroSerif,
    marginBottom: Spacing.lg,
  },
  // C. Subtext - Uses Typography.subtextItalic
  subtext: {
    ...Typography.subtextItalic,
    marginBottom: Spacing.xl,
  },
  // D. Divider - subtle
  divider: {
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.08)',
    marginBottom: Spacing.lg,
  },
  // E. TODAY section
  todaySection: {
    marginBottom: Spacing.md,
  },
  intelligenceSignal: {
    ...Typography.intelligenceSignal,
  },
  // F. Reflect section
  reflectSection: {
    paddingTop: Spacing.lg,
    paddingBottom: Spacing.lg,
    marginTop: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.08)',
  },
  reflectQuestion: {
    ...Typography.reflectQuestion,
  },
  // Continue button
  continueButton: {
    marginTop: Spacing.xl,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.lg,
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderRadius: Spacing.sm,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    alignItems: 'center',
  },
  continueButtonText: {
    ...Typography.buttonText,
    marginBottom: Spacing.xxs,
  },
  continueButtonSubtext: {
    ...Typography.buttonSubtext,
  },
  // Footer
  footer: {
    marginTop: 'auto',
    paddingTop: Spacing.xxl,
    paddingBottom: Spacing.sm,
  },
  footerText: {
    ...Typography.footerText,
  },
  bottomSpacer: {
    height: Spacing.lg,
  },
});
