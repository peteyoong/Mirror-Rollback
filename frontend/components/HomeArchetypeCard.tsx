/**
 * HomeArchetypeCard.tsx
 * 
 * Task 75: Unified Narrative Engine
 * 
 * Compact archetype teaser for the home screen.
 * Uses /api/pattern-archetype as the single source of truth.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useTheme } from '../contexts/ThemeContext';
import { useAppStore } from '../store';
import api from '../services/api';

// Types
interface ArchetypeNarrative {
  headline: string;
  summary: string;
  short_description: string;
  current_expression: string;
  reflection_question: string;
}

interface Archetype {
  id: string;
  name: string;
  icon: string;
  score: number;
  narrative: ArchetypeNarrative;
}

interface ArchetypeResponse {
  success: boolean;
  confidence: number;
  primary_archetype?: Archetype;
}

// Colors
const COLORS = {
  accent: '#9B8AC4',
  accentLight: 'rgba(155, 138, 196, 0.12)',
};

export default function HomeArchetypeCard() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  
  const [data, setData] = useState<ArchetypeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.id) {
      fetchArchetype();
    }
  }, [user?.id]);

  const fetchArchetype = async () => {
    if (!user?.id) return;
    
    try {
      setLoading(true);
      const response = await api.get<ArchetypeResponse>(`/pattern-archetype/${user.id}`);
      setData(response.data);
    } catch (err) {
      console.log('[HomeArchetypeCard] Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color={COLORS.accent} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Reading patterns...
          </Text>
        </View>
      </View>
    );
  }

  // No data state
  if (!data || !data.primary_archetype) {
    return null;
  }

  const archetype = data.primary_archetype;
  const narrative = archetype.narrative;

  return (
    <TouchableOpacity
      style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}
      onPress={() => router.push('/(tabs)/patterns')}
      activeOpacity={0.7}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={[styles.iconBadge, { backgroundColor: COLORS.accentLight }]}>
          <Text style={styles.archetypeIcon}>{archetype.icon}</Text>
        </View>
        <View style={styles.headerText}>
          <Text style={[styles.labelText, { color: theme.textTertiary }]}>
            YOUR PATTERN
          </Text>
          <Text style={[styles.archetypeName, { color: theme.text }]}>
            {archetype.name}
          </Text>
        </View>
        <Ionicons name="chevron-forward" size={18} color={theme.textTertiary} />
      </View>

      {/* Current Expression - Direct, behavioral language */}
      <Text style={[styles.currentExpression, { color: theme.textSecondary }]}>
        {narrative.current_expression}
      </Text>

      {/* Subtle reflection hint */}
      <View style={styles.reflectionHint}>
        <Ionicons name="help-circle-outline" size={14} color={COLORS.accent} />
        <Text style={[styles.reflectionText, { color: theme.textTertiary }]} numberOfLines={1}>
          {narrative.reflection_question}
        </Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
    marginBottom: 16,
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 8,
  },
  loadingText: {
    fontSize: 13,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  iconBadge: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  archetypeIcon: {
    fontSize: 18,
  },
  headerText: {
    flex: 1,
  },
  labelText: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  archetypeName: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  currentExpression: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 10,
  },
  reflectionHint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255, 255, 255, 0.08)',
  },
  reflectionText: {
    fontSize: 12,
    fontStyle: 'italic',
    flex: 1,
  },
});
