import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Colors } from '../../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import { useAppStore } from '../../store';
import { getChartDetails, ChartDetails } from '../../services/api';

const LENS_CONTENT: { [key: string]: any } = {
  astrology: {
    name: 'True Sidereal Astrology',
    summary: 'A lens for understanding cosmic rhythms and archetypal patterns. This shows where celestial bodies were at your birth, using the True Sidereal system (aligned with actual star positions, not seasons).',
    howToUse: [
      'Notice patterns in timing and cycles',
      'Consider archetypal themes, not fixed traits'
    ],
    deepDive: {
      intro: 'Your natal chart is calculated using True Sidereal positions aligned to star-based coordinates, which accounts for the precession of the equinoxes.',
      sections: [
        {
          title: 'What This Shows',
          content: 'Planet positions at your birth moment, showing energetic patterns and cycles. This is descriptive, not deterministic—it offers one way to see themes in your life.'
        },
        {
          title: 'Key Points',
          content: 'Sun, Moon, and Rising sign form the core. Planets represent different life areas. Houses show where these play out. Aspects reveal relationships between energies.'
        },
        {
          title: 'What It Does NOT Do',
          content: 'Does not predict events. Does not define who you are. Does not limit your choices. It\'s a map, not a mandate.'
        }
      ]
    }
  },
  human_design: {
    name: 'Human Design',
    summary: 'A synthesis showing how you\'re designed to interact with the world. Combines aspects of astrology, I-Ching, Kabbalah, and the chakra system into a unique "bodygraph."',
    howToUse: [
      'Understand your natural decision-making process',
      'Recognize your energy type and how you engage'
    ],
    deepDive: {
      intro: 'Your Human Design is calculated from two charts: Personality (conscious, at birth) and Design (unconscious, ~88 days before birth).',
      sections: [
        {
          title: 'What This Shows',
          content: 'Your Type shows how you best interact with the world. Authority indicates your decision-making process. Profile reveals your role and learning style. Centers show consistent vs. variable energy.'
        },
        {
          title: 'The 64 Gates',
          content: 'Gates correspond to I-Ching hexagrams and are activated by planetary positions. When two gates connect, they form a channel, creating defined energy.'
        },
        {
          title: 'V1 Note',
          content: 'Current calculations use simplified gate-to-center mapping without full channel analysis. This may affect Type accuracy. Full channel logic coming in future updates.'
        },
        {
          title: 'What It Does NOT Do',
          content: 'Does not tell you who you should be. Does not predict your future. Does not limit your potential. It\'s information, not instruction.'
        }
      ]
    }
  },
  numerology: {
    name: 'Numerology',
    summary: 'A system revealing patterns in numbers and life paths. Uses your birth date and name to identify recurring themes and natural rhythms in your life journey.',
    howToUse: [
      'Recognize core themes in your experience',
      'Notice when certain patterns repeat'
    ],
    deepDive: {
      intro: 'Numerology reduces numbers to single digits (or master numbers 11, 22, 33), each carrying specific archetypal meaning.',
      sections: [
        {
          title: 'Life Path Number',
          content: 'Calculated from your full birth date. Represents the primary theme of your life journey—not your destiny, but a lens for understanding patterns.'
        },
        {
          title: 'Expression Number',
          content: 'Derived from your full name at birth. Shows natural talents and how you express yourself in the world.'
        },
        {
          title: 'What It Does NOT Do',
          content: 'Does not guarantee outcomes. Does not define your limits. Does not predict specific events. It highlights patterns, not prescriptions.'
        }
      ]
    }
  },
  consciousness: {
    name: 'Levels of Consciousness',
    summary: 'A map of emotional and spiritual development based on Dr. David Hawkins\' research. Shows 17 levels from Shame (20) to Enlightenment (700-1000).',
    howToUse: [
      'Understand where you currently are, not where you "should" be',
      'Notice what might shift as you move between levels'
    ],
    deepDive: {
      intro: 'The Map of Consciousness calibrates emotions and viewpoints on a logarithmic scale from 1-1000, where 200 is the critical threshold of integrity.',
      sections: [
        {
          title: 'Below 200: Force',
          content: 'Levels like Shame, Guilt, Fear, and Anger. Take more energy than they give. Survival-based. Life feels like something happening TO you.'
        },
        {
          title: 'Above 200: Power',
          content: 'Levels like Courage, Acceptance, and Love. Generate more than they consume. Life feels like something you participate IN.'
        },
        {
          title: 'What It Does NOT Do',
          content: 'Does not rank people\'s worth. Does not mean "higher is better" morally. Does not guarantee you won\'t move between levels. It describes, not judges.'
        }
      ]
    }
  }
};

