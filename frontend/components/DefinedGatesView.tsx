import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';
import { InlineResonanceReflect } from './ResonanceReflectButtons';

interface GateData {
  gate_number: number;
  line_numbers_present: number[];
  center_name: string;
  gate_name: string;
  themes: string[];
  shadow: string;
  gift: string;
  siddhi: string;
  what_this_means: string;
  your_challenge: string;
  your_genius: string;
  practical_experiments: string[];
  remember: string;
}

interface GatesResponse {
  success: boolean;
  gates: GateData[];
  summary?: {
    total_gates: number;
    centers_with_gates: number;
  };
}

interface Props {
  userId: string;
}

export default function DefinedGatesView({ userId }: Props) {
  const { theme } = useTheme();
  const [gates, setGates] = useState<GateData[]>([]);
  const [summary, setSummary] = useState<{ total_gates: number } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedGate, setExpandedGate] = useState<number | null>(null);
  
  // Accordion state - collapsed by default
  const [isAccordionExpanded, setIsAccordionExpanded] = useState(false);

  useEffect(() => {
    loadGates();
  }, [userId]);

  const loadGates = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<GatesResponse>(`/human-design/gates/${userId}`);
      if (response.data.success) {
        setGates(response.data.gates);
        setSummary(response.data.summary || null);
      } else {
        setError('Unable to load gates data.');
      }
    } catch (err: any) {
      console.error('Gates load error:', err);
      setError('Unable to load gates right now.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleGate = (gateNumber: number) => {
    setExpandedGate(expandedGate === gateNumber ? null : gateNumber);
  };

  const renderGateCard = (gate: GateData) => {
    const isExpanded = expandedGate === gate.gate_number;

    return (
      <View
        key={gate.gate_number}
        style={[styles.gateCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
      >
        {/* Header - always visible */}
        <TouchableOpacity
          style={styles.gateHeader}
          onPress={() => toggleGate(gate.gate_number)}
          activeOpacity={0.7}
        >
          <View style={styles.gateHeaderLeft}>
            <View style={styles.gateNumberBadge}>
              <Text style={[styles.gateNumber, { color: theme.accent }]}>
                {gate.gate_number}
              </Text>
            </View>
            <View style={styles.gateHeaderInfo}>
              <Text style={[styles.gateName, { color: theme.text }]}>
                {gate.gate_name}
              </Text>
              <Text style={[styles.gateCenter, { color: theme.textTertiary }]}>
                {gate.center_name}
              </Text>
            </View>
          </View>
          <Text style={[styles.expandIcon, { color: theme.textTertiary }]}>
            {isExpanded ? '▾' : '▸'}
          </Text>
        </TouchableOpacity>

        {/* Themes row - always visible */}
        <View style={[styles.themesRow, { borderTopColor: theme.border }]}>
          {gate.themes.map((themeText, idx) => (
            <Text key={idx} style={[styles.themeTag, { color: theme.textSecondary }]}>
              {themeText}
            </Text>
          ))}
        </View>

        {/* Expanded content */}
        {isExpanded && (
          <View style={[styles.expandedContent, { borderTopColor: theme.border }]}>
            {/* What This Means */}
            <View style={styles.sectionBlock}>
              <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
                What This Means
              </Text>
              <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
                {gate.what_this_means}
              </Text>
            </View>

            {/* Your Challenge */}
            <View style={styles.sectionBlock}>
              <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
                Your Challenge
              </Text>
              <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
                {gate.your_challenge}
              </Text>
            </View>

            {/* Your Genius */}
            <View style={styles.sectionBlock}>
              <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
                Your Genius
              </Text>
              <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
                {gate.your_genius}
              </Text>
            </View>

            {/* Practical Experiments */}
            <View style={styles.sectionBlock}>
              <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
                Practical Experiments
              </Text>
              {gate.practical_experiments.map((exp, idx) => (
                <View key={idx} style={styles.experimentRow}>
                  <Text style={[styles.experimentBullet, { color: theme.accent }]}>•</Text>
                  <Text style={[styles.experimentText, { color: theme.textSecondary }]}>
                    {exp}
                  </Text>
                </View>
              ))}
            </View>

            {/* Remember */}
            <View style={[styles.rememberBlock, { backgroundColor: 'rgba(255,255,255,0.02)', borderLeftColor: theme.accent }]}>
              <Text style={[styles.rememberLabel, { color: theme.textTertiary }]}>
                Remember
              </Text>
              <Text style={[styles.rememberText, { color: theme.text }]}>
                {gate.remember}
              </Text>
            </View>

            {/* Gene Keys Bridge */}
            <View style={[styles.geneKeysBridge, { borderTopColor: theme.border }]}>
              <Text style={[styles.bridgeLabel, { color: theme.textTertiary }]}>
                Gene Keys Bridge
              </Text>
              <View style={styles.bridgeRow}>
                <View style={styles.bridgeItem}>
                  <Text style={[styles.bridgeType, { color: theme.textTertiary }]}>Shadow</Text>
                  <Text style={[styles.bridgeValue, { color: theme.textSecondary }]}>{gate.shadow}</Text>
                </View>
                <Text style={[styles.bridgeArrow, { color: theme.textTertiary }]}>→</Text>
                <View style={styles.bridgeItem}>
                  <Text style={[styles.bridgeType, { color: theme.textTertiary }]}>Gift</Text>
                  <Text style={[styles.bridgeValue, { color: theme.accent }]}>{gate.gift}</Text>
                </View>
                <Text style={[styles.bridgeArrow, { color: theme.textTertiary }]}>→</Text>
                <View style={styles.bridgeItem}>
                  <Text style={[styles.bridgeType, { color: theme.textTertiary }]}>Siddhi</Text>
                  <Text style={[styles.bridgeValue, { color: theme.textSecondary }]}>{gate.siddhi}</Text>
                </View>
              </View>
            </View>

            {/* Reflect Button */}
            <View style={styles.reflectContainer}>
              <InlineResonanceReflect
                source={{
                  lens: 'human_design',
                  type: 'gate',
                  name: `Gate ${gate.gate_number}: ${gate.gate_name}`,
                  value: gate.center_name,
                  id: `hd_gate_${gate.gate_number}`,
                }}
                prompt={gate.what_this_means}
              />
            </View>
          </View>
        )}
      </View>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="small" color={theme.textTertiary} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading gates...
        </Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Accordion Header - Always visible, collapsed by default */}
      <TouchableOpacity
        style={[styles.accordionHeader, { backgroundColor: theme.surface, borderColor: theme.border }]}
        onPress={() => setIsAccordionExpanded(!isAccordionExpanded)}
        activeOpacity={0.7}
      >
        <View style={styles.accordionHeaderLeft}>
          <Text style={[styles.accordionTitle, { color: theme.text }]}>
            Defined Gates
          </Text>
          {summary && (
            <Text style={[styles.accordionSubtitle, { color: theme.textTertiary }]}>
              {summary.total_gates} gates active
            </Text>
          )}
        </View>
        <Text style={[styles.accordionChevron, { color: theme.textTertiary }]}>
          {isAccordionExpanded ? '▲' : '▼'}
        </Text>
      </TouchableOpacity>

      {/* Accordion Content - Only visible when expanded */}
      {isAccordionExpanded && (
        <View style={[styles.accordionContent, { borderColor: theme.border }]}>
          {/* Intro text */}
          <Text style={[styles.introText, { color: theme.textSecondary }]}>
            Gates are specific energies that live within your centers. Each gate carries themes you naturally express.
          </Text>

          {/* Gates list */}
          <View style={styles.gatesList}>
            {gates.map(gate => renderGateCard(gate))}
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 16,
    marginBottom: 16,
  },
  // Accordion Header
  accordionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  accordionHeaderLeft: {
    flex: 1,
  },
  accordionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  accordionSubtitle: {
    fontSize: 14,
    marginTop: 2,
  },
  accordionChevron: {
    fontSize: 14,
  },
  accordionContent: {
    marginTop: 8,
    paddingTop: 12,
  },
  loadingContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    gap: 8,
  },
  loadingText: {
    fontSize: 16,
  },
  errorContainer: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
  },
  
  // Section header (kept for reference, not used in accordion)
  sectionHeader: {
    marginBottom: 16,
  },
  sectionHeaderTitle: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1.5,
    marginBottom: 4,
  },
  sectionHeaderMeta: {
    fontSize: 14,
  },
  
  // Intro
  introText: {
    fontSize: 16,
    lineHeight: 28,
    marginBottom: 16,
  },
  
  // Gates list
  gatesList: {
    gap: 12,
  },
  
  // Gate card
  gateCard: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    overflow: 'hidden',
  },
  
  // Gate header
  gateHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 14,
  },
  gateHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  gateNumberBadge: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.05)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  gateNumber: {
    fontSize: 16,
    fontWeight: '600',
  },
  gateHeaderInfo: {
    flex: 1,
  },
  gateName: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 2,
  },
  gateCenter: {
    fontSize: 14,
  },
  expandIcon: {
    fontSize: 16,
    marginLeft: 8,
  },
  
  // Themes row
  themesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: 8,
  },
  themeTag: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  
  // Expanded content
  expandedContent: {
    padding: 14,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  
  // Section blocks
  sectionBlock: {
    marginBottom: 18,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  sectionBody: {
    fontSize: 16,
    lineHeight: 26,
  },
  
  // Experiments
  experimentRow: {
    flexDirection: 'row',
    marginBottom: 14,
  },
  experimentBullet: {
    fontSize: 16,
    marginRight: 8,
    marginTop: 1,
  },
  experimentText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 28,
  },
  
  // Remember block
  rememberBlock: {
    borderRadius: 8,
    padding: 12,
    borderLeftWidth: 2,
    marginBottom: 16,
  },
  rememberLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  rememberText: {
    fontSize: 16,
    lineHeight: 28,
    fontStyle: 'italic',
  },
  
  // Gene Keys Bridge
  geneKeysBridge: {
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  bridgeLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 14,
  },
  bridgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  bridgeItem: {
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  bridgeType: {
    fontSize: 14,
    marginBottom: 2,
  },
  bridgeValue: {
    fontSize: 16,
    fontWeight: '500',
  },
  bridgeArrow: {
    fontSize: 16,
    paddingHorizontal: 4,
  },
  
  // Reflect button container
  reflectContainer: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center',
  },
});
