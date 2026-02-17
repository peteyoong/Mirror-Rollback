import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import ChatBot from '../../components/ChatBot';
import { getLenses } from '../../services/api';
import { Ionicons } from '@expo/vector-icons';

interface Lens {
  name: string;
  description: string;
  helps_with: string;
  does_not: string;
  icon: string;
}

const LENS_KEYS: { [key: string]: string } = {
  'True Sidereal Astrology': 'astrology',
  'Human Design': 'human_design',
  'Numerology': 'numerology',
  'Levels of Consciousness': 'consciousness',
  'Enneagram': 'enneagram',
};

// STATIC FALLBACK LENSES - Always render even if API fails
const STATIC_LENSES: Lens[] = [
  {
    name: 'Enneagram',
    description: 'A map of nine personality patterns and their interconnections.',
    helps_with: 'Understanding core motivations and growth paths',
    does_not: 'Define or limit who you can become',
    icon: '🔷',
  },
  {
    name: 'Human Design',
    description: 'A synthesis of ancient wisdom and modern science for self-understanding.',
    helps_with: 'Discovering your natural energy patterns and decision-making style',
    does_not: 'Predict your future or dictate your choices',
    icon: '⬡',
  },
  {
    name: 'True Sidereal Astrology',
    description: 'Celestial positions at birth as a lens for self-reflection.',
    helps_with: 'Exploring archetypal themes and cycles in your life',
    does_not: 'Determine your fate or limit your potential',
    icon: '✦',
  },
  {
    name: 'Numerology',
    description: 'Patterns in numbers as a framework for understanding life themes.',
    helps_with: 'Reflecting on personal cycles and life path themes',
    does_not: 'Predict specific events or outcomes',
    icon: '𝟙',
  },
];

export default function LensesScreen() {
  const { user } = useAppStore();
  const router = useRouter();
  const [lenses, setLenses] = useState<Lens[]>(STATIC_LENSES); // Start with static
  const [isLoading, setIsLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    loadLenses();
  }, []);

  const loadLenses = async () => {
    setIsLoading(true);
    setFetchError(null);
    try {
      const data = await getLenses();
      if (data?.lenses?.length > 0) {
        setLenses(data.lenses);
      }
      // If API returns empty, keep static lenses
    } catch (err: any) {
      console.error('Load lenses error:', err);
      setFetchError(err?.message || 'Failed to load');
      // Keep static lenses on error
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewSummary = (lensName: string) => {
    const lensKey = LENS_KEYS[lensName];
    if (lensKey === 'enneagram') {
      // Enneagram has its own intro/assessment flow
      router.push('/enneagram');
    } else if (lensKey) {
      router.push(`/lenses/${lensKey}`);
    }
  };

  // ALWAYS RENDER - even without user
  const displayLenses = lenses.length > 0 ? lenses : STATIC_LENSES;

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Your Lenses</Text>
          <Text style={styles.subtitle}>
            Four perspectives for understanding yourself. Each offers a different way of
            seeing, not a definition of who you are.
          </Text>
        </View>

        {/* ALWAYS RENDER LENS CARDS - Loading indicator is overlay only */}
        <View style={styles.lensesContainer}>
          {isLoading && (
            <View style={styles.loadingOverlay}>
              <ActivityIndicator size="small" color={Colors.textSecondary} />
            </View>
          )}
          {displayLenses.map((lens, index) => (
            <View key={index} style={styles.lensCard}>
              <Text style={styles.lensName}>{lens.name}</Text>
              <Text style={styles.lensDescription}>{lens.description}</Text>
              
              <View style={styles.infoSection}>
                <View style={styles.infoRow}>
                  <Ionicons name="checkmark-circle-outline" size={16} color={Colors.textSecondary} />
                  <Text style={styles.infoLabel}>Helps with:</Text>
                </View>
                <Text style={styles.infoText}>{lens.helps_with}</Text>
              </View>

              <View style={styles.infoSection}>
                <View style={styles.infoRow}>
                  <Ionicons name="close-circle-outline" size={16} color={Colors.textTertiary} />
                  <Text style={styles.infoLabel}>Does not:</Text>
                </View>
                <Text style={styles.infoText}>{lens.does_not}</Text>
              </View>

              <TouchableOpacity
                style={styles.viewButton}
                onPress={() => handleViewSummary(lens.name)}
              >
                <Text style={styles.viewButtonText}>Explore</Text>
                <Ionicons name="arrow-forward" size={16} color={Colors.background} />
              </TouchableOpacity>
            </View>
          ))}
        </View>

        {/* Footer Note */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            These frameworks are tools for reflection, not rigid definitions. They work best
            when held lightly.
          </Text>
        </View>

        <View style={styles.spacer} />
      </ScrollView>

      {/* Persistent Chatbot - only if user exists */}
      {user && <ChatBot userId={user.id} />}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    padding: 24,
    paddingBottom: 100,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 60,
  },
  loadingOverlay: {
    position: 'absolute',
    top: 10,
    right: 10,
    zIndex: 10,
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
  },
  lensesContainer: {
    marginBottom: 24,
    position: 'relative',
  },
  lensCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  lensName: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 12,
  },
  lensDescription: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    marginBottom: 16,
  },
  infoSection: {
    marginBottom: 12,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  infoLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginLeft: 6,
  },
  infoText: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.textTertiary,
    marginLeft: 22,
  },
  viewButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.text,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 20,
    marginTop: 16,
    gap: 6,
  },
  viewButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.background,
  },
  footer: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 20,
  },
  footerText: {
    fontSize: 13,
    lineHeight: 20,
    color: Colors.textTertiary,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  errorText: {
    fontSize: 14,
    color: Colors.error,
  },
  spacer: {
    height: 60,
  },
});