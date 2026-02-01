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
  const { user } = useAppStore();
  
  // State for chart details
  const [chartDetails, setChartDetails] = useState<ChartDetails | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const content = LENS_CONTENT[lens as string];
  
  // Fetch chart details on mount
  useEffect(() => {
    const fetchChartDetails = async () => {
      if (!user?.id) return;
      
      setIsLoading(true);
      setError(null);
      
      try {
        const details = await getChartDetails(user.id);
        setChartDetails(details);
      } catch (err: any) {
        console.error('Failed to fetch chart details:', err);
        setError(err?.response?.data?.detail || 'Failed to load your chart data');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchChartDetails();
  }, [user?.id]);
  
  // Helper to format planet position for display
  const formatPlanetPosition = (planet: any): string => {
    if (!planet) return 'Not available';
    const sign = planet.sign || 'Unknown';
    const degree = planet.longitude_in_sign != null 
      ? `${Math.floor(planet.longitude_in_sign)}°` 
      : (planet.degree != null ? `${Math.floor(planet.degree)}°` : '');
    return degree ? `${sign} ${degree}` : sign;
  };
  
  // Get sidereal system label from chart details
  const getSiderealSystemLabel = (): string => {
    const settings = chartDetails?.astrology?.sidereal_settings;
    if (!settings) return 'True Sidereal';
    
    if (settings.ayanamsa_name) {
      return settings.ayanamsa_name;
    }
    if (settings.svp_degrees != null) {
      return `True Sidereal (SVP ${settings.svp_degrees}°)`;
    }
    return 'True Sidereal';
  };

  // Navigate to different modes
  const navigateToMode = (targetMode: string) => {
    router.push(`/lenses/${lens}?mode=${targetMode}` as any);
  };
  
  // Render personalized Astrology snapshot (compact version for summary)
  const renderAstrologySnapshotCompact = () => {
    if (!chartDetails?.astrology) return null;
    
    const { sun, moon, rising } = chartDetails.astrology;
    
    return (
      <View style={styles.snapshotCard}>
        <View style={styles.snapshotHeader}>
          <Ionicons name="sparkles" size={20} color={Colors.text} />
          <Text style={styles.snapshotTitle}>Your Sidereal Snapshot</Text>
        </View>
        
        <View style={styles.snapshotGrid}>
          <View style={styles.snapshotItem}>
            <Text style={styles.snapshotLabel}>Sun</Text>
            <Text style={styles.snapshotValue}>{formatPlanetPosition(sun)}</Text>
          </View>
          
          <View style={styles.snapshotItem}>
            <Text style={styles.snapshotLabel}>Moon</Text>
            <Text style={styles.snapshotValue}>{formatPlanetPosition(moon)}</Text>
          </View>
          
          <View style={styles.snapshotItem}>
            <Text style={styles.snapshotLabel}>Ascendant</Text>
            <Text style={styles.snapshotValue}>{formatPlanetPosition(rising)}</Text>
          </View>
        </View>
        
        <View style={styles.systemLabel}>
          <Ionicons name="information-circle-outline" size={14} color={Colors.textTertiary} />
          <Text style={styles.systemLabelText}>
            Calculated using {getSiderealSystemLabel()}
          </Text>
        </View>
      </View>
    );
  };

  // Render full snapshot view (Sun/Moon/Asc + houses summary)
  const renderSnapshotView = () => {
    if (!chartDetails?.astrology) {
      return (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateText}>Chart data not available</Text>
        </View>
      );
    }
    
    const { sun, moon, rising, houses } = chartDetails.astrology;
    const hasHouses = houses && houses.length > 0;
    
    return (
      <>
        {/* Main Placements */}
        <View style={styles.snapshotCard}>
          <View style={styles.snapshotHeader}>
            <Ionicons name="sparkles" size={20} color={Colors.text} />
            <Text style={styles.snapshotTitle}>Your Core Placements</Text>
          </View>
          
          <View style={styles.placementsList}>
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
            
            <View style={styles.placementRow}>
              <View style={styles.placementIcon}>
                <Ionicons name="arrow-up-circle" size={20} color={Colors.text} />
              </View>
              <View style={styles.placementInfo}>
                <Text style={styles.placementLabel}>Ascendant (Rising)</Text>
                <Text style={styles.placementValue}>{formatPlanetPosition(rising)}</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Houses Summary */}
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
                    <Text style={styles.planetDegree}>{Math.floor(planet.degree)}°</Text>
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
            <Ionicons name="time-outline" size={20} color={Colors.textTertiary} />
            <Text style={styles.comingSoonText}>Planets data coming soon</Text>
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
                <Text style={styles.houseRowSign}>{house.formatted || `${house.sign} ${Math.floor(house.degree)}°`}</Text>
              </View>
            ))}
          </View>
        ) : (
          <View style={styles.comingSoonCard}>
            <Ionicons name="time-outline" size={20} color={Colors.textTertiary} />
            <Text style={styles.comingSoonText}>Houses data coming soon</Text>
          </View>
        )}

        {/* Aspects - Coming Soon */}
        <View style={styles.comingSoonCard}>
          <Ionicons name="git-network-outline" size={20} color={Colors.textTertiary} />
          <Text style={styles.comingSoonText}>Aspects analysis coming soon</Text>
        </View>

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
            style={styles.modeNavButton}
            onPress={() => navigateToMode('snapshot')}
          >
            <Ionicons name="sparkles-outline" size={18} color={Colors.text} />
            <Text style={styles.modeNavButtonText}>Snapshot</Text>
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
  const isAstrologyLens = lens === 'astrology';
  const hasAstrologyData = chartDetails?.astrology?.sun || chartDetails?.astrology?.moon;

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
                  <Text style={styles.modeNavButtonTextPrimary}>View Summary</Text>
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
});
