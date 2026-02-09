/**
 * DEBUG PAGE: Wing State Visual Verification
 * 
 * Purpose: Visual verification of P0 Wing UX Fix
 * Active only when EXPO_PUBLIC_DEBUG_MIRROR=true
 * 
 * This page renders all 4 wing display states without authentication
 * to allow visual inspection of the P0 implementation.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { Ionicons } from '@expo/vector-icons';

// Check if DEBUG mode is enabled
const DEBUG_MIRROR_ENV = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

// Type names for display
const TYPE_NAMES: { [key: number]: string } = {
  1: 'The Perfectionist',
  2: 'The Helper',
  3: 'The Achiever',
  4: 'The Individualist',
  5: 'The Investigator',
  6: 'The Loyalist',
  7: 'The Enthusiast',
  8: 'The Challenger',
  9: 'The Peacemaker',
};

// Wing display states
type WingDisplayState = 'dominant' | 'leaning' | 'balanced' | 'not_clear';

interface WingDisplayInfo {
  state: WingDisplayState;
  typeLabel: string;
  confidenceBadge: 'High' | 'Exploratory' | 'Low';
  helperText: string | null;
}

// Helper to compute adjacent wing types
function getWingTypes(coreType: number): { left: number; right: number } {
  const left = coreType === 1 ? 9 : coreType - 1;
  const right = coreType === 9 ? 1 : coreType + 1;
  return { left, right };
}

// Generate wing display info for each state
function getWingDisplayInfo(
  coreType: number,
  wing: number | 'balanced' | null,
  confidenceTier: string
): WingDisplayInfo {
  const wingTypes = getWingTypes(coreType);
  
  // Case D: Wing Not Yet Clear
  if (wing === null || wing === undefined) {
    return {
      state: 'not_clear',
      typeLabel: `Type ${coreType} — wing not yet clear`,
      confidenceBadge: 'Low',
      helperText: 'With more reflections or questions, a clearer wing may emerge.',
    };
  }
  
  // Case C: Balanced Wings
  if (wing === 'balanced') {
    return {
      state: 'balanced',
      typeLabel: `Type ${coreType} — balanced wings (${wingTypes.left} & ${wingTypes.right})`,
      confidenceBadge: 'Low',
      helperText: 'Both adjacent patterns appear active. This often clarifies over time.',
    };
  }
  
  const isHighConfidence = confidenceTier === 'high';
  const isMediumConfidence = confidenceTier === 'medium';
  
  // Case A: Dominant Wing
  if (isHighConfidence) {
    return {
      state: 'dominant',
      typeLabel: `Type ${coreType}w${wing}`,
      confidenceBadge: 'High',
      helperText: null,
    };
  }
  
  // Case B: Leaning Wing
  return {
    state: 'leaning',
    typeLabel: `Type ${coreType} — leaning toward Wing ${wing}`,
    confidenceBadge: isMediumConfidence ? 'Exploratory' : 'Exploratory',
    helperText: 'One adjacent pattern appears slightly stronger, though not yet decisive.',
  };
}

// Mock configurations for each wing state
interface MockConfig {
  label: string;
  description: string;
  getWing: (coreType: number) => number | 'balanced' | null;
  confidenceTier: string;
}

const MOCK_CONFIGS: Record<WingDisplayState, MockConfig> = {
  dominant: {
    label: 'A) Dominant Wing',
    description: 'High confidence - clear wing',
    getWing: (coreType) => coreType === 1 ? 9 : coreType - 1,  // Left wing
    confidenceTier: 'high',
  },
  leaning: {
    label: 'B) Leaning Wing',
    description: 'Medium confidence - slightly stronger wing',
    getWing: (coreType) => coreType === 1 ? 9 : coreType - 1,  // Left wing
    confidenceTier: 'medium',
  },
  balanced: {
    label: 'C) Balanced Wings',
    description: 'Both wings equally active',
    getWing: () => 'balanced',
    confidenceTier: 'low',
  },
  not_clear: {
    label: 'D) Wing Not Yet Clear',
    description: 'Insufficient data for wing determination',
    getWing: () => null,
    confidenceTier: 'low',
  },
};

// Wing state selector for exploring states
const WING_STATES: WingDisplayState[] = ['dominant', 'leaning', 'balanced', 'not_clear'];

export default function WingStatesDebugPage() {
  const router = useRouter();
  const [coreType, setCoreType] = useState(7);  // Default to Type 7
  
  // Gate: Only show if DEBUG mode enabled
  if (!DEBUG_MIRROR_ENV) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        <View style={styles.gateContainer}>
          <Ionicons name="lock-closed" size={48} color={Colors.textTertiary} />
          <Text style={styles.gateTitle}>Debug Mode Disabled</Text>
          <Text style={styles.gateText}>
            Set EXPO_PUBLIC_DEBUG_MIRROR=true to access this page.
          </Text>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Text style={styles.backButtonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.closeButton}>
          <Ionicons name="close" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>P0 Wing States Debug</Text>
        <View style={styles.headerSpacer} />
      </View>
      
      <ScrollView contentContainerStyle={styles.content}>
        {/* DEBUG BADGE */}
        <View style={styles.debugBadge}>
          <Ionicons name="bug-outline" size={16} color="#FF6B6B" />
          <Text style={styles.debugBadgeText}>DEBUG PAGE — MOCK DATA ONLY</Text>
        </View>
        
        {/* Core Type Selector */}
        <View style={styles.selectorCard}>
          <Text style={styles.selectorLabel}>Core Type</Text>
          <View style={styles.typeSelector}>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((type) => (
              <TouchableOpacity
                key={type}
                style={[
                  styles.typeButton,
                  coreType === type && styles.typeButtonSelected,
                ]}
                onPress={() => setCoreType(type)}
              >
                <Text style={[
                  styles.typeButtonText,
                  coreType === type && styles.typeButtonTextSelected,
                ]}>
                  {type}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          <Text style={styles.typeName}>
            {TYPE_NAMES[coreType]}
          </Text>
        </View>
        
        {/* Wing States Gallery */}
        <Text style={styles.sectionTitle}>All 4 Wing Display States</Text>
        
        {WING_STATES.map((state) => {
          const config = MOCK_CONFIGS[state];
          const mockWing = config.getWing(coreType);
          const wingInfo = getWingDisplayInfo(coreType, mockWing, config.confidenceTier);
          
          return (
            <View key={state} style={styles.stateCard}>
              {/* State Label */}
              <View style={styles.stateHeader}>
                <Text style={styles.stateLabel}>{config.label}</Text>
                <Text style={styles.stateDescription}>{config.description}</Text>
              </View>
              
              {/* Rendered Result (as it would appear in the app) */}
              <View style={styles.resultPreview}>
                <View style={styles.typeBadge}>
                  <Text style={styles.typeNumber}>{coreType}</Text>
                </View>
                
                <Text style={styles.typeTitle}>
                  {wingInfo.typeLabel}
                </Text>
                <Text style={styles.typeSubtitle}>
                  {TYPE_NAMES[coreType]}
                </Text>
                
                <View style={[
                  styles.confidenceBadge,
                  wingInfo.confidenceBadge === 'High' && styles.confidenceHigh,
                  wingInfo.confidenceBadge === 'Exploratory' && styles.confidenceMedium,
                  wingInfo.confidenceBadge === 'Low' && styles.confidenceLow,
                ]}>
                  <Text style={styles.confidenceText}>
                    {wingInfo.confidenceBadge}
                  </Text>
                </View>
                
                {wingInfo.helperText && (
                  <Text style={styles.helperText}>
                    {wingInfo.helperText}
                  </Text>
                )}
              </View>
              
              {/* Technical Details */}
              <View style={styles.techDetails}>
                <Text style={styles.techText}>
                  wing_state: {state} | wing: {mockWing === null ? '(none)' : JSON.stringify(mockWing)} | confidence_tier: "{config.confidenceTier}"
                </Text>
              </View>
            </View>
          );
        })}
        
        <View style={styles.bottomSpacer} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  
  // Gate (when debug disabled)
  gateContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  gateTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginTop: 16,
    marginBottom: 8,
  },
  gateText: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
  },
  backButton: {
    backgroundColor: Colors.text,
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 32,
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.background,
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  closeButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.text,
  },
  headerSpacer: {
    width: 32,
  },
  
  content: {
    padding: 16,
  },
  
  // Debug Badge
  debugBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#1a1a2e',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 16,
  },
  debugBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FF6B6B',
    letterSpacing: 1,
  },
  
  // Type Selector
  selectorCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 20,
  },
  selectorLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  typeSelector: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  typeButton: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: Colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  typeButtonSelected: {
    backgroundColor: Colors.text,
    borderColor: Colors.text,
  },
  typeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  typeButtonTextSelected: {
    color: Colors.background,
  },
  typeName: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.text,
    textAlign: 'center',
  },
  
  // Section Title
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textTertiary,
    marginBottom: 16,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  
  // State Card
  stateCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: 'hidden',
  },
  stateHeader: {
    backgroundColor: '#1a1a2e',
    padding: 12,
  },
  stateLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#4CAF50',
    marginBottom: 2,
  },
  stateDescription: {
    fontSize: 12,
    color: '#aaaacc',
  },
  
  // Result Preview (mimics the actual UI)
  resultPreview: {
    padding: 20,
    alignItems: 'center',
  },
  typeBadge: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.text,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  typeNumber: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.background,
  },
  typeTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 4,
    textAlign: 'center',
  },
  typeSubtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: 12,
  },
  confidenceBadge: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: Colors.border,
    marginBottom: 8,
  },
  confidenceHigh: {
    backgroundColor: '#D4EDDA',
  },
  confidenceMedium: {
    backgroundColor: '#FFF3CD',
  },
  confidenceLow: {
    backgroundColor: '#F8D7DA',
  },
  confidenceText: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.text,
  },
  helperText: {
    fontSize: 13,
    lineHeight: 19,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    textAlign: 'center',
    paddingHorizontal: 16,
    marginTop: 4,
  },
  
  // Technical Details
  techDetails: {
    backgroundColor: '#f5f5f5',
    padding: 10,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  techText: {
    fontSize: 10,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: Colors.textTertiary,
    textAlign: 'center',
  },
  
  bottomSpacer: {
    height: 40,
  },
});
