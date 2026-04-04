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
  is_outer_planet?: boolean;
  is_applying?: boolean;
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
  scan_start_utc?: string;
  scan_end_utc?: string;
  computed_at?: string;
  total_events: number;
  all_events: TransitEvent[];
  moon_ingresses: TransitEvent[];
  house_ingresses?: TransitEvent[];
  aspect_events: TransitEvent[];
  slow_transits_active: SlowTransit[];
  current_moon_sign: string;
  current_moon_house?: number;
  transit_houses?: { [key: string]: number };
  next_moon_sign?: string;
  next_moon_ingress_time?: string;
  strongest_active_aspect?: ActiveAspect;
  current_active_aspects?: ActiveAspect[];
  daily_theme?: DailyTheme;
  house_system?: string;
  calculation_method?: string;
  user_timezone?: string;
  error?: string;
}

/**
 * DEV/DEBUG FOOTER - Shows calculation provenance
 * Proves config parity with external tools like Chimenti reports
 */
const DebugFooter: React.FC<{
  data: DailyWindowData;
  theme: any;
  showFull?: boolean;
}> = ({ data, theme, showFull = false }) => {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <View style={styles.debugFooter}>
      <TouchableOpacity 
        style={styles.debugToggle}
        onPress={() => setExpanded(!expanded)}
        activeOpacity={0.7}
      >
        <View style={[styles.debugBadge, { backgroundColor: theme.surfaceLight }]}>
          <Text style={[styles.debugBadgeText, { color: theme.textTertiary }]}>
            True Sidereal
          </Text>
        </View>
        <Text style={[styles.debugSvp, { color: theme.textTertiary }]}>
          SVP 31.2836°
        </Text>
        <Ionicons
          name={expanded ? 'chevron-up' : 'information-circle-outline'}
          size={12}
          color={theme.textTertiary}
        />
      </TouchableOpacity>
      
      {expanded && (
        <View style={[styles.debugDetails, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
          <View style={styles.debugRow}>
            <Text style={[styles.debugLabel, { color: theme.textTertiary }]}>Config:</Text>
            <Text style={[styles.debugValue, { color: theme.textSecondary }]}>
              Swiss Ephemeris SIDM_USER
            </Text>
          </View>
          <View style={styles.debugRow}>
            <Text style={[styles.debugLabel, { color: theme.textTertiary }]}>SVP:</Text>
            <Text style={[styles.debugValue, { color: theme.textSecondary }]}>
              31.2836° at J2000
            </Text>
          </View>
          <View style={styles.debugRow}>
            <Text style={[styles.debugLabel, { color: theme.textTertiary }]}>House System:</Text>
            <Text style={[styles.debugValue, { color: theme.textSecondary }]}>
              {data.house_system || 'Equal (Asc-based)'}
            </Text>
          </View>
          <View style={styles.debugRow}>
            <Text style={[styles.debugLabel, { color: theme.textTertiary }]}>Timezone:</Text>
            <Text style={[styles.debugValue, { color: theme.textSecondary }]}>
              {data.local_timezone}
            </Text>
          </View>
          <View style={styles.debugRow}>
            <Text style={[styles.debugLabel, { color: theme.textTertiary }]}>Computed:</Text>
            <Text style={[styles.debugValue, { color: theme.textSecondary }]}>
              {data.computed_at ? new Date(data.computed_at).toLocaleTimeString() : 'Now'}
            </Text>
          </View>
          {data.transit_houses && Object.keys(data.transit_houses).length > 0 && (
            <View style={styles.debugRow}>
              <Text style={[styles.debugLabel, { color: theme.textTertiary }]}>Moon House:</Text>
              <Text style={[styles.debugValue, { color: theme.textSecondary }]}>
                {data.transit_houses.Moon || data.current_moon_house || '—'}
              </Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
};

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

/**
 * HERO ASPECT - Most significant transit displayed prominently
 * Shows the tightest active aspect at the top
 */
const HeroAspectCard: React.FC<{
  aspect: ActiveAspect;
  exactTime?: string;
  theme: any;
}> = ({ aspect, exactTime, theme }) => (
  <View style={[styles.heroCard, { backgroundColor: theme.surfaceLight, borderColor: theme.accent + '30' }]}>
    <View style={styles.heroHeader}>
      <Text style={[styles.heroLabel, { color: theme.accent }]}>
        TODAY'S MAIN TRANSIT
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

/**
 * MOON CONTEXT - Current Moon sign and house
 * Second in hierarchy after Hero aspect
 */
const MoonContextCard: React.FC<{
  currentSign: string;
  currentHouse?: number;
  nextSign?: string;
  ingressTime?: string;
  theme: any;
}> = ({ currentSign, currentHouse, nextSign, ingressTime, theme }) => {
  const houseLabel = currentHouse ? `${currentHouse}${getOrdinalSuffix(currentHouse)} house` : null;
  
  return (
    <View style={[styles.moonCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      <View style={styles.moonHeader}>
        <Text style={styles.moonEmoji}>☽</Text>
        <Text style={[styles.moonLabel, { color: theme.textSecondary }]}>MOON NOW</Text>
      </View>
      <View style={styles.moonContent}>
        <Text style={[styles.moonSign, { color: theme.text }]}>
          {currentSign}
        </Text>
        {houseLabel && (
          <Text style={[styles.moonHouse, { color: theme.textSecondary }]}>
            in {houseLabel}
          </Text>
        )}
      </View>
      {nextSign && ingressTime && (
        <Text style={[styles.moonIngress, { color: theme.textTertiary }]}>
          → {nextSign} at {ingressTime}
        </Text>
      )}
    </View>
  );
};

/**
 * Helper to get ordinal suffix (1st, 2nd, 3rd, etc.)
 */
const getOrdinalSuffix = (n: number): string => {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return s[(v - 20) % 10] || s[v] || s[0];
};

/**
 * TIMED EVENTS - Top 3 upcoming exact times
 * Shows only 3 by default with "show more" expansion
 */
const TimedEventsList: React.FC<{
  events: TransitEvent[];
  expanded: boolean;
  onToggle: () => void;
  theme: any;
  onEventPress?: (event: TransitEvent) => void;
}> = ({ events, expanded, onToggle, theme, onEventPress }) => {
  if (events.length === 0) {
    return (
      <View style={styles.noEventsContainer}>
        <Text style={[styles.noEventsText, { color: theme.textTertiary }]}>
          No timed events remaining today
        </Text>
      </View>
    );
  }

  // Show top 3 by default, all if expanded
  const displayEvents = expanded ? events : events.slice(0, 3);
  const hasMore = events.length > 3;

  return (
    <View style={styles.eventsList}>
      {displayEvents.map((event, index) => (
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
      
      {/* Show More / Show Less toggle */}
      {hasMore && (
        <TouchableOpacity
          style={styles.showMoreButton}
          onPress={onToggle}
          activeOpacity={0.7}
        >
          <Text style={[styles.showMoreText, { color: theme.accent }]}>
            {expanded ? 'Show less' : `Show ${events.length - 3} more`}
          </Text>
          <Ionicons
            name={expanded ? 'chevron-up' : 'chevron-down'}
            size={14}
            color={theme.accent}
          />
        </TouchableOpacity>
      )}
    </View>
  );
};

/**
 * SLOW TRANSITS - Top 3 outer planet transits active all day
 * Shows top 3 by default, expandable
 */
const SlowTransitsSection: React.FC<{
  transits: SlowTransit[];
  theme: any;
  expanded: boolean;
  onToggle: () => void;
}> = ({ transits, theme, expanded, onToggle }) => {
  if (transits.length === 0) return null;

  // Show top 3 by default
  const displayTransits = expanded ? transits : transits.slice(0, 3);
  const hasMore = transits.length > 3;

  return (
    <View style={[styles.slowSection, { borderTopColor: theme.border }]}>
      <TouchableOpacity style={styles.slowHeader} onPress={onToggle}>
        <View style={styles.slowHeaderLeft}>
          <Ionicons name="planet-outline" size={14} color={theme.textSecondary} />
          <Text style={[styles.slowLabel, { color: theme.textSecondary }]}>
            SLOW TRANSITS
          </Text>
          <Text style={[styles.slowCount, { color: theme.textTertiary }]}>
            ({transits.length})
          </Text>
        </View>
        <Ionicons
          name={expanded ? 'chevron-up' : 'chevron-down'}
          size={16}
          color={theme.textTertiary}
        />
      </TouchableOpacity>
      
      <View style={styles.slowList}>
        {displayTransits.map((transit, index) => (
          <View key={index} style={styles.slowItem}>
            <View style={styles.slowItemLeft}>
              <Text style={[styles.slowPlanet, { color: theme.text }]}>
                {PLANET_SYMBOLS[transit.transit_planet]}
                {' '}
                {ASPECT_SYMBOLS[transit.aspect_type]}
                {' '}
                {PLANET_SYMBOLS[transit.natal_planet] || transit.natal_planet}
              </Text>
              {transit.is_outer_planet && (
                <View style={[styles.outerPlanetBadge, { backgroundColor: theme.surfaceLight }]}>
                  <Text style={[styles.outerPlanetText, { color: theme.textTertiary }]}>
                    outer
                  </Text>
                </View>
              )}
            </View>
            <Text style={[styles.slowOrb, { color: theme.textTertiary }]}>
              {transit.orb.toFixed(1)}°
            </Text>
          </View>
        ))}
      </View>
      
      {/* Show more indicator */}
      {hasMore && !expanded && (
        <TouchableOpacity
          style={styles.showMoreButton}
          onPress={onToggle}
          activeOpacity={0.7}
        >
          <Text style={[styles.showMoreText, { color: theme.accent }]}>
            +{transits.length - 3} more
          </Text>
        </TouchableOpacity>
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
  const [eventsExpanded, setEventsExpanded] = useState(false);

  useEffect(() => {
    loadDailyWindow();
  }, [userId, timezone]);

  const loadDailyWindow = async () => {
    try {
      setLoading(true);
      setError(null);

      const { getDailyTransitWindow } = await import('../services/api');
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

  // Get current Moon house from transit_houses or current_moon_house
  const currentMoonHouse = data.transit_houses?.Moon || data.current_moon_house;

  return (
    <View style={[styles.container, { backgroundColor: theme.surface }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: theme.text }]}>
          Today's Transits
        </Text>
        <Text style={[styles.headerDate, { color: theme.textTertiary }]}>
          {data.date}
        </Text>
      </View>

      {/* ============================================================ */}
      {/* STRICT HIERARCHY:                                            */}
      {/* 1. Hero Aspect (most significant transit)                    */}
      {/* 2. Moon Context (sign + house)                               */}
      {/* 3. Top 3 Timed Events (with "show more")                     */}
      {/* 4. Top 3 Slow Transits (with "show more")                    */}
      {/* 5. Debug Footer (provenance info)                            */}
      {/* ============================================================ */}

      {/* 1. HERO: Strongest Active Aspect */}
      {data.strongest_active_aspect && (
        <HeroAspectCard
          aspect={data.strongest_active_aspect}
          exactTime={strongestExactEvent?.local_time}
          theme={theme}
        />
      )}

      {/* 2. MOON CONTEXT (sign + house) */}
      <MoonContextCard
        currentSign={data.current_moon_sign}
        currentHouse={currentMoonHouse}
        nextSign={data.next_moon_sign}
        ingressTime={data.next_moon_ingress_time}
        theme={theme}
      />

      {/* 3. TOP 3 TIMED EVENTS (expandable) */}
      {!compact && (
        <>
          <View style={styles.sectionHeader}>
            <Ionicons name="time-outline" size={14} color={theme.textSecondary} />
            <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
              TIMED EVENTS
            </Text>
            {upcomingEvents.length > 0 && (
              <Text style={[styles.sectionCount, { color: theme.textTertiary }]}>
                ({upcomingEvents.length})
              </Text>
            )}
          </View>
          
          <TimedEventsList
            events={upcomingEvents}
            expanded={eventsExpanded}
            onToggle={() => setEventsExpanded(!eventsExpanded)}
            theme={theme}
            onEventPress={onEventPress}
          />
        </>
      )}

      {/* 4. TOP 3 SLOW TRANSITS (expandable) */}
      {!compact && data.slow_transits_active.length > 0 && (
        <SlowTransitsSection
          transits={data.slow_transits_active}
          theme={theme}
          expanded={slowExpanded}
          onToggle={() => setSlowExpanded(!slowExpanded)}
        />
      )}

      {/* 5. DEBUG FOOTER - Calculation provenance */}
      <DebugFooter data={data} theme={theme} />
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
  
  // Moon Content (new for house display)
  moonContent: {
    flex: 1,
  },
  moonHouse: {
    fontSize: 12,
    marginTop: 2,
  },
  
  // Section Count
  sectionCount: {
    fontSize: 10,
    marginLeft: 4,
  },
  
  // Show More Button
  showMoreButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    gap: 4,
  },
  showMoreText: {
    fontSize: 12,
    fontWeight: '600',
  },
  
  // Slow Section Header Left
  slowHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  slowCount: {
    fontSize: 10,
  },
  
  // Slow Item Left (for outer planet badge)
  slowItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  
  // Outer Planet Badge
  outerPlanetBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  outerPlanetText: {
    fontSize: 9,
    fontWeight: '500',
    textTransform: 'uppercase',
  },
  
  // Debug Footer
  debugFooter: {
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.05)',
  },
  debugToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  debugBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  debugBadgeText: {
    fontSize: 10,
    fontWeight: '600',
  },
  debugSvp: {
    fontSize: 10,
  },
  debugDetails: {
    marginTop: 10,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
  },
  debugRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  debugLabel: {
    fontSize: 11,
  },
  debugValue: {
    fontSize: 11,
    fontWeight: '500',
  },
});

export default TrueSiderealTransitsCard;
