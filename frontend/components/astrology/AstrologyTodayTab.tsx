// ============================================
// ASTROLOGY TODAY TAB V5.0 - Expert Interpreter Primary
// ============================================
// 
// CORE RULE: Must feel like a Master Astrologer who knows you
// 
// Primary Experience: Expert Interpretation (6-section structure)
// Secondary: Raw signals as "What this is based on" (supporting proof layer)
// 
// NO: Leading with "Top Active Transits" or signal inventory
// YES: Lead with interpreted meaning, demote raw signals

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import TrueSiderealTransitsCard from '../TrueSiderealTransitsCard';

import {
  FullChartData,
  TransitHit,
  TransitWindow,
  Timeframe,
} from '../../services/astrology/astrologyTypes';

// ============================================
// V5.0 EXPERT DATA INTERFACES
// ============================================

interface AstroExpertData {
  success: boolean;
  lens: string;
  date: string;
  version: string;
  timeframe: string;  // V5.2: Added to verify horizon
  todays_theme: string;
  whats_happening: string[];
  how_it_interacts: string[];
  what_it_feels_like: string[];
  what_to_do: string[];
  one_question: string;
  pattern_memory_state: string;
  evolution_state: string;
  event_priority?: {
    has_dominant_event: boolean;
    dominant_event?: any;
    explicit_event_name?: string;
    event_sign?: string;
  };
  horizon_interpretation?: {
    timeframe: string;
    theme_description: string;
    horizon_source: string;
  };
  signals?: {
    transits: any[];
    active_houses: number[];
    dominant_planet: string;
    primary_house: number;
  };
  // V5.3: Scope debug metadata for verification
  scope_debug?: {
    scope: string;
    cache_key: string;
    window_start: string;
    window_end: string;
    generated_at: string;
  };
  debug?: any;
}

// ============================================
// PROPS INTERFACE
// ============================================

interface AstrologyTodayTabProps {
  userId: string;
  fullChartData: FullChartData | null;
  theme: any;
  onOpenChat: () => void;
  onReflect: (question: string) => void;
  onSwitchToTimeline?: () => void;
}

// ============================================
// RAW SIGNALS SECTION (Supporting Proof Layer)
// ============================================

interface RawSignalsSectionProps {
  transits: TransitHit[];
  expanded: boolean;
  onToggle: () => void;
  theme: any;
  activeHouses?: number[];
  dominantPlanet?: string;
}

const getAspectSymbol = (aspectType: string): string => {
  const symbols: { [key: string]: string } = {
    'conjunction': '☌',
    'opposition': '☍',
    'trine': '△',
    'square': '□',
    'sextile': '⚹'
  };
  return symbols[aspectType] || '•';
};

