import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';
import { useRouter } from 'expo-router';

// Import types from the types module
import {
  FullChartData,
  CorePlacements,
  AstrologyDeepDiveCard,
  AstrologySummaryData,
} from '../services/astrology/astrologyTypes';

// Import the new tab components
import AstrologyAtAGlanceTab from './astrology/AstrologyAtAGlanceTab';
import AstrologyTodayTab from './astrology/AstrologyTodayTab';
import AstrologyTodayV3 from './astrology/AstrologyTodayV3';
import AstrologyDeepDiveTab from './astrology/AstrologyDeepDiveTab';
import AstrologyTimelineTab from './astrology/AstrologyTimelineTab';

// ============================================
// MAIN COMPONENT
// ============================================

interface AstrologyLensViewProps {
  userId: string;
  onOpenChat: () => void;
}

export default function AstrologyLensView({ userId, onOpenChat }: AstrologyLensViewProps) {
  const { theme } = useTheme();
  const router = useRouter();

  const [activeTab, setActiveTab] = useState<'at_a_glance' | 'today' | 'deep_dive' | 'timeline'>('at_a_glance');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summaryData, setSummaryData] = useState<AstrologySummaryData | null>(null);
  const [deepDiveData, setDeepDiveData] = useState<any>(null);
  const [snapshotData, setSnapshotData] = useState<any>(null);
  const [fullChartData, setFullChartData] = useState<FullChartData | null>(null);
  
  // State for collapsible sections (passed to AtAGlanceTab)
  const [aspectsExpanded, setAspectsExpanded] = useState(false);
  const [tensionsGiftsExpanded, setTensionsGiftsExpanded] = useState(false);
  
  // State for Deep Dive expanded cards
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set(['sun']));

  useEffect(() => {
    if (userId) {
      // Always fetch full chart data for deterministic astrology
      loadFullChartData();
      loadTabData(activeTab);
    }
  }, [userId, activeTab]);

  const loadFullChartData = async () => {
    if (!userId) return;
    try {
      const response = await api.get(`/astrology/chart/${userId}`);
      setFullChartData(response.data);
      console.log('[AstrologyLens] Full chart data loaded:', {
        success: response.data.success,
        chiron_present: !!response.data.natal?.planets?.Chiron,
        north_node_present: !!response.data.natal?.planets?.['North Node'],
        jupiter_present: !!response.data.natal?.planets?.Jupiter,
        saturn_present: !!response.data.natal?.planets?.Saturn,
        aspects_count: response.data.natal?.aspects?.length,
        transit_aspects_count: response.data.transits?.total_active_aspects,
        strongest_hits: response.data.transits?.strongest_hits?.length
      });
    } catch (err) {
      console.error('[AstrologyLens] Full chart data error:', err);
    }
  };

  const loadTabData = async (tab: string) => {
    if (!userId) return;
    setIsLoading(true);
    setError(null);

    try {
      if (tab === 'at_a_glance' || tab === 'summary') {
        const response = await api.get(`/astrology/summary/${userId}`);
        setSummaryData(response.data);
      } else if (tab === 'today') {
        try {
          const response = await api.get(`/astrology/snapshot/${userId}`);
          setSnapshotData(response.data);
        } catch {
          const response = await api.get(`/astrology/today/${userId}`);
          setSummaryData(response.data);
        }
      } else if (tab === 'deep_dive') {
        const response = await api.get(`/astrology/deep-dive/${userId}`);
        setDeepDiveData(response.data);
      }
    } catch (err: any) {
      console.error('Tab data error:', err);
      setError('Unable to load astrology data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleCard = (cardId: string) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(cardId)) {
        newSet.delete(cardId);
      } else {
        newSet.add(cardId);
      }
      return newSet;
    });
  };

  // Action handlers for Deep Dive
  const handleReflect = (card: AstrologyDeepDiveCard) => {
    router.push({
      pathname: '/(tabs)/reflect',
      params: {
        tab: 'mirror',
        context: `I'd like to reflect on "${card.title}": ${card.reflection}`
      }
    });
  };

  const handleJournal = (card: AstrologyDeepDiveCard) => {
    const journalPrompt = `Reflecting on: ${card.title}\n\n"${card.reflection}"\n\nMy thoughts:\n`;
    router.push({
      pathname: '/(tabs)/reflect',
      params: {
        tab: 'journal',
        prefill: journalPrompt
      }
    });
  };

  const handleAskMirror = (card: AstrologyDeepDiveCard) => {
    const mirrorContext = `I want to explore ${card.title.toLowerCase()} in my chart. ${card.whatThisIs}`;
    router.push({
      pathname: '/(tabs)/reflect',
      params: {
        tab: 'mirror',
        context: mirrorContext
      }
    });
  };

  // Handler for Today tab reflection
  const handleTodayReflect = (question: string) => {
    router.push({
      pathname: '/(tabs)/reflect',
      params: {
        tab: 'mirror',
        context: `Reflecting on this question: ${question}`
      }
    });
  };

  // Get placements from available data - prefer full chart data
  const getPlacements = (): CorePlacements => {
    // Use full chart data if available (most complete)
    if (fullChartData?.natal?.planets) {
      const planets = fullChartData.natal.planets;
      const nodes = fullChartData.natal.nodes;
      const angles = fullChartData.natal.angles;
      
      return {
        sun: planets.Sun?.sign || 'Unknown',
        sun_house: planets.Sun?.house,
        moon: planets.Moon?.sign || 'Unknown',
        moon_house: planets.Moon?.house,
        ascendant: angles?.asc?.sign || 'Unknown',
        mercury: planets.Mercury?.sign,
        mercury_house: planets.Mercury?.house,
        venus: planets.Venus?.sign,
        venus_house: planets.Venus?.house,
        mars: planets.Mars?.sign,
        mars_house: planets.Mars?.house,
        jupiter: planets.Jupiter?.sign,
        jupiter_house: planets.Jupiter?.house,
        saturn: planets.Saturn?.sign,
        saturn_house: planets.Saturn?.house,
        chiron: planets.Chiron?.sign,
        chiron_house: planets.Chiron?.house,
        north_node: planets['North Node']?.sign || nodes?.north?.sign,
        north_node_house: planets['North Node']?.house || nodes?.north?.house,
        south_node: planets['South Node']?.sign || nodes?.south?.sign,
        south_node_house: planets['South Node']?.house || nodes?.south?.house
      };
    }
    // Fallback to deep dive data
    if (deepDiveData?.core_placements) {
      return deepDiveData.core_placements;
    }
    // Fallback to summary data
    if (summaryData?.core_placements) {
      return summaryData.core_placements;
    }
    return {
      sun: 'Unknown',
      moon: 'Unknown',
      ascendant: 'Unknown'
    };
  };

  const placements = getPlacements();

  // ============================================
  // RENDER: TABS
  // ============================================
  const renderTabs = () => (
    <View style={[styles.tabContainer, { borderBottomColor: theme.border }]}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'at_a_glance' && styles.activeTab]}
        onPress={() => setActiveTab('at_a_glance')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'at_a_glance' && { color: theme.text }]}>
          At a Glance
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'today' && styles.activeTab]}
        onPress={() => setActiveTab('today')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'today' && { color: theme.text }]}>
          Today
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'deep_dive' && styles.activeTab]}
        onPress={() => setActiveTab('deep_dive')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'deep_dive' && { color: theme.text }]}>
          Deep Dive
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'timeline' && styles.activeTab]}
        onPress={() => setActiveTab('timeline')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'timeline' && { color: theme.text }]}>
          Timeline
        </Text>
      </TouchableOpacity>
    </View>
  );

  // ============================================
  // RENDER: CONTENT
  // ============================================
  const renderContent = () => {
    if (activeTab === 'at_a_glance') {
      return (
        <AstrologyAtAGlanceTab
          placements={placements}
          fullChartData={fullChartData}
          theme={theme}
          onOpenChat={onOpenChat}
          aspectsExpanded={aspectsExpanded}
          setAspectsExpanded={setAspectsExpanded}
          tensionsGiftsExpanded={tensionsGiftsExpanded}
          setTensionsGiftsExpanded={setTensionsGiftsExpanded}
        />
      );
    }
    
    if (activeTab === 'today') {
      // V3: Use the new Real-World Clarity Engine
      return (
        <AstrologyTodayV3
          userId={userId}
          theme={theme}
          onReflect={handleTodayReflect}
        />
      );
    }
    
    if (activeTab === 'deep_dive') {
      return (
        <AstrologyDeepDiveTab
          placements={placements}
          fullChartData={fullChartData}
          expandedCards={expandedCards}
          toggleCard={toggleCard}
          onReflect={handleReflect}
          onJournal={handleJournal}
          onAskMirror={handleAskMirror}
          theme={theme}
        />
      );
    }
    
    if (activeTab === 'timeline') {
      return (
        <AstrologyTimelineTab
          fullChartData={fullChartData}
          theme={theme}
          onOpenChat={onOpenChat}
        />
      );
    }
    
    return null;
  };

  // ============================================
  // MAIN RENDER
  // ============================================
  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {renderTabs()}

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.textTertiary} />
            <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
              {activeTab === 'deep_dive'
                ? 'Generating your personalized reading...'
                : 'Loading...'}
            </Text>
          </View>
        ) : error ? (
          <View style={styles.errorContainer}>
            <Text style={{ fontSize: 28, color: theme.textTertiary }}>⚠</Text>
            <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
            <TouchableOpacity
              style={[styles.retryButton, { backgroundColor: theme.surface }]}
              onPress={() => loadTabData(activeTab)}
            >
              <Text style={[styles.retryText, { color: theme.text }]}>Try Again</Text>
            </TouchableOpacity>
          </View>
        ) : (
          renderContent()
        )}
      </ScrollView>
    </View>
  );
}

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  activeTab: {},
  tabText: {
    fontSize: 13,
    fontWeight: '500',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    paddingBottom: 40,
  },
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    textAlign: 'center',
  },
  errorContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    marginTop: 8,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },
});
