import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';

interface SphereData {
  sphere_name: string;
  gene_key: number;
  line: number;
  shadow: string;
  gift: string;
  siddhi: string;
  what_this_means: string;
  your_challenge: string;
  your_higher_expression: string;
  practical_tips: string;
  remember: string;
}

interface SequenceData {
  sequence_name: string;
  spheres: SphereData[];
}

interface Props {
  userId: string;
}

// Sequence descriptions for clarity
const SEQUENCE_INFO = {
  "Activation Sequence": {
    description: "Self-discovery & core stability",
    intro: "These four spheres reveal themes in how you develop as an individual."
  },
  "Venus Sequence": {
    description: "Relationships & emotional patterns",
    intro: "These five spheres reflect patterns in how you connect with others."
  },
  "Pearl Sequence": {
    description: "Vocation, contribution & prosperity",
    intro: "These four spheres highlight themes in work and material life."
  }
};

export default function GeneKeysView({ userId }: Props) {
  const { theme } = useTheme();
  const [activationSequence, setActivationSequence] = useState<SequenceData | null>(null);
  const [venusSequence, setVenusSequence] = useState<SequenceData | null>(null);
  const [pearlSequence, setPearlSequence] = useState<SequenceData | null>(null);
  const [selectedSphere, setSelectedSphere] = useState<SphereData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [howToUseExpanded, setHowToUseExpanded] = useState(false);

  useEffect(() => {
    loadSequences();
  }, [userId]);

  const loadSequences = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [activationRes, venusRes, pearlRes] = await Promise.all([
        api.get(`/gene-keys/activation-sequence/${userId}`),
        api.get(`/gene-keys/venus-sequence/${userId}`),
        api.get(`/gene-keys/pearl-sequence/${userId}`)
      ]);
      
      setActivationSequence(activationRes.data);
      setVenusSequence(venusRes.data);
      setPearlSequence(pearlRes.data);
      
      if (activationRes.data.spheres?.length > 0) {
        setSelectedSphere(activationRes.data.spheres[0]);
      }
    } catch (err: any) {
      console.error('Gene Keys fetch error:', err);
      setError(err.response?.data?.detail || 'Unable to load Gene Keys.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.textTertiary} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading Gene Keys...
        </Text>
      </View>
    );
  }

  if (error || !activationSequence) {
    return (
      <View style={styles.errorContainer}>
        <Text style={{ fontSize: 28, color: theme.textTertiary }}>⚠</Text>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error || 'Unable to load Gene Keys.'}
        </Text>
      </View>
    );
  }

  const renderSphereCard = (sphere: SphereData, isSelected: boolean) => {
    return (
      <TouchableOpacity
        key={sphere.sphere_name}
        style={[
          styles.sphereCard,
          { 
            backgroundColor: isSelected ? theme.accent + '15' : theme.surface,
            borderColor: isSelected ? theme.accent : theme.border,
            borderWidth: isSelected ? 2 : 1,
          }
        ]}
        onPress={() => setSelectedSphere(sphere)}
        activeOpacity={0.7}
      >
        <Text style={[
          styles.sphereLabel, 
          { color: isSelected ? theme.accent : theme.textTertiary }
        ]}>
          {sphere.sphere_name.toUpperCase()}
        </Text>
        <Text style={[styles.sphereGeneKey, { color: theme.text }]}>
          {sphere.gene_key}.{sphere.line}
        </Text>
        <View style={styles.sphereSpectrum}>
          <Text style={[styles.sphereShadow, { color: theme.textTertiary }]} numberOfLines={1}>
            {sphere.shadow}
          </Text>
          <Text style={[styles.sphereArrow, { color: theme.textTertiary }]}>→</Text>
          <Text style={[styles.sphereGift, { color: theme.accent }]} numberOfLines={1}>
            {sphere.gift}
          </Text>
        </View>
      </TouchableOpacity>
    );
  };

  const renderSequenceSection = (sequence: SequenceData) => {
    const info = SEQUENCE_INFO[sequence.sequence_name as keyof typeof SEQUENCE_INFO] || {
      description: "",
      intro: ""
    };
    
    return (
      <View style={styles.sequenceSection}>
        <View style={styles.sequenceHeader}>
          <Text style={[styles.sequenceTitle, { color: theme.text }]}>
            {sequence.sequence_name}
          </Text>
          <Text style={[styles.sequenceDescription, { color: theme.textTertiary }]}>
            {info.description}
          </Text>
        </View>
        
        <View style={styles.sphereGrid}>
          {sequence.spheres.map((sphere) => 
            renderSphereCard(sphere, selectedSphere?.sphere_name === sphere.sphere_name)
          )}
        </View>
      </View>
    );
  };

  // Helper to render practical tips with proper formatting
  const renderPracticalTips = (tips: string) => {
    const lines = tips.split('\n').filter(line => line.trim());
    return (
      <View style={styles.tipsContainer}>
        {lines.map((line, index) => (
          <Text key={index} style={[styles.tipLine, { color: theme.textSecondary }]}>
            {line}
          </Text>
        ))}
      </View>
    );
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
    >
      {/* Intro Block */}
      <View style={styles.introBlock}>
        <Text style={[styles.introTitle, { color: theme.text }]}>
          Gene Keys
        </Text>
        <Text style={[styles.introSubtext, { color: theme.textTertiary }]}>
          A contemplative layer within Human Design.
        </Text>
        <Text style={[styles.introBody, { color: theme.textSecondary }]}>
          Gene Keys explores the deeper potential inside the same gates in your Human Design chart.
        </Text>
        <Text style={[styles.introBody, { color: theme.textSecondary, marginTop: 12 }]}>
          Each sphere can show up in three ways:{'\n'}
          • Shadow — when a pattern feels contracted{'\n'}
          • Gift — when awareness opens{'\n'}
          • Siddhi — the highest expression of the same energy
        </Text>
        <Text style={[styles.introBody, { color: theme.textSecondary, marginTop: 12 }]}>
          You don't need to force change here. Start by noticing which patterns feel familiar.
        </Text>
        
        {/* Collapsible How to Use */}
        <TouchableOpacity
          style={styles.howToUseHeader}
          onPress={() => setHowToUseExpanded(!howToUseExpanded)}
          activeOpacity={0.7}
        >
          <Text style={[styles.howToUseTitle, { color: theme.textTertiary }]}>
            How to use this lens
          </Text>
          <Text style={[styles.howToUseChevron, { color: theme.textTertiary }]}>
            {howToUseExpanded ? '▾' : '▸'}
          </Text>
        </TouchableOpacity>
        
        {howToUseExpanded && (
          <View style={styles.howToUseContent}>
            <Text style={[styles.howToUseItem, { color: theme.textSecondary }]}>
              • Start with the sphere that feels most alive right now.
            </Text>
            <Text style={[styles.howToUseItem, { color: theme.textSecondary }]}>
              • Read the challenge and higher expression slowly.
            </Text>
            <Text style={[styles.howToUseItem, { color: theme.textSecondary }]}>
              • Use the practical tips as experiments, not rules.
            </Text>
            <Text style={[styles.howToUseItem, { color: theme.textSecondary }]}>
              • Let the reflection question stay with you.
            </Text>
          </View>
        )}
      </View>

      {/* Sequences Overview */}
      {activationSequence && renderSequenceSection(activationSequence)}
      {venusSequence && renderSequenceSection(venusSequence)}
      {pearlSequence && renderSequenceSection(pearlSequence)}

      {/* Selected Sphere Detail */}
      {selectedSphere && (
        <View style={styles.detailSection}>
          {/* Divider */}
          <View style={[styles.divider, { backgroundColor: theme.border }]} />
          
          {/* Clean Title Block */}
          <View style={[styles.detailHeader, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.detailSphereLabel, { color: theme.accent }]}>
              {selectedSphere.sphere_name}
            </Text>
            <Text style={[styles.detailGeneKeyTitle, { color: theme.text }]}>
              Gene Key {selectedSphere.gene_key}.{selectedSphere.line}
            </Text>
            {/* Spectrum row */}
            <View style={styles.spectrumInline}>
              <Text style={[styles.spectrumText, { color: theme.textTertiary }]}>
                {selectedSphere.shadow}
              </Text>
              <Text style={[styles.spectrumArrowSmall, { color: theme.textTertiary }]}> → </Text>
              <Text style={[styles.spectrumText, { color: theme.accent }]}>
                {selectedSphere.gift}
              </Text>
              <Text style={[styles.spectrumArrowSmall, { color: theme.textTertiary }]}> → </Text>
              <Text style={[styles.spectrumText, { color: theme.textTertiary }]}>
                {selectedSphere.siddhi}
              </Text>
            </View>
          </View>

          {/* What This Means */}
          <View style={[styles.sectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>What This Means</Text>
            <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
              {selectedSphere.what_this_means}
            </Text>
          </View>

          {/* Your Challenge */}
          <View style={[styles.sectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>Your Challenge (Shadow Expression)</Text>
            <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
              {selectedSphere.your_challenge}
            </Text>
          </View>

          {/* Your Genius */}
          <View style={[styles.sectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>Your Genius (Higher Expression)</Text>
            <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
              {selectedSphere.your_higher_expression}
            </Text>
          </View>

          {/* Practical Tips */}
          <View style={[styles.sectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>Practical Tips</Text>
            {renderPracticalTips(selectedSphere.practical_tips)}
          </View>

          {/* Remember */}
          <View style={[styles.rememberCard, { backgroundColor: theme.surface, borderLeftColor: theme.accent }]}>
            <Text style={[styles.rememberLabel, { color: theme.textTertiary }]}>Remember</Text>
            <Text style={[styles.rememberText, { color: theme.text }]}>
              {selectedSphere.remember}
            </Text>
          </View>
        </View>
      )}

      {/* Footer */}
      <Text style={[styles.footer, { color: theme.textTertiary }]}>
        Gene Keys offers one lens for self-reflection—a starting point, not a final word.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 40,
  },
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
  },
  errorContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  
  // Sequence Section
  sequenceSection: {
    marginBottom: 20,
  },
  sequenceHeader: {
    marginBottom: 12,
  },
  sequenceTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 2,
  },
  sequenceDescription: {
    fontSize: 12,
    fontStyle: 'italic',
  },
  sphereGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  sphereCard: {
    width: '48%',
    borderRadius: 10,
    padding: 10,
    minHeight: 80,
  },
  sphereLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  sphereGeneKey: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 4,
  },
  sphereSpectrum: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  sphereShadow: {
    fontSize: 10,
    flex: 1,
  },
  sphereArrow: {
    fontSize: 9,
    opacity: 0.6,
  },
  sphereGift: {
    fontSize: 10,
    fontWeight: '500',
    flex: 1,
  },
  
  // Divider
  divider: {
    height: 1,
    marginVertical: 20,
    opacity: 0.5,
  },
  
  // Detail Section
  detailSection: {
    marginBottom: 16,
  },
  detailHeader: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
    alignItems: 'center',
  },
  detailSphereLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  detailGeneKeyTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 8,
  },
  spectrumInline: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  spectrumText: {
    fontSize: 12,
    fontWeight: '500',
  },
  spectrumArrowSmall: {
    fontSize: 11,
    opacity: 0.6,
  },
  sectionCard: {
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.3,
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  sectionBody: {
    fontSize: 14,
    lineHeight: 21,
  },
  tipsContainer: {
    gap: 6,
  },
  tipLine: {
    fontSize: 14,
    lineHeight: 20,
  },
  rememberCard: {
    borderRadius: 10,
    padding: 14,
    marginBottom: 16,
    borderLeftWidth: 3,
  },
  rememberLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
    textTransform: 'uppercase',
  },
  rememberText: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
  footer: {
    fontSize: 11,
    textAlign: 'center',
    fontStyle: 'italic',
    opacity: 0.7,
    marginTop: 8,
  },
});
