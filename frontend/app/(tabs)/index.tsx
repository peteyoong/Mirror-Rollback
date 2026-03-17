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
import DailyPatternSignalCard from '../../components/DailyPatternSignalCard';
import LunarReflectionSignalCard from '../../components/LunarReflectionSignalCard';
import HomeArchetypeCard from '../../components/HomeArchetypeCard';

interface DailyKeystone {
  date: string;
  title: string;
  keystone: string;
  reflect_question: string;
  micro_affirmation: string;
  personal_echo?: string | null;
  cause_layer?: string | null;
  decision_replay?: string | null;
  pattern_phase_line?: string | null;
  pattern_phase?: {
    phase: string;
    display: string;
    description: string;
    confidence: number;
    sequence_labels: string[];
  } | null;
  decision_awareness_prompt?: string | null;
  decision_awareness?: {
    style: string;
    style_display: string;
    confidence: number;
  } | null;
  source_signals: {
    used: string[];
    tone: string;
  };
  daily_seed: string;
  is_first_visit: boolean;
  is_enriched?: boolean;
}

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

interface ActiveInfluence {
  source: string;
  label: string;
  detail?: string;
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
  
  // Core data states
  const [keystone, setKeystone] = useState<DailyKeystone | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentDate, setCurrentDate] = useState<string>(getLocalDateString());
  const lastLoadedDateRef = useRef<string | null>(null);
  
  // Active influences for "Why This Is Showing Up"
  const [activeInfluences, setActiveInfluences] = useState<ActiveInfluence[]>([]);
  
  // Top patterns for depth preview
  const [topPatterns, setTopPatterns] = useState<PatternCategory[]>([]);
  const [patternTension, setPatternTension] = useState<PatternTension | null>(null);
  
  // Recent reflection for continuity
  const [recentReflection, setRecentReflection] = useState<JournalEntry | null>(null);
  
  // Cross-lens synthesis teaser
  const [synthesisTeaser, setSynthesisTeaser] = useState<SynthesisTeaserData | null>(null);
  const [isSynthesisLoading, setIsSynthesisLoading] = useState(false);
  
  // Lifeline event count for bridge section
  const [lifelineEventCount, setLifelineEventCount] = useState<number>(0);
  
  // Reflector status for conditional signal card rendering (Task 49)
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
      loadKeystone(),
      loadPatternData(),
      loadRecentReflection(),
      loadSynthesisTeaser(),
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

  const loadSynthesisTeaser = async () => {
    if (!user?.id) return;
    setIsSynthesisLoading(true);
    
    try {
      const response = await api.get(`/synthesis/${user.id}/teaser`);
      if (response.data) {
        setSynthesisTeaser(response.data);
      }
    } catch (err) {
      console.log('[SynthesisTeaser] Failed to load:', err);
      // Silently fail - synthesis teaser is optional
      setSynthesisTeaser(null);
    } finally {
      setIsSynthesisLoading(false);
    }
  };

  const loadKeystone = async () => {
    if (!user?.id) return;
    const dateToLoad = getLocalDateString();

    try {
      const response = await api.get(`/mirror/home/${user.id}`, {
        params: { date: dateToLoad }
      });
      setKeystone(response.data);
      lastLoadedDateRef.current = dateToLoad;
      
      // Extract active influences from source_signals
      const influences: ActiveInfluence[] = [];
      const signals = response.data.source_signals?.used || [];
      
      if (signals.includes('lens_core')) {
        influences.push({ source: 'Human Design', label: 'Your core pattern is active' });
      }
      if (signals.includes('timeline')) {
        influences.push({ source: 'Timeline', label: 'Current life phase' });
      }
      if (signals.includes('transit')) {
        influences.push({ source: 'Transit', label: 'Planetary movement today' });
      }
      if (signals.includes('gene_keys')) {
        influences.push({ source: 'Gene Keys', label: 'Shadow/Gift dynamic' });
      }
      
      setActiveInfluences(influences);
      
      // Poll for enriched version if needed
      if (response.data.is_enriched === false) {
        setTimeout(async () => {
          try {
            const enrichedResponse = await api.get(`/mirror/home/${user.id}`, {
              params: { date: dateToLoad }
            });
            if (enrichedResponse.data.is_enriched && lastLoadedDateRef.current === dateToLoad) {
              setKeystone(enrichedResponse.data);
            }
          } catch (e) {
            console.log('[MirrorHome] Enrichment poll failed');
          }
        }, 5000);
      }
    } catch (err: any) {
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
    }
  };

  const loadPatternData = async () => {
    if (!user?.id) return;
    
    try {
      const response = await api.get(`/pattern-graph/${user.id}`);
      if (response.data.success) {
        const { pattern_tensions, categories } = response.data;
        
        // Get top 3 patterns by score
        const sortedPatterns = (categories || [])
          .filter((c: PatternCategory) => c.signal_strength !== 'quiet')
          .sort((a: PatternCategory, b: PatternCategory) => b.pattern_score - a.pattern_score)
          .slice(0, 3);
        setTopPatterns(sortedPatterns);
        
        // Get top tension
        if (pattern_tensions && pattern_tensions.length > 0) {
          setPatternTension(pattern_tensions[0]);
        }
        
        // Add pattern influence if recurring
        if (sortedPatterns.length > 0 && sortedPatterns[0].signal_strength === 'recurring') {
          setActiveInfluences(prev => {
            if (!prev.find(i => i.source === 'Pattern')) {
              return [...prev, { 
                source: 'Pattern', 
                label: `${sortedPatterns[0].category_name} is recurring` 
              }];
            }
            return prev;
          });
        }
      }
    } catch (err) {
      console.log('[PatternData] Failed to load:', err);
    }
  };

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
        {/* Loading State */}
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.textTertiary} />
          </View>
        )}

        {/* ===================================================================
            SECTION 1: OPENING HIT - Hero Block
            =================================================================== */}
        {keystone && !isLoading && (
          <View style={styles.heroSection}>
            {/* Primary Personalized Statement */}
            <Text style={[styles.heroStatement, { color: theme.text }]}>
              {keystone.keystone}
            </Text>
            
            {/* Personal Echo from Lifeline (if available) */}
            {keystone.personal_echo && (
              <Text style={[styles.heroEcho, { color: theme.accent }]}>
                {keystone.personal_echo}
              </Text>
            )}
            
            {/* Cause Layer - Why this pattern keeps returning (if available) */}
            {keystone.cause_layer && (
              <Text style={[styles.heroCause, { color: theme.textSecondary }]}>
                {keystone.cause_layer}
              </Text>
            )}
            
            {/* Decision Replay - Past decision reference (if available) */}
            {keystone.decision_replay && (
              <View style={[styles.heroDecisionReplay, { borderColor: theme.accent, backgroundColor: `${theme.accent}08` }]}>
                <Text style={[styles.heroDecisionReplayText, { color: theme.text }]}>
                  {keystone.decision_replay}
                </Text>
              </View>
            )}
            
            {/* Pattern Phase Line - Current phase detection (if available) */}
            {keystone.pattern_phase_line && (
              <View style={[styles.heroPhaseLine, { backgroundColor: 'rgba(16, 185, 129, 0.08)', borderColor: 'rgba(16, 185, 129, 0.3)' }]}>
                <Text style={[styles.heroPhaseLineText, { color: '#10B981' }]}>
                  {keystone.pattern_phase_line}
                </Text>
              </View>
            )}
            
            {/* Decision Awareness Prompt - Reflective prompt (if available) */}
            {keystone.decision_awareness_prompt && (
              <View style={[styles.heroAwarenessPrompt, { borderColor: theme.border, backgroundColor: theme.surface }]}>
                <Text style={[styles.heroAwarenessLabel, { color: theme.textTertiary }]}>
                  DECISION AWARENESS
                </Text>
                <Text style={[styles.heroAwarenessText, { color: theme.textSecondary }]}>
                  {keystone.decision_awareness_prompt}
                </Text>
              </View>
            )}
            
            {/* Supporting Explanation */}
            <Text style={[styles.heroSupport, { color: theme.textSecondary }]}>
              {keystone.micro_affirmation}
            </Text>
            
            {/* Primary CTA */}
            <TouchableOpacity
              style={[styles.heroCTA, { backgroundColor: theme.accent }]}
              onPress={handleReflect}
              activeOpacity={0.8}
            >
              <Text style={[styles.heroCTAText, { color: '#FFFFFF' }]}>Reflect</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* ===================================================================
            SECTION 1.5: DAILY SIGNAL CARD - Task 43 & Task 49
            Shows either Lunar Reflection (for Reflectors) or Pattern Signal (for others)
            The LunarReflectionSignalCard notifies parent of Reflector status
            =================================================================== */}
        {!isLoading && user?.id && (
          <>
            {/* Lunar Reflection Signal - shows ONLY for Reflectors */}
            <LunarReflectionSignalCard 
              userId={user.id} 
              onReflectorStatus={(isReflector) => {
                // Store in local state to hide DailyPatternSignalCard for Reflectors
                if (isReflector && !userIsReflector) {
                  setUserIsReflector(true);
                }
              }}
            />
            {/* Daily Pattern Signal - shows ONLY for non-Reflectors */}
            {!userIsReflector && <DailyPatternSignalCard userId={user.id} />}
          </>
        )}

        {/* ===================================================================
            SECTION 2: WHY THIS IS SHOWING UP
            =================================================================== */}
        {activeInfluences.length > 0 && !isLoading && (
          <View style={[styles.influencesSection, { borderColor: theme.border }]}>
            <Text style={[styles.influencesTitle, { color: theme.textTertiary }]}>
              ACTIVE INFLUENCES
            </Text>
            <View style={styles.influencesList}>
              {activeInfluences.slice(0, 4).map((influence, index) => (
                <View key={index} style={styles.influenceItem}>
                  <View style={[styles.influenceDot, { backgroundColor: theme.accent }]} />
                  <Text style={[styles.influenceText, { color: theme.textSecondary }]}>
                    <Text style={{ fontWeight: '500', color: theme.text }}>{influence.source}</Text>
                    {' · '}
                    {influence.label}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* ===================================================================
            SECTION 3: THREE CLEAR DOORWAYS
            =================================================================== */}
        {!isLoading && (
          <View style={styles.doorwaysSection}>
            {/* Primary Doorway - Reflect */}
            <TouchableOpacity
              style={[styles.doorwayPrimary, { backgroundColor: theme.surface, borderColor: theme.border }]}
              onPress={handleReflect}
              activeOpacity={0.7}
            >
              <Text style={[styles.doorwayIcon, { color: theme.accent }]}>◉</Text>
              <View style={styles.doorwayContent}>
                <Text style={[styles.doorwayTitle, { color: theme.text }]}>Reflect</Text>
                <Text style={[styles.doorwaySubtitle, { color: theme.textTertiary }]}>
                  {keystone?.reflect_question || 'What feels present right now?'}
                </Text>
              </View>
              <Text style={[styles.doorwayChevron, { color: theme.textTertiary }]}>›</Text>
            </TouchableOpacity>

            {/* Secondary Doorways */}
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
                onPress={() => router.push('/(tabs)/patterns')}
                activeOpacity={0.7}
              >
                <Text style={[styles.doorwayIconSmall, { color: theme.textSecondary }]}>◈</Text>
                <Text style={[styles.doorwayTitleSmall, { color: theme.text }]}>View Patterns</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* ===================================================================
            SECTION 4: CROSS-LENS SYNTHESIS TEASER
            =================================================================== */}
        {!isLoading && (synthesisTeaser?.show_teaser || isSynthesisLoading) && (
          <View style={[styles.synthesisSection, { borderColor: theme.border }]}>
            <SynthesisTeaser 
              synthesis={synthesisTeaser} 
              isLoading={isSynthesisLoading} 
            />
          </View>
        )}

        {/* ===================================================================
            SECTION 4.5: LIFELINE BRIDGE
            =================================================================== */}
        {!isLoading && (
          <View style={[styles.lifelineBridge, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
            <Text style={[styles.lifelineBridgeLabel, { color: theme.textTertiary }]}>
              YOUR LIFELINE
            </Text>
            <Text style={[styles.lifelineBridgeText, { color: theme.textSecondary }]}>
              {lifelineEventCount > 0 
                ? "The patterns you see here often begin in the turning points of your life."
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
        )}

        {/* ===================================================================
            SECTION 5: CONTINUITY / MEMORY
            =================================================================== */}
        {!isLoading && (recentReflection || patternTension) && (
          <View style={[styles.continuitySection, { borderColor: theme.border }]}>
            <Text style={[styles.continuityTitle, { color: theme.textTertiary }]}>
              MIRROR REMEMBERS
            </Text>
            
            {/* Recent Reflection */}
            {recentReflection && (
              <TouchableOpacity 
                style={[styles.continuityCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
                onPress={() => router.push('/(tabs)/journal')}
                activeOpacity={0.7}
              >
                <Text style={[styles.continuityLabel, { color: theme.textTertiary }]}>
                  Last reflection · {formatRelativeDate(recentReflection.timestamp)}
                </Text>
                <Text 
                  style={[styles.continuityText, { color: theme.textSecondary }]}
                  numberOfLines={2}
                >
                  "{recentReflection.content}"
                </Text>
              </TouchableOpacity>
            )}
            
            {/* Active Tension */}
            {patternTension && (
              <TouchableOpacity 
                style={[styles.continuityCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
                onPress={() => router.push('/(tabs)/patterns')}
                activeOpacity={0.7}
              >
                <Text style={[styles.continuityLabel, { color: theme.textTertiary }]}>
                  Recurring dynamic
                </Text>
                <Text style={[styles.tensionTitle, { color: theme.text }]}>
                  {patternTension.category_a} ↔ {patternTension.category_b}
                </Text>
                <Text 
                  style={[styles.continuityText, { color: theme.textSecondary }]}
                  numberOfLines={2}
                >
                  {patternTension.summary}
                </Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* ===================================================================
            SECTION 6: DEPTH PREVIEW
            =================================================================== */}
        {!isLoading && topPatterns.length > 0 && (
          <View style={[styles.depthSection, { borderColor: theme.border }]}>
            <View style={styles.depthHeader}>
              <Text style={[styles.depthTitle, { color: theme.textTertiary }]}>
                TODAY'S ACTIVE PATTERNS
              </Text>
              <TouchableOpacity onPress={() => router.push('/(tabs)/patterns')}>
                <Text style={[styles.depthLink, { color: theme.accent }]}>See all</Text>
              </TouchableOpacity>
            </View>
            
            <View style={styles.patternPills}>
              {topPatterns.map((pattern, index) => (
                <View 
                  key={pattern.category_id} 
                  style={[
                    styles.patternPill, 
                    { 
                      backgroundColor: pattern.signal_strength === 'recurring' 
                        ? `${theme.accent}20` 
                        : theme.surface,
                      borderColor: pattern.signal_strength === 'recurring' 
                        ? theme.accent 
                        : theme.border 
                    }
                  ]}
                >
                  <Text style={[
                    styles.patternPillText, 
                    { 
                      color: pattern.signal_strength === 'recurring' 
                        ? theme.accent 
                        : theme.textSecondary 
                    }
                  ]}>
                    {pattern.category_name}
                  </Text>
                  {pattern.signal_strength === 'recurring' && (
                    <Text style={[styles.patternPillBadge, { color: theme.accent }]}>↑</Text>
                  )}
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Forums Entry */}
        {!isLoading && (
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
  // SECTION 4: SYNTHESIS
  // =========================================================================
  synthesisSection: {
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
