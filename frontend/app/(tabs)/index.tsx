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
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTheme, ThemeMode } from '../../contexts/ThemeContext';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import api from '../../services/api';
import { storage } from '../../store';
import DailyFocusCard, { DailyFocusState } from '../../components/DailyFocusCard';
import ReflectionEntry from '../../components/ReflectionEntry';
import DebugComputeInputs from '../../components/DebugComputeInputs';

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
  is_enriched?: boolean;  // True when LLM-personalized, false when deterministic
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
  const { theme, isDark } = useTheme();
  const { user, hasTriedSessionRestore, isRestoringSession, clearUser } = useAppStore();
  const router = useRouter();
  const [keystone, setKeystone] = useState<DailyKeystone | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentDate, setCurrentDate] = useState<string>(getLocalDateString());
  const lastLoadedDateRef = useRef<string | null>(null);
  
  // Track daily focus state for reflection entry
  const [focusState, setFocusState] = useState<DailyFocusState>({
    isLoading: true,
    isDismissed: false,
    hasContext: false,
    context: null,
    ambientLine: null,
  });

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
      
      // If we got a deterministic (non-enriched) version, poll for enriched version
      // This ensures instant first render + richer content when ready
      if (response.data.is_enriched === false) {
        // Start silent polling for enriched version
        const pollForEnriched = async () => {
          // Wait a few seconds for background LLM to complete
          await new Promise(resolve => setTimeout(resolve, 5000));
          
          try {
            const enrichedResponse = await api.get(`/mirror/home/${user.id}`, {
              params: { date: dateToLoad }
            });
            
            // Only update if we got the enriched version and still on same date
            if (enrichedResponse.data.is_enriched === true && 
                lastLoadedDateRef.current === dateToLoad) {
              // Silently update - no loading state change
              setKeystone(enrichedResponse.data);
              console.log('[MirrorHome] Silent update with enriched keystone');
            } else if (enrichedResponse.data.is_enriched === false) {
              // Still not enriched, try once more after another delay
              await new Promise(resolve => setTimeout(resolve, 5000));
              const finalResponse = await api.get(`/mirror/home/${user.id}`, {
                params: { date: dateToLoad }
              });
              if (finalResponse.data.is_enriched === true && 
                  lastLoadedDateRef.current === dateToLoad) {
                setKeystone(finalResponse.data);
                console.log('[MirrorHome] Silent update with enriched keystone (2nd poll)');
              }
            }
          } catch (pollErr) {
            // Silent failure - deterministic version is fine
            console.log('[MirrorHome] Enrichment poll failed, keeping deterministic version');
          }
        };
        
        // Start polling in background (don't await)
        pollForEnriched();
      }
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
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={theme.textTertiary} />
          <Text style={[styles.restoringText, { color: theme.textSecondary }]}>Restoring your profile...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Show loading if no user
  if (!user) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={theme.textTertiary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      
      {/* Compact Header: "THE MIRROR" on left, User name + chevron on right */}
      <Pressable 
        style={[styles.header, { backgroundColor: theme.background }]}
        onPress={handleUserPress}
      >
        <Text style={[styles.headerTitle, { color: theme.text }]}>THE MIRROR</Text>
        <View style={styles.userCluster}>
          <Text style={[styles.userName, { color: theme.textSecondary }]} numberOfLines={1} ellipsizeMode="tail">
            {user?.name || 'Account'}
          </Text>
          <Ionicons name="chevron-forward" size={14} color={theme.textTertiary} />
        </View>
      </Pressable>
      
      {/* Subtle header separation */}
      <View style={[styles.headerDivider, { backgroundColor: theme.border }]} />
      
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={theme.textTertiary}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Daily Focus Card - Context Surfacing */}
        <DailyFocusCard 
          userId={user.id} 
          onStateChange={handleFocusStateChange}
        />
        
        {/* Reflection Entry - Subtle entry to daily reflection */}
        {!focusState.isLoading && (
          <ReflectionEntry onPress={handleReflect} />
        )}

        {/* Loading State */}
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color={theme.textTertiary} />
          </View>
        )}

        {/* The Daily Keystone */}
        {keystone && !isLoading && (
          <View style={[styles.keystoneContainer, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
            {/* Title as section header */}
            <Text style={[styles.keystoneTitle, { color: theme.textTertiary }]}>
              {keystone.title.toUpperCase()}
            </Text>

            {/* Main keystone text - the emotional center */}
            <Text style={[styles.keystoneText, { color: theme.text }]}>
              {keystone.keystone}
            </Text>

            {/* Micro-affirmation - soft grounding line */}
            <Text style={[styles.microAffirmation, { color: theme.textSecondary }]}>
              {keystone.micro_affirmation}
            </Text>

            {/* Reflective question - separate section */}
            <View style={[styles.reflectContainer, { borderTopColor: theme.border }]}>
              <Text style={[styles.reflectLabel, { color: theme.textTertiary }]}>Reflect</Text>
              <Text style={[styles.reflectQuestion, { color: theme.textSecondary }]}>
                {keystone.reflect_question}
              </Text>
            </View>

            {/* Continue with Mirror button */}
            <TouchableOpacity
              style={[styles.continueButton, { 
                backgroundColor: theme.buttonPrimaryBg,
                borderColor: theme.border 
              }]}
              onPress={handleContinueWithMirror}
              activeOpacity={0.7}
            >
              <Text style={[styles.continueButtonText, { color: theme.buttonPrimaryText }]}>Continue with Mirror</Text>
              <Text style={[styles.continueButtonSubtext, { color: theme.textTertiary }]}>Stay with this for a moment.</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Gentle footer */}
        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: theme.textTertiary }]}>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 14,
    height: 52,
  },
  headerTitle: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.text,
    letterSpacing: 1.2,
  },
  userCluster: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  userName: {
    fontSize: 14,
    color: Colors.textTertiary,
    maxWidth: 140,
  },
  headerDivider: {
    height: 1,
    backgroundColor: Colors.border,
    opacity: 0.5,
    marginHorizontal: 20,
  },
  scrollContent: {
    flexGrow: 1,
    paddingTop: 12,
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
  keystoneContainer: {
    paddingTop: 16,
    paddingBottom: 8,
    paddingHorizontal: 20,
  },
  keystoneTitle: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.2,
    marginBottom: 14,
    opacity: 0.7,
  },
  keystoneText: {
    fontSize: 19,
    lineHeight: 30,
    color: Colors.text,
    fontWeight: '400',
    letterSpacing: 0.2,
    marginBottom: 16,
  },
  microAffirmation: {
    fontSize: 14,
    lineHeight: 22,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    marginBottom: 24,
    paddingLeft: 12,
    borderLeftWidth: 2,
    borderLeftColor: Colors.border,
  },
  reflectContainer: {
    paddingTop: 20,
    paddingBottom: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  reflectLabel: {
    fontSize: 9,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 10,
    opacity: 0.6,
  },
  reflectQuestion: {
    fontSize: 16,
    lineHeight: 26,
    color: Colors.text,
    fontWeight: '400',
  },
  continueButton: {
    marginTop: 24,
    paddingVertical: 14,
    paddingHorizontal: 20,
    backgroundColor: Colors.surface,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
    alignItems: 'center',
  },
  continueButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 2,
  },
  continueButtonSubtext: {
    fontSize: 11,
    color: Colors.textTertiary,
    fontStyle: 'italic',
  },
  footer: {
    marginTop: 'auto',
    paddingTop: 24,
    paddingBottom: 8,
    paddingHorizontal: 20,
  },
  footerText: {
    fontSize: 10,
    color: Colors.textTertiary,
    opacity: 0.3,
    textAlign: 'center',
  },
  bottomSpacer: {
    height: 24,
  },
});
