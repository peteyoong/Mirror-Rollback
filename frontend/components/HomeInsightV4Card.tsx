// ============================================
// HOME INSIGHT V4 - Earned Claims & Progressive Reveal
// ============================================
// 
// CORE PRINCIPLE:
// Every strong statement must be EARNED, not assumed.
// User should feel RECOGNIZED, not ACCUSED.
// 
// V4 OUTPUT STRUCTURE:
// 1. PATTERN LABEL: Short soft label (max 4 words)
// 2. HEADLINE: Grounded, specific, not accusatory
// 3. WHAT'S GOING ON: Real-world dynamics
// 4. WHERE IT SHOWS UP: Life area anchor
// 5. WHAT YOU MAY BE DOING: Observable behaviors
// 6. WHAT THIS CREATES: Consequence, not dramatic
// 7. THE MOVE: Small non-prescriptive shift
// 8. WHY SHOWING UP: Hidden proof layer (collapsible)
//

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Constants from 'expo-constants';

// ============================================
// V4 DATA INTERFACE
// ============================================

interface WhyShowingUp {
  signals: string[];
  trigger_confidence: string;
  note: string;
}

interface HomeInsightV4Data {
  success: boolean;
  version: string;
  date: string;
  pattern_label: string;
  headline: string;
  whats_going_on: string[];
  where_it_shows_up: string;
  what_you_may_be_doing: string[];
  what_this_creates: string;
  the_move: string;
  why_showing_up?: WhyShowingUp | null;
  cluster: string;
  house?: number;
  trigger_confidence: string;
  narrative?: string;
}

// ============================================
// API CONFIGURATION
// ============================================

const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL 
  || process.env.EXPO_PUBLIC_BACKEND_URL 
  || '';

const getBackendBaseUrl = () => {
  if (typeof window !== 'undefined' && Platform.OS === 'web') {
    if (EXPO_PUBLIC_BACKEND_URL) {
      return EXPO_PUBLIC_BACKEND_URL;
    }
    return '';
  }
  return EXPO_PUBLIC_BACKEND_URL;
};

const BACKEND_BASE_URL = getBackendBaseUrl();

// ============================================
// PROPS INTERFACE
// ============================================

interface HomeInsightV4CardProps {
  userId: string;
  theme: any;
  onReflect?: (question: string) => void;
}

// ============================================
// BULLET ITEM COMPONENT
// ============================================

const BulletItem: React.FC<{ text: string; theme: any; icon?: string }> = ({ text, theme, icon }) => (
  <View style={styles.bulletRow}>
    <Ionicons 
      name={(icon || 'chevron-forward') as any} 
      size={12} 
      color={theme.textTertiary} 
      style={styles.bulletIcon}
    />
    <Text style={[styles.bulletText, { color: theme.textSecondary }]}>
      {text}
    </Text>
  </View>
);

// ============================================
// SECTION HEADER COMPONENT
// ============================================

const SectionHeader: React.FC<{ title: string; theme: any }> = ({ title, theme }) => (
  <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
    {title}
  </Text>
);

// ============================================
// MAIN COMPONENT
// ============================================

