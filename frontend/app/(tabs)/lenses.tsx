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
      setLenses(data.lenses);
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
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.centered}>
          <Text style={styles.errorText}>No user found</Text>
        </View>
      </SafeAreaView>
    );
  }

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

        {/* Loading State */}
        {isLoading ? (
          <View style={styles.centered}>
            <ActivityIndicator size="large" color={Colors.textSecondary} />
          </View>
        ) : (
          <View style={styles.lensesContainer}>
            {lenses.map((lens, index) => (
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
                  <Text style={styles.viewButtonText}>View Summary</Text>
                  <Ionicons name="arrow-forward" size={16} color={Colors.background} />
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}

        {/* Footer Note */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
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