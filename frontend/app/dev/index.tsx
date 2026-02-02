/**
 * DEV-ONLY: Lens Test Harness
 * 
 * Tests Astrology & Human Design rendering paths with hardcoded payloads.
 * Does NOT require auth/Zustand store.
 * 
 * ASTROLOGY CASES:
 * 1. success:true, houses_computed:true (Pete)
 * 2. success:true, houses_computed:false (no houses)
 * 3. success:false, error:"INCOMPLETE_BIRTH_DATA"
 * 4. success:false, error:"ASCENDANT_COMPUTE_FAILED"
 * 
 * HUMAN DESIGN CASES:
 * 1. success:true, full data (Pete - Manifestor)
 * 2. success:true, Reflector (Mel - no channels)
 * 3. success:false, error:"INCOMPLETE_BIRTH_DATA"
 * 4. success:false, error:"HD_COMPUTE_FAILED"
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { Colors } from '../../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import IncompleteBirthDataCard from '../../components/IncompleteBirthDataCard';

// =============================================================================
// ASTROLOGY MOCK PAYLOADS
// =============================================================================

const ASTROLOGY_PAYLOADS = {
  successWithHouses: {
    label: '✅ Astro 1: Houses Computed',
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
        { label: 'Sun in Pisces', body: 'Your Sun in Pisces suggests a natural attunement to emotional undercurrents.' },
        { label: 'Moon in Aries', body: 'Your Moon in Aries may bring emotional directness.' },
      ],
      mirror_prompt: 'What in these descriptions feels true to your lived experience?',
    },
  },
  successNoHouses: {
    label: '⚠️ Astro 2: No Houses',
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
      sections: [{ label: 'Sun in Gemini', body: 'Your Sun in Gemini suggests curiosity.' }],
      mirror_prompt: 'Notice which themes resonate.',
    },
  },
  incompleteBirthData: {
    label: '❌ Astro 3: INCOMPLETE',
    data: {
      success: false,
      error: 'INCOMPLETE_BIRTH_DATA',
      missing_fields: ['birth_time_local', 'timezone_iana'],
      message: 'Birth data is incomplete.',
    },
  },
  computeError: {
    label: '❌ Astro 4: COMPUTE_FAILED',
    data: {
      success: false,
      error: 'ASCENDANT_COMPUTE_FAILED',
      message: 'Could not compute ascendant.',
      core_placements: { sun: 'Pisces', moon: 'Aries', ascendant: null, houses_computed: false },
    },
  },
};

// =============================================================================
// HUMAN DESIGN MOCK PAYLOADS
// =============================================================================

const HD_PAYLOADS = {
  manifestor: {
    label: '✅ HD 1: Pete (Manifestor)',
    data: {
      success: true,
      title: 'Your Core Mechanics',
      core_mechanics: {
        type: 'Manifestor',
        strategy: 'Inform before acting',
        authority: 'Emotional',
        profile: '5/1',
        definition: 'Split',
        incarnation_cross: 'Left Angle Cross of 37/5 | 40/35',
        incarnation_cross_label: 'LAX Migration',
        incarnation_cross_gates: '37/5 • 40/35',
        channels: ['4–63', '35–36', '37–40'],
      },
      sections: [
        { label: 'Type: Manifestor', body: 'As a Manifestor, you have the capacity to initiate and bring things into being.' },
        { label: 'Authority: Emotional', body: 'Your clarity comes from riding the emotional wave.' },
      ],
      mirror_prompt: 'What would be a small way to experiment with informing today?',
    },
  },
  reflector: {
    label: '✅ HD 2: Mel (Reflector)',
    data: {
      success: true,
      title: 'Your Core Mechanics',
      core_mechanics: {
        type: 'Reflector',
        strategy: 'Wait a lunar cycle',
        authority: 'None (Lunar)',
        profile: '3/5',
        definition: 'None',
        incarnation_cross: 'Right Angle Cross of 45/22 | 26/47',
        incarnation_cross_label: 'RAX Rulership',
        incarnation_cross_gates: '45/22 • 26/47',
        channels: [],  // Reflectors have no defined channels
      },
      sections: [
        { label: 'Type: Reflector', body: 'As a Reflector, you mirror the health of your environment.' },
        { label: 'Authority: Lunar', body: 'Your clarity comes from waiting a full lunar cycle.' },
      ],
      mirror_prompt: 'Notice how different environments affect your sense of clarity.',
    },
  },
  incompleteBirthData: {
    label: '❌ HD 3: INCOMPLETE',
    data: {
      success: false,
      error: 'INCOMPLETE_BIRTH_DATA',
      missing_fields: ['birth_time_local', 'lat', 'lon'],
      message: 'Birth data is incomplete.',
    },
  },
  computeError: {
    label: '❌ HD 4: HD_COMPUTE_FAILED',
    data: {
      success: false,
      error: 'HD_COMPUTE_FAILED',
      message: 'Could not compute Human Design chart.',
      core_mechanics: { type: null, strategy: null, authority: null },
    },
  },
};

// =============================================================================
// MOCK ASTROLOGY RENDERER
// =============================================================================

function MockAstrologyView({ data }: { data: any }) {
  const placements = data?.core_placements;

  const formatWithHouse = (sign: string | null, house: number | null | undefined) => {
    if (!sign || sign === 'Unknown') return '—';
    if (placements?.houses_computed && house != null) return `${sign} (H${house})`;
    return sign;
  };

  if (data?.success === false) {
    if (data.error === 'INCOMPLETE_BIRTH_DATA') {
      return (
        <View style={styles.testCase}>
          <IncompleteBirthDataCard missingFields={data.missing_fields} lensName="Astrology" />
          <View style={styles.renderPathBadge}><Text style={styles.renderPathText}>PATH: IncompleteBirthDataCard</Text></View>
        </View>
      );
    }
    return (
      <View style={styles.testCase}>
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={24} color={Colors.textTertiary} />
          <Text style={styles.errorText}>{data.message}</Text>
          <Text style={styles.errorCode}>Error: {data.error}</Text>
        </View>
        <View style={styles.renderPathBadge}><Text style={styles.renderPathText}>PATH: GenericErrorCard</Text></View>
      </View>
    );
  }

  const hasAsc = placements?.ascendant && placements.ascendant !== 'Unknown';
  
  return (
    <View style={styles.testCase}>
      <Text style={styles.title}>{data.title}</Text>
      <View style={styles.coreCard}>
        <Text style={styles.coreCardTitle}>SUN • MOON • ASCENDANT</Text>
        <View style={styles.coreRow}>
          <View style={styles.coreItem}>
            <Ionicons name="sunny-outline" size={16} color={Colors.accent} />
            <Text style={styles.coreValue}>{formatWithHouse(placements?.sun, placements?.sun_house)}</Text>
          </View>
          <View style={styles.coreDivider} />
          <View style={styles.coreItem}>
            <Ionicons name="moon-outline" size={16} color={Colors.accent} />
            <Text style={styles.coreValue}>{formatWithHouse(placements?.moon, placements?.moon_house)}</Text>
          </View>
          <View style={styles.coreDivider} />
          <View style={styles.coreItem}>
            <Ionicons name="arrow-up-outline" size={16} color={hasAsc ? Colors.accent : Colors.textTertiary} />
            <Text style={[styles.coreValue, !hasAsc && styles.coreMissing]}>{hasAsc ? placements?.ascendant : '—'}</Text>
          </View>
        </View>
      </View>
      <View style={styles.renderPathBadge}>
        <Text style={styles.renderPathText}>PATH: Success {placements?.houses_computed ? '+ Houses (H#)' : '+ No Houses'}</Text>
      </View>
    </View>
  );
}

// =============================================================================
// MOCK HUMAN DESIGN RENDERER
// =============================================================================

function MockHumanDesignView({ data }: { data: any }) {
  const mechanics = data?.core_mechanics;

  const formatChannels = (channels: string[] | undefined): string => {
    if (!channels || channels.length === 0) return 'None defined';
    return [...channels].sort((a, b) => parseInt(a.split(/[–-]/)[0]) - parseInt(b.split(/[–-]/)[0])).join(', ');
  };

  if (data?.success === false) {
    if (data.error === 'INCOMPLETE_BIRTH_DATA') {
      return (
        <View style={styles.testCase}>
          <IncompleteBirthDataCard missingFields={data.missing_fields} lensName="Human Design" />
          <View style={styles.renderPathBadge}><Text style={styles.renderPathText}>PATH: IncompleteBirthDataCard</Text></View>
        </View>
      );
    }
    return (
      <View style={styles.testCase}>
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={24} color={Colors.textTertiary} />
          <Text style={styles.errorText}>{data.message}</Text>
          <Text style={styles.errorCode}>Error: {data.error}</Text>
        </View>
        <View style={styles.renderPathBadge}><Text style={styles.renderPathText}>PATH: GenericErrorCard</Text></View>
      </View>
    );
  }

  return (
    <View style={styles.testCase}>
      <Text style={styles.title}>{data.title}</Text>
      <View style={styles.coreCard}>
        <Text style={styles.coreCardTitle}>CORE MECHANICS</Text>
        
        {/* Row 1: Type • Strategy */}
        <View style={styles.hdRow}>
          <View style={styles.hdItem}>
            <Text style={styles.hdLabel}>Type</Text>
            <Text style={styles.hdValue}>{mechanics?.type || '—'}</Text>
          </View>
          <View style={styles.coreDivider} />
          <View style={styles.hdItem}>
            <Text style={styles.hdLabel}>Strategy</Text>
            <Text style={styles.hdValue}>{mechanics?.strategy || '—'}</Text>
          </View>
        </View>
        
        {/* Row 2: Authority • Profile */}
        <View style={[styles.hdRow, { marginTop: 12 }]}>
          <View style={styles.hdItem}>
            <Text style={styles.hdLabel}>Authority</Text>
            <Text style={styles.hdValue}>{mechanics?.authority || '—'}</Text>
          </View>
          <View style={styles.coreDivider} />
          <View style={styles.hdItem}>
            <Text style={styles.hdLabel}>Profile</Text>
            <Text style={styles.hdValue}>{mechanics?.profile || '—'}</Text>
          </View>
        </View>
        
        {/* Definition */}
        <View style={styles.hdFullRow}>
          <Text style={styles.hdFullLabel}>Definition</Text>
          <Text style={styles.hdFullValue}>{mechanics?.definition || '—'}</Text>
        </View>
        
        {/* Incarnation Cross */}
        <View style={styles.hdFullRow}>
          <Text style={styles.hdFullLabel}>Incarnation Cross</Text>
          <Text style={styles.hdFullValue}>{mechanics?.incarnation_cross || '—'}</Text>
        </View>
        
        {/* Channels */}
        <View style={styles.hdFullRow}>
          <Text style={styles.hdFullLabel}>Channels</Text>
          <Text style={styles.hdFullValue}>{formatChannels(mechanics?.channels)}</Text>
        </View>
      </View>
      
      <View style={styles.renderPathBadge}>
        <Text style={styles.renderPathText}>
          PATH: Success ({mechanics?.type || 'Unknown'}, {mechanics?.channels?.length || 0} channels)
        </Text>
      </View>
    </View>
  );
}

