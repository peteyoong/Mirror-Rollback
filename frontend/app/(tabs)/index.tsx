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
  Platform,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { useTheme, ThemeMode } from '../../contexts/ThemeContext';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import api from '../../services/api';
import { storage } from '../../store';
import DebugComputeInputs from '../../components/DebugComputeInputs';
import { InlineReflectButton } from '../../components/UniversalReflectButton';
import LunarReflectionSignalCard from '../../components/LunarReflectionSignalCard';
import KeystoneHeroCard, { KeystonePatternData } from '../../components/KeystoneHeroCard';

interface PatternCategory {
  category_id: string;
  category_name: string;
  signal_strength: string;
  pattern_score: number;
  synthesis?: string;
  summary: string;
}

interface PatternTension {
  category_a: string;
  category_b: string;
  summary: string;
  reflection_prompt: string;
}

interface JournalEntry {
  id: string;
  content: string;
  timestamp: string;
  source_lens?: string;
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
  const { theme, isDark, themeMode, setThemeMode } = useTheme();
  const { user, hasTriedSessionRestore, isRestoringSession, clearUser } = useAppStore();
  const router = useRouter();
  
  // KEYSTONE PATTERN: Single source of truth for the day
  const [keystoneData, setKeystoneData] = useState<KeystonePatternData | null>(null);
  const [keystoneLoading, setKeystoneLoading] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentDate, setCurrentDate] = useState<string>(getLocalDateString());
  const lastLoadedDateRef = useRef<string | null>(null);
  
  // REMOVED: activeInfluences - no longer rendered
  // REMOVED: topPatterns, patternTension - Patterns tab disabled
  
  // Recent reflection for continuity (demoted below navigation)
  const [recentReflection, setRecentReflection] = useState<JournalEntry | null>(null);
  
  // Lifeline event count for bridge section (demoted)
  const [lifelineEventCount, setLifelineEventCount] = useState<number>(0);
  
  // Reflector status for Lunar card
  const [userIsReflector, setUserIsReflector] = useState(false);
  
  // Settings modal
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  // Handler for logout action sheet
  const handleUserPress = () => {
    setShowSettingsModal(true);
  };

  const handleLogout = async () => {
    setShowSettingsModal(false);
    await clearUser();
    router.replace('/welcome');
  };

  const handleThemeChange = (mode: ThemeMode) => {
    setThemeMode(mode);
  };

  // Settings Modal Component
  const renderSettingsModal = () => (
    <Modal
      visible={showSettingsModal}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowSettingsModal(false)}
    >
      <SafeAreaView style={[styles.modalContainer, { backgroundColor: theme.background }]}>
        <View style={[styles.modalHeader, { borderBottomColor: theme.border }]}>
          <Text style={[styles.modalTitle, { color: theme.text }]}>Settings</Text>
          <TouchableOpacity 
            onPress={() => setShowSettingsModal(false)}
            style={styles.closeButton}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={[styles.closeButtonText, { color: theme.text }]}>Done</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.modalContent}>
          <View style={[styles.settingsSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.settingsSectionTitle, { color: theme.textTertiary }]}>ACCOUNT</Text>
            <View style={styles.settingsRow}>
              <Text style={[styles.settingsLabel, { color: theme.text }]}>Name</Text>
              <Text style={[styles.settingsValue, { color: theme.textSecondary }]}>{user?.name || 'Unknown'}</Text>
            </View>
            <View style={[styles.settingsDivider, { backgroundColor: theme.border }]} />
            <View style={styles.settingsRow}>
              <Text style={[styles.settingsLabel, { color: theme.text }]}>Email</Text>
              <Text style={[styles.settingsValue, { color: theme.textSecondary }]}>{user?.email || 'Unknown'}</Text>
            </View>
          </View>

          <View style={[styles.settingsSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.settingsSectionTitle, { color: theme.textTertiary }]}>APPEARANCE</Text>
            <TouchableOpacity style={styles.settingsRow} onPress={() => handleThemeChange('system')}>
              <Text style={[styles.settingsLabel, { color: theme.text }]}>System</Text>
              {themeMode === 'system' && <Text style={[styles.checkmark, { color: theme.accent }]}>✓</Text>}
            </TouchableOpacity>
            <View style={[styles.settingsDivider, { backgroundColor: theme.border }]} />
            <TouchableOpacity style={styles.settingsRow} onPress={() => handleThemeChange('light')}>
              <Text style={[styles.settingsLabel, { color: theme.text }]}>Light</Text>
              {themeMode === 'light' && <Text style={[styles.checkmark, { color: theme.accent }]}>✓</Text>}
            </TouchableOpacity>
            <View style={[styles.settingsDivider, { backgroundColor: theme.border }]} />
            <TouchableOpacity style={styles.settingsRow} onPress={() => handleThemeChange('dark')}>
              <Text style={[styles.settingsLabel, { color: theme.text }]}>Dark</Text>
              {themeMode === 'dark' && <Text style={[styles.checkmark, { color: theme.accent }]}>✓</Text>}
            </TouchableOpacity>
          </View>

          <View style={[styles.settingsSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <TouchableOpacity style={styles.settingsRow} onPress={handleLogout}>
              <Text style={[styles.logoutText, { color: theme.error }]}>Log Out</Text>
            </TouchableOpacity>
          </View>

          <Text style={[styles.appVersion, { color: theme.textTertiary }]}>Mirror v1.0.0</Text>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );

  // Check for date change
  useEffect(() => {
    const checkDateChange = () => {
      const newDate = getLocalDateString();
      if (newDate !== currentDate) {
        setCurrentDate(newDate);
        lastLoadedDateRef.current = null;
      }
    };
    const interval = setInterval(checkDateChange, 60000);
    return () => clearInterval(interval);
  }, [currentDate]);

  // Main data loading
  useEffect(() => {
    if (hasTriedSessionRestore && !isRestoringSession && user?.id) {
      if (lastLoadedDateRef.current !== currentDate) {
        loadAllData();
      }
    }
  }, [user, hasTriedSessionRestore, isRestoringSession, currentDate]);

  const loadAllData = async () => {
    if (!user?.id) return;
    setIsLoading(true);
    
    await Promise.all([
      loadKeystonePattern(),  // KEYSTONE: Single source of truth
      // loadPatternData(),    // REMOVED: Patterns tab disabled
      loadRecentReflection(),
      loadLifelineCount(),
    ]);
    
    setIsLoading(false);
  };

  const loadLifelineCount = async () => {
    if (!user?.id) return;
    
    try {
      const response = await api.get(`/lifeline/${user.id}`);
      if (response.data?.event_count !== undefined) {
        setLifelineEventCount(response.data.event_count);
      }
    } catch (err) {
      console.log('[Lifeline] Failed to load count:', err);
      setLifelineEventCount(0);
    }
  };

  // Task 75: Removed loadSynthesisTeaser - HomeArchetypeCard fetches its own data

  // KEYSTONE PATTERN: Load the single source of truth for the day
  const loadKeystonePattern = async () => {
    if (!user?.id) return;
    setKeystoneLoading(true);
    const dateToLoad = getLocalDateString();

    try {
      const response = await api.get(`/keystone-pattern/${user.id}`);
      const data = response.data;
      
      setKeystoneData({
        pattern_id: data.pattern_id,
        pattern_label: data.pattern_label,
        behavior_sequence: data.behavior_sequence,
        confidence: data.confidence,
        sources: data.sources || [],
        date: data.date || dateToLoad,
        cached: data.cached,
      });
      
      lastLoadedDateRef.current = dateToLoad;
      console.log('[KeystonePattern] Loaded:', data.pattern_label);
    } catch (err: any) {
      console.log('[KeystonePattern] Load error:', err);
      // Fallback pattern
      setKeystoneData({
        pattern_id: "fallback",
        pattern_label: "Something's Here",
        behavior_sequence: [
          "There's a pattern present today.",
          "You might not have words for it yet.",
          "That's okay. Start noticing."
        ],
        confidence: 0.3,
        sources: [],
        date: dateToLoad,
        cached: false,
      });
      lastLoadedDateRef.current = dateToLoad;
    } finally {
      setKeystoneLoading(false);
    }
  };

  // REMOVED: loadPatternData - Patterns tab disabled
  // const loadPatternData = async () => { ... };

  const loadRecentReflection = async () => {
    if (!user?.id) return;
    
    try {
      const response = await api.get(`/journal/${user.id}`, {
        params: { limit: 1 }
      });
      if (response.data && response.data.length > 0) {
        setRecentReflection(response.data[0]);
      }
    } catch (err) {
      console.log('[RecentReflection] Failed to load:', err);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadAllData();
    setIsRefreshing(false);
  };

  // Navigate to reflection chat
  const handleReflect = useCallback(() => {
    router.push('/reflection-chat');
  }, [router]);

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

  // Format recent reflection date
  const formatRelativeDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return 'recently';
      
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) return 'Today';
      if (diffDays === 1) return 'Yesterday';
      if (diffDays < 7) return `${diffDays} days ago`;
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return 'recently';
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      
      {/* Minimal Header */}
      <View style={[styles.header, { backgroundColor: theme.background }]}>
        <Text style={[styles.headerTitle, { color: theme.textTertiary }]}>MIRROR</Text>
        <TouchableOpacity 
          style={styles.userCluster}
          onPress={handleUserPress}
          activeOpacity={0.7}
          hitSlop={{ top: 15, bottom: 15, left: 15, right: 15 }}
        >
          <Text style={[styles.userName, { color: theme.textSecondary }]} numberOfLines={1}>
            {user?.name?.split(' ')[0] || 'Account'}
          </Text>
          <Text style={[styles.chevron, { color: theme.textTertiary }]}>›</Text>
        </TouchableOpacity>
      </View>
      
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
        {/* ===================================================================
            POSITION 1: KEYSTONE PATTERN - ALWAYS FIRST. NO EXCEPTIONS.
            ARCHITECTURE LOCK: This must be the FIRST rendered content block.
            - If loading: show skeleton placeholder IN THIS POSITION
            - If no data: show fallback IN THIS POSITION
            - NEVER shift this position based on data availability
            =================================================================== */}
        {!userIsReflector && (
          <KeystoneHeroCard 
            data={keystoneData} 
            isLoading={isLoading || keystoneLoading} 
          />
        )}

        {/* ===================================================================
            POSITION 1 (REFLECTORS ONLY): LUNAR REFLECTION
            Replaces Keystone for Reflector types only
            =================================================================== */}
        {userIsReflector && user?.id && (
          <LunarReflectionSignalCard 
            userId={user.id} 
            onReflectorStatus={(isReflector) => {
              if (isReflector && !userIsReflector) {
                setUserIsReflector(true);
              }
            }}
          />
        )}

        {/* ===================================================================
            POSITION 2: NAVIGATION - Explore Lenses / Life
            ALWAYS renders after Keystone, even if loading
            =================================================================== */}
        <View style={styles.doorwaysSection}>
          <View style={styles.doorwaysRow}>
            <TouchableOpacity
              style={[styles.doorwaySecondary, { backgroundColor: theme.surface, borderColor: theme.border }]}
              onPress={() => router.push('/(tabs)/lenses')}
              activeOpacity={0.7}
            >
              <Text style={[styles.doorwayIconSmall, { color: theme.textSecondary }]}>◇</Text>
              <Text style={[styles.doorwayTitleSmall, { color: theme.text }]}>Explore Lenses</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.doorwaySecondary, { backgroundColor: theme.surface, borderColor: theme.border }]}
              onPress={() => router.push('/(tabs)/life')}
              activeOpacity={0.7}
            >
              <Text style={[styles.doorwayIconSmall, { color: theme.textSecondary }]}>❧</Text>
              <Text style={[styles.doorwayTitleSmall, { color: theme.text }]}>Your Lifeline</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* ===================================================================
            POSITION 3: YOUR LIFELINE
            ALWAYS renders in this position after Navigation
            =================================================================== */}
        <View style={[styles.lifelineBridge, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.lifelineBridgeLabel, { color: theme.textTertiary }]}>
            YOUR LIFELINE
          </Text>
          <Text style={[styles.lifelineBridgeText, { color: theme.textSecondary }]}>
            {lifelineEventCount > 0 
              ? "The patterns you notice today often began much earlier."
              : "Mirror learns from the moments that shaped you."}
          </Text>
          <TouchableOpacity
            style={[styles.lifelineBridgeCTA, { backgroundColor: theme.accent }]}
            onPress={() => router.push('/(tabs)/life')}
            activeOpacity={0.8}
          >
            <Text style={styles.lifelineBridgeCTAText}>
              {lifelineEventCount > 0 ? 'Explore your Lifeline' : 'Start your Lifeline'}
            </Text>
          </TouchableOpacity>
          {lifelineEventCount > 0 && (
            <Text style={[styles.lifelineBridgeCount, { color: theme.textTertiary }]}>
              {lifelineEventCount} moment{lifelineEventCount !== 1 ? 's' : ''} mapped
            </Text>
          )}
        </View>

        {/* ===================================================================
            POSITION 4: MIRROR REMEMBERS
            Renders in position, content appears when data available
            =================================================================== */}
        {recentReflection && (
          <View style={[styles.continuitySection, { borderColor: theme.border }]}>
            <Text style={[styles.continuityTitle, { color: theme.textTertiary }]}>
              MIRROR REMEMBERS
            </Text>
            
            {/* Recent Reflection - feels like a note to self */}
            <TouchableOpacity 
              style={[styles.continuityCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
              onPress={() => router.push('/(tabs)/journal')}
              activeOpacity={0.7}
            >
              <Text style={[styles.continuityLabel, { color: theme.textTertiary }]}>
                A thought you left yourself · {formatRelativeDate(recentReflection.timestamp)}
              </Text>
              <Text 
                style={[styles.continuityText, { color: theme.textSecondary }]}
                numberOfLines={2}
              >
                "{recentReflection.content}"
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {/* ===================================================================
            POSITION 5: ACTIVE PATTERNS - TEMPORARILY HIDDEN (pending rebuild)
            =================================================================== */}
        {/* Patterns section removed - will be rebuilt as standalone feature */}

        {/* ===================================================================
            POSITION 6: FORUMS
            =================================================================== */}
        <TouchableOpacity 
          style={[styles.forumsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
          onPress={() => router.push('/forums')}
          activeOpacity={0.7}
        >
          <View style={styles.forumsCardContent}>
            <Text style={[styles.forumsIcon, { color: theme.accent }]}>◎</Text>
            <View style={styles.forumsTextContent}>
              <Text style={[styles.forumsTitle, { color: theme.text }]}>Forums</Text>
              <Text style={[styles.forumsSubtitle, { color: theme.textTertiary }]}>
                Reflect with your trusted circle
              </Text>
            </View>
          </View>
          <Text style={[styles.forumsChevron, { color: theme.textTertiary }]}>›</Text>
        </TouchableOpacity>

        {/* Debug Panel */}
        {user?.id && <DebugComputeInputs userId={user.id} />}

        <View style={styles.bottomSpacer} />
      </ScrollView>

      {/* Settings Modal */}
      {renderSettingsModal()}
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
    paddingVertical: 12,
    height: 48,
  },
  headerTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.5,
    opacity: 0.6,
  },
  userCluster: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  userName: {
    fontSize: 14,
    maxWidth: 120,
  },
  chevron: {
    fontSize: 18,
    fontWeight: '400',
    marginLeft: 2,
  },
  scrollContent: {
    flexGrow: 1,
    paddingTop: 8,
    paddingBottom: 120, // Extra padding for PWA banner overlay
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  restoringText: {
    fontSize: 14,
    marginTop: 8,
  },
  loadingContainer: {
    paddingVertical: 80,
    alignItems: 'center',
  },

  // =========================================================================
  // SECTION 1: HERO
  // =========================================================================
  heroSection: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 28,
  },
  heroStatement: {
    fontSize: 22,
    lineHeight: 32,
    fontWeight: '400',
    letterSpacing: 0.2,
    marginBottom: 16,
  },
  heroSupport: {
    fontSize: 15,
    lineHeight: 23,
    fontStyle: 'italic',
    marginBottom: 24,
    paddingLeft: 14,
    borderLeftWidth: 2,
    borderLeftColor: Colors.border,
  },
  heroEcho: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
    marginBottom: 16,
    paddingVertical: 10,
    paddingHorizontal: 14,
    backgroundColor: 'rgba(139, 92, 246, 0.08)',
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: Colors.accent,
  },
  heroCause: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 16,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: 'rgba(100, 100, 100, 0.06)',
    borderRadius: 6,
    borderLeftWidth: 2,
    borderLeftColor: Colors.border,
  },
  heroDecisionReplay: {
    marginBottom: 16,
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderStyle: 'dashed',
  },
  heroDecisionReplayText: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
  heroPhaseLine: {
    marginBottom: 16,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
  },
  heroPhaseLineText: {
    fontSize: 13,
    lineHeight: 20,
    fontWeight: '500',
  },
  heroAwarenessPrompt: {
    marginBottom: 16,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
  },
  heroAwarenessLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  heroAwarenessText: {
    fontSize: 14,
    lineHeight: 22,
  },
  heroCTA: {
    alignSelf: 'flex-start',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 24,
  },
  heroCTAText: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.3,
  },

  // =========================================================================
  // SECTION 2: INFLUENCES
  // =========================================================================
  influencesSection: {
    marginHorizontal: 20,
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    marginBottom: 8,
  },
  influencesTitle: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1.2,
    marginBottom: 12,
    opacity: 0.7,
  },
  influencesList: {
    gap: 8,
  },
  influenceItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  influenceDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    marginRight: 10,
  },
  influenceText: {
    fontSize: 13,
    lineHeight: 18,
  },

  // =========================================================================
  // SECTION 3: DOORWAYS
  // =========================================================================
  doorwaysSection: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  doorwayPrimary: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
  },
  doorwayIcon: {
    fontSize: 28,
    marginRight: 14,
  },
  doorwayContent: {
    flex: 1,
  },
  doorwayTitle: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 4,
  },
  doorwaySubtitle: {
    fontSize: 13,
    lineHeight: 18,
  },
  doorwayChevron: {
    fontSize: 22,
    marginLeft: 8,
  },
  doorwaysRow: {
    flexDirection: 'row',
    gap: 12,
  },
  doorwaySecondary: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 18,
    paddingHorizontal: 12,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  doorwayIconSmall: {
    fontSize: 22,
    marginBottom: 8,
  },
  doorwayTitleSmall: {
    fontSize: 13,
    fontWeight: '500',
  },

  // =========================================================================
  // =========================================================================
  // SECTION 4: ARCHETYPE CARD (Task 75: Unified Narrative)
  // =========================================================================
  archetypeSection: {
    marginHorizontal: 20,
    marginTop: 8,
    marginBottom: 4,
  },

  // =========================================================================
  // SECTION 4.5: LIFELINE BRIDGE
  // =========================================================================
  lifelineBridge: {
    marginHorizontal: 20,
    marginTop: 16,
    marginBottom: 8,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
  },
  lifelineBridgeLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 8,
  },
  lifelineBridgeText: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 16,
  },
  lifelineBridgeCTA: {
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  lifelineBridgeCTAText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  lifelineBridgeCount: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 10,
  },

  // =========================================================================
  // SECTION 5: CONTINUITY
  // =========================================================================
  continuitySection: {
    marginHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  continuityTitle: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1.2,
    marginBottom: 12,
    opacity: 0.7,
  },
  continuityCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 10,
  },
  continuityLabel: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 0.3,
    marginBottom: 6,
  },
  continuityText: {
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  tensionTitle: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 4,
  },

  // =========================================================================
  // SECTION 5: DEPTH PREVIEW
  // =========================================================================
  depthSection: {
    marginHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  depthHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  depthTitle: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1.2,
    opacity: 0.7,
  },
  depthLink: {
    fontSize: 13,
    fontWeight: '500',
  },
  patternPills: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  patternPill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 20,
    borderWidth: StyleSheet.hairlineWidth,
  },
  patternPillText: {
    fontSize: 13,
    fontWeight: '500',
  },
  patternPillBadge: {
    marginLeft: 4,
    fontSize: 12,
    fontWeight: '600',
  },

  // =========================================================================
  // FORUMS CARD
  // =========================================================================
  forumsCard: {
    marginHorizontal: 20,
    marginTop: 8,
    marginBottom: 4,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  forumsCardContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  forumsIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  forumsTextContent: {
    flex: 1,
  },
  forumsTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 2,
  },
  forumsSubtitle: {
    fontSize: 12,
  },
  forumsChevron: {
    fontSize: 22,
    marginLeft: 8,
  },

  bottomSpacer: {
    height: 24,
  },

  // =========================================================================
  // SETTINGS MODAL
  // =========================================================================
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  closeButton: {
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  closeButtonText: {
    fontSize: 17,
    fontWeight: '500',
  },
  modalContent: {
    flex: 1,
    paddingTop: 20,
  },
  settingsSection: {
    marginHorizontal: 16,
    marginBottom: 20,
    borderRadius: 12,
    borderWidth: 1,
    overflow: 'hidden',
  },
  settingsSectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  settingsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  settingsLabel: {
    fontSize: 16,
  },
  settingsValue: {
    fontSize: 16,
  },
  settingsDivider: {
    height: 1,
    marginLeft: 16,
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '500',
  },
  checkmark: {
    fontSize: 18,
    fontWeight: '600',
  },
  appVersion: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 20,
    marginBottom: 40,
  },
});
