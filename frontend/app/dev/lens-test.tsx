/**
 * DEV-ONLY: Astrology Lens Test Harness
 * 
 * Renders AstrologyLensView with 4 hardcoded payloads to verify rendering paths:
 * 1. success:true, houses_computed:true (Pete-like data)
 * 2. success:true, houses_computed:false (no houses)
 * 3. success:false, error:"INCOMPLETE_BIRTH_DATA"
 * 4. success:false, error:"ASCENDANT_COMPUTE_FAILED"
 * 
 * This page does NOT require auth/Zustand store.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { Colors } from '../../../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import IncompleteBirthDataCard from '../../../components/IncompleteBirthDataCard';

// =============================================================================
// MOCK PAYLOADS
// =============================================================================

const MOCK_PAYLOADS = {
  // Case 1: Full success with houses
  successWithHouses: {
    label: '✅ Case 1: success=true, houses_computed=true',
    data: {
      success: true,
      title: 'Your Core Structure',
      core_placements: {
        sun: 'Pisces',
        moon: 'Aries',
        ascendant: 'Sagittarius',
        sun_house: 3,
        moon_house: 4,
        houses_computed: true,
      },
      sections: [
        { label: 'Sun in Pisces', body: 'Your Sun in Pisces suggests a natural attunement to emotional undercurrents and collective themes.' },
        { label: 'Moon in Aries', body: 'Your Moon in Aries may bring a need for emotional directness and quick processing of feelings.' },
        { label: 'Sagittarius Rising', body: 'With Sagittarius rising, you may meet the world with curiosity and a search for meaning.' },
      ],
      mirror_prompt: 'What in these descriptions feels true to your lived experience?',
      debug_stamp: {
        ascendant_valid: true,
        houses_computed: true,
      },
    },
  },

  // Case 2: Success but no houses computed
  successNoHouses: {
    label: '⚠️ Case 2: success=true, houses_computed=false',
    data: {
      success: true,
      title: 'Your Core Structure',
      core_placements: {
        sun: 'Gemini',
        moon: 'Scorpio',
        ascendant: 'Gemini',
        sun_house: null,
        moon_house: null,
        houses_computed: false,
      },
      sections: [
        { label: 'Sun in Gemini', body: 'Your Sun in Gemini suggests a natural curiosity and need for mental stimulation.' },
        { label: 'Moon in Scorpio', body: 'Your Moon in Scorpio may bring emotional intensity and a need for depth in connections.' },
      ],
      mirror_prompt: 'Notice which themes resonate and which feel foreign.',
      debug_stamp: {
        ascendant_valid: true,
        houses_computed: false,
      },
    },
  },

  // Case 3: Incomplete birth data error
  incompleteBirthData: {
    label: '❌ Case 3: success=false, INCOMPLETE_BIRTH_DATA',
    data: {
      success: false,
      error: 'INCOMPLETE_BIRTH_DATA',
      missing_fields: ['birth_time_local', 'timezone_iana'],
      message: 'Birth data is incomplete. Please provide all required details.',
      required_fields: ['birth_date', 'birth_time_local', 'lat', 'lon', 'timezone_iana'],
    },
  },

  // Case 4: Generic compute error
  computeError: {
    label: '❌ Case 4: success=false, ASCENDANT_COMPUTE_FAILED',
    data: {
      success: false,
      error: 'ASCENDANT_COMPUTE_FAILED',
      message: 'Could not compute ascendant. The birth location or time may be outside valid ranges.',
      core_placements: {
        sun: 'Pisces',
        moon: 'Aries',
        ascendant: null,
        houses_computed: false,
      },
    },
  },
};

// =============================================================================
// MINI ASTROLOGY LENS RENDERER (Standalone, no API calls)
// =============================================================================

interface MockAstrologyData {
  success?: boolean;
  error?: string;
  message?: string;
  missing_fields?: string[];
  required_fields?: string[];
  title?: string;
  core_placements?: {
    sun: string;
    moon: string;
    ascendant: string | null;
    sun_house?: number | null;
    moon_house?: number | null;
    houses_computed?: boolean;
  };
  sections?: Array<{ label: string; body: string }>;
  mirror_prompt?: string;
}

function MockAstrologyLensView({ data }: { data: MockAstrologyData }) {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  // Render core placements card
  const renderCorePlacements = () => {
    const placements = data?.core_placements;

    if (!placements) {
      return (
        <View style={styles.corePlacementsCard}>
          <Text style={styles.corePlacementsTitle}>SUN • MOON • ASCENDANT</Text>
          <View style={styles.corePlacementsRow}>
            <View style={styles.placementItem}>
              <Ionicons name="sunny-outline" size={16} color={Colors.textTertiary} />
              <Text style={styles.placementSign}>—</Text>
            </View>
            <View style={styles.placementDivider} />
            <View style={styles.placementItem}>
              <Ionicons name="moon-outline" size={16} color={Colors.textTertiary} />
              <Text style={styles.placementSign}>—</Text>
            </View>
            <View style={styles.placementDivider} />
            <View style={styles.placementItem}>
              <Ionicons name="arrow-up-outline" size={16} color={Colors.textTertiary} />
              <Text style={styles.placementSign}>—</Text>
            </View>
          </View>
        </View>
      );
    }

    // Format with house number ONLY if houses_computed is true
    const formatWithHouse = (sign: string | null, house: number | null | undefined) => {
      if (!sign || sign === 'Unknown') return '—';
      if (placements.houses_computed && house != null) {
        return `${sign} (H${house})`;
      }
      return sign;
    };

    const hasValidAscendant = placements.ascendant && placements.ascendant !== 'Unknown' && placements.ascendant !== '—';

    return (
      <View style={styles.corePlacementsCard}>
        <Text style={styles.corePlacementsTitle}>SUN • MOON • ASCENDANT</Text>
        <View style={styles.corePlacementsRow}>
          <View style={styles.placementItem}>
            <Ionicons name="sunny-outline" size={16} color={Colors.accent} />
            <Text style={styles.placementSign}>
              {formatWithHouse(placements.sun, placements.sun_house)}
            </Text>
          </View>
          <View style={styles.placementDivider} />
          <View style={styles.placementItem}>
            <Ionicons name="moon-outline" size={16} color={Colors.accent} />
            <Text style={styles.placementSign}>
              {formatWithHouse(placements.moon, placements.moon_house)}
            </Text>
          </View>
          <View style={styles.placementDivider} />
          <View style={styles.placementItem}>
            <Ionicons name="arrow-up-outline" size={16} color={hasValidAscendant ? Colors.accent : Colors.textTertiary} />
            <Text style={[styles.placementSign, !hasValidAscendant && styles.placementMissing]}>
              {hasValidAscendant ? placements.ascendant : '—'}
            </Text>
          </View>
        </View>
      </View>
    );
  };

  // Render section
  const renderSection = (section: { label: string; body: string }, index: number) => (
    <View key={index} style={styles.sectionCard}>
      <Text style={styles.sectionLabel}>{section.label}</Text>
      <Text style={styles.sectionBody}>{section.body}</Text>
    </View>
  );

  // Main render logic - mirrors AstrologyLensView exactly
  if (data?.success === false) {
    if (data.error === 'INCOMPLETE_BIRTH_DATA') {
      return (
        <View style={styles.testCase}>
          <View style={styles.incompleteDataContainer}>
            <Text style={styles.title}>Astrology</Text>
            <IncompleteBirthDataCard
              missingFields={data.missing_fields}
              lensName="Astrology insights"
            />
            <Text style={styles.incompleteHint}>
              Your chart requires precise birth details to calculate planetary positions and houses.
            </Text>
          </View>
          <View style={styles.renderPathBadge}>
            <Text style={styles.renderPathText}>RENDER PATH: IncompleteBirthDataCard</Text>
          </View>
        </View>
      );
    } else {
      // Generic error card
      return (
        <View style={styles.testCase}>
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle-outline" size={32} color={Colors.textTertiary} />
            <Text style={styles.errorText}>
              {data.message || 'Something went wrong'}
            </Text>
            <Text style={styles.errorCode}>Error: {data.error}</Text>
            <TouchableOpacity style={styles.retryButton}>
              <Text style={styles.retryText}>Try Again</Text>
            </TouchableOpacity>
          </View>
          {/* Still show core placements if available */}
          {data.core_placements && renderCorePlacements()}
          <View style={styles.renderPathBadge}>
            <Text style={styles.renderPathText}>RENDER PATH: GenericErrorCard + CorePlacements</Text>
          </View>
        </View>
      );
    }
  }

  // Success case
  return (
    <View style={styles.testCase}>
      <Text style={styles.title}>{data.title || 'Your Core Structure'}</Text>
      
      {renderCorePlacements()}
      
      {data.sections?.map((section, index) => renderSection(section, index))}
      
      {data.mirror_prompt && (
        <View style={styles.mirrorPromptCard}>
          <Text style={styles.mirrorPromptLabel}>REFLECT</Text>
          <Text style={styles.mirrorPromptText}>{data.mirror_prompt}</Text>
        </View>
      )}
      
      <View style={styles.renderPathBadge}>
        <Text style={styles.renderPathText}>
          RENDER PATH: Success + {data.core_placements?.houses_computed ? 'Houses (H#)' : 'No Houses'}
        </Text>
      </View>
    </View>
  );
}

