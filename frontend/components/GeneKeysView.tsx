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

export default function GeneKeysView({ userId }: Props) {
  const { theme } = useTheme();
  const [activationSequence, setActivationSequence] = useState<SequenceData | null>(null);
  const [venusSequence, setVenusSequence] = useState<SequenceData | null>(null);
  const [pearlSequence, setPearlSequence] = useState<SequenceData | null>(null);
  const [selectedSphere, setSelectedSphere] = useState<SphereData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSequences();
  }, [userId]);

  const loadSequences = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Load all three sequences in parallel
      const [activationRes, venusRes, pearlRes] = await Promise.all([
        api.get(`/gene-keys/activation-sequence/${userId}`),
        api.get(`/gene-keys/venus-sequence/${userId}`),
        api.get(`/gene-keys/pearl-sequence/${userId}`)
      ]);
      
      setActivationSequence(activationRes.data);
      setVenusSequence(venusRes.data);
      setPearlSequence(pearlRes.data);
      
      // Default to Life's Work (first sphere of Activation)
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
            backgroundColor: isSelected ? theme.accent + '20' : theme.surface,
            borderColor: isSelected ? theme.accent : theme.border 
          }
        ]}
        onPress={() => setSelectedSphere(sphere)}
        activeOpacity={0.7}
      >
        <Text style={[styles.sphereLabel, { color: theme.textTertiary }]}>
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

  const renderSequenceSection = (sequence: SequenceData, description: string) => (
    <View style={styles.sequenceSection}>
      <Text style={[styles.sequenceTitle, { color: theme.textTertiary }]}>
        {sequence.sequence_name.toUpperCase()}
      </Text>
      <Text style={[styles.sequenceSubtitle, { color: theme.textSecondary }]}>
        {description}
      </Text>
      
      <View style={styles.sphereGrid}>
        {sequence.spheres.map((sphere) => 
          renderSphereCard(sphere, selectedSphere?.sphere_name === sphere.sphere_name)
        )}
      </View>
    </View>
  );

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
    >
      {/* Activation Sequence */}
      {activationSequence && renderSequenceSection(
        activationSequence,
        "Your path of self-discovery"
      )}

      {/* Venus Sequence */}
      {venusSequence && renderSequenceSection(
        venusSequence,
        "Your path through relationships"
      )}

      {/* Pearl Sequence */}
      {pearlSequence && renderSequenceSection(
        pearlSequence,
        "Your path to prosperity"
      )}

      {/* Selected Sphere Detail */}
      {selectedSphere && (
        <View style={styles.detailSection}>
          {/* Header with Gene Key number */}
          <View style={[styles.detailHeader, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.detailSphereLabel, { color: theme.accent }]}>
              {selectedSphere.sphere_name}
            </Text>
            <Text style={[styles.detailGeneKeyLabel, { color: theme.textTertiary }]}>GENE KEY</Text>
            <Text style={[styles.detailGeneKeyTitle, { color: theme.text }]}>
              {selectedSphere.gene_key}.{selectedSphere.line}
            </Text>
          </View>

          {/* Shadow / Gift / Siddhi Spectrum */}
          <View style={[styles.spectrumCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <View style={styles.spectrumRow}>
              <View style={styles.spectrumItem}>
                <Text style={[styles.spectrumLabel, { color: theme.textTertiary }]}>SHADOW</Text>
                <Text style={[styles.spectrumValue, { color: theme.text }]}>{selectedSphere.shadow}</Text>
              </View>
              <Text style={[styles.spectrumArrow, { color: theme.textTertiary }]}>→</Text>
              <View style={styles.spectrumItem}>
                <Text style={[styles.spectrumLabel, { color: theme.accent }]}>GIFT</Text>
                <Text style={[styles.spectrumValue, { color: theme.text }]}>{selectedSphere.gift}</Text>
              </View>
              <Text style={[styles.spectrumArrow, { color: theme.textTertiary }]}>→</Text>
              <View style={styles.spectrumItem}>
                <Text style={[styles.spectrumLabel, { color: theme.textTertiary }]}>SIDDHI</Text>
                <Text style={[styles.spectrumValue, { color: theme.text }]}>{selectedSphere.siddhi}</Text>
              </View>
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
            <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
              {selectedSphere.practical_tips}
            </Text>
          </View>

          {/* Remember */}
          <View style={[styles.rememberCard, { backgroundColor: theme.surface, borderLeftColor: theme.accent }]}>
            <Text style={[styles.rememberLabel, { color: theme.textTertiary }]}>REMEMBER</Text>
            <Text style={[styles.rememberText, { color: theme.text }]}>
              {selectedSphere.remember}
            </Text>
          </View>
        </View>
      )}

      {/* Footer */}
      <Text style={[styles.footer, { color: theme.textTertiary }]}>
        Gene Keys is one lens for understanding patterns, not a definition of who you are.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
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
    marginBottom: 24,
  },
  sequenceTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.5,
    textAlign: 'center',
    marginBottom: 4,
  },
  sequenceSubtitle: {
    fontSize: 13,
    textAlign: 'center',
    marginBottom: 16,
  },
  sphereGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    justifyContent: 'space-between',
  },
  sphereCard: {
    width: '48%',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1.5,
  },
  sphereLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 4,
  },
  sphereGeneKey: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 6,
  },
  sphereSpectrum: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  sphereShadow: {
    fontSize: 11,
    flex: 1,
  },
  sphereArrow: {
    fontSize: 10,
  },
  sphereGift: {
    fontSize: 11,
    fontWeight: '500',
    flex: 1,
  },
  
  // Detail Section
  detailSection: {
    marginBottom: 20,
    marginTop: 8,
  },
  detailHeader: {
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  detailSphereLabel: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  detailGeneKeyLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1.5,
    marginBottom: 4,
  },
  detailGeneKeyTitle: {
    fontSize: 28,
    fontWeight: '600',
  },
  spectrumCard: {
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
  },
  spectrumRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  spectrumItem: {
    alignItems: 'center',
    flex: 1,
  },
  spectrumLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 4,
  },
  spectrumValue: {
    fontSize: 13,
    fontWeight: '500',
    textAlign: 'center',
  },
  spectrumArrow: {
    fontSize: 16,
    paddingHorizontal: 4,
  },
  sectionCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  sectionBody: {
    fontSize: 14,
    lineHeight: 22,
  },
  rememberCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    borderLeftWidth: 3,
    backgroundColor: 'rgba(255,255,255,0.02)',
  },
  rememberLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 8,
  },
  rememberText: {
    fontSize: 14,
    lineHeight: 22,
    fontStyle: 'italic',
  },
  footer: {
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
    opacity: 0.7,
  },
});
