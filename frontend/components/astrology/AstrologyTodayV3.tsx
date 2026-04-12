// ============================================
// ASTROLOGY TODAY V3 - Real-World Clarity Engine
// ============================================
// 
// MANDATORY OUTPUT FORMAT:
// 1. HEADLINE: One clear sentence
// 2. WHAT'S ACTUALLY HAPPENING: 2-3 real-world dynamics
// 3. HOW THIS SHOWS UP FOR YOU: 2-3 observable behaviors
// 4. WHAT THIS MAY FEEL LIKE: 2-3 physical/emotional signals
// 5. THE MOVE: Small behavioral shift (not advice)
// 
// SUCCESS CRITERIA:
// Non-astrology user should immediately understand without asking "what does this mean?"
// 

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Constants from 'expo-constants';
import { InsightCardFooter } from '../InsightCardFooter';

// ============================================
// V3 DATA INTERFACE
// ============================================

interface AstrologyTodayV3Data {
  success: boolean;
  version: string;
  date: string;
  headline: string;
  whats_happening: string[];
  how_it_shows_up: string[];
  what_it_feels_like: string[];
  the_move: string;
  where_context?: string | null;
  technical?: {
    transit_info?: string;
    activated_house?: number;
    house_meaning?: string;
  } | null;
  tension_type: string;
  day_class: string;
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

interface AstrologyTodayV3Props {
  userId: string;
  theme: any;
  onReflect?: (question: string) => void;
}

// ============================================
// BULLET ITEM COMPONENT
// ============================================

const BulletItem: React.FC<{ text: string; theme: any }> = ({ text, theme }) => (
  <View style={styles.bulletRow}>
    <View style={[styles.bulletDot, { backgroundColor: theme.textTertiary }]} />
    <Text style={[styles.bulletText, { color: theme.textSecondary }]}>
      {text}
    </Text>
  </View>
);

// ============================================
// SECTION HEADER COMPONENT
// ============================================

const SectionHeader: React.FC<{ title: string; icon: string; theme: any }> = ({ title, icon, theme }) => (
  <View style={styles.sectionHeader}>
    <Ionicons name={icon as any} size={16} color={theme.textTertiary} />
    <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
      {title}
    </Text>
  </View>
);

// ============================================
// MAIN COMPONENT
// ============================================

const AstrologyTodayV3: React.FC<AstrologyTodayV3Props> = ({
  userId,
  theme,
  onReflect,
}) => {
  const [data, setData] = useState<AstrologyTodayV3Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [technicalExpanded, setTechnicalExpanded] = useState(false);

  useEffect(() => {
    loadTodayV3();
  }, [userId]);

  const loadTodayV3 = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${BACKEND_BASE_URL}/api/astrology/today-v3/${userId}`);
      if (!response.ok) {
        throw new Error('Failed to load today insight');
      }
      
      const result = await response.json();
      setData(result);
    } catch (err: any) {
      console.error('[AstrologyTodayV3] Error:', err);
      setError(err.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  const handleReflect = () => {
    if (onReflect && data) {
      // Generate a reflection question based on the headline
      const question = `Looking at today: "${data.headline}" — what comes up for you?`;
      onReflect(question);
    }
  };

  // Loading state
  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="small" color={theme.accent} />
        <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
          Reading today's energy...
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
        <TouchableOpacity onPress={loadTodayV3}>
          <Text style={[styles.retryText, { color: theme.accent }]}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!data) return null;

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
        
        {/* ============================================================ */}
        {/* HEADLINE - One clear sentence, grounded, specific            */}
        {/* ============================================================ */}
        <View style={styles.headlineSection}>
          <Text style={[styles.headlineText, { color: theme.text }]}>
            {data.headline}
          </Text>
          
          {/* WHERE CONTEXT - Life area anchor */}
          {data.where_context && (
            <Text style={[styles.whereContext, { color: theme.textTertiary }]}>
              {data.where_context}
            </Text>
          )}
        </View>

        {/* ============================================================ */}
        {/* WHAT'S ACTUALLY HAPPENING - Real-world dynamics              */}
        {/* ============================================================ */}
        <View style={styles.section}>
          <SectionHeader title="What's Actually Happening" icon="flash-outline" theme={theme} />
          {data.whats_happening?.map((item, index) => (
            <BulletItem key={`happening-${index}`} text={item} theme={theme} />
          ))}
        </View>

        {/* ============================================================ */}
        {/* HOW THIS SHOWS UP - Observable behaviors                     */}
        {/* ============================================================ */}
        <View style={[styles.section, styles.highlightedSection, { backgroundColor: theme.cardBackground || theme.background }]}>
          <SectionHeader title="How This Shows Up For You" icon="person-outline" theme={theme} />
          {data.how_it_shows_up?.map((item, index) => (
            <BulletItem key={`shows-${index}`} text={item} theme={theme} />
          ))}
        </View>

        {/* ============================================================ */}
        {/* WHAT THIS MAY FEEL LIKE - Physical/emotional signals         */}
        {/* ============================================================ */}
        <View style={styles.section}>
          <SectionHeader title="What This May Feel Like" icon="heart-outline" theme={theme} />
          {data.what_it_feels_like?.map((item, index) => (
            <BulletItem key={`feels-${index}`} text={item} theme={theme} />
          ))}
        </View>

        {/* ============================================================ */}
        {/* THE MOVE - Small behavioral shift, non-prescriptive          */}
        {/* ============================================================ */}
        <View style={[styles.moveSection, { borderLeftColor: theme.accent }]}>
          <Text style={[styles.moveLabel, { color: theme.textTertiary }]}>
            THE MOVE
          </Text>
          <Text style={[styles.moveText, { color: theme.text }]}>
            {data.the_move}
          </Text>
        </View>

        {/* ============================================================ */}
        {/* TECHNICAL - Hidden layer, expandable                         */}
        {/* ============================================================ */}
        {data.technical && (
          <TouchableOpacity
            style={[styles.technicalToggle, { borderColor: theme.border }]}
            onPress={() => setTechnicalExpanded(!technicalExpanded)}
            activeOpacity={0.7}
          >
            <Text style={[styles.technicalToggleText, { color: theme.textTertiary }]}>
              {technicalExpanded ? 'Hide technical details' : 'What this is based on'}
            </Text>
            <Ionicons
              name={technicalExpanded ? 'chevron-up' : 'chevron-down'}
              size={14}
              color={theme.textTertiary}
            />
          </TouchableOpacity>
        )}

        {technicalExpanded && data.technical && (
          <View style={[styles.technicalSection, { backgroundColor: theme.cardBackground || theme.background, borderColor: theme.border }]}>
            {data.technical.transit_info && (
              <Text style={[styles.technicalText, { color: theme.textTertiary }]}>
                {data.technical.transit_info}
              </Text>
            )}
            {data.technical.activated_house && data.technical.house_meaning && (
              <Text style={[styles.technicalText, { color: theme.textTertiary }]}>
                House {data.technical.activated_house}: {data.technical.house_meaning}
              </Text>
            )}
          </View>
        )}

        {/* INSIGHT CARD FOOTER */}
        <InsightCardFooter
          source={{
            lens: 'astrology',
            type: 'today_v3',
            name: data.headline,
            value: data.the_move,
            id: `astro_today_v3_${data.date}`,
          }}
          patternSignature={`astro_today_v3_${data.date}`}
          context="astrology_today_v3"
          prompt={`Looking at today: "${data.headline}" — what comes up for you?`}
          showBorder={true}
          borderColor={theme.border}
        />

      </View>
    </ScrollView>
  );
};

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
  },
  errorContainer: {
    padding: 24,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  retryText: {
    fontSize: 14,
    fontWeight: '600',
  },
  card: {
    margin: 16,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
  },
  
  // Headline
  headlineSection: {
    marginBottom: 20,
  },
  headlineText: {
    fontSize: 20,
    fontWeight: '600',
    lineHeight: 28,
  },
  whereContext: {
    fontSize: 13,
    fontStyle: 'italic',
    marginTop: 8,
  },
  
  // Sections
  section: {
    marginBottom: 20,
  },
  highlightedSection: {
    padding: 16,
    borderRadius: 12,
    marginHorizontal: -4,
    marginBottom: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  
  // Bullets
  bulletRow: {
    flexDirection: 'row',
    paddingLeft: 4,
    marginBottom: 10,
  },
  bulletDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    marginTop: 7,
    marginRight: 10,
  },
  bulletText: {
    flex: 1,
    fontSize: 15,
    lineHeight: 22,
  },
  
  // The Move
  moveSection: {
    paddingLeft: 14,
    borderLeftWidth: 3,
    marginBottom: 20,
  },
  moveLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 6,
  },
  moveText: {
    fontSize: 15,
    fontWeight: '500',
    lineHeight: 22,
    fontStyle: 'italic',
  },
  
  // Technical
  technicalToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    marginTop: 8,
  },
  technicalToggleText: {
    fontSize: 12,
  },
  technicalSection: {
    padding: 14,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    marginTop: 12,
  },
  technicalText: {
    fontSize: 12,
    lineHeight: 18,
    fontStyle: 'italic',
    marginBottom: 4,
  },
});

export default AstrologyTodayV3;
