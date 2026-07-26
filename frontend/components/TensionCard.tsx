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

interface LifeAreaContext {
  label: string;
  source: string;  // astrology_house, bazi_domain, pattern_memory, cluster_default
  house?: number;
  confidence: number;
}

// V3.2: Split WHY drivers
interface WhyDriver {
  source: string;
  text: string;
}

interface TensionData {
  success: boolean;
  mode: 'converged' | 'repeating' | 'low_signal';
  trigger_confidence?: 'recurring_only' | 'recurring_plus_trigger' | 'strongly_active_now';
  // V3.3: New clarity fields
  moment: string;
  cause_line?: string;        // Why now, human language
  where?: string;             // Life area
  about?: string;             // Explicit object (mandatory)
  contradiction?: string;
  current_cost?: string;
  supporting_line: string;
  why_now_plain?: string;     // Visible why now
  pattern_reason?: string;    // Behavioral tendency
  why_now_technical?: string; // Hidden astrology
  tension_label_dynamic?: string;  // Situation-specific label
  tension_label: string;      // Generic label for compat
  energy_title: string;
  avoided_move?: string;
  micro_shift: string;
  // V3.1 Life Area Context (backward compat)
  life_area_context?: LifeAreaContext | null;
  object_of_tension?: string;  // Alias for 'about'
  // V3.2: Split WHY layers
  why_recurring?: WhyDriver[];
  why_now?: WhyDriver[];
  // Legacy drivers (backward compat)
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

      {/* V3.3: Real-world moment */}
      <Text style={[styles.moment, { color: theme.text }]}>
        {tension.moment}
      </Text>

      {/* V3.3: Cause line (why now, human language) */}
      {tension.cause_line && (
        <Text style={[styles.causeLine, { color: theme.textSecondary }]}>
          {tension.cause_line}
        </Text>
      )}

      {/* V3.3: Where (life area) */}
      {(tension.where || tension.life_area_context?.label) && (
        <View style={styles.lifeAreaRow}>
          <Text style={[styles.lifeAreaLabel, { color: theme.textTertiary }]}>
            Where:
          </Text>
          <Text style={[styles.lifeAreaText, { color: theme.textSecondary }]}>
            {tension.where || tension.life_area_context?.label}
          </Text>
        </View>
      )}

      {/* V3.3: About (explicit object - mandatory) */}
      {(tension.about || tension.object_of_tension) && (
        <View style={[styles.sceneObjectRow, { borderColor: theme.border }]}>
          <Text style={[styles.sceneObjectLabel, { color: theme.textTertiary }]}>
            About:
          </Text>
          <Text style={[styles.sceneObjectText, { color: theme.textSecondary }]}>
            {tension.about || tension.object_of_tension}
          </Text>
        </View>
      )}

      {/* V3.3: Tight contradiction */}
      {tension.contradiction && (
        <Text style={[styles.contradictionText, { color: theme.text }]}>
          {tension.contradiction}
        </Text>
      )}

      {/* V3.3: Current cost */}
      {tension.current_cost && (
        <View style={[styles.costRow, { backgroundColor: intensityColor + '12' }]}>
          <Ionicons name="warning-outline" size={14} color={intensityColor} />
          <Text style={[styles.costText, { color: theme.textSecondary }]}>
            {tension.current_cost}
          </Text>
        </View>
      )}

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
          size={20} 
          color={theme.textSecondary} 
        />
      </TouchableOpacity>

      {/* Expanded Section: What's Driving This */}
      {expanded && (
        <View style={[styles.expandedSection, { backgroundColor: theme.cardBackground || theme.background, borderColor: theme.border }]}>
          
          {/* V3.3: Section A - WHAT'S HAPPENING NOW (plain language) */}
          {tension.why_now_plain && (
            <>
              <Text style={[styles.expandedHeader, { color: intensityColor }]}>
                WHAT'S HAPPENING NOW
              </Text>
              <Text style={[styles.whyNowPlainText, { color: theme.text }]}>
                {tension.why_now_plain}
              </Text>
            </>
          )}

          {/* V3.3: Section B - WHAT'S DRIVING IT (pattern/tendency) */}
          {tension.pattern_reason && (
            <>
              <Text style={[styles.expandedHeader, { color: theme.textTertiary, marginTop: 16 }]}>
                THE PATTERN
              </Text>
              <Text style={[styles.patternReasonText, { color: theme.textSecondary }]}>
                {tension.pattern_reason}
              </Text>
            </>
          )}

          {/* V3.3: Dynamic Tension Label (situation-specific) */}
          <View style={[styles.tensionLabelBox, { borderColor: intensityColor + '30', marginTop: 16 }]}>
            <Text style={[styles.tensionLabelHeader, { color: theme.textTertiary }]}>
              THE TENSION
            </Text>
            <Text style={[styles.tensionLabel, { color: theme.text }]}>
              {tension.tension_label_dynamic || tension.tension_label}
            </Text>
          </View>

          {/* Driver Synthesis */}
          <View style={[styles.synthesisBox, { borderLeftColor: intensityColor }]}>
            <Text style={[styles.synthesisText, { color: theme.text }]}>
              {tension.driver_synthesis}
            </Text>
          </View>

          {/* V3.3: Section C - TECHNICAL (optional, astrology hidden layer) */}
          {tension.why_now_technical && (
            <View style={[styles.technicalBox, { borderColor: theme.border }]}>
              <Text style={[styles.technicalHeader, { color: theme.textTertiary }]}>
                TECHNICAL
              </Text>
              <Text style={[styles.technicalText, { color: theme.textTertiary }]}>
                {tension.why_now_technical}
              </Text>
            </View>
          )}

          {/* Avoided Move */}
          {tension.avoided_move && (
            <View style={[styles.avoidedMoveBox, { backgroundColor: theme.cardBackground || theme.background }]}>
              <Text style={[styles.avoidedMoveLabel, { color: theme.textTertiary }]}>
                THE AVOIDED MOVE
              </Text>
              <Text style={[styles.avoidedMoveText, { color: theme.text }]}>
                {tension.avoided_move}
              </Text>
            </View>
          )}

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
    fontSize: 16,
    fontStyle: 'italic',
  },
  
  errorText: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 14,
  },
  retryText: {
    fontSize: 16,
    fontWeight: '500',
    textAlign: 'center',
  },

