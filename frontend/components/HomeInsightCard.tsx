/**
 * HomeInsightCard.tsx
 * 
 * New structured daily insight for Home Screen.
 * Replaces old keystone paragraph format.
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';

// Types
export interface DailyInsight {
  success: boolean;
  date: string;
  pattern_id: string;
  title: string;
  what_happening: string;
  why_feels: string;
  watch_for: string;
  better_move: string;
  interrupt: string;
  phase?: string;
  phase_description?: string;
  confidence: string;
}

interface Props {
  insight: DailyInsight | null;
  isLoading: boolean;
}

// Phase colors and icons
const PHASE_CONFIG: Record<string, { color: string; icon: string }> = {
  'INITIATION': { color: '#85C88A', icon: 'rocket-outline' },
  'BUILD_UP': { color: '#6BB5E0', icon: 'trending-up-outline' },
  'FRICTION': { color: '#E8A87C', icon: 'warning-outline' },
  'RECOVERY': { color: '#9B8AC4', icon: 'leaf-outline' },
};

// Section component for consistent styling
const InsightSection = ({ 
  icon, 
  label, 
  content, 
  theme,
  accentColor 
}: { 
  icon: string; 
  label: string; 
  content: string; 
  theme: any;
  accentColor?: string;
}) => (
  <View style={styles.section}>
    <View style={styles.sectionHeader}>
      <Ionicons 
        name={icon as any} 
        size={14} 
        color={accentColor || theme.textTertiary} 
      />
      <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
        {label}
      </Text>
    </View>
    <Text style={[styles.sectionContent, { color: theme.text }]}>
      {content}
    </Text>
  </View>
);

export default function HomeInsightCard({ insight, isLoading }: Props) {
  const { theme } = useTheme();

  // Loading state
  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color="#9B8AC4" />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Reading patterns...
          </Text>
        </View>
      </View>
    );
  }

  // No data state
  if (!insight) {
    return null;
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Phase Indicator (if available) */}
      {insight.phase && (
        <View style={[
          styles.phaseIndicator, 
          { backgroundColor: `${PHASE_CONFIG[insight.phase]?.color || theme.textTertiary}15` }
        ]}>
          <Ionicons 
            name={PHASE_CONFIG[insight.phase]?.icon as any || 'ellipse-outline'} 
            size={12} 
            color={PHASE_CONFIG[insight.phase]?.color || theme.textTertiary} 
          />
          <Text style={[
            styles.phaseText, 
            { color: PHASE_CONFIG[insight.phase]?.color || theme.textTertiary }
          ]}>
            {insight.phase_description || insight.phase}
          </Text>
        </View>
      )}

      {/* Title */}
      <Text style={[styles.title, { color: theme.text }]}>
        {insight.title}
      </Text>

      {/* What's Happening */}
      <InsightSection
        icon="analytics-outline"
        label="WHAT'S HAPPENING"
        content={insight.what_happening}
        theme={theme}
      />

      {/* Why It Feels This Way */}
      <InsightSection
        icon="heart-outline"
        label="WHY IT FEELS THIS WAY"
        content={insight.why_feels}
        theme={theme}
      />

      {/* Watch For */}
      <InsightSection
        icon="eye-outline"
        label="WATCH FOR"
        content={insight.watch_for}
        theme={theme}
        accentColor="#E8A87C"
      />

      {/* Better Move */}
      <InsightSection
        icon="arrow-forward-outline"
        label="BETTER MOVE"
        content={insight.better_move}
        theme={theme}
        accentColor="#85C88A"
      />

      {/* Interrupt */}
      <InsightSection
        icon="pause-outline"
        label="INTERRUPT"
        content={insight.interrupt}
        theme={theme}
        accentColor="#9B8AC4"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
    marginBottom: 16,
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 20,
  },
  loadingText: {
    fontSize: 14,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    letterSpacing: -0.5,
    marginBottom: 20,
  },
  section: {
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.8,
  },
  sectionContent: {
    fontSize: 15,
    lineHeight: 22,
  },
});