const HomeInsightV4Card: React.FC<HomeInsightV4CardProps> = ({
  userId,
  theme,
  onReflect,
}) => {
  const [data, setData] = useState<HomeInsightV4Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [proofExpanded, setProofExpanded] = useState(false);

  useEffect(() => {
    loadInsightV4();
  }, [userId]);

  const loadInsightV4 = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${BACKEND_BASE_URL}/api/home-insight-v4/${userId}`);
      if (!response.ok) {
        throw new Error('Failed to load insight');
      }
      
      const result = await response.json();
      setData(result);
    } catch (err: any) {
      console.error('[HomeInsightV4] Error:', err);
      setError(err.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="small" color={theme.accent} />
        <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
          Reading what's present...
        </Text>
      </View>
    );
  }

  // Error state
  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error}
        </Text>
        <TouchableOpacity onPress={loadInsightV4}>
          <Text style={[styles.retryText, { color: theme.accent }]}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!data) return null;

  // Get accent color based on trigger confidence
  const getAccentColor = () => {
    switch (data.trigger_confidence) {
      case 'strongly_active_now':
        return theme.accent || '#FF6B6B';
      case 'recurring_plus_trigger':
        return '#F5A623';
      default:
        return theme.textTertiary;
    }
  };

  const accentColor = getAccentColor();

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: accentColor + '40' }]}>
      
      {/* ============================================================ */}
      {/* PATTERN LABEL - Soft, max 4 words                           */}
      {/* ============================================================ */}
      <View style={[styles.patternLabelContainer, { backgroundColor: accentColor + '15' }]}>
        <Text style={[styles.patternLabel, { color: accentColor }]}>
          {data.pattern_label.toUpperCase()}
        </Text>
      </View>

      {/* ============================================================ */}
      {/* HEADLINE - Grounded, specific, not accusatory               */}
      {/* ============================================================ */}
      <Text style={[styles.headline, { color: theme.text }]}>
        {data.headline}
      </Text>

      {/* ============================================================ */}
      {/* WHAT'S GOING ON - Real-world dynamics                       */}
      {/* ============================================================ */}
      <View style={styles.section}>
        <SectionHeader title="WHAT'S GOING ON" theme={theme} />
        {data.whats_going_on?.map((item, index) => (
          <BulletItem key={`wgo-${index}`} text={item} theme={theme} />
        ))}
      </View>

      {/* ============================================================ */}
      {/* WHERE IT SHOWS UP - Life area anchor                        */}
      {/* ============================================================ */}
      <View style={[styles.whereSection, { backgroundColor: theme.cardBackground || theme.background }]}>
        <Ionicons name="location-outline" size={14} color={theme.textTertiary} />
        <Text style={[styles.whereText, { color: theme.textSecondary }]}>
          {data.where_it_shows_up}
        </Text>
      </View>

      {/* ============================================================ */}
      {/* WHAT YOU MAY BE DOING - Observable behaviors                */}
      {/* ============================================================ */}
      <View style={styles.section}>
        <SectionHeader title="WHAT YOU MAY BE DOING" theme={theme} />
        {data.what_you_may_be_doing?.map((item, index) => (
          <BulletItem key={`doing-${index}`} text={item} theme={theme} icon="remove-outline" />
        ))}
      </View>

      {/* ============================================================ */}
      {/* WHAT THIS CREATES - Consequence, not dramatic               */}
      {/* ============================================================ */}
      <View style={[styles.createsSection, { borderLeftColor: accentColor }]}>
        <Text style={[styles.createsLabel, { color: theme.textTertiary }]}>
          WHAT THIS CREATES
        </Text>
        <Text style={[styles.createsText, { color: theme.text }]}>
          {data.what_this_creates}
        </Text>
      </View>

      {/* ============================================================ */}
      {/* THE MOVE - Small non-prescriptive shift                     */}
      {/* ============================================================ */}
      <View style={[styles.moveSection, { backgroundColor: accentColor + '10', borderColor: accentColor + '30' }]}>
        <Text style={[styles.moveLabel, { color: accentColor }]}>
          THE MOVE
        </Text>
        <Text style={[styles.moveText, { color: theme.text }]}>
          {data.the_move}
        </Text>
      </View>

      {/* ============================================================ */}
      {/* WHY SHOWING UP - Hidden proof layer (collapsible)           */}
      {/* ============================================================ */}
      {data.why_showing_up && data.why_showing_up.signals && data.why_showing_up.signals.length > 0 && (
        <>
          <TouchableOpacity
            style={[styles.proofToggle, { borderColor: theme.border }]}
            onPress={() => setProofExpanded(!proofExpanded)}
            activeOpacity={0.7}
          >
            <Text style={[styles.proofToggleText, { color: theme.textTertiary }]}>
              {proofExpanded ? 'Hide what informed this' : 'Why this is showing up'}
            </Text>
            <Ionicons
              name={proofExpanded ? 'chevron-up' : 'chevron-down'}
              size={20}
              color={theme.textTertiary}
            />
          </TouchableOpacity>

          {proofExpanded && (
            <View style={[styles.proofSection, { backgroundColor: theme.cardBackground || theme.background, borderColor: theme.border }]}>
              <Text style={[styles.proofNote, { color: theme.textTertiary }]}>
                {data.why_showing_up.note}
              </Text>
              {data.why_showing_up.signals.map((signal, index) => (
                <Text key={`signal-${index}`} style={[styles.proofSignal, { color: theme.textSecondary }]}>
                  • {signal}
                </Text>
              ))}
            </View>
          )}
        </>
      )}
    </View>
  );
};

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    marginBottom: 16,
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 16,
  },
  errorContainer: {
    padding: 24,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
  },
  retryText: {
    fontSize: 16,
    fontWeight: '500',
  },
  
  // Pattern Label
  patternLabelContainer: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    marginBottom: 16,
  },
  patternLabel: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.8,
  },
  
  // Headline
  headline: {
    fontSize: 22,
    fontWeight: '500',
    lineHeight: 30,
    marginBottom: 20,
  },
  
  // Sections
  section: {
    marginBottom: 18,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.6,
    marginBottom: 14,
  },
  
  // Bullets
  bulletRow: {
    flexDirection: 'row',
    marginBottom: 14,
    paddingRight: 8,
  },
  bulletIcon: {
    marginTop: 3,
    marginRight: 8,
  },
  bulletText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 32,
  },
  
  // Where Section
  whereSection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 12,
    borderRadius: 8,
    marginBottom: 18,
    gap: 8,
  },
  whereText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 31,
    fontStyle: 'italic',
  },
  
  // Creates Section
  createsSection: {
    paddingLeft: 14,
    borderLeftWidth: 3,
    marginBottom: 18,
  },
  createsLabel: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  createsText: {
    fontSize: 16,
    lineHeight: 32,
  },
  
  // The Move Section
  moveSection: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 16,
  },
  moveLabel: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.6,
    marginBottom: 6,
  },
  moveText: {
    fontSize: 17,
    fontWeight: '500',
    lineHeight: 30,
  },
  
  // Proof Section
  proofToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    marginTop: 8,
  },
  proofToggleText: {
    fontSize: 14,
  },
  proofSection: {
    padding: 14,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    marginTop: 12,
  },
  proofNote: {
    fontSize: 14,
    fontStyle: 'italic',
    marginBottom: 14,
  },
  proofSignal: {
    fontSize: 14,
    lineHeight: 31,
    marginBottom: 4,
  },
});

export default HomeInsightV4Card;
