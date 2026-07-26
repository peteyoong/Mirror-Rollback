/**
 * AstroExpertCard V5.1 - Expert Interpreter with Event Priority
 * 
 * Must feel like: "A master astrologer who knows the user"
 * If Full Moon is happening: "Oh — THAT'S why everything feels heightened"
 * 
 * 6-SECTION STRUCTURE:
 * 1. TODAY'S THEME (1 line tension) - MUST derive from Tier 1 event if present
 * 2. WHAT'S ACTUALLY HAPPENING (real transit bullets + main event)
 * 3. HOW THIS INTERACTS WITH YOU (personalization - CRITICAL)
 * 4. WHAT THIS MAY FEEL LIKE (concrete felt experience)
 * 5. WHAT TO DO WITH IT (actionable, grounded)
 * 6. ONE QUESTION (clean reflective prompt)
 * 
 * V5.1 UPGRADES:
 * - Event Priority: Tier 1 events (Full Moon, New Moon, Eclipse) prominently displayed
 * - Explicit Naming: "Full Moon in Libra", not vague descriptions
 * - Visual Event Badge: Clear indicator when major event is active
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
import { InsightCardFooter } from './InsightCardFooter';

interface EventPriority {
  has_dominant_event: boolean;
  dominant_event?: {
    type: string;
    explicit_name: string;
    sign: string;
    is_exact: boolean;
    days_until: number;
    salience: number;
  };
  explicit_event_name?: string;
  event_sign?: string;
  tier_summary: {
    tier_1_count: number;
    tier_2_count: number;
    tier_3_count: number;
  };
  moon_phase: string;
  days_to_full: number;
  days_to_new: number;
}

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
  event_priority?: EventPriority;
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
  timeframe?: 'today' | 'week' | 'month';
}

const AstroExpertCard: React.FC<AstroExpertCardProps> = ({
  userId,
  theme,
  onReflect,
  timeframe = 'today',
}) => {
  const [data, setData] = useState<AstroExpertData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [signalsExpanded, setSignalsExpanded] = useState(false);

  useEffect(() => {
    loadData();
  }, [userId, timeframe]);

  const loadData = async () => {
    if (!userId) {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get(`/astro-expert/${userId}?timeframe=${timeframe}`);
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

  // Get event icon based on event type
  const getEventIcon = (eventType: string): string => {
    if (eventType.includes('full_moon')) return '🌕';
    if (eventType.includes('new_moon')) return '🌑';
    if (eventType.includes('eclipse_solar')) return '⬤';
    if (eventType.includes('eclipse_lunar')) return '🌒';
    return '✨';
  };

  // Get event badge color based on event type
  const getEventBadgeColor = (eventType: string): string => {
    if (eventType.includes('full_moon')) return '#FFD700';
    if (eventType.includes('new_moon')) return '#6B5B95';
    if (eventType.includes('eclipse')) return '#E94E77';
    return theme.accent;
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
  const BulletItem: React.FC<{ text: string; isMainEvent?: boolean }> = ({ text, isMainEvent }) => (
    <View style={styles.bulletItem}>
      {isMainEvent ? (
        <Text style={styles.mainEventIcon}>
          {text.startsWith('🌕') || text.startsWith('🌑') || text.startsWith('⬤') ? '' : '•'}
        </Text>
      ) : (
        <View style={[styles.bulletDot, { backgroundColor: theme.accent + '60' }]} />
      )}
      <Text style={[
        styles.bulletText, 
        { color: theme.text },
        isMainEvent && styles.mainEventText
      ]}>
        {text}
      </Text>
    </View>
  );

  // Event Badge Component
  const EventBadge: React.FC<{ event: EventPriority['dominant_event'] }> = ({ event }) => {
    if (!event) return null;
    
    const icon = getEventIcon(event.type);
    const badgeColor = getEventBadgeColor(event.type);
    
    return (
      <View style={[styles.eventBadge, { backgroundColor: badgeColor + '20', borderColor: badgeColor }]}>
        <Text style={styles.eventBadgeIcon}>{icon}</Text>
        <View style={styles.eventBadgeContent}>
          <Text style={[styles.eventBadgeName, { color: theme.text }]}>
            {event.explicit_name}
          </Text>
          {event.is_exact ? (
            <Text style={[styles.eventBadgeTiming, { color: badgeColor }]}>
              PEAK TODAY
            </Text>
          ) : event.days_until > 0 ? (
            <Text style={[styles.eventBadgeTiming, { color: theme.textSecondary }]}>
              in {event.days_until} day{event.days_until !== 1 ? 's' : ''}
            </Text>
          ) : null}
        </View>
      </View>
    );
  };

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

  const hasEvent = data.event_priority?.has_dominant_event;
  const dominantEvent = data.event_priority?.dominant_event;

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
      
      {/* Event Badge (if Tier 1 event active) */}
      {hasEvent && dominantEvent && (
        <EventBadge event={dominantEvent} />
      )}

      {/* 1. TODAY'S THEME */}
      <View style={styles.themeSection}>
        <Text style={[styles.themeLabel, { color: theme.textTertiary }]}>
          {timeframe === 'today' ? "TODAY'S THEME" : timeframe === 'week' ? "THIS WEEK'S THEME" : "THIS MONTH'S THEME"}
        </Text>
        <Text style={[styles.themeText, { color: theme.text }]}>
          {data.todays_theme}
        </Text>
        
        {/* Moon phase indicator */}
        {data.event_priority && !hasEvent && (
          <Text style={[styles.moonPhaseText, { color: theme.textTertiary }]}>
            {data.event_priority.moon_phase} • {Math.round(data.event_priority.days_to_full)} days to full moon
          </Text>
        )}
      </View>

      {/* 2. WHAT'S ACTUALLY HAPPENING */}
      <View style={styles.section}>
        <SectionHeader title="What's Actually Happening" icon="planet-outline" />
        {data.whats_happening.map((item, index) => {
          // Check if this is the main event line (starts with emoji)
          const isMainEvent = index === 0 && (
            item.startsWith('🌕') || 
            item.startsWith('🌑') || 
            item.startsWith('⬤')
          );
          return (
            <BulletItem 
              key={`happening-${index}`} 
              text={item} 
              isMainEvent={isMainEvent}
            />
          );
        })}
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
      <View style={[styles.questionSection, { backgroundColor: theme.accent + '10', borderColor: theme.accent + '30' }]}>
        <Ionicons name="help-circle-outline" size={20} color={theme.accent} />
        <Text style={[styles.questionText, { color: theme.text }]}>
          {data.one_question}
        </Text>
      </View>

      {/* Unified Insight Card Footer (Resonate + Reflect) */}
      <InsightCardFooter
        source={{
          lens: 'astrology',
          type: `astro_expert_${timeframe}`,
          name: `Astrology ${timeframe === 'today' ? 'Today' : timeframe === 'week' ? 'This Week' : 'This Month'}`,
          value: data.todays_theme,
          id: `astro_expert_${timeframe}_${data.date}`,
        }}
        patternSignature={`astro_expert_${timeframe}_${data.date}`}
        context={`astrology_${timeframe}`}
        prompt={data.one_question}
        showBorder={true}
        borderColor={theme.border}
      />

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
          size={20} 
          color={theme.textTertiary} 
        />
      </TouchableOpacity>

      {signalsExpanded && (
        <View style={[styles.signalsContainer, { backgroundColor: theme.background }]}>
          {/* Event Priority Info */}
          {data.event_priority && (
            <>
              <Text style={[styles.signalsLabel, { color: theme.textSecondary, fontWeight: '500' }]}>
                Event Priority V5.1
              </Text>
              <Text style={[styles.signalsDetail, { color: theme.textTertiary }]}>
                Dominant Event: {data.event_priority.has_dominant_event ? 'YES' : 'No'}
              </Text>
              {data.event_priority.dominant_event && (
                <Text style={[styles.signalsDetail, { color: theme.textTertiary }]}>
                  Event: {data.event_priority.dominant_event.explicit_name} (salience: {Math.round(data.event_priority.dominant_event.salience * 100)}%)
                </Text>
              )}
              <Text style={[styles.signalsDetail, { color: theme.textTertiary }]}>
                Tiers: T1={data.event_priority.tier_summary?.tier_1_count || 0}, T2={data.event_priority.tier_summary?.tier_2_count || 0}, T3={data.event_priority.tier_summary?.tier_3_count || 0}
              </Text>
              <View style={{ height: 8 }} />
            </>
          )}
          
          {/* Original signals */}
          {data.signals && (
            <>
              <Text style={[styles.signalsLabel, { color: theme.textTertiary }]}>
                Dominant: {data.signals.dominant_planet} in House {data.signals.primary_house}
              </Text>
              <Text style={[styles.signalsLabel, { color: theme.textTertiary }]}>
                Active Houses: {data.signals.active_houses.join(', ')}
              </Text>
              {data.signals.transits.slice(0, 3).map((transit, idx) => (
                <Text key={idx} style={[styles.signalsDetail, { color: theme.textTertiary }]}>
                  {transit.planet} {transit.aspect} {transit.natal_planet} {transit.orb ? `(${transit.orb}°)` : ''}
                </Text>
              ))}
            </>
          )}
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
    fontSize: 16,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
    paddingVertical: 16,
  },
  retryText: {
    fontSize: 16,
    textAlign: 'center',
    fontWeight: '500',
  },
  eventBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 16,
    gap: 10,
  },
  eventBadgeIcon: {
    fontSize: 28,
  },
  eventBadgeContent: {
    flex: 1,
  },
  eventBadgeName: {
    fontSize: 16,
    fontWeight: '500',
    letterSpacing: -0.3,
  },
  eventBadgeTiming: {
    fontSize: 14,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: 2,
  },
  themeSection: {
    marginBottom: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.06)',
  },
  themeLabel: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  themeText: {
    fontSize: 24,
    fontWeight: '500',
    lineHeight: 30,
    letterSpacing: -0.3,
  },
  moonPhaseText: {
    fontSize: 14,
    marginTop: 8,
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
    marginBottom: 14,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 14,
    paddingRight: 8,
  },
  bulletDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 7,
    marginRight: 10,
  },
  mainEventIcon: {
    fontSize: 6,
    marginRight: 10,
    marginTop: 7,
  },
  bulletText: {
    flex: 1,
    fontSize: 17,
    lineHeight: 30,
  },
  mainEventText: {
    fontWeight: '500',
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
    fontSize: 17,
    fontWeight: '500',
    fontStyle: 'italic',
    lineHeight: 30,
  },
  signalsToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 16,
    gap: 6,
  },
  signalsToggleText: {
    fontSize: 14,
  },
  signalsContainer: {
    marginTop: 12,
    padding: 12,
    borderRadius: 8,
  },
  signalsLabel: {
    fontSize: 14,
    marginBottom: 4,
  },
  signalsDetail: {
    fontSize: 14,
    marginTop: 2,
  },
});

export default AstroExpertCard;