// =============================================================================
// MAIN TEST HARNESS
// =============================================================================

type LensType = 'astrology' | 'humandesign';

export default function LensTestPage() {
  const [activeLens, setActiveLens] = useState<LensType>('astrology');
  const [selectedAstro, setSelectedAstro] = useState<keyof typeof ASTROLOGY_PAYLOADS>('successWithHouses');
  const [selectedHD, setSelectedHD] = useState<keyof typeof HD_PAYLOADS>('manifestor');

  const currentPayloads = activeLens === 'astrology' ? ASTROLOGY_PAYLOADS : HD_PAYLOADS;
  const selectedCase = activeLens === 'astrology' ? selectedAstro : selectedHD;
  const setSelectedCase = activeLens === 'astrology' ? setSelectedAstro : setSelectedHD;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar style="dark" />
      
      {/* Header */}
      <View style={styles.header}>
        <Ionicons name="flask-outline" size={20} color={Colors.accent} />
        <Text style={styles.headerTitle}>DEV: Lens Test Harness</Text>
      </View>
      
      {/* Lens Tabs */}
      <View style={styles.lensTabs}>
        <TouchableOpacity
          style={[styles.lensTab, activeLens === 'astrology' && styles.lensTabActive]}
          onPress={() => setActiveLens('astrology')}
        >
          <Text style={[styles.lensTabText, activeLens === 'astrology' && styles.lensTabTextActive]}>
            ✦ Astrology
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.lensTab, activeLens === 'humandesign' && styles.lensTabActive]}
          onPress={() => setActiveLens('humandesign')}
        >
          <Text style={[styles.lensTabText, activeLens === 'humandesign' && styles.lensTabTextActive]}>
            ◈ Human Design
          </Text>
        </TouchableOpacity>
      </View>
      
      {/* Case Selector */}
      <View style={styles.caseSelector}>
        {Object.entries(currentPayloads).map(([key, { label }]) => (
          <TouchableOpacity
            key={key}
            style={[styles.caseButton, selectedCase === key && styles.caseButtonActive]}
            onPress={() => setSelectedCase(key as any)}
          >
            <Text style={[styles.caseButtonText, selectedCase === key && styles.caseButtonTextActive]} numberOfLines={1}>
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Rendered Component */}
      <ScrollView style={styles.previewArea} contentContainerStyle={styles.previewContent}>
        <Text style={styles.previewLabel}>RENDERED OUTPUT:</Text>
        
        {activeLens === 'astrology' ? (
          <MockAstrologyView data={ASTROLOGY_PAYLOADS[selectedAstro].data} />
        ) : (
          <MockHumanDesignView data={HD_PAYLOADS[selectedHD].data} />
        )}
        
        {/* Raw JSON */}
        <View style={styles.rawDataCard}>
          <Text style={styles.rawDataLabel}>RAW PAYLOAD:</Text>
          <Text style={styles.rawDataText}>
            {JSON.stringify(currentPayloads[selectedCase as keyof typeof currentPayloads].data, null, 2)}
          </Text>
        </View>
      </ScrollView>

      {/* Checklist */}
      <View style={styles.checklist}>
        <Text style={styles.checklistTitle}>
          {activeLens === 'astrology' ? '✓ ASTROLOGY CHECKLIST' : '✓ HUMAN DESIGN CHECKLIST'}
        </Text>
        {activeLens === 'astrology' ? (
          <>
            <Text style={styles.checklistItem}>• House labels (H#) only when houses_computed=true</Text>
            <Text style={styles.checklistItem}>• No "Ascendant is unknown" legacy text</Text>
            <Text style={styles.checklistItem}>• GenericErrorCard for non-INCOMPLETE errors</Text>
          </>
        ) : (
          <>
            <Text style={styles.checklistItem}>• Type, Strategy, Authority, Profile, Definition shown</Text>
            <Text style={styles.checklistItem}>• Channels sorted numerically (4–63, 35–36, 37–40)</Text>
            <Text style={styles.checklistItem}>• Incarnation Cross in gate notation</Text>
            <Text style={styles.checklistItem}>• No identity/prescriptive text when compute fails</Text>
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 10, gap: 6, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: Colors.border },
  headerTitle: { fontSize: 15, fontWeight: '600', color: Colors.text },
  lensTabs: { flexDirection: 'row', backgroundColor: Colors.surface, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: Colors.border },
  lensTab: { flex: 1, paddingVertical: 10, alignItems: 'center' },
  lensTabActive: { borderBottomWidth: 2, borderBottomColor: Colors.accent },
  lensTabText: { fontSize: 13, color: Colors.textTertiary, fontWeight: '500' },
  lensTabTextActive: { color: Colors.accent },
  caseSelector: { flexDirection: 'row', flexWrap: 'wrap', padding: 6, gap: 4, backgroundColor: Colors.surface },
  caseButton: { flex: 1, minWidth: '45%', padding: 6, borderRadius: 6, backgroundColor: Colors.background, borderWidth: 1, borderColor: Colors.border },
  caseButtonActive: { backgroundColor: Colors.accent, borderColor: Colors.accent },
  caseButtonText: { fontSize: 10, color: Colors.text, textAlign: 'center' },
  caseButtonTextActive: { color: '#FFFFFF', fontWeight: '600' },
  previewArea: { flex: 1 },
  previewContent: { padding: 12 },
  previewLabel: { fontSize: 9, fontWeight: '600', color: Colors.textTertiary, letterSpacing: 1, marginBottom: 8 },
  testCase: { backgroundColor: Colors.surface, borderRadius: 10, padding: 12, marginBottom: 12 },
  title: { fontSize: 16, fontWeight: '600', color: Colors.text, marginBottom: 10 },
  coreCard: { backgroundColor: Colors.background, borderRadius: 10, padding: 12, borderWidth: StyleSheet.hairlineWidth, borderColor: Colors.border },
  coreCardTitle: { fontSize: 9, fontWeight: '600', color: Colors.textTertiary, letterSpacing: 1.5, textAlign: 'center', marginBottom: 10 },
  coreRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center' },
  coreItem: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 6 },
  coreValue: { fontSize: 13, fontWeight: '500', color: Colors.text },
  coreMissing: { color: Colors.textTertiary, fontStyle: 'italic' },
  coreDivider: { width: 1, height: 28, backgroundColor: Colors.border },
  hdRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center' },
  hdItem: { flex: 1, alignItems: 'center', paddingHorizontal: 6, gap: 2 },
  hdLabel: { fontSize: 9, color: Colors.textTertiary, textTransform: 'uppercase', letterSpacing: 0.5 },
  hdValue: { fontSize: 12, fontWeight: '500', color: Colors.text, textAlign: 'center' },
  hdFullRow: { marginTop: 10, paddingTop: 10, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: Colors.border, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  hdFullLabel: { fontSize: 11, color: Colors.textTertiary, fontWeight: '500' },
  hdFullValue: { fontSize: 11, color: Colors.text, fontWeight: '500', textAlign: 'right', flex: 1, marginLeft: 8 },
  errorContainer: { alignItems: 'center', gap: 8, paddingVertical: 16 },
  errorText: { fontSize: 13, color: Colors.textSecondary, textAlign: 'center' },
  errorCode: { fontSize: 10, color: Colors.textTertiary, fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace' },
  renderPathBadge: { marginTop: 10, padding: 6, backgroundColor: '#E8F5E9', borderRadius: 4 },
  renderPathText: { fontSize: 9, fontWeight: '600', color: '#2E7D32', textAlign: 'center', letterSpacing: 0.5 },
  rawDataCard: { backgroundColor: '#1E1E1E', borderRadius: 6, padding: 10, marginTop: 8 },
  rawDataLabel: { fontSize: 9, fontWeight: '600', color: '#888', letterSpacing: 1, marginBottom: 6 },
  rawDataText: { fontSize: 9, color: '#D4D4D4', fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace' },
  checklist: { padding: 10, backgroundColor: Colors.surface, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: Colors.border },
  checklistTitle: { fontSize: 11, fontWeight: '600', color: Colors.text, marginBottom: 4 },
  checklistItem: { fontSize: 10, color: Colors.textSecondary, marginBottom: 1 },
});