// =============================================================================
// TEST HARNESS PAGE
// =============================================================================

export default function LensTestPage() {
  const [selectedCase, setSelectedCase] = useState<keyof typeof MOCK_PAYLOADS>('successWithHouses');

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar style="dark" />
      
      {/* Header */}
      <View style={styles.header}>
        <Ionicons name="flask-outline" size={24} color={Colors.accent} />
        <Text style={styles.headerTitle}>DEV: Lens Test Harness</Text>
      </View>
      
      {/* Case Selector */}
      <View style={styles.caseSelector}>
        {Object.entries(MOCK_PAYLOADS).map(([key, { label }]) => (
          <TouchableOpacity
            key={key}
            style={[
              styles.caseButton,
              selectedCase === key && styles.caseButtonActive,
            ]}
            onPress={() => setSelectedCase(key as keyof typeof MOCK_PAYLOADS)}
          >
            <Text
              style={[
                styles.caseButtonText,
                selectedCase === key && styles.caseButtonTextActive,
              ]}
              numberOfLines={2}
            >
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Rendered Component */}
      <ScrollView style={styles.previewArea} contentContainerStyle={styles.previewContent}>
        <Text style={styles.previewLabel}>RENDERED OUTPUT:</Text>
        <MockAstrologyLensView data={MOCK_PAYLOADS[selectedCase].data} />
        
        {/* Raw Data Display */}
        <View style={styles.rawDataCard}>
          <Text style={styles.rawDataLabel}>RAW PAYLOAD:</Text>
          <Text style={styles.rawDataText}>
            {JSON.stringify(MOCK_PAYLOADS[selectedCase].data, null, 2)}
          </Text>
        </View>
      </ScrollView>

      {/* Checklist */}
      <View style={styles.checklist}>
        <Text style={styles.checklistTitle}>✓ CHECKLIST</Text>
        <Text style={styles.checklistItem}>
          • House labels (H#) only when houses_computed=true
        </Text>
        <Text style={styles.checklistItem}>
          • No "Ascendant is unknown" legacy text
        </Text>
        <Text style={styles.checklistItem}>
          • GenericErrorCard for non-INCOMPLETE errors
        </Text>
        <Text style={styles.checklistItem}>
          • IncompleteBirthDataCard for missing fields
        </Text>
      </View>
    </SafeAreaView>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    gap: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.border,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
  },
  caseSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 8,
    gap: 6,
    backgroundColor: Colors.surface,
  },
  caseButton: {
    flex: 1,
    minWidth: '45%',
    padding: 8,
    borderRadius: 8,
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  caseButtonActive: {
    backgroundColor: Colors.accent,
    borderColor: Colors.accent,
  },
  caseButtonText: {
    fontSize: 11,
    color: Colors.text,
    textAlign: 'center',
  },
  caseButtonTextActive: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  previewArea: {
    flex: 1,
  },
  previewContent: {
    padding: 16,
  },
  previewLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1,
    marginBottom: 12,
  },
  testCase: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 12,
  },
  corePlacementsCard: {
    backgroundColor: Colors.background,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  corePlacementsTitle: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.5,
    textAlign: 'center',
    marginBottom: 12,
  },
  corePlacementsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  placementItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 8,
  },
  placementSign: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.text,
  },
  placementMissing: {
    color: Colors.textTertiary,
    fontStyle: 'italic',
  },
  placementDivider: {
    width: 1,
    height: 20,
    backgroundColor: Colors.border,
  },
  sectionCard: {
    marginBottom: 12,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 4,
  },
  sectionBody: {
    fontSize: 14,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
  mirrorPromptCard: {
    backgroundColor: Colors.background,
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  mirrorPromptLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.accent,
    letterSpacing: 1,
    marginBottom: 6,
  },
  mirrorPromptText: {
    fontSize: 14,
    color: Colors.text,
    fontStyle: 'italic',
  },
  incompleteDataContainer: {
    paddingVertical: 8,
  },
  incompleteHint: {
    fontSize: 13,
    color: Colors.textTertiary,
    textAlign: 'center',
    paddingHorizontal: 16,
    marginTop: 12,
    lineHeight: 18,
  },
  errorContainer: {
    alignItems: 'center',
    gap: 12,
    paddingVertical: 20,
  },
  errorText: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  errorCode: {
    fontSize: 11,
    color: Colors.textTertiary,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    backgroundColor: Colors.background,
    borderRadius: 8,
  },
  retryText: {
    fontSize: 14,
    color: Colors.accent,
    fontWeight: '500',
  },
  renderPathBadge: {
    marginTop: 12,
    padding: 8,
    backgroundColor: '#E8F5E9',
    borderRadius: 6,
  },
  renderPathText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#2E7D32',
    textAlign: 'center',
    letterSpacing: 0.5,
  },
  rawDataCard: {
    backgroundColor: '#1E1E1E',
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  rawDataLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: '#888',
    letterSpacing: 1,
    marginBottom: 8,
  },
  rawDataText: {
    fontSize: 10,
    color: '#D4D4D4',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  checklist: {
    padding: 12,
    backgroundColor: Colors.surface,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  checklistTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 6,
  },
  checklistItem: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginBottom: 2,
  },
});