export default function LensDetail() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const { lens } = params;
  // Support modes: "summary" | "snapshot" | "deep_dive"
  const mode = (params.mode as string) || 'summary';
  const { user, chartDetails: cachedChartDetails, cacheChartDetails, getChartDetailsCacheKey } = useAppStore();
  
  // Local state for chart details (uses cache if available)
  const [chartDetails, setChartDetails] = useState<ChartDetails | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const content = LENS_CONTENT[lens as string];
  
  // Fetch chart details on mount - use cache if valid
  useEffect(() => {
    const fetchChartDetails = async () => {
      if (!user?.id) return;
      
      // Check if we have valid cached data
      const currentCacheKey = getChartDetailsCacheKey();
      if (cachedChartDetails && cachedChartDetails._userBirthDataHash === currentCacheKey) {
        console.log('[LensDetail] Using cached chartDetails');
        // [DEBUG] Log full response shape
        console.log('[DEBUG] chartDetails response shape:', JSON.stringify(cachedChartDetails, null, 2));
        setChartDetails(cachedChartDetails);
        return;
      }
      
      // No valid cache, fetch from API
      console.log('[LensDetail] Fetching chartDetails from API');
      setIsLoading(true);
      setError(null);
      
      try {
        const details = await getChartDetails(user.id);
        // [DEBUG] Log full response shape from API
        console.log('[DEBUG] chartDetails response shape:', JSON.stringify(details, null, 2));
        setChartDetails(details);
        // Cache the fetched details
        cacheChartDetails(details);
      } catch (err: any) {
        console.error('Failed to fetch chart details:', err);
        setError(err?.response?.data?.detail || 'Failed to load your chart data');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchChartDetails();
  }, [user?.id, cachedChartDetails, getChartDetailsCacheKey, cacheChartDetails]);
  
  // Zodiac signs for longitude to sign conversion
  const ZODIAC_SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
  ];

  // Convert longitude to sign
  const getSignFromLongitude = (longitude: number): string => {
    const signIndex = Math.floor(longitude / 30) % 12;
    return ZODIAC_SIGNS[signIndex];
  };

  // Format degrees and minutes (19°37' style)
  const formatDegreeMinutes = (decimalDegree: number): string => {
    const degrees = Math.floor(decimalDegree);
    const minutes = Math.floor((decimalDegree - degrees) * 60);
    return minutes > 0 ? `${degrees}°${minutes}'` : `${degrees}°`;
  };

  // =========================================================================
  // PROMPT 1: Format planet position with formatted-first priority
  // =========================================================================
  // Priority: formatted > sign+degree > longitude-computed > "—"
  // =========================================================================
  const formatPlanetPosition = (obj: any): string => {
    if (!obj) return '—';
    
    // Priority 1: Use formatted string if exists
    if (obj.formatted) {
      return obj.formatted;
    }
    
    // Priority 2: Use sign + degree if both exist
    if (obj.sign && obj.degree != null) {
      return `${obj.sign} ${formatDegreeMinutes(obj.degree)}`;
    }
    
    // Priority 3: Compute from longitude if available
    if (typeof obj.longitude === 'number') {
      const sign = getSignFromLongitude(obj.longitude);
      const degreeInSign = obj.longitude % 30;
      return `${sign} ${formatDegreeMinutes(degreeInSign)}`;
    }
    
    // Priority 4: Just sign if available
    if (obj.sign) {
      return obj.sign;
    }
    
    // Fallback
    return '—';
  };
  
  // Get sidereal system label - neutral copy only (PROMPT 4)
  const getSiderealSystemLabel = (): string => {
    // Always return neutral copy - do not expose internal settings
    // NO ayanamsa names, NO SVP numbers
    return 'True Sidereal positions';
  };

  // Navigate to different modes
  const navigateToMode = (targetMode: string) => {
    router.push(`/lenses/${lens}?mode=${targetMode}` as any);
  };

  // =========================================================================
  // PROMPT 2: UI INVARIANT with partial rising safety
  // =========================================================================
  // sun/moon should always exist post-compute
  // rising may be present but partially null - handle gracefully
  // =========================================================================
  const isOnboardedUser = !!user?.id;
  const fetchSucceeded = !isLoading && !error;
  const isAstrologyLens = lens === 'astrology';
  
  // Astrology object from response
  const astrology = chartDetails?.astrology;
  const hasAstrologyInResponse = !!astrology;
  
  // Core placements - use rising (the actual backend field name)
  const sun = astrology?.sun;
  const moon = astrology?.moon;
  const rising = astrology?.rising; // Backend uses "rising" for Ascendant
  
  // PROMPT 2: Check if placement has ANY usable data (not just existence)
  const hasSun = !!sun?.formatted || !!sun?.sign || typeof sun?.longitude === 'number';
  const hasMoon = !!moon?.formatted || !!moon?.sign || typeof moon?.longitude === 'number';
  const hasRising = !!rising?.formatted || !!rising?.sign || typeof rising?.longitude === 'number';
  
  // Count how many of the 3 core placements have usable data
  const corePlacementsCount = [hasSun, hasMoon, hasRising].filter(Boolean).length;
  
  // Can render personalized if at least 1 core placement exists
  const hasAnyCorePlacement = corePlacementsCount >= 1;
  
  // PROMPT 2: Invariant violation ONLY if astrology object exists but NONE of sun/moon/rising have data
  // Partial null fields in rising are OK if Sun/Moon are present
  const invariantViolation = isOnboardedUser && 
    fetchSucceeded && 
    isAstrologyLens &&
    hasAstrologyInResponse && 
    !hasAnyCorePlacement;
  
  // For rendering: show personalized section if we have ANY core placement
  const hasAstrologyData = hasAnyCorePlacement;
  
  // Log warning in development when invariant fails
  useEffect(() => {
    if (invariantViolation) {
      console.warn(
        '[UI INVARIANT VIOLATION] LensDetail: Onboarded user with astrology object but NO usable core placements.',
        {
          userId: user?.id,
          hasChartDetails: !!chartDetails,
          hasAstrology: hasAstrologyInResponse,
          hasSun,
          hasMoon,
          hasRising,
          corePlacementsCount,
          sunData: sun,
          moonData: moon,
          risingData: rising,
        }
      );
    }
  }, [invariantViolation, user?.id, chartDetails, hasAstrologyInResponse, hasSun, hasMoon, hasRising, corePlacementsCount]);

  // Shared retry handler for both error banners
  const handleRetry = () => {
    if (!user?.id) return;
    
    setError(null);
    setChartDetails(null);
    setIsLoading(true);
    
    getChartDetails(user.id)
      .then((details) => {
        setChartDetails(details);
        cacheChartDetails(details);
        console.log('[LensDetail] Retry successful, data cached');
      })
      .catch((err) => {
        console.error('[LensDetail] Retry failed:', err);
        setError(err?.response?.data?.detail || 'Failed to load your chart data');
      })
      .finally(() => setIsLoading(false));
  };

  // Render error banner for invariant violation
  const renderInvariantErrorBanner = () => (
    <View style={styles.invariantErrorBanner}>
      <Ionicons name="warning-outline" size={18} color="#D97706" />
      <Text style={styles.invariantErrorText}>
        We couldn't load your snapshot. Try again.
      </Text>
      <TouchableOpacity 
        style={styles.invariantRetryButton}
        onPress={handleRetry}
      >
        <Ionicons name="refresh" size={16} color="#D97706" />
      </TouchableOpacity>
    </View>
  );
  
  // Render personalized Astrology snapshot (compact version for summary)
  const renderAstrologySnapshotCompact = () => {
    if (!hasAstrologyInResponse) return null;
    
    // Use component-level sun, moon, asc variables (with hardened field mapping)
    return (
      <View style={styles.snapshotCard}>
        <View style={styles.snapshotHeader}>
          <Ionicons name="sparkles" size={20} color={Colors.text} />
          <Text style={styles.snapshotTitle}>Your Sidereal Snapshot</Text>
        </View>
        
        {/* Sun/Moon/Rising rows - only render if data exists */}
        <View style={styles.snapshotRows}>
          {hasSun && (
            <View style={styles.snapshotRow}>
              <View style={styles.snapshotRowIcon}>
                <Ionicons name="sunny" size={18} color={Colors.text} />
              </View>
              <Text style={styles.snapshotRowLabel}>Sun</Text>
              <Text style={styles.snapshotRowValue}>{formatPlanetPosition(sun)}</Text>
            </View>
          )}
          
          {hasMoon && (
            <View style={styles.snapshotRow}>
              <View style={styles.snapshotRowIcon}>
                <Ionicons name="moon" size={18} color={Colors.text} />
              </View>
              <Text style={styles.snapshotRowLabel}>Moon</Text>
              <Text style={styles.snapshotRowValue}>{formatPlanetPosition(moon)}</Text>
            </View>
          )}
          
          {hasRising && (
            <View style={styles.snapshotRow}>
              <View style={styles.snapshotRowIcon}>
                <Ionicons name="arrow-up-circle" size={18} color={Colors.text} />
              </View>
              <Text style={styles.snapshotRowLabel}>Ascendant</Text>
              <Text style={styles.snapshotRowValue}>{formatPlanetPosition(rising)}</Text>
            </View>
          )}
        </View>
        
        {/* System label - neutral copy (PROMPT 4) */}
        <View style={styles.systemLabel}>
          <Text style={styles.systemLabelText}>
            Calculated using {getSiderealSystemLabel()}.
          </Text>
        </View>

        {/* Navigation buttons */}
        <View style={styles.snapshotButtons}>
          <TouchableOpacity 
            style={styles.snapshotButtonPrimary}
            onPress={() => navigateToMode('snapshot')}
          >
            <Text style={styles.snapshotButtonPrimaryText}>Full Snapshot</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.snapshotButtonSecondary}
            onPress={() => navigateToMode('deep_dive')}
          >
            <Text style={styles.snapshotButtonSecondaryText}>Go Deeper</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  // Render full snapshot view (Sun/Moon/Rising + houses summary)
  const renderSnapshotView = () => {
    if (!chartDetails?.astrology) {
      return (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateText}>Chart data not available</Text>
        </View>
      );
    }
    
    // PROMPT 3: Use astrology.houses array for house data
    const houses = astrology?.houses;
    const hasHouses = Array.isArray(houses) && houses.length > 0;
    
    return (
      <>
        {/* Main Placements */}
        <View style={styles.snapshotCard}>
          <View style={styles.snapshotHeader}>
            <Ionicons name="sparkles" size={20} color={Colors.text} />
            <Text style={styles.snapshotTitle}>Your Core Placements</Text>
          </View>
          
          <View style={styles.placementsList}>
            {hasSun && (
              <View style={styles.placementRow}>
                <View style={styles.placementIcon}>
                  <Ionicons name="sunny" size={20} color={Colors.text} />
                </View>
                <View style={styles.placementInfo}>
                  <Text style={styles.placementLabel}>Sun</Text>
                  <Text style={styles.placementValue}>{formatPlanetPosition(sun)}</Text>
                  {sun?.house && <Text style={styles.placementHouse}>House {sun.house}</Text>}
                </View>
              </View>
            )}
            
            {hasMoon && (
              <View style={styles.placementRow}>
                <View style={styles.placementIcon}>
                  <Ionicons name="moon" size={20} color={Colors.text} />
                </View>
                <View style={styles.placementInfo}>
                  <Text style={styles.placementLabel}>Moon</Text>
                  <Text style={styles.placementValue}>{formatPlanetPosition(moon)}</Text>
                  {moon?.house && <Text style={styles.placementHouse}>House {moon.house}</Text>}
                </View>
              </View>
            )}
            
            {hasRising && (
              <View style={styles.placementRow}>
                <View style={styles.placementIcon}>
                  <Ionicons name="arrow-up-circle" size={20} color={Colors.text} />
                </View>
                <View style={styles.placementInfo}>
                  <Text style={styles.placementLabel}>Ascendant (Rising)</Text>
                  <Text style={styles.placementValue}>{formatPlanetPosition(rising)}</Text>
                </View>
              </View>
            )}
          </View>
        </View>

        {/* Houses Summary - PROMPT 3: render from astrology.houses[] */}
        {hasHouses ? (
          <View style={styles.housesCard}>
            <Text style={styles.cardTitle}>Houses Overview</Text>
            <Text style={styles.cardSubtitle}>Equal House System</Text>
            
            <View style={styles.housesGrid}>
              {houses.slice(0, 6).map((house: any) => (
                <View key={house.house} style={styles.houseItem}>
                  <Text style={styles.houseNumber}>{house.house}</Text>
                  <Text style={styles.houseSign}>{house.sign}</Text>
                </View>
              ))}
            </View>
            <View style={styles.housesGrid}>
              {houses.slice(6, 12).map((house: any) => (
                <View key={house.house} style={styles.houseItem}>
                  <Text style={styles.houseNumber}>{house.house}</Text>
                  <Text style={styles.houseSign}>{house.sign}</Text>
                </View>
              ))}
            </View>
          </View>
        ) : (
          <View style={styles.comingSoonCard}>
            <Ionicons name="time-outline" size={20} color={Colors.textTertiary} />
            <Text style={styles.comingSoonText}>Houses data coming soon</Text>
          </View>
        )}
        
        <View style={styles.systemLabel}>
          <Ionicons name="information-circle-outline" size={14} color={Colors.textTertiary} />
          <Text style={styles.systemLabelText}>
            Calculated using {getSiderealSystemLabel()}
          </Text>
        </View>

        {/* Navigation buttons */}
        <View style={styles.modeNavigation}>
          <TouchableOpacity 
            style={styles.modeNavButton}
            onPress={() => navigateToMode('summary')}
          >
            <Ionicons name="book-outline" size={18} color={Colors.text} />
            <Text style={styles.modeNavButtonText}>About This Lens</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.modeNavButton, styles.modeNavButtonPrimary]}
            onPress={() => navigateToMode('deep_dive')}
          >
            <Ionicons name="telescope-outline" size={18} color={Colors.background} />
            <Text style={styles.modeNavButtonTextPrimary}>Full Chart</Text>
          </TouchableOpacity>
        </View>
      </>
    );
  };

  // Render deep dive view (all planets, houses, aspects)
  const renderDeepDiveView = () => {
    if (!chartDetails?.astrology) {
      return (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateText}>Chart data not available</Text>
        </View>
      );
    }
    
    const { planets, houses } = chartDetails.astrology;
    const hasPlanets = planets && planets.length > 0;
    const hasHouses = houses && houses.length > 0;
    
    return (
      <>
        {/* Always show compact snapshot at top of deep dive */}
        <View style={styles.snapshotCard}>
          <View style={styles.snapshotHeader}>
            <Ionicons name="sparkles" size={20} color={Colors.text} />
            <Text style={styles.snapshotTitle}>Your Sidereal Snapshot</Text>
          </View>
          
          <View style={styles.snapshotRows}>
            {hasSun && (
              <View style={styles.snapshotRow}>
                <View style={styles.snapshotRowIcon}>
                  <Ionicons name="sunny" size={18} color={Colors.text} />
                </View>
                <Text style={styles.snapshotRowLabel}>Sun</Text>
                <Text style={styles.snapshotRowValue}>{formatPlanetPosition(sun)}</Text>
              </View>
            )}
            
            {hasMoon && (
              <View style={styles.snapshotRow}>
                <View style={styles.snapshotRowIcon}>
                  <Ionicons name="moon" size={18} color={Colors.text} />
                </View>
                <Text style={styles.snapshotRowLabel}>Moon</Text>
                <Text style={styles.snapshotRowValue}>{formatPlanetPosition(moon)}</Text>
              </View>
            )}
            
            {hasAscendant && (
              <View style={styles.snapshotRow}>
                <View style={styles.snapshotRowIcon}>
                  <Ionicons name="arrow-up-circle" size={18} color={Colors.text} />
                </View>
                <Text style={styles.snapshotRowLabel}>Ascendant</Text>
                <Text style={styles.snapshotRowValue}>{formatPlanetPosition(asc)}</Text>
              </View>
            )}
          </View>
        </View>

        {/* Disclaimer */}
        <View style={styles.disclaimerCard}>
          <Ionicons name="information-circle-outline" size={20} color={Colors.textSecondary} />
          <Text style={styles.disclaimerText}>
            Descriptive, not deterministic. These positions are factual data—interpretation is up to you.
          </Text>
        </View>

        {/* All Planets */}
        {hasPlanets ? (
          <View style={styles.deepDiveSection}>
            <Text style={styles.deepDiveSectionTitle}>Planetary Positions</Text>
            
            {planets.map((planet: any) => (
              <View key={planet.name} style={styles.planetRow}>
                <Text style={styles.planetName}>{planet.name}</Text>
                <View style={styles.planetDetails}>
                  <Text style={styles.planetSign}>{planet.sign || 'Unknown'}</Text>
                  {planet.degree != null && (
                    <Text style={styles.planetDegree}>{formatDegreeMinutes(planet.degree)}</Text>
                  )}
                  {planet.house && (
                    <Text style={styles.planetHouse}>H{planet.house}</Text>
                  )}
                </View>
              </View>
            ))}
          </View>
        ) : (
          <View style={styles.comingSoonCard}>
            <Ionicons name="planet-outline" size={20} color={Colors.textTertiary} />
            <Text style={styles.comingSoonText}>More depth will appear here as your lenses expand.</Text>
          </View>
        )}

        {/* All Houses */}
        {hasHouses ? (
          <View style={styles.deepDiveSection}>
            <Text style={styles.deepDiveSectionTitle}>House Cusps</Text>
            <Text style={styles.deepDiveSectionSubtitle}>Equal House System</Text>
            
            {houses.map((house: any) => (
              <View key={house.house} style={styles.houseRow}>
                <Text style={styles.houseRowNumber}>House {house.house}</Text>
                <Text style={styles.houseRowSign}>{house.formatted || `${house.sign} ${formatDegreeMinutes(house.degree)}`}</Text>
              </View>
            ))}
          </View>
        ) : (
          <View style={styles.comingSoonCard}>
            <Ionicons name="home-outline" size={20} color={Colors.textTertiary} />
            <Text style={styles.comingSoonText}>House data coming soon</Text>
          </View>
        )}

        {/* Aspects - Coming Soon */}
        <View style={styles.comingSoonCard}>
          <Ionicons name="git-network-outline" size={20} color={Colors.textTertiary} />
          <Text style={styles.comingSoonText}>Aspects analysis coming soon</Text>
        </View>

        {/* System metadata */}
        <View style={styles.systemLabel}>
          <Text style={styles.systemLabelText}>
            Calculated using {getSiderealSystemLabel()}
          </Text>
        </View>
        
        {/* Debug/System metadata - computation version */}
        {chartDetails.computation_version && (
          <View style={styles.systemLabel}>
            <Text style={styles.systemLabelText}>
              Engine: {chartDetails.computation_version}
            </Text>
          </View>
        )}

        {/* Navigation buttons */}
        <View style={styles.modeNavigation}>
          <TouchableOpacity 
            style={styles.modeNavButton}
            onPress={() => navigateToMode('summary')}
          >
            <Ionicons name="book-outline" size={18} color={Colors.text} />
            <Text style={styles.modeNavButtonText}>About This Lens</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.modeNavButton}
            onPress={() => navigateToMode('snapshot')}
          >
            <Ionicons name="sparkles-outline" size={18} color={Colors.text} />
            <Text style={styles.modeNavButtonText}>Full Snapshot</Text>
          </TouchableOpacity>
        </View>
      </>
    );
  };
  
  if (!content) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.centered}>
          <Text style={styles.errorText}>Lens not found</Text>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.headerBackButton}>
            <Ionicons name="arrow-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>{content.name}</Text>
        </View>
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={Colors.textSecondary} />
          <Text style={styles.loadingText}>Loading your chart...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Check if user needs to complete onboarding (no user or no chart)
  const showOnboardingCTA = !user?.id || (error && error.includes('not found'));

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      
      {/* Header with back button */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.headerBackButton}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{content.name}</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* UI Invariant Error Banner - shown when onboarded user can't see personalized content */}
        {invariantViolation && renderInvariantErrorBanner()}

        {/* Fetch Error Banner for onboarded users */}
        {isOnboardedUser && error && !showOnboardingCTA && (
          <View style={styles.invariantErrorBanner}>
            <Ionicons name="warning-outline" size={18} color="#D97706" />
            <Text style={styles.invariantErrorText}>
              We couldn't load your snapshot. Try again.
            </Text>
            <TouchableOpacity 
              style={styles.invariantRetryButton}
              onPress={handleRetry}
            >
              <Ionicons name="refresh" size={16} color="#D97706" />
            </TouchableOpacity>
          </View>
        )}

        {/* Onboarding CTA for users without chart data */}
        {showOnboardingCTA && (
          <View style={styles.onboardingCTA}>
            <Ionicons name="person-add-outline" size={24} color={Colors.textSecondary} />
            <Text style={styles.onboardingCTATitle}>Complete Your Profile</Text>
            <Text style={styles.onboardingCTAText}>
              Add your birth details to see your personalized {content.name} snapshot.
            </Text>
            <TouchableOpacity 
              style={styles.onboardingCTAButton}
              onPress={() => router.push('/onboarding')}
            >
              <Text style={styles.onboardingCTAButtonText}>Get Started</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* MODE: SUMMARY - Short snapshot + explainer */}
        {mode === 'summary' && (
          <>
            {/* Personalized Astrology Snapshot (only for astrology lens with data) */}
            {isAstrologyLens && hasAstrologyData && !showOnboardingCTA && renderAstrologySnapshotCompact()}

            {/* About This Lens Section */}
            <View style={styles.aboutSection}>
              <Text style={styles.aboutSectionTitle}>About This Lens</Text>
            </View>
            
            {/* Summary View */}
            <View style={styles.summaryCard}>
              <Text style={styles.summaryText}>{content.summary}</Text>
            </View>

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>How to use this lens</Text>
              {content.howToUse.map((item: string, index: number) => (
                <View key={index} style={styles.bulletPoint}>
                  <Text style={styles.bullet}>•</Text>
                  <Text style={styles.bulletText}>{item}</Text>
                </View>
              ))}
            </View>

            {/* Navigation buttons for Astrology lens */}
            {isAstrologyLens && hasAstrologyData && !showOnboardingCTA && (
              <View style={styles.modeNavigation}>
                <TouchableOpacity 
                  style={[styles.modeNavButton, styles.modeNavButtonPrimary]}
                  onPress={() => navigateToMode('snapshot')}
                >
                  <Ionicons name="sparkles" size={18} color={Colors.background} />
                  <Text style={styles.modeNavButtonTextPrimary}>Full Snapshot</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  style={styles.modeNavButton}
                  onPress={() => navigateToMode('deep_dive')}
                >
                  <Ionicons name="telescope-outline" size={18} color={Colors.text} />
                  <Text style={styles.modeNavButtonText}>Go Deeper</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Static deep dive button for non-astrology or no data */}
            {(!isAstrologyLens || !hasAstrologyData || showOnboardingCTA) && (
              <TouchableOpacity
                style={styles.deepDiveButton}
                onPress={() => navigateToMode('deep_dive')}
              >
                <Text style={styles.deepDiveButtonText}>Go Deeper</Text>
                <Ionicons name="arrow-forward" size={20} color={Colors.background} />
              </TouchableOpacity>
            )}
          </>
        )}

        {/* MODE: SNAPSHOT - Personalized chart overview */}
        {mode === 'snapshot' && isAstrologyLens && (
          <>
            {hasAstrologyData && !showOnboardingCTA ? (
              renderSnapshotView()
            ) : (
              <>
                <View style={styles.emptyState}>
                  <Ionicons name="telescope-outline" size={32} color={Colors.textTertiary} />
                  <Text style={styles.emptyStateText}>No chart data available</Text>
                  <Text style={styles.emptyStateSubtext}>Complete onboarding to see your snapshot</Text>
                </View>
                <TouchableOpacity 
                  style={styles.modeNavButton}
                  onPress={() => navigateToMode('summary')}
                >
                  <Ionicons name="arrow-back" size={18} color={Colors.text} />
                  <Text style={styles.modeNavButtonText}>Back to Summary</Text>
                </TouchableOpacity>
              </>
            )}
          </>
        )}

        {/* MODE: DEEP_DIVE - Full chart details */}
        {mode === 'deep_dive' && (
          <>
            {isAstrologyLens && hasAstrologyData && !showOnboardingCTA ? (
              renderDeepDiveView()
            ) : (
              <>
                {/* Static deep dive content for non-astrology lenses */}
                <View style={styles.disclaimerCard}>
                  <Ionicons name="information-circle-outline" size={20} color={Colors.textSecondary} />
                  <Text style={styles.disclaimerText}>
                    Descriptive, not deterministic. Not predictive. Offers perspective, not prescription.
                  </Text>
                </View>

                <Text style={styles.intro}>{content.deepDive.intro}</Text>

                {content.deepDive.sections.map((section: any, index: number) => (
                  <View key={index} style={styles.deepSection}>
                    <Text style={styles.deepSectionTitle}>{section.title}</Text>
                    <Text style={styles.deepSectionContent}>{section.content}</Text>
                  </View>
                ))}

                <View style={styles.footerNote}>
                  <Text style={styles.footerNoteText}>
                    Remember: These frameworks work best when held lightly. They're tools for reflection, not rigid definitions.
                  </Text>
                </View>

                <TouchableOpacity 
                  style={[styles.modeNavButton, { marginTop: 24 }]}
                  onPress={() => navigateToMode('summary')}
                >
                  <Ionicons name="arrow-back" size={18} color={Colors.text} />
                  <Text style={styles.modeNavButtonText}>Back to Summary</Text>
                </TouchableOpacity>
              </>
            )}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 15,
    color: Colors.textSecondary,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerBackButton: {
    padding: 8,
    marginRight: 12,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    flex: 1,
  },
  scrollContent: {
    padding: 24,
    paddingBottom: 60,
  },
  // Onboarding CTA styles
  onboardingCTA: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    marginBottom: 24,
    alignItems: 'center',
  },
  onboardingCTATitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginTop: 12,
    marginBottom: 8,
  },
  onboardingCTAText: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 16,
  },
  onboardingCTAButton: {
    backgroundColor: Colors.text,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  onboardingCTAButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.background,
  },
  // Personalized Snapshot styles
  snapshotCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  snapshotHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 10,
  },
  snapshotTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
  },
  snapshotGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  snapshotItem: {
    flex: 1,
    alignItems: 'center',
  },
  snapshotLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 6,
  },
  snapshotValue: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.text,
    textAlign: 'center',
  },
  // Row-based snapshot layout
  snapshotRows: {
    gap: 12,
    marginBottom: 16,
  },
  snapshotRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  snapshotRowIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  snapshotRowLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.textSecondary,
    width: 80,
  },
  snapshotRowValue: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
    textAlign: 'right',
  },
  // Snapshot navigation buttons
  snapshotButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 16,
  },
  snapshotButtonPrimary: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.text,
    borderRadius: 10,
    paddingVertical: 12,
  },
  snapshotButtonPrimaryText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.background,
  },
  snapshotButtonSecondary: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'transparent',
    borderRadius: 10,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  snapshotButtonSecondaryText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  systemLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  systemLabelText: {
    fontSize: 12,
    color: Colors.textTertiary,
  },
  // About section
  aboutSection: {
    marginBottom: 8,
  },
  aboutSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  summaryCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    marginBottom: 24,
  },
  summaryText: {
    fontSize: 16,
    lineHeight: 24,
    color: Colors.text,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 16,
  },
  bulletPoint: {
    flexDirection: 'row',
    marginBottom: 12,
    paddingLeft: 8,
  },
  bullet: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginRight: 12,
    marginTop: 2,
  },
  bulletText: {
    flex: 1,
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
  },
  deepDiveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.text,
    borderRadius: 12,
    padding: 16,
    gap: 8,
  },
  deepDiveButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.background,
  },
  disclaimerCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    gap: 12,
  },
  disclaimerText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 20,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  intro: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.textSecondary,
    marginBottom: 32,
  },
  deepSection: {
    marginBottom: 32,
  },
  deepSectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 12,
  },
  deepSectionContent: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.textSecondary,
  },
  footerNote: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 20,
    marginTop: 16,
  },
  footerNoteText: {
    fontSize: 14,
    lineHeight: 22,
    color: Colors.textTertiary,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  errorText: {
    fontSize: 16,
    color: Colors.error,
    marginBottom: 24,
  },
  backButton: {
    backgroundColor: Colors.surface,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  backButtonText: {
    fontSize: 16,
    color: Colors.text,
  },
  // Mode Navigation styles
  modeNavigation: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  modeNavButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 14,
    gap: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  modeNavButtonPrimary: {
    backgroundColor: Colors.text,
    borderColor: Colors.text,
  },
  modeNavButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  modeNavButtonTextPrimary: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.background,
  },
  // Snapshot view styles
  placementsList: {
    gap: 16,
  },
  placementRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  placementIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placementInfo: {
    flex: 1,
  },
  placementLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  placementValue: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.text,
  },
  placementHouse: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  // Houses card styles
  housesCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginBottom: 16,
  },
  housesGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  houseItem: {
    alignItems: 'center',
    width: '16%',
  },
  houseNumber: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    marginBottom: 2,
  },
  houseSign: {
    fontSize: 12,
    color: Colors.text,
  },
  // Deep dive styles
  deepDiveSection: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  deepDiveSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 16,
  },
  deepDiveSectionSubtitle: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginTop: -12,
    marginBottom: 16,
  },
  planetRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  planetName: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.text,
  },
  planetDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  planetSign: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  planetDegree: {
    fontSize: 13,
    color: Colors.textTertiary,
    minWidth: 30,
  },
  planetHouse: {
    fontSize: 12,
    color: Colors.textTertiary,
    backgroundColor: Colors.background,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  houseRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  houseRowNumber: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.text,
  },
  houseRowSign: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  // Coming soon & empty state styles
  comingSoonCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    gap: 12,
  },
  comingSoonText: {
    fontSize: 14,
    color: Colors.textTertiary,
    fontStyle: 'italic',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
    gap: 12,
  },
  emptyStateText: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: Colors.textTertiary,
  },
  // UI Invariant Error Banner styles
  invariantErrorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    gap: 10,
    borderWidth: 1,
    borderColor: '#FCD34D',
  },
  invariantErrorText: {
    flex: 1,
    fontSize: 14,
    color: '#92400E',
    fontWeight: '500',
  },
  invariantRetryButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: '#FDE68A',
  },
});
