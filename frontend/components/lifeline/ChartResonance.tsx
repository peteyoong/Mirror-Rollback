/**
 * ResonanceMarker & ResonanceModal
 * 
 * Components for displaying chart-timeline resonance on lifeline events.
 * Shows a subtle ✧ symbol when an event aligns with a significant chart signal.
 * 
 * IMPORTANT: Mirror does NOT claim prediction.
 * All language is observational, highlighting resonance/alignment, not causation.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';

// =============================================================================
// TYPES
// =============================================================================

export interface ChartResonance {
  event_id: string;
  event_year: number;
  event_title: string;
  signal_type: string;
  signal_year: number;
  signal_name: string;
  system: 'astrology' | 'bazi' | 'human_design';
  description: string;
  reflection: string;
  age_at_event: number;
  match_quality: 'exact' | 'near';
  display_title: string;
  display_timing: string;
  display_reflection: string;
  display_footer: string;
}

interface ResonanceMarkerProps {
  resonances: ChartResonance[];
  onPress?: () => void;
  size?: 'small' | 'medium';
}

interface ResonanceModalProps {
  resonance: ChartResonance | null;
  visible: boolean;
  onClose: () => void;
}

interface ResonanceInlineProps {
  resonances: ChartResonance[];
}

// =============================================================================
// SYSTEM ICONS & COLORS
// =============================================================================

const SYSTEM_CONFIG = {
  astrology: {
    icon: '✧',
    color: '#9B8AC4', // Soft purple
    label: 'Astrology',
  },
  bazi: {
    icon: '✧',
    color: '#C4A98B', // Warm gold
    label: 'BaZi',
  },
  human_design: {
    icon: '✧',
    color: '#8AC4B4', // Soft teal
    label: 'Human Design',
  },
};

// =============================================================================
// RESONANCE MARKER (Timeline Icon)
// =============================================================================

export function ResonanceMarker({ resonances, onPress, size = 'small' }: ResonanceMarkerProps) {
  const { theme } = useTheme();
  
  if (!resonances || resonances.length === 0) return null;
  
  // Get the primary system for coloring
  const primarySystem = resonances[0]?.system || 'astrology';
  const config = SYSTEM_CONFIG[primarySystem] || SYSTEM_CONFIG.astrology;
  
  const isSmall = size === 'small';
  
  return (
    <TouchableOpacity
      style={[
        styles.marker,
        isSmall ? styles.markerSmall : styles.markerMedium,
        { backgroundColor: `${config.color}20` }
      ]}
      onPress={onPress}
      activeOpacity={0.7}
      hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
    >
      <Text style={[
        styles.markerIcon,
        isSmall ? styles.markerIconSmall : styles.markerIconMedium,
        { color: config.color }
      ]}>
        {config.icon}
      </Text>
    </TouchableOpacity>
  );
}

// =============================================================================
// RESONANCE MODAL (Detail View)
// =============================================================================

export function ResonanceModal({ resonance, visible, onClose }: ResonanceModalProps) {
  const { theme } = useTheme();
  
  if (!resonance) return null;
  
  const config = SYSTEM_CONFIG[resonance.system] || SYSTEM_CONFIG.astrology;
  
  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={[styles.modalContainer, { backgroundColor: theme.background }]}>
        {/* Header */}
        <View style={[styles.modalHeader, { borderBottomColor: theme.border }]}>
          <View style={styles.modalHeaderLeft}>
            <Text style={[styles.modalIcon, { color: config.color }]}>{config.icon}</Text>
            <View>
              <Text style={[styles.modalTitle, { color: theme.text }]}>
                {resonance.display_title}
              </Text>
              <Text style={[styles.modalSubtitle, { color: theme.textSecondary }]}>
                {config.label} • {resonance.event_year}
              </Text>
            </View>
          </View>
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <Ionicons name="close" size={24} color={theme.textSecondary} />
          </TouchableOpacity>
        </View>
        
        {/* Content */}
        <ScrollView 
          style={styles.modalContent}
          contentContainerStyle={styles.modalContentContainer}
        >
          {/* Signal Info */}
          <View style={[styles.signalCard, { backgroundColor: theme.surface }]}>
            <Text style={[styles.signalName, { color: theme.text }]}>
              {resonance.signal_name}
            </Text>
            <Text style={[styles.signalTiming, { color: theme.textSecondary }]}>
              {resonance.display_timing}
            </Text>
          </View>
          
          {/* Reflection */}
          <View style={[styles.reflectionCard, { backgroundColor: `${config.color}10`, borderColor: `${config.color}30` }]}>
            <Text style={[styles.reflectionText, { color: theme.textSecondary }]}>
              {resonance.display_reflection}
            </Text>
          </View>
          
          {/* Event Connection */}
          <View style={styles.eventSection}>
            <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
              YOUR TIMELINE
            </Text>
            <View style={[styles.eventCard, { backgroundColor: theme.surface, borderLeftColor: config.color }]}>
              <Text style={[styles.eventYear, { color: theme.textSecondary }]}>
                {resonance.event_year}
              </Text>
              <Text style={[styles.eventTitle, { color: theme.text }]}>
                {resonance.event_title}
              </Text>
            </View>
          </View>
          
          {/* Footer */}
          <View style={styles.footerSection}>
            <Text style={[styles.footerText, { color: theme.textTertiary }]}>
              {resonance.display_footer}
            </Text>
          </View>
          
          {/* Disclaimer */}
          <View style={styles.disclaimerSection}>
            <Text style={[styles.disclaimerText, { color: theme.textTertiary }]}>
              This is a timing coincidence, not a prediction. These signals describe patterns, not outcomes.
            </Text>
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