const RawSignalsSection: React.FC<RawSignalsSectionProps> = ({ 
  transits, 
  expanded, 
  onToggle, 
  theme,
  activeHouses = [],
  dominantPlanet
}) => {
  if (!transits || transits.length === 0) return null;

  return (
    <View style={styles.rawSignalsWrapper}>
      <TouchableOpacity
        style={[styles.rawSignalsToggle, { borderColor: theme.border }]}
        onPress={onToggle}
        activeOpacity={0.7}
      >
        <Ionicons 
          name="analytics-outline" 
          size={14} 
          color={theme.textTertiary} 
        />
        <Text style={[styles.rawSignalsToggleText, { color: theme.textTertiary }]}>
          What this is based on
        </Text>
        <Ionicons 
          name={expanded ? 'chevron-up' : 'chevron-down'} 
          size={14} 
          color={theme.textTertiary} 
        />
      </TouchableOpacity>

      {expanded && (
        <View style={[styles.rawSignalsContainer, { backgroundColor: theme.background, borderColor: theme.border }]}>
          
          {/* Active Transits */}
          <View style={styles.rawSignalsGroup}>
            <Text style={[styles.rawSignalsLabel, { color: theme.textTertiary }]}>
              ACTIVE TRANSITS
            </Text>
            {transits.slice(0, 5).map((hit, index) => (
              <View key={index} style={styles.rawTransitRow}>
                <Text style={[styles.rawTransitAspect, { color: theme.textSecondary }]}>
                  {getAspectSymbol(hit.aspect_type)} {hit.transit_point} {hit.aspect_type} {hit.natal_point}
                </Text>
                <Text style={[styles.rawTransitOrb, { color: theme.textTertiary }]}>
                  {hit.orb?.toFixed(1) || '—'}°
                </Text>
              </View>
            ))}
          </View>

          {/* Natal Points Being Touched */}
          <View style={styles.rawSignalsGroup}>
            <Text style={[styles.rawSignalsLabel, { color: theme.textTertiary }]}>
              NATAL POINTS ACTIVATED
            </Text>
            <View style={styles.rawChipsRow}>
              {[...new Set(transits.slice(0, 6).map(t => t.natal_point))].map((point, i) => (
                <View key={i} style={[styles.rawChip, { backgroundColor: theme.accent + '10' }]}>
                  <Text style={[styles.rawChipText, { color: theme.accent }]}>{point}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Houses Activated */}
          {activeHouses.length > 0 && (
            <View style={styles.rawSignalsGroup}>
              <Text style={[styles.rawSignalsLabel, { color: theme.textTertiary }]}>
                LIFE AREAS (HOUSES)
              </Text>
              <Text style={[styles.rawHousesText, { color: theme.textSecondary }]}>
                Houses {activeHouses.join(', ')}
              </Text>
            </View>
          )}

          {/* Dominant Energy */}
          {dominantPlanet && (
            <View style={styles.rawSignalsGroup}>
              <Text style={[styles.rawSignalsLabel, { color: theme.textTertiary }]}>
                DOMINANT ENERGY
              </Text>
              <Text style={[styles.rawDominantText, { color: theme.textSecondary }]}>
                {dominantPlanet}
              </Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
};

// ============================================
// SECTION HEADER COMPONENT
// ============================================

const SectionHeader: React.FC<{ title: string; icon: string; theme: any }> = ({ title, icon, theme }) => (
  <View style={styles.sectionHeader}>
    <Ionicons name={icon as any} size={16} color={theme.accent} />
    <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
      {title}
    </Text>
  </View>
);

// ============================================
// BULLET ITEM COMPONENT
// ============================================

const BulletItem: React.FC<{ text: string; theme: any }> = ({ text, theme }) => (
  <View style={styles.bulletItem}>
    <View style={[styles.bulletDot, { backgroundColor: theme.accent + '60' }]} />
    <Text style={[styles.bulletText, { color: theme.text }]}>{text}</Text>
  </View>
);

// ============================================
// MAIN COMPONENT
// ============================================

const AstrologyTodayTab: React.FC<AstrologyTodayTabProps> = ({
  userId,
  fullChartData,
  theme,
  onOpenChat,
  onReflect,
  onSwitchToTimeline,
}) => {
  const [activeAltitude, setActiveAltitude] = useState<Timeframe>('today');
  const [signalsExpanded, setSignalsExpanded] = useState(false);
  const [expertData, setExpertData] = useState<AstroExpertData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load expert data when userId or altitude changes
  useEffect(() => {
    if (userId) {
      loadExpertData();
    }
  }, [userId, activeAltitude]);

  const loadExpertData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // V5.2: Pass timeframe to get DISTINCT horizon interpretations
      const { getAstroExpert } = await import('../../services/api');
      
      // Map UI altitude to API timeframe
      const timeframeMap: Record<Timeframe, 'today' | 'week' | 'month'> = {
        'today': 'today',
        'week': 'week',
        'month': 'month',
      };
      const timeframe = timeframeMap[activeAltitude];
      
      console.log(`[AstrologyTodayTab] Loading expert data for timeframe: ${timeframe}`);
      const data = await getAstroExpert(userId, timeframe);
      console.log(`[AstrologyTodayTab] Received theme: "${data.todays_theme}", timeframe: "${data.timeframe}"`);
      
      setExpertData(data);
    } catch (err: any) {
      console.error('[AstrologyTodayTab V5.2] Error:', err);
      setError(err.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  // Get transit window for raw signals
  const getTransitWindow = (): TransitWindow | null => {
    if (!fullChartData?.transits?.windows) return null;
    
    switch (activeAltitude) {
      case 'today': return fullChartData.transits.windows.today;
      case 'week': return fullChartData.transits.windows.this_week;
      case 'month': return fullChartData.transits.windows.this_month;
      default: return fullChartData.transits.windows.today;
    }
  };

  const currentWindow = getTransitWindow();
  const transits = currentWindow?.strongest_hits || [];

  // Timeframe label
  const getTimeframeLabel = () => {
    switch (activeAltitude) {
      case 'today': return 'Today';
      case 'week': return 'This Week';
      case 'month': return 'This Month';
    }
  };

  // Adjust content based on timeframe
  const getTimeframeAdjustedContent = () => {
    if (!expertData) return null;
    
    // For week/month, we could adjust the phrasing
    // For now, use same content but could be enhanced with timeframe-specific endpoints
    return expertData;
  };

  const content = getTimeframeAdjustedContent();

  // Handle reflection
  const handleReflect = () => {
    if (content?.one_question) {
      onReflect(content.one_question);
    }
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      
      {/* Altitude Selector */}
      <View style={[styles.altitudeSelector, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
        {(['today', 'week', 'month'] as Timeframe[]).map((alt) => (
          <TouchableOpacity
            key={alt}
            style={[styles.altitudeButton, activeAltitude === alt && { backgroundColor: theme.surface }]}
            onPress={() => setActiveAltitude(alt)}
          >
            <Text style={[styles.altitudeText, { color: activeAltitude === alt ? theme.text : theme.textTertiary }]}>
              {alt === 'today' ? 'Today' : alt === 'week' ? 'This Week' : 'This Month'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* ============================================================ */}
      {/* HIERARCHY INVERSION (v6.0):                                  */}
      {/* 1. MAIN SYNTHESIS CARD (top) - Master astrologer message     */}
      {/* 2. SUPPORTING INTERPRETATION BLOCKS                          */}
      {/* 3. TRANSIT EVIDENCE (below) - Supporting data                */}
      {/* 4. EXPANDABLE TECHNICAL DETAILS                              */}
      {/* ============================================================ */}

      {/* LOADING STATE */}
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Reading your chart...
          </Text>
        </View>
      )}

      {/* ERROR STATE */}
      {error && !loading && (
        <View style={styles.errorContainer}>
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>
            {error}
          </Text>
          <TouchableOpacity onPress={loadExpertData}>
            <Text style={[styles.retryText, { color: theme.accent }]}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* ============================================================ */}
      {/* 1. MAIN SYNTHESIS CARD - Master Astrologer Voice First       */}
      {/* ============================================================ */}
      {content && !loading && (
        <View style={[styles.expertContainer, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
          
          {/* 1. TODAY'S THEME */}
          <View style={styles.themeSection}>
            <Text style={[styles.themeLabel, { color: theme.textTertiary }]}>
              {activeAltitude === 'today' ? "TODAY'S THEME" : 
               activeAltitude === 'week' ? "THIS WEEK'S THEME" : 
               "THIS MONTH'S THEME"}
            </Text>
            <Text style={[styles.themeText, { color: theme.text }]}>
              {content.todays_theme}
            </Text>
          </View>

          {/* 2. WHAT'S ACTUALLY HAPPENING */}
          <View style={styles.section}>
            <SectionHeader title="What's Actually Happening" icon="planet-outline" theme={theme} />
            {content.whats_happening?.map((item, index) => (
              <BulletItem key={`happening-${index}`} text={item} theme={theme} />
            ))}
          </View>

          {/* 3. HOW THIS INTERACTS WITH YOU (Personalization - CRITICAL) */}
          <View style={[styles.section, styles.personalSection, { backgroundColor: theme.cardBackground || theme.background }]}>
            <SectionHeader title="How This Interacts With You" icon="person-outline" theme={theme} />
            {content.how_it_interacts?.map((item, index) => (
              <BulletItem key={`interacts-${index}`} text={item} theme={theme} />
            ))}
          </View>

          {/* 4. WHAT THIS MAY FEEL LIKE */}
          <View style={styles.section}>
            <SectionHeader title="What This May Feel Like" icon="heart-outline" theme={theme} />
            {content.what_it_feels_like?.map((item, index) => (
              <BulletItem key={`feels-${index}`} text={item} theme={theme} />
            ))}
          </View>

          {/* 5. WHAT TO DO WITH IT */}
          <View style={[styles.section, styles.actionSection, { borderLeftColor: theme.accent }]}>
            <SectionHeader title="What To Do With It" icon="arrow-forward-circle-outline" theme={theme} />
            {content.what_to_do?.map((item, index) => (
              <BulletItem key={`todo-${index}`} text={item} theme={theme} />
            ))}
          </View>

          {/* 6. ONE QUESTION */}
          <TouchableOpacity 
            style={[styles.questionSection, { backgroundColor: theme.accent + '10', borderColor: theme.accent + '30' }]}
            onPress={handleReflect}
            activeOpacity={0.7}
          >
            <Ionicons name="help-circle-outline" size={20} color={theme.accent} />
            <Text style={[styles.questionText, { color: theme.text }]}>
              {content.one_question}
            </Text>
          </TouchableOpacity>

        </View>
      )}

      {/* V5.0: RAW SIGNALS - SUPPORTING PROOF LAYER (Demoted) */}
      <RawSignalsSection
        transits={transits}
        expanded={signalsExpanded}
        onToggle={() => setSignalsExpanded(!signalsExpanded)}
        theme={theme}
        activeHouses={content?.signals?.active_houses}
        dominantPlanet={content?.signals?.dominant_planet}
      />

      {/* V5.3: SCOPE DEBUG FOOTER - Verify scope isolation */}
      {content?.scope_debug && (
        <View style={[styles.scopeDebugFooter, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
          <Text style={[styles.scopeDebugText, { color: theme.textTertiary }]}>
            scope: {content.scope_debug.scope} | window: {content.scope_debug.window_start} → {content.scope_debug.window_end}
          </Text>
          <Text style={[styles.scopeDebugText, { color: theme.textTertiary }]}>
            cache_key: {content.scope_debug.cache_key?.slice(0, 40)}...
          </Text>
        </View>
      )}

      {/* ============================================================ */}
      {/* 3. TRANSIT EVIDENCE - Supporting data (BELOW interpretation) */}
      {/* Shows: Strongest aspect, Moon context, upcoming events       */}
      {/* ============================================================ */}
      {activeAltitude === 'today' && !loading && content && (
        <>
          <View style={[styles.sectionDivider, { borderColor: theme.border }]}>
            <View style={[styles.dividerLine, { backgroundColor: theme.border }]} />
            <Text style={[styles.dividerText, { color: theme.textTertiary }]}>
              TRANSIT EVIDENCE
            </Text>
            <View style={[styles.dividerLine, { backgroundColor: theme.border }]} />
          </View>
          
          <View style={styles.trueSiderealSection}>
            <TrueSiderealTransitsCard
              userId={userId}
              timezone="Asia/Singapore"
              theme={{
                background: theme.background,
                surface: theme.surface,
                surfaceLight: theme.surfaceLight || theme.surface,
                text: theme.text,
                textSecondary: theme.textSecondary,
                textTertiary: theme.textTertiary,
                accent: theme.accent,
                border: theme.border,
              }}
              compact={false}
            />
          </View>
        </>
      )}

      {/* Ask Mirror Button */}
      <TouchableOpacity
        style={[styles.askMirrorButton, { backgroundColor: theme.text }]}
        onPress={onOpenChat}
      >
        <Text style={{ fontSize: 16, color: theme.background }}>💬</Text>
        <Text style={[styles.askMirrorText, { color: theme.background }]}>
          {activeAltitude === 'today' ? 'Ask about today' : 
           activeAltitude === 'week' ? 'Ask about this week' : 
           'Ask about this month'}
        </Text>
      </TouchableOpacity>

      {/* Spacing at bottom */}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
};

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    padding: 16,
    flex: 1,
  },
  altitudeSelector: {
    flexDirection: 'row',
    borderRadius: 10,
    padding: 4,
    borderWidth: 1,
    marginBottom: 16,
  },
  altitudeButton: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 8,
  },
  altitudeText: {
    fontSize: 13,
    fontWeight: '600',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
  },
  errorContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  errorText: {
    fontSize: 14,
    marginBottom: 12,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '600',
  },
  expertContainer: {
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    marginBottom: 16,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.06,
        shadowRadius: 8,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  themeSection: {
    marginBottom: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.06)',
  },
  themeLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  themeText: {
    fontSize: 20,
    fontWeight: '700',
    lineHeight: 26,
    letterSpacing: -0.3,
  },
  section: {
    marginBottom: 20,
  },
  personalSection: {
    padding: 14,
    borderRadius: 10,
    marginHorizontal: -4,
  },
  actionSection: {
    borderLeftWidth: 3,
    paddingLeft: 14,
    marginLeft: -4,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
    paddingRight: 8,
  },
  bulletDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 7,
    marginRight: 10,
  },
  bulletText: {
    flex: 1,
    fontSize: 15,
    lineHeight: 22,
  },
  questionSection: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginTop: 4,
    gap: 10,
  },
  questionText: {
    flex: 1,
    fontSize: 15,
    fontWeight: '500',
    fontStyle: 'italic',
    lineHeight: 22,
  },
  rawSignalsWrapper: {
    marginTop: 8,
    marginBottom: 16,
  },
  rawSignalsToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    gap: 8,
    borderTopWidth: 1,
  },
  rawSignalsToggleText: {
    fontSize: 12,
    fontWeight: '500',
  },
  rawSignalsContainer: {
    marginTop: 8,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  rawSignalsGroup: {
    marginBottom: 16,
  },
  rawSignalsLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  rawTransitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  rawTransitAspect: {
    fontSize: 13,
  },
  rawTransitOrb: {
    fontSize: 11,
  },
  rawChipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  rawChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  rawChipText: {
    fontSize: 12,
    fontWeight: '500',
  },
  rawHousesText: {
    fontSize: 13,
  },
  rawDominantText: {
    fontSize: 13,
    fontWeight: '500',
  },
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    gap: 8,
  },
  askMirrorText: {
    fontSize: 15,
    fontWeight: '600',
  },
  
  // True Sidereal Transit Card Section
  trueSiderealSection: {
    marginBottom: 20,
  },
  
  // Section Divider between data and interpretation
  sectionDivider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 16,
    paddingHorizontal: 4,
  },
  dividerLine: {
    flex: 1,
    height: 1,
  },
  dividerText: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginHorizontal: 12,
  },
  
  // V5.3: Scope Debug Footer
  scopeDebugFooter: {
    padding: 8,
    borderRadius: 6,
    borderWidth: 1,
    marginTop: 12,
    marginBottom: 8,
  },
  scopeDebugText: {
    fontSize: 9,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    lineHeight: 14,
  },
});

export default AstrologyTodayTab;
