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
import TodayPatternCard from '../../components/TodayPatternCard';
import ActionCard from '../../components/ActionCard';
import { useExperienceControls } from '../../hooks/useExperienceControls';
import { HOME_LAYOUT, MirrorMode } from '../../types/mirror-profile';
// PatternCard (Pattern Mirror) TEMPORARILY REMOVED - will reintroduce after signal-based engine upgrade
// InlineSignalsCard REMOVED - Signals now live only inside TodayPatternCard + dedicated Signals page

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
  
  // MODE-BASED LAYOUT - Get current mode and layout config
  const { mode, controls } = useExperienceControls();
  const homeLayout = HOME_LAYOUT[mode];
  
  // Track rendered card count for maxCards enforcement
  let cardCount = 0;
  
  // REMOVED: keystoneData, keystoneLoading - PatternCard now handles its own data
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
      // REMOVED: loadKeystonePattern - PatternCard handles its own data
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

  // REMOVED: loadKeystonePattern - PatternCard (Pattern Mirror V1) now handles its own data

  // REMOVED: loadPatternData - Patterns tab disabled

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
      
      {/* Minimal Header - Daily entry point feel */}
      <View style={[styles.header, { backgroundColor: theme.background }]}>
        <View style={styles.headerLeft}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Mirror</Text>
          <Text style={[styles.headerSubtitle, { color: theme.textTertiary }]}>Right now</Text>
        </View>
        <TouchableOpacity 
          style={styles.userCluster}
          onPress={handleUserPress}
          activeOpacity={0.7}
          hitSlop={{ top: 15, bottom: 15, left: 15, right: 15 }}
        >
          <Text style={[styles.userName, { color: theme.textSecondary }]} numberOfLines={1}>
            {user?.name?.split(' ')[0] || 'You'}
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
            MODE-BASED HOME LAYOUT
            
            GROUNDING: Minimal - 2 cards max, no signals inline
            EXPLORATORY: Rich - 4 cards, signals inline, synthesis
            DIRECTIVE: Clear - 3 cards, action card
            =================================================================== */}
        
        {/* ===================================================================
            POSITION 1: TODAY'S PATTERN (Always first - primary card)
            =================================================================== */}
        {user?.id && (
          <View style={{ paddingHorizontal: 20, marginBottom: 16 }}>
            <TodayPatternCard 
              userId={user.id} 
              theme={theme}
              onReflect={() => router.push('/(tabs)/reflect?view=mirror')}
            />
          </View>
        )}

        {/* ===================================================================
            POSITION 2: SECONDARY CARD (Mode-dependent)
            - grounding → journal/reflection card
            - exploratory → lenses exploration (signals now ONLY in TodayPatternCard)
            - directive → action card
            
            NOTE: InlineSignalsCard REMOVED - Signals should not compete with 
            TodayPatternCard. Signals live inside the pattern, not as a separate card.
            =================================================================== */}
        
        {homeLayout.secondary === 'action' && user?.id && (
          <View style={{ paddingHorizontal: 20, marginBottom: 16 }}>
            <ActionCard userId={user.id} theme={theme} />
          </View>
        )}
        
        {/* Lenses exploration card for exploratory mode */}
        {homeLayout.secondary === 'lenses' && (
          <View style={{ paddingHorizontal: 20, marginBottom: 16 }}>
            <TouchableOpacity
              style={[styles.lensesExploreCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
              onPress={() => router.push('/(tabs)/lenses')}
              activeOpacity={0.7}
            >
              <Text style={[styles.lensesExploreLabel, { color: theme.textTertiary }]}>EXPLORE DEEPER</Text>
              <Text style={[styles.lensesExploreTitle, { color: theme.text }]}>
                Your lenses hold more
              </Text>
              <Text style={[styles.lensesExploreDescription, { color: theme.textSecondary }]}>
                See how astrology, human design, and more illuminate today's pattern.
              </Text>
              <View style={styles.lensesExploreFooter}>
                <Text style={[styles.lensesExploreCta, { color: theme.accent }]}>
                  See your lenses →
                </Text>
              </View>
            </TouchableOpacity>
          </View>
        )}
        
        {homeLayout.secondary === 'journal' && recentReflection && (
          <View style={[styles.continuitySection, { borderColor: theme.border }]}>
            <Text style={[styles.continuityTitle, { color: theme.textTertiary }]}>
              A THOUGHT YOU LEFT YOURSELF
            </Text>
            <TouchableOpacity 
              style={[styles.continuityCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
              onPress={() => router.push('/(tabs)/reflect')}
              activeOpacity={0.7}
            >
              <Text style={[styles.continuityLabel, { color: theme.textTertiary }]}>
                {formatRelativeDate(recentReflection.timestamp)}
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
            POSITION 2b (REFLECTORS ONLY): LUNAR REFLECTION
            Additional card for Reflector types only - respects maxCards
            =================================================================== */}
        {userIsReflector && user?.id && homeLayout.maxCards > 2 && (
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
            POSITION 3: NAVIGATION (Mode-dependent)
            Hidden in grounding mode for minimal feel
            =================================================================== */}
        {homeLayout.showNavigation && (
          <View style={styles.doorwaysSection}>
            <View style={styles.doorwaysRow}>
              <TouchableOpacity
                style={[styles.doorwaySecondary, { backgroundColor: theme.surface, borderColor: theme.border }]}
                onPress={() => router.push('/(tabs)/lenses')}
                activeOpacity={0.7}
              >
                <Text style={[styles.doorwayTitleSmall, { color: theme.text }]}>See your lenses</Text>
                <Text style={[styles.doorwaySubtext, { color: theme.textTertiary }]}>Astrology, HD, more</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.doorwaySecondary, { backgroundColor: theme.surface, borderColor: theme.border }]}
                onPress={() => router.push('/(tabs)/life')}
                activeOpacity={0.7}
              >
                <Text style={[styles.doorwayTitleSmall, { color: theme.text }]}>Your past</Text>
                <Text style={[styles.doorwaySubtext, { color: theme.textTertiary }]}>Key moments mapped</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* ===================================================================
            POSITION 4: MIRROR REMEMBERS (exploratory mode only, if not journal secondary)
            =================================================================== */}
        {homeLayout.secondary !== 'journal' && recentReflection && homeLayout.maxCards >= 3 && (
          <View style={[styles.continuitySection, { borderColor: theme.border }]}>
            <Text style={[styles.continuityTitle, { color: theme.textTertiary }]}>
              MIRROR REMEMBERS
            </Text>
            
            <TouchableOpacity 
              style={[styles.continuityCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
              onPress={() => router.push('/(tabs)/reflect')}
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
            POSITION 5: DEEPER CONTEXT (exploratory mode only)
            Only shown for users without lifeline events
            =================================================================== */}
        {lifelineEventCount === 0 && homeLayout.maxCards >= 4 && (
          <View style={[styles.lifelineBridge, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.lifelineBridgeText, { color: theme.textSecondary }]}>
              Mirror gets sharper the more it knows about you.
            </Text>
            <TouchableOpacity
              style={[styles.lifelineBridgeCTA, { backgroundColor: theme.accent }]}
              onPress={() => router.push('/(tabs)/life')}
              activeOpacity={0.8}
            >
              <Text style={styles.lifelineBridgeCTAText}>
                Add key moments from your past
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {/* ===================================================================
            POSITION 6: FORUMS (Mode-dependent)
            Hidden in grounding and directive for focus
            =================================================================== */}
        {homeLayout.showForums && (
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
        )}

        {/* Debug Panel */}
        {user?.id && <DebugComputeInputs userId={user.id} />}

        {/* ===================================================================
            FORUM ENTRY FOOTER - ALWAYS VISIBLE
            Subtle text links for forum access, visually understated
            =================================================================== */}
        <View style={styles.forumFooter}>
          <TouchableOpacity
            style={styles.forumFooterLink}
            onPress={() => router.push('/forums/create')}
            activeOpacity={0.6}
          >
            <Text style={[styles.forumFooterText, { color: theme.textTertiary }]}>
              Create Forum
            </Text>
          </TouchableOpacity>
          
          <Text style={[styles.forumFooterDivider, { color: theme.textTertiary }]}>·</Text>
          
          <TouchableOpacity
            style={styles.forumFooterLink}
            onPress={() => router.push('/forums')}
            activeOpacity={0.6}
          >
            <Text style={[styles.forumFooterText, { color: theme.textTertiary }]}>
              Join Forum
            </Text>
          </TouchableOpacity>
        </View>

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
    height: 52,
  },
  headerLeft: {
    flexDirection: 'column',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  headerSubtitle: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 0.5,
    marginTop: 2,
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
  // REMOVED: patternSection, sectionLabel - Pattern card handles its own layout
  // =========================================================================

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
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 4,
  },
  doorwaySubtext: {
    fontSize: 11,
    fontWeight: '400',
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

  // =========================================================================
  // LENSES EXPLORATION CARD (for exploratory mode)
  // =========================================================================
  lensesExploreCard: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 16,
  },
  lensesExploreLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  lensesExploreTitle: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 6,
  },
  lensesExploreDescription: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  lensesExploreFooter: {
    marginTop: 4,
  },
  lensesExploreCta: {
    fontSize: 14,
    fontWeight: '500',
  },
  
  // =========================================================================
  // FORUM FOOTER - Subtle entry links
  // =========================================================================
  forumFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    marginTop: 8,
    gap: 12,
  },
  forumFooterLink: {
    paddingVertical: 6,
    paddingHorizontal: 4,
  },
  forumFooterText: {
    fontSize: 13,
    fontWeight: '400',
  },
  forumFooterDivider: {
    fontSize: 13,
    opacity: 0.5,
  },
});