// =============================================================================
// RESONANCE INLINE (For Event Cards)
// =============================================================================

export function ResonanceInline({ resonances }: ResonanceInlineProps) {
  const { theme } = useTheme();
  const [showModal, setShowModal] = useState(false);
  const [selectedResonance, setSelectedResonance] = useState<ChartResonance | null>(null);
  
  if (!resonances || resonances.length === 0) return null;
  
  const handlePress = () => {
    setSelectedResonance(resonances[0]);
    setShowModal(true);
  };
  
  const config = SYSTEM_CONFIG[resonances[0]?.system] || SYSTEM_CONFIG.astrology;
  
  return (
    <>
      <TouchableOpacity
        style={[styles.inlineContainer, { backgroundColor: `${config.color}12` }]}
        onPress={handlePress}
        activeOpacity={0.7}
      >
        <Text style={[styles.inlineIcon, { color: config.color }]}>✧</Text>
        <Text style={[styles.inlineText, { color: config.color }]}>
          Resonance
        </Text>
      </TouchableOpacity>
      
      <ResonanceModal
        resonance={selectedResonance}
        visible={showModal}
        onClose={() => setShowModal(false)}
      />
    </>
  );
}

// =============================================================================
// PATTERN LENS SECTION
// =============================================================================

export interface PatternResonanceSummary {
  year: number;
  event_title: string;
  signal_name: string;
  system: string;
  summary: string;
}

interface ChartResonanceSectionProps {
  resonances: PatternResonanceSummary[];
}

export function ChartResonanceSection({ resonances }: ChartResonanceSectionProps) {
  const { theme } = useTheme();
  
  if (!resonances || resonances.length === 0) return null;
  
  return (
    <View style={styles.patternSection}>
      <Text style={[styles.patternSectionHeader, { color: theme.text }]}>
        CHART RESONANCE
      </Text>
      
      {resonances.map((r, index) => {
        const config = SYSTEM_CONFIG[r.system as keyof typeof SYSTEM_CONFIG] || SYSTEM_CONFIG.astrology;
        
        return (
          <View 
            key={`${r.year}-${index}`}
            style={[styles.patternItem, { borderLeftColor: config.color }]}
          >
            <View style={styles.patternItemHeader}>
              <Text style={[styles.patternItemYear, { color: theme.text }]}>
                {r.year}
              </Text>
              <Text style={[styles.patternItemIcon, { color: config.color }]}>✧</Text>
            </View>
            <Text style={[styles.patternItemTitle, { color: theme.textSecondary }]}>
              {r.event_title}
            </Text>
            <Text style={[styles.patternItemSummary, { color: theme.textTertiary }]}>
              {r.summary}
            </Text>
          </View>
        );
      })}
      
      <Text style={[styles.patternDisclaimer, { color: theme.textTertiary }]}>
        These are timing alignments, not predictions.
      </Text>
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  // Marker styles
  marker: {
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
  },
  markerSmall: {
    width: 20,
    height: 20,
    borderRadius: 10,
  },
  markerMedium: {
    width: 26,
    height: 26,
    borderRadius: 13,
  },
  markerIcon: {
    fontWeight: '600',
  },
  markerIconSmall: {
    fontSize: 12,
  },
  markerIconMedium: {
    fontSize: 16,
  },
  
  // Modal styles
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  modalHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  modalIcon: {
    fontSize: 28,
    marginRight: 14,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  modalSubtitle: {
    fontSize: 14,
    marginTop: 2,
  },
  closeButton: {
    padding: 4,
  },
  modalContent: {
    flex: 1,
  },
  modalContentContainer: {
    padding: 20,
  },
  
  // Signal card
  signalCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  signalName: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 6,
  },
  signalTiming: {
    fontSize: 14,
    lineHeight: 20,
  },
  
  // Reflection card
  reflectionCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 24,
  },
  reflectionText: {
    fontSize: 15,
    lineHeight: 22,
    fontStyle: 'italic',
  },
  
  // Event section
  eventSection: {
    marginBottom: 24,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  eventCard: {
    borderLeftWidth: 3,
    paddingLeft: 14,
    paddingVertical: 12,
    paddingRight: 12,
    borderRadius: 8,
  },
  eventYear: {
    fontSize: 13,
    marginBottom: 4,
  },
  eventTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  
  // Footer
  footerSection: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  
  // Disclaimer
  disclaimerSection: {
    paddingTop: 24,
    paddingBottom: 8,
  },
  disclaimerText: {
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
  
  // Inline styles
  inlineContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  inlineIcon: {
    fontSize: 12,
    marginRight: 4,
  },
  inlineText: {
    fontSize: 11,
    fontWeight: '500',
  },
  
  // Pattern Lens section
  patternSection: {
    marginTop: 24,
    marginBottom: 16,
  },
  patternSectionHeader: {
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 14,
  },
  patternItem: {
    borderLeftWidth: 3,
    paddingLeft: 14,
    marginBottom: 16,
  },
  patternItemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  patternItemYear: {
    fontSize: 15,
    fontWeight: '600',
    marginRight: 8,
  },
  patternItemIcon: {
    fontSize: 14,
  },
  patternItemTitle: {
    fontSize: 14,
    marginBottom: 4,
  },
  patternItemSummary: {
    fontSize: 13,
    lineHeight: 18,
  },
  patternDisclaimer: {
    fontSize: 11,
    fontStyle: 'italic',
    marginTop: 8,
  },
});

export default ResonanceMarker;
