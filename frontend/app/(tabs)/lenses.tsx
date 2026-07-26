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
import { useTheme } from '../../contexts/ThemeContext';
import { useForumContext } from '../../contexts/ForumContext';
import { Colors } from '../../constants/colors';
import { fontFamily } from '../../theme/tokens';
import { useAppStore } from '../../store';
import ChatBot from '../../components/ChatBot';
import { ForumContextBanner } from '../../components/ForumContextBanner';
import { getLenses } from '../../services/api';
// Removed Ionicons - using text-based alternatives for web compatibility

// =============================================================================
// FEATURE FLAGS
// =============================================================================
// Consciousness lens is not sufficiently differentiated/personalized yet.
// It will return as a tone/governor layer or behavior-inferred meta layer.
const FEATURE_CONSCIOUSNESS_LENS = false;

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
  // Consciousness lens disabled - will return as meta layer
  ...(FEATURE_CONSCIOUSNESS_LENS ? { 'Levels of Consciousness': 'consciousness' } : {}),
  'Enneagram': 'enneagram',
  'BaZi': 'bazi',
};

export default function LensesScreen() {
  const { theme, isDark } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const [lenses, setLenses] = useState<Lens[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadLenses();
  }, []);

  const loadLenses = async () => {
    setIsLoading(true);
    try {
      const data = await getLenses();
      // Filter out Consciousness lens if feature flag is disabled
      const filteredLenses = FEATURE_CONSCIOUSNESS_LENS 
        ? data.lenses 
        : data.lenses.filter((lens: Lens) => lens.name !== 'Levels of Consciousness');
      setLenses(filteredLenses);
    } catch (err) {
      console.error('Load lenses error:', err);
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

  if (!user) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.centered}>
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>No user found</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <ForumContextBanner />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.title, { color: theme.text }]}>Your Lenses</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            {/* Session-1 fix (audit §3a): count was hardcoded "Four" while
                five lenses render (Astrology / Human Design / Numerology /
                Enneagram / BaZi). Compute from the actual rendered list so
                the header can never drift again.
                build_marker: lens-library-dynamic-count-v1 */}
            {(() => {
              const NUMS = ['Zero','One','Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten'];
              const n = lenses.length;
              const noun = NUMS[n] || String(n);
              return `${noun} perspectives for understanding yourself. Each offers a different way of seeing, not a definition of who you are.`;
            })()}
          </Text>
        </View>

        {/* Loading State */}
        {isLoading ? (
          <View style={styles.centered}>
            <ActivityIndicator size="large" color={theme.textSecondary} />
          </View>
        ) : (
          <View style={styles.lensesContainer}>
            {lenses.map((lens, index) => (
              <View key={index} style={[styles.lensCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
                <Text style={[styles.lensName, { color: theme.text }]}>{lens.name}</Text>
                <Text style={[styles.lensDescription, { color: theme.textSecondary }]}>{lens.description}</Text>
                
                <View style={styles.infoSection}>
                  <View style={styles.infoRow}>
                    <Text style={{ fontSize: 16, color: theme.textSecondary }}>✓</Text>
                    <Text style={[styles.infoLabel, { color: theme.textSecondary }]}>Helps with:</Text>
                  </View>
                  <Text style={[styles.infoText, { color: theme.textTertiary }]}>{lens.helps_with}</Text>
                </View>

                <View style={styles.infoSection}>
                  <View style={styles.infoRow}>
                    <Text style={{ fontSize: 16, color: theme.textTertiary }}>✗</Text>
                    <Text style={[styles.infoLabel, { color: theme.textTertiary }]}>Does not:</Text>
                  </View>
                  <Text style={[styles.infoText, { color: theme.textTertiary }]}>{lens.does_not}</Text>
                </View>

                <TouchableOpacity
                  style={[styles.viewButton, { backgroundColor: theme.buttonPrimaryBg }]}
                  onPress={() => handleViewSummary(lens.name)}
                >
                  <Text style={[styles.viewButtonText, { color: theme.buttonPrimaryText }]}>View Summary</Text>
                  <Text style={{ fontSize: 16, color: theme.buttonPrimaryText }}>→</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}

        {/* Footer Note */}
        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: theme.textTertiary }]}>
            These frameworks are tools for reflection, not rigid definitions. They work best
            when held lightly.
          </Text>
        </View>

        <View style={styles.spacer} />
      </ScrollView>

      {/* Persistent Chatbot */}
      <ChatBot userId={user.id} />
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
  header: {
    marginBottom: 32,
  },
  title: {
    fontFamily: fontFamily.display,
    fontSize: 24,
    fontWeight: '400',
    letterSpacing: 0.3,
    color: Colors.text,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.textSecondary,
  },
  lensesContainer: {
    marginBottom: 24,
  },
  lensCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  lensName: {
    fontFamily: fontFamily.display,
    fontSize: 19,
    fontWeight: '400',
    letterSpacing: 0.3,
    color: Colors.text,
    marginBottom: 10,
  },
  lensDescription: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.textSecondary,
    marginBottom: 16,
  },
  infoSection: {
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  infoLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.textSecondary,
    marginLeft: 6,
  },
  infoText: {
    fontSize: 16,
    lineHeight: 32,
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
    fontSize: 16,
    fontWeight: '500',
    color: Colors.background,
  },
  footer: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 20,
  },
  footerText: {
    fontSize: 16,
    lineHeight: 32,
    color: Colors.textTertiary,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  errorText: {
    fontSize: 16,
    color: Colors.error,
  },
  spacer: {
    height: 60,
  },
});