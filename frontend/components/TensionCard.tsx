/**
 * TensionCard V1.0 - Real-Time Tension Engine UI
 * 
 * Mirror is NOT a lens aggregator.
 * Mirror is a REAL-TIME TENSION ENGINE.
 * 
 * This component displays ONE dominant tension with:
 * - Energy title (short, punchy)
 * - Moment statement (sharp, second-person)
 * - Supporting line
 * - CTA: "See what's driving this →"
 * - Expandable "What's Driving This" section
 * 
 * LANGUAGE RULES:
 * - Second person ("you")
 * - No soft language
 * - Sharp, direct, immediate
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Animated,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface TensionDriver {
  source: string;
  text: string;
}

interface TensionData {
  success: boolean;
  mode: 'converged' | 'repeating' | 'low_signal';  // V2: Confidence mode
  tension_label: string;
  energy_title: string;
  moment: string;
  supporting_line: string;
  micro_shift: string;
  drivers: TensionDriver[];
  driver_synthesis: string;
  confidence: number;
  intensity: number;
  fallback_used: boolean;
  debug?: {
    cluster: string;
    dominance_score: number;
    signal_count: number;
    strong_signal_count: number;
    mode_reason: string;
    signals_used: string[];
  };
}

interface TensionCardProps {
  userId: string;
  theme: {
    background: string;
    surface: string;
    surfaceLight?: string;
    text: string;
    textSecondary: string;
    textTertiary: string;
    accent: string;
    border: string;
    cardBackground?: string;
    textInverse?: string;
  };
  onExpand?: () => void;
}

// Source labels for display
const SOURCE_LABELS: Record<string, string> = {
  pattern_memory: 'Pattern Memory',
  astrology: 'Transits',
  human_design: 'Human Design',
  bazi: 'BaZi',
  enneagram: 'Enneagram',
};

// Source icons
const SOURCE_ICONS: Record<string, string> = {
  pattern_memory: 'repeat',
  astrology: 'planet',
  human_design: 'git-network',
  bazi: 'grid',
  enneagram: 'triangle',
};

const TensionCard: React.FC<TensionCardProps> = ({
  userId,
  theme,
  onExpand,
}) => {
  const [tension, setTension] = useState<TensionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  
  // Animation for expansion
  const [expandAnim] = useState(new Animated.Value(0));

  useEffect(() => {
    loadTension();
  }, [userId]);

  const loadTension = async () => {
    if (!userId) {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get(`/home-tension/${userId}`);
      
      if (response.data?.success) {
        setTension(response.data);
      } else {
        setError(response.data?.error || 'Failed to load tension');
      }
    } catch (err: any) {
      console.error('[TensionCard] Error:', err);
      setError(err.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  const toggleExpanded = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpanded(!expanded);
    onExpand?.();
    
    Animated.spring(expandAnim, {
      toValue: expanded ? 0 : 1,
      useNativeDriver: true,
      tension: 50,
      friction: 9,
    }).start();
  };

  // Intensity indicator color
  const getIntensityColor = (intensity: number) => {
    if (intensity > 0.7) return '#E53935'; // High - red
    if (intensity > 0.4) return '#FF9800'; // Medium - orange
    return theme.accent; // Low - accent
  };

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Reading the moment...
          </Text>
        </View>
      </View>
    );
  }

  if (error || !tension) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error || 'Unable to read tension'}
        </Text>
        <TouchableOpacity onPress={loadTension}>
          <Text style={[styles.retryText, { color: theme.accent }]}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const intensityColor = getIntensityColor(tension.intensity);

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: intensityColor + '40' }]}>
      
      {/* Energy Title */}
      <View style={styles.energyTitleRow}>
        <View style={[styles.intensityDot, { backgroundColor: intensityColor }]} />
        <Text style={[styles.energyTitle, { color: intensityColor }]}>
          {tension.energy_title}
        </Text>
      </View>

      {/* The Moment - Sharp, direct */}
      <Text style={[styles.moment, { color: theme.text }]}>
        {tension.moment}
      </Text>

      {/* Supporting Line */}
      <Text style={[styles.supportingLine, { color: theme.textTertiary }]}>
        {tension.supporting_line}
      </Text>

      {/* CTA Button */}
      <TouchableOpacity
        style={[styles.ctaButton, { backgroundColor: theme.cardBackground || theme.background, borderColor: theme.border }]}
        onPress={toggleExpanded}
        activeOpacity={0.7}
      >
        <Text style={[styles.ctaText, { color: theme.text }]}>
          {expanded ? 'Close' : "See what's driving this"}
        </Text>
        <Ionicons 
          name={expanded ? "chevron-up" : "chevron-forward"} 
          size={16} 
          color={theme.textSecondary} 
        />
      </TouchableOpacity>

      {/* Expanded Section: What's Driving This */}
      {expanded && (
        <View style={[styles.expandedSection, { backgroundColor: theme.cardBackground || theme.background, borderColor: theme.border }]}>
          
          {/* Section Header */}
          <Text style={[styles.expandedHeader, { color: theme.textTertiary }]}>
            WHAT'S DRIVING THIS
          </Text>

          {/* Drivers List */}
          <View style={styles.driversList}>
            {tension.drivers.map((driver, index) => (
              <View key={index} style={styles.driverRow}>
                <View style={styles.driverBullet}>
                  <Ionicons 
                    name={(SOURCE_ICONS[driver.source] || 'ellipse') as any} 
                    size={12} 
                    color={theme.textTertiary} 
                  />
                </View>
                <View style={styles.driverContent}>
                  <Text style={[styles.driverSource, { color: theme.textTertiary }]}>
                    {SOURCE_LABELS[driver.source] || driver.source}
                  </Text>
                  <Text style={[styles.driverText, { color: theme.textSecondary }]}>
                    {driver.text}
                  </Text>
                </View>
              </View>
            ))}
          </View>

          {/* Tension Label */}
          <View style={[styles.tensionLabelBox, { borderColor: intensityColor + '30' }]}>
            <Text style={[styles.tensionLabelHeader, { color: theme.textTertiary }]}>
              THE TENSION
            </Text>
            <Text style={[styles.tensionLabel, { color: theme.text }]}>
              {tension.tension_label}
            </Text>
          </View>

          {/* Driver Synthesis */}
          <View style={[styles.synthesisBox, { borderLeftColor: intensityColor }]}>
            <Text style={[styles.synthesisText, { color: theme.text }]}>
              {tension.driver_synthesis}
            </Text>
          </View>

          {/* Micro-Shift */}
          {tension.micro_shift && (
            <View style={styles.microShiftBox}>
              <Text style={[styles.microShiftLabel, { color: theme.textTertiary }]}>
                ONE SHIFT
              </Text>
              <Text style={[styles.microShiftText, { color: theme.textSecondary }]}>
                {tension.micro_shift}
              </Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    borderWidth: 1.5,
    padding: 20,
    marginBottom: 16,
  },
  
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    gap: 10,
  },
  loadingText: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  
  errorText: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 8,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },

  // Energy Title
  energyTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 8,
  },
  intensityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  energyTitle: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },

  // Moment
  moment: {
    fontSize: 20,
    fontWeight: '600',
    lineHeight: 28,
    marginBottom: 8,
  },

  // Supporting Line
  supportingLine: {
    fontSize: 14,
    fontStyle: 'italic',
    marginBottom: 16,
  },

  // CTA Button
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    gap: 6,
  },
  ctaText: {
    fontSize: 14,
    fontWeight: '500',
  },

  // Expanded Section
  expandedSection: {
    marginTop: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  expandedHeader: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 12,
  },

  // Drivers
  driversList: {
    gap: 10,
    marginBottom: 16,
  },
  driverRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  driverBullet: {
    width: 20,
    alignItems: 'center',
    paddingTop: 2,
  },
  driverContent: {
    flex: 1,
  },
  driverSource: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
    marginBottom: 2,
  },
  driverText: {
    fontSize: 13,
    lineHeight: 18,
  },

  // Tension Label
  tensionLabelBox: {
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 12,
    alignItems: 'center',
  },
  tensionLabelHeader: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 4,
  },
  tensionLabel: {
    fontSize: 16,
    fontWeight: '600',
  },

  // Synthesis
  synthesisBox: {
    paddingLeft: 12,
    borderLeftWidth: 3,
    marginBottom: 12,
  },
  synthesisText: {
    fontSize: 15,
    fontWeight: '500',
    lineHeight: 22,
    fontStyle: 'italic',
  },

  // Micro-Shift
  microShiftBox: {
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.1)',
  },
  microShiftLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  microShiftText: {
    fontSize: 14,
    lineHeight: 20,
  },
});

export default TensionCard;
