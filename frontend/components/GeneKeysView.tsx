import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';

interface GeneKeyInterpretation {
  gene_key: number;
  line: number;
  shadow: string;
  gift: string;
  siddhi: string;
  available: boolean;
  message?: string;
}

interface Props {
  gate: number;
  line: number;
}

export default function GeneKeysView({ gate, line }: Props) {
  const { theme } = useTheme();
  const [data, setData] = useState<GeneKeyInterpretation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadGeneKeyData();
  }, [gate, line]);

  const loadGeneKeyData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get(`/gene-keys/${gate}/${line}`);
      setData(response.data);
    } catch (err: any) {
      console.error('Gene Keys fetch error:', err);
      setError('Unable to load Gene Key interpretation.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.textTertiary} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading Gene Key...
        </Text>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={styles.errorContainer}>
        <Text style={{ fontSize: 28, color: theme.textTertiary }}>⚠</Text>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error || 'Unable to load Gene Key.'}
        </Text>
      </View>
    );
  }

  // Handle unavailable Gene Keys
  if (!data.available) {
    return (
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        <View style={[styles.headerCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.geneKeyTitle, { color: theme.text }]}>
            Gene Key {data.gene_key}.{data.line}
          </Text>
          <Text style={[styles.unavailableText, { color: theme.textSecondary }]}>
            {data.message}
          </Text>
        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
    >
      {/* Header with Gene Key number */}
      <View style={[styles.headerCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.geneKeyLabel, { color: theme.textTertiary }]}>GENE KEY</Text>
        <Text style={[styles.geneKeyTitle, { color: theme.text }]}>
          {data.gene_key}.{data.line}
        </Text>
      </View>

      {/* Shadow / Gift / Siddhi Spectrum */}
      <View style={[styles.spectrumCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.spectrumRow}>
          <View style={styles.spectrumItem}>
            <Text style={[styles.spectrumLabel, { color: theme.textTertiary }]}>SHADOW</Text>
            <Text style={[styles.spectrumValue, { color: theme.text }]}>{data.shadow}</Text>
          </View>
          <Text style={[styles.spectrumArrow, { color: theme.textTertiary }]}>→</Text>
          <View style={styles.spectrumItem}>
            <Text style={[styles.spectrumLabel, { color: theme.accent }]}>GIFT</Text>
            <Text style={[styles.spectrumValue, { color: theme.text }]}>{data.gift}</Text>
          </View>
          <Text style={[styles.spectrumArrow, { color: theme.textTertiary }]}>→</Text>
          <View style={styles.spectrumItem}>
            <Text style={[styles.spectrumLabel, { color: theme.textTertiary }]}>SIDDHI</Text>
            <Text style={[styles.spectrumValue, { color: theme.text }]}>{data.siddhi}</Text>
          </View>
        </View>
      </View>

      {/* What This Means */}
      <View style={[styles.sectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>What This Means</Text>
        <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
          This Gene Key represents a spectrum of consciousness. The Shadow ({data.shadow}) is not 
          "bad"—it's the unconscious pattern that creates tension. The Gift ({data.gift}) emerges when 
          you bring awareness to the Shadow. The Siddhi ({data.siddhi}) is the highest expression, 
          available in moments of deep presence.
        </Text>
      </View>

      {/* Your Challenge */}
      <View style={[styles.sectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>Your Challenge</Text>
        <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
          Notice when {data.shadow.toLowerCase()} shows up in your life. This isn't about 
          fixing or changing anything—just witnessing. The Shadow is often most visible in 
          moments of stress, reactivity, or when you feel triggered.
        </Text>
      </View>

      {/* Your Higher Expression */}
      <View style={[styles.sectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>Your Higher Expression</Text>
        <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
          {data.gift} is already within you—it's not something to achieve. It naturally 
          emerges when you embrace the Shadow with compassion rather than resistance. 
          This is the gift you bring to the world when you're living authentically.
        </Text>
      </View>

      {/* Ways to Experiment */}
      <View style={[styles.sectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>Ways to Experiment</Text>
        <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
          When you notice the Shadow pattern arising, pause. Take a breath. Ask yourself: 
          "What would {data.gift.toLowerCase()} look like right now?" This isn't about forcing 
          a change—it's about creating space for a different response to emerge naturally.
        </Text>
      </View>

      {/* Remember */}
      <View style={[styles.rememberCard, { backgroundColor: theme.surface, borderLeftColor: theme.accent }]}>
        <Text style={[styles.rememberLabel, { color: theme.textTertiary }]}>REMEMBER</Text>
        <Text style={[styles.rememberText, { color: theme.text }]}>
          Gene Keys is not about becoming something you're not. It's about recognizing the 
          full spectrum of who you already are. The journey from {data.shadow} to {data.gift} 
          to {data.siddhi} is not linear—it's an unfolding awareness.
        </Text>
      </View>

      {/* Footer */}
      <Text style={[styles.footer, { color: theme.textTertiary }]}>
        This is one lens for understanding patterns, not a definition of who you are.
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
  headerCard: {
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  geneKeyLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1.5,
    marginBottom: 4,
  },
  geneKeyTitle: {
    fontSize: 28,
    fontWeight: '600',
  },
  unavailableText: {
    fontSize: 14,
    textAlign: 'center',
    marginTop: 8,
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