  // Energy Title
  energyTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  intensityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  energyTitle: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },

  // Moment
  moment: {
    fontSize: 24,
    fontWeight: '500',
    lineHeight: 32,
    marginBottom: 14,
  },

  // V3.3: Cause line (why now)
  causeLine: {
    fontSize: 16,
    lineHeight: 32,
    marginBottom: 16,
    fontStyle: 'italic',
  },

  // V3.1 Life Area Context
  lifeAreaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 6,
  },
  lifeAreaLabel: {
    fontSize: 16,
    fontWeight: '500',
  },
  lifeAreaText: {
    fontSize: 16,
    fontStyle: 'italic',
  },

  // Supporting Line
  supportingLine: {
    fontSize: 16,
    fontStyle: 'italic',
    marginBottom: 16,
  },

  // V3 Scene Engine: Object of Tension
  sceneObjectRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    backgroundColor: 'rgba(255,255,255,0.03)',
  },
  sceneObjectLabel: {
    fontSize: 14,
    fontWeight: '500',
    marginRight: 6,
  },
  sceneObjectText: {
    flex: 1,
    fontSize: 16,
    fontStyle: 'italic',
  },

  // V3 Scene Engine: Contradiction
  contradictionText: {
    fontSize: 17,
    lineHeight: 30,
    marginBottom: 16,
    fontWeight: '500',
  },

  // V3 Scene Engine: Current Cost
  costRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  costText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 31,
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
    fontSize: 16,
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
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.8,
    marginBottom: 16,
  },

  // V3.3: Why now plain text
  whyNowPlainText: {
    fontSize: 17,
    fontWeight: '500',
    lineHeight: 30,
    marginBottom: 16,
  },

  // V3.3: Pattern reason text
  patternReasonText: {
    fontSize: 16,
    lineHeight: 32,
    fontStyle: 'italic',
    marginBottom: 16,
  },

  // V3.3: Technical section (hidden layer)
  technicalBox: {
    marginTop: 16,
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    opacity: 0.7,
  },
  technicalHeader: {
    fontSize: 9,
    fontWeight: '500',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  technicalText: {
    fontSize: 14,
    lineHeight: 30,
    fontStyle: 'italic',
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
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
    marginBottom: 2,
  },
  driverText: {
    fontSize: 16,
    lineHeight: 31,
  },

  // Tension Label
  tensionLabelBox: {
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 16,
    alignItems: 'center',
  },
  tensionLabelHeader: {
    fontSize: 9,
    fontWeight: '500',
    letterSpacing: 0.6,
    marginBottom: 4,
  },
  tensionLabel: {
    fontSize: 16,
    fontWeight: '500',
  },

  // Synthesis
  synthesisBox: {
    paddingLeft: 12,
    borderLeftWidth: 3,
    marginBottom: 16,
  },
  synthesisText: {
    fontSize: 17,
    fontWeight: '500',
    lineHeight: 30,
    fontStyle: 'italic',
  },

  // V3 Scene Engine: Avoided Move
  avoidedMoveBox: {
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 8,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
    borderStyle: 'dashed',
  },
  avoidedMoveLabel: {
    fontSize: 9,
    fontWeight: '500',
    letterSpacing: 0.6,
    marginBottom: 4,
  },
  avoidedMoveText: {
    fontSize: 16,
    fontWeight: '500',
    lineHeight: 32,
  },

  // Micro-Shift
  microShiftBox: {
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.1)',
  },
  microShiftLabel: {
    fontSize: 9,
    fontWeight: '500',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  microShiftText: {
    fontSize: 16,
    lineHeight: 32,
  },
});

export default TensionCard;
