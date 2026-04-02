/**
 * AstroExpertCard V5.0 - Expert Interpreter
 * 
 * Must feel like: "A master astrologer who knows the user"
 * 
 * 6-SECTION STRUCTURE:
 * 1. TODAY'S THEME (1 line tension)
 * 2. WHAT'S ACTUALLY HAPPENING (real transit bullets)
 * 3. HOW THIS INTERACTS WITH YOU (personalization - CRITICAL)
 * 4. WHAT THIS MAY FEEL LIKE (concrete felt experience)
 * 5. WHAT TO DO WITH IT (actionable, grounded)
 * 6. ONE QUESTION (clean reflective prompt)
 * 
 * STRICT RULES:
 * - NO vague poetic language
 * - NO generic horoscope tone
 * - MUST include real signals + personal interaction
 * - MUST feel specific to THIS user + THIS day
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, Platform, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';

interface AstroExpertData {
  success: boolean;
  lens: string;
  date: string;
  version: string;
  todays_theme: string;
  whats_happening: string[];
  how_it_interacts: string[];
  what_it_feels_like: string[];
  what_to_do: string[];
  one_question: string;
  pattern_memory_state: string;
  evolution_state: string;
  signals?: {
    transits: any[];
    active_houses: number[];
    dominant_planet: string;
    primary_house: number;
  };
  debug?: any;
}

interface AstroExpertCardProps {
  userId: string;
  theme: {
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    textTertiary: string;
    accent: string;
    border: string;
    cardBackground?: string;
  };
  onReflect?: (question: string) => void;
}

const AstroExpertCard: React.FC<AstroExpertCardProps> = ({
  userId,
  theme,
  onReflect,
}) => {
  const [data, setData] = useState<AstroExpertData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [signalsExpanded, setSignalsExpanded] = useState(false);

  useEffect(() => {
    loadData();
  }, [userId]);

  const loadData = async () => {
    if (!userId) {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get(`/astro-expert/${userId}`);
      setData(response.data);
    } catch (err: any) {
      console.error('[AstroExpertCard] Error:', err);
      setError(err.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  const handleReflect = () => {
    if (data && onReflect) {
      onReflect(data.one_question);
    }
  };

  // Section Header Component
  const SectionHeader: React.FC<{ title: string; icon: string }> = ({ title, icon }) => (
    <View style={styles.sectionHeader}>
      <Ionicons name={icon as any} size={16} color={theme.accent} />
      <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
        {title}
      </Text>
    </View>
  );

  // Bullet Item Component
  const BulletItem: React.FC<{ text: string }> = ({ text }) => (
    <View style={styles.bulletItem}>
      <View style={[styles.bulletDot, { backgroundColor: theme.accent + '60' }]} />
      <Text style={[styles.bulletText, { color: theme.text }]}>{text}</Text>
    </View>
  );

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Reading your chart...
          </Text>
        </View>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error || 'Unable to load astrology data'}
        </Text>
        <TouchableOpacity onPress={loadData}>
          <Text style={[styles.retryText, { color: theme.accent }]}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
      
      {/* 1. TODAY'S THEME */}
      <View style={styles.themeSection}>
        <Text style={[styles.themeLabel, { color: theme.textTertiary }]}>
          TODAY'S THEME
        </Text>
        <Text style={[styles.themeText, { color: theme.text }]}>
          {data.todays_theme}
        </Text>
      </View>

      {/* 2. WHAT'S ACTUALLY HAPPENING */}
      <View style={styles.section}>
        <SectionHeader title="What's Actually Happening" icon="planet-outline" />
        {data.whats_happening.map((item, index) => (
          <BulletItem key={`happening-${index}`} text={item} />
        ))}
      </View>

      {/* 3. HOW THIS INTERACTS WITH YOU */}
      <View style={[styles.section, styles.personalSection, { backgroundColor: theme.cardBackground || theme.background }]}>
        <SectionHeader title="How This Interacts With You" icon="person-outline" />
        {data.how_it_interacts.map((item, index) => (
          <BulletItem key={`interacts-${index}`} text={item} />
        ))}
      </View>

      {/* 4. WHAT THIS MAY FEEL LIKE */}
      <View style={styles.section}>
        <SectionHeader title="What This May Feel Like" icon="heart-outline" />
        {data.what_it_feels_like.map((item, index) => (
          <BulletItem key={`feels-${index}`} text={item} />
        ))}
      </View>

      {/* 5. WHAT TO DO WITH IT */}
      <View style={[styles.section, styles.actionSection, { borderLeftColor: theme.accent }]}>
        <SectionHeader title="What To Do With It" icon="arrow-forward-circle-outline" />
        {data.what_to_do.map((item, index) => (
          <BulletItem key={`todo-${index}`} text={item} />
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
          {data.one_question}
        </Text>
      </TouchableOpacity>

      {/* Collapsible: Raw Signals */}
      <TouchableOpacity
        style={styles.signalsToggle}
        onPress={() => setSignalsExpanded(!signalsExpanded)}
      >
        <Text style={[styles.signalsToggleText, { color: theme.textTertiary }]}>
          {signalsExpanded ? 'Hide raw signals' : 'Show raw signals'}
        </Text>
        <Ionicons 
          name={signalsExpanded ? 'chevron-up' : 'chevron-down'} 
          size={16} 
          color={theme.textTertiary} 
        />
      </TouchableOpacity>

      {signalsExpanded && data.signals && (
        <View style={[styles.signalsContainer, { backgroundColor: theme.background }]}>
          <Text style={[styles.signalsLabel, { color: theme.textTertiary }]}>
            Dominant: {data.signals.dominant_planet} in House {data.signals.primary_house}
          </Text>
          <Text style={[styles.signalsLabel, { color: theme.textTertiary }]}>
            Active Houses: {data.signals.active_houses.join(', ')}
          </Text>
          {data.signals.transits.slice(0, 3).map((transit, idx) => (
            <Text key={idx} style={[styles.signalsDetail, { color: theme.textTertiary }]}>
              {transit.planet} {transit.aspect} {transit.natal_planet}
            </Text>
          ))}
        </View>
      )}

    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    padding: 20,
    marginVertical: 8,
    borderWidth: 1,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.08,
        shadowRadius: 8,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 32,
  },
  loadingText: {
    marginLeft: 12,
    fontSize: 14,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 16,
  },
  retryText: {
    fontSize: 14,
    textAlign: 'center',
    fontWeight: '600',
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
  signalsToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 16,
    gap: 6,
  },
  signalsToggleText: {
    fontSize: 12,
  },
  signalsContainer: {
    marginTop: 12,
    padding: 12,
    borderRadius: 8,
  },
  signalsLabel: {
    fontSize: 12,
    marginBottom: 4,
  },
  signalsDetail: {
    fontSize: 11,
    marginTop: 2,
  },
});

export default AstroExpertCard;
