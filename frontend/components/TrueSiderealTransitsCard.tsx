/**
 * TrueSiderealTransitsCard V1.0
 * 
 * Displays TRUE SIDEREAL transit events from the daily window scanner.
 * 
 * Shows:
 * - Current strongest active aspect (hero)
 * - Upcoming exact events today (timed list)
 * - Moon sign / ingress context
 * - Slow-moving transits (active all day)
 * - Concise theme from actual events
 * 
 * All calculations use Swiss Ephemeris True Sidereal (SVP 31.2836°, J2000)
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

// =============================================================================
// TYPES
// =============================================================================

interface TransitEvent {
  event_type: string;
  timestamp_utc: string;
  timestamp_local: string;
  local_time: string;
  local_timezone: string;
  description: string;
  significance: string;
  timing: 'passed' | 'current' | 'upcoming';
  minutes_from_now: number;
  transit_planet?: string;
  natal_planet?: string;
  aspect_type?: string;
  orb_at_peak?: number;
  from_sign?: string;
  to_sign?: string;
}

interface SlowTransit {
  transit_planet: string;
  natal_planet: string;
  aspect_type: string;
  orb: number;
  description: string;
  note: string;
}

interface ActiveAspect {
  transit_planet: string;
  natal_planet: string;
  aspect_type: string;
  orb: number;
  is_applying: boolean;
  description: string;
}

interface DailyTheme {
  primary_theme: string;
  moon_context: {
    current_sign: string;
    next_sign?: string;
    ingress_time?: string;
  };
  sun_context: {
    sign: string;
    degree: number;
  };
  theme_keywords: string[];
  upcoming_events: any[];
}

interface DailyWindowData {
  date: string;
  local_timezone: string;
  total_events: number;
  all_events: TransitEvent[];
  moon_ingresses: TransitEvent[];
  aspect_events: TransitEvent[];
  slow_transits_active: SlowTransit[];
  current_moon_sign: string;
  next_moon_sign?: string;
  next_moon_ingress_time?: string;
  strongest_active_aspect?: ActiveAspect;
  current_active_aspects?: ActiveAspect[];
  daily_theme: DailyTheme;
  error?: string;
}

interface TrueSiderealTransitsCardProps {
  userId: string;
  timezone?: string;
  theme: {
    background: string;
    surface: string;
    surfaceLight: string;
    text: string;
    textSecondary: string;
    textTertiary: string;
    accent: string;
    border: string;
  };
  onEventPress?: (event: TransitEvent) => void;
  compact?: boolean;
}

// =============================================================================
// ASPECT SYMBOLS
// =============================================================================

const ASPECT_SYMBOLS: Record<string, string> = {
  conjunction: '☌',
  opposition: '☍',
  trine: '△',
  square: '□',
  sextile: '⚹',
  quincunx: '⚻',
  'semi-sextile': '⚺',
};

const PLANET_SYMBOLS: Record<string, string> = {
  Sun: '☉',
  Moon: '☽',
  Mercury: '☿',
  Venus: '♀',
  Mars: '♂',
  Jupiter: '♃',
  Saturn: '♄',
  Uranus: '♅',
  Neptune: '♆',
  Pluto: '♇',
};

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

const StrongestAspectHero: React.FC<{
  aspect: ActiveAspect;
  exactTime?: string;
  theme: any;
}> = ({ aspect, exactTime, theme }) => (
  <View style={[styles.heroCard, { backgroundColor: theme.surfaceLight, borderColor: theme.accent + '30' }]}>
    <View style={styles.heroHeader}>
      <Text style={[styles.heroLabel, { color: theme.accent }]}>
        STRONGEST ACTIVE
      </Text>
      {exactTime && (
        <Text style={[styles.heroExactTime, { color: theme.textSecondary }]}>
          Exact at {exactTime}
        </Text>
      )}
    </View>
    
    <View style={styles.heroContent}>
      <Text style={[styles.heroPlanets, { color: theme.text }]}>
        {PLANET_SYMBOLS[aspect.transit_planet] || aspect.transit_planet}
        {' '}
        {ASPECT_SYMBOLS[aspect.aspect_type] || '•'}
        {' '}
        {PLANET_SYMBOLS[aspect.natal_planet] || aspect.natal_planet}
      </Text>
      <Text style={[styles.heroDescription, { color: theme.text }]}>
        {aspect.transit_planet} {aspect.aspect_type} natal {aspect.natal_planet}
      </Text>
      <Text style={[styles.heroOrb, { color: theme.textSecondary }]}>
        {aspect.orb.toFixed(1)}° orb • {aspect.is_applying ? 'applying' : 'separating'}
      </Text>
    </View>
  </View>
);

const MoonContextCard: React.FC<{
  currentSign: string;
  nextSign?: string;
  ingressTime?: string;
  theme: any;
}> = ({ currentSign, nextSign, ingressTime, theme }) => (
  <View style={[styles.moonCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
    <View style={styles.moonHeader}>
      <Text style={styles.moonEmoji}>☽</Text>
      <Text style={[styles.moonLabel, { color: theme.textSecondary }]}>MOON</Text>
    </View>
    <Text style={[styles.moonSign, { color: theme.text }]}>
      {currentSign}
    </Text>
    {nextSign && ingressTime && (
      <Text style={[styles.moonIngress, { color: theme.textTertiary }]}>
        → {nextSign} at {ingressTime}
      </Text>
    )}
  </View>
);

const UpcomingEventsList: React.FC<{
  events: TransitEvent[];
  theme: any;
  onEventPress?: (event: TransitEvent) => void;
}> = ({ events, theme, onEventPress }) => {
  if (events.length === 0) {
    return (
      <View style={styles.noEventsContainer}>
        <Text style={[styles.noEventsText, { color: theme.textTertiary }]}>
          No timed events remaining today
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.eventsList}>
      {events.map((event, index) => (
        <TouchableOpacity
          key={`${event.timestamp_utc}-${index}`}
          style={[styles.eventRow, { borderBottomColor: theme.border + '30' }]}
          onPress={() => onEventPress?.(event)}
          activeOpacity={0.7}
        >
          <View style={styles.eventTime}>
            <Text style={[styles.eventTimeText, { color: theme.accent }]}>
              {event.local_time}
            </Text>
          </View>
          
          <View style={styles.eventDetails}>
            <Text style={[styles.eventPlanet, { color: theme.text }]}>
              {PLANET_SYMBOLS[event.transit_planet || ''] || '•'}
              {' '}
              {ASPECT_SYMBOLS[event.aspect_type || ''] || '•'}
              {' '}
              natal {event.natal_planet}
            </Text>
            <Text style={[styles.eventOrb, { color: theme.textTertiary }]}>
              {event.orb_at_peak?.toFixed(2)}° orb
            </Text>
          </View>
          
          {event.significance === 'major' && (
            <View style={[styles.majorBadge, { backgroundColor: theme.accent + '20' }]}>
              <Text style={[styles.majorBadgeText, { color: theme.accent }]}>★</Text>
            </View>
          )}
        </TouchableOpacity>
      ))}
    </View>
  );
};

const SlowTransitsSection: React.FC<{
  transits: SlowTransit[];
  theme: any;
  expanded: boolean;
  onToggle: () => void;
}> = ({ transits, theme, expanded, onToggle }) => {
  if (transits.length === 0) return null;

  return (
    <View style={[styles.slowSection, { borderTopColor: theme.border }]}>
      <TouchableOpacity style={styles.slowHeader} onPress={onToggle}>
        <Text style={[styles.slowLabel, { color: theme.textSecondary }]}>
          SLOW TRANSITS (all day)
        </Text>
        <Ionicons
          name={expanded ? 'chevron-up' : 'chevron-down'}
          size={16}
          color={theme.textTertiary}
        />
      </TouchableOpacity>
      
      {expanded && (
        <View style={styles.slowList}>
          {transits.map((transit, index) => (
            <View key={index} style={styles.slowItem}>
              <Text style={[styles.slowPlanet, { color: theme.text }]}>
                {PLANET_SYMBOLS[transit.transit_planet]}
                {' '}
                {ASPECT_SYMBOLS[transit.aspect_type]}
                {' '}
                {PLANET_SYMBOLS[transit.natal_planet] || transit.natal_planet}
              </Text>
              <Text style={[styles.slowOrb, { color: theme.textTertiary }]}>
                {transit.orb.toFixed(1)}°
              </Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
};

const ThemeKeywords: React.FC<{
  keywords: string[];
  theme: any;
}> = ({ keywords, theme }) => (
  <View style={styles.keywordsContainer}>
    {keywords.map((keyword, index) => (
      <View
        key={index}
        style={[styles.keywordPill, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}
      >
        <Text style={[styles.keywordText, { color: theme.textSecondary }]}>
          {keyword}
        </Text>
      </View>
    ))}
  </View>
);

// =============================================================================
// MAIN COMPONENT
// =============================================================================

const TrueSiderealTransitsCard: React.FC<TrueSiderealTransitsCardProps> = ({
  userId,
  timezone = 'UTC',
  theme,
  onEventPress,
  compact = false,
}) => {
  const [data, setData] = useState<DailyWindowData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [slowExpanded, setSlowExpanded] = useState(false);

  useEffect(() => {
    loadDailyWindow();
  }, [userId, timezone]);

  const loadDailyWindow = async () => {
    try {
      setLoading(true);
      setError(null);

      const { getDailyTransitWindow } = await import('../../services/api');
      const response = await getDailyTransitWindow(userId, timezone);
      
      if (response.error) {
        throw new Error(response.error);
      }
      
      setData(response);
    } catch (err: any) {
      console.error('[TrueSiderealTransits] Error:', err);
      setError(err.message || 'Failed to load transit data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Calculating transits...
          </Text>
        </View>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface }]}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error || 'Unable to load transit data'}
        </Text>
        <TouchableOpacity onPress={loadDailyWindow}>
          <Text style={[styles.retryText, { color: theme.accent }]}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Filter to upcoming events only
  const upcomingEvents = data.all_events.filter(e => e.timing === 'upcoming');
  
  // Find exact time for strongest aspect
  const strongestExactEvent = data.aspect_events.find(
    e => data.strongest_active_aspect &&
         e.transit_planet === data.strongest_active_aspect.transit_planet &&
         e.natal_planet === data.strongest_active_aspect.natal_planet
  );

  return (
    <View style={[styles.container, { backgroundColor: theme.surface }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: theme.text }]}>
          True Sidereal Transits
        </Text>
        <Text style={[styles.headerDate, { color: theme.textTertiary }]}>
          {data.date} • {data.local_timezone}
        </Text>
      </View>

      {/* Theme Keywords */}
      {data.daily_theme?.theme_keywords?.length > 0 && (
        <ThemeKeywords keywords={data.daily_theme.theme_keywords} theme={theme} />
      )}

      {/* Hero: Strongest Active Aspect */}
      {data.strongest_active_aspect && (
        <StrongestAspectHero
          aspect={data.strongest_active_aspect}
          exactTime={strongestExactEvent?.local_time}
          theme={theme}
        />
      )}

      {/* Moon Context */}
      <MoonContextCard
        currentSign={data.current_moon_sign}
        nextSign={data.next_moon_sign}
        ingressTime={data.next_moon_ingress_time}
        theme={theme}
      />

      {/* Upcoming Events */}
      {!compact && (
        <>
          <View style={styles.sectionHeader}>
            <Ionicons name="time-outline" size={14} color={theme.textSecondary} />
            <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
              UPCOMING TODAY ({upcomingEvents.length})
            </Text>
          </View>
          
          <UpcomingEventsList
            events={upcomingEvents}
            theme={theme}
            onEventPress={onEventPress}
          />
        </>
      )}

      {/* Slow Transits */}
      {!compact && data.slow_transits_active.length > 0 && (
        <SlowTransitsSection
          transits={data.slow_transits_active}
          theme={theme}
          expanded={slowExpanded}
          onToggle={() => setSlowExpanded(!slowExpanded)}
        />
      )}

      {/* Footer: Calculation Method */}
      <View style={styles.footer}>
        <Text style={[styles.footerText, { color: theme.textTertiary }]}>
          Swiss Ephemeris • True Sidereal (SVP 31.28°)
        </Text>
      </View>
    </View>
  );
};

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    padding: 16,
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
  
  // Loading/Error
  loadingContainer: {
    padding: 32,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 8,
    fontSize: 13,
    fontStyle: 'italic',
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
    padding: 16,
  },
  retryText: {
    fontSize: 14,
    textAlign: 'center',
    fontWeight: '600',
  },
  
  // Header
  header: {
    marginBottom: 12,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: -0.3,
  },
  headerDate: {
    fontSize: 12,
    marginTop: 2,
  },
  
  // Keywords
  keywordsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 16,
  },
  keywordPill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
  },
  keywordText: {
    fontSize: 11,
    fontWeight: '500',
    textTransform: 'lowercase',
  },
  
  // Hero Card
  heroCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    marginBottom: 12,
  },
  heroHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  heroLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  heroExactTime: {
    fontSize: 11,
  },
  heroContent: {
    alignItems: 'center',
  },
  heroPlanets: {
    fontSize: 28,
    fontWeight: '300',
    letterSpacing: 4,
    marginBottom: 4,
  },
  heroDescription: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 4,
  },
  heroOrb: {
    fontSize: 12,
  },
  
  // Moon Card
  moonCard: {
    borderRadius: 10,
    borderWidth: 1,
    padding: 12,
    marginBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  moonHeader: {
    alignItems: 'center',
  },
  moonEmoji: {
    fontSize: 24,
  },
  moonLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  moonSign: {
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  moonIngress: {
    fontSize: 12,
  },
  
  // Section Header
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  
  // Events List
  eventsList: {
    marginBottom: 12,
  },
  eventRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  eventTime: {
    width: 70,
  },
  eventTimeText: {
    fontSize: 13,
    fontWeight: '600',
  },
  eventDetails: {
    flex: 1,
  },
  eventPlanet: {
    fontSize: 14,
    fontWeight: '500',
  },
  eventOrb: {
    fontSize: 11,
    marginTop: 2,
  },
  majorBadge: {
    width: 20,
    height: 20,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  majorBadgeText: {
    fontSize: 10,
  },
  noEventsContainer: {
    padding: 16,
    alignItems: 'center',
  },
  noEventsText: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  
  // Slow Transits
  slowSection: {
    borderTopWidth: 1,
    paddingTop: 12,
    marginTop: 4,
  },
  slowHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  slowLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  slowList: {
    marginTop: 8,
  },
  slowItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  slowPlanet: {
    fontSize: 14,
  },
  slowOrb: {
    fontSize: 12,
  },
  
  // Footer
  footer: {
    marginTop: 12,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 10,
    fontStyle: 'italic',
  },
});

export default TrueSiderealTransitsCard;
