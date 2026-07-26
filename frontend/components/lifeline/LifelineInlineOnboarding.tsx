/**
 * LifelineInlineOnboarding
 * 
 * Inline onboarding state that renders INSIDE the Life tab structure.
 * This replaces full-screen onboarding so that tabs remain visible.
 * 
 * Contains:
 * - Emotional hook copy
 * - Pattern teaser
 * - Start My Lifeline button
 * - Import a Lifeline button
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';

interface LifelineInlineOnboardingProps {
  onStartLifeline: () => void;
  tabContext?: 'lifeline' | 'relationships' | 'work' | 'self';
}

// Tab-specific copy
const TAB_COPY = {
  lifeline: {
    title: 'Your Lifeline begins here',
    description: 'Add key moments from your past—turning points, beginnings, endings, changes.',
    hint: 'Start with five moments to reveal your pattern.',
  },
  relationships: {
    title: 'Map your relationship patterns',
    description: 'Add relationship milestones—meetings, commitments, separations, reconciliations.',
    hint: 'See how your connections mirror your chart.',
  },
  work: {
    title: 'Track your work journey',
    description: 'Add career moments—first jobs, promotions, pivots, projects that changed you.',
    hint: 'Discover the cycles in your professional life.',
  },
  self: {
    title: 'Chart your inner growth',
    description: 'Add personal milestones—realizations, challenges overcome, identity shifts.',
    hint: 'See how your inner life maps to cosmic patterns.',
  },
};

export default function LifelineInlineOnboarding({ 
  onStartLifeline, 
  tabContext = 'lifeline' 
}: LifelineInlineOnboardingProps) {
  const { theme } = useTheme();
  const router = useRouter();
  
  const copy = TAB_COPY[tabContext];

  return (
    <ScrollView 
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {/* Main Emotional Hook */}
      <View style={styles.hookSection}>
        <Text style={[styles.hookLine, { color: theme.text }]}>
          Your chart shows potential.
        </Text>
        <Text style={[styles.hookLine, { color: theme.text }]}>
          Your life reveals the pattern.
        </Text>
      </View>

      {/* Tab-specific intro card */}
      <View style={[styles.introCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.introTitle, { color: theme.text }]}>
          {copy.title}
        </Text>
        <Text style={[styles.introDescription, { color: theme.textSecondary }]}>
          {copy.description}
        </Text>
        <Text style={[styles.introHint, { color: theme.textTertiary }]}>
          {copy.hint}
        </Text>
      </View>

      {/* Pattern Teaser (compact version) */}
      <View style={[styles.teaserCard, { backgroundColor: `${theme.accent}08`, borderColor: `${theme.accent}30` }]}>
        <Text style={[styles.teaserTitle, { color: theme.text }]}>
          A pattern may already exist
        </Text>
        
        {/* Pattern Arc Visual */}
        <View style={styles.patternArc}>
          <View style={[styles.arcNode, { backgroundColor: `${theme.accent}15`, borderColor: theme.accent }]}>
            <Text style={[styles.arcNodeText, { color: theme.accent }]}>Start</Text>
          </View>
          <View style={[styles.arcConnector, { backgroundColor: `${theme.accent}40` }]} />
          <View style={[styles.arcNode, { backgroundColor: `${theme.accent}15`, borderColor: theme.accent }]}>
            <Text style={[styles.arcNodeText, { color: theme.accent }]}>Shift</Text>
          </View>
          <View style={[styles.arcConnector, { backgroundColor: `${theme.accent}40` }]} />
          <View style={[styles.arcNode, { backgroundColor: `${theme.accent}15`, borderColor: theme.accent }]}>
            <Text style={[styles.arcNodeText, { color: theme.accent }]}>Change</Text>
          </View>
        </View>
        
        <Text style={[styles.teaserBody, { color: theme.textSecondary }]}>
          Add five turning points to begin revealing it.
        </Text>
      </View>

      {/* Actions */}
      <View style={styles.actionsContainer}>
        <TouchableOpacity
          style={[styles.primaryButton, { backgroundColor: theme.accent }]}
          onPress={onStartLifeline}
          activeOpacity={0.8}
        >
          <Text style={styles.primaryButtonText}>Start My Lifeline</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.secondaryButton, { borderColor: theme.border }]}
          onPress={() => router.push('/lifeline-upload')}
          activeOpacity={0.7}
        >
          <Text style={[styles.secondaryButtonText, { color: theme.text }]}>
            Import a Lifeline
          </Text>
        </TouchableOpacity>
        
        <Text style={[styles.importHint, { color: theme.textTertiary }]}>
          PowerPoint, spreadsheet, PDF, or image
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  
  // Hook section
  hookSection: {
    marginBottom: 24,
    alignItems: 'center',
  },
  hookLine: {
    fontSize: 22,
    fontWeight: '500',
    lineHeight: 32,
    textAlign: 'center',
    marginBottom: 8,
  },
  
  // Intro card
  introCard: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 20,
    marginBottom: 16,
    alignItems: 'center',
  },
  introTitle: {
    fontSize: 17,
    fontWeight: '500',
    marginBottom: 10,
    textAlign: 'center',
  },
  introDescription: {
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
    marginBottom: 8,
  },
  introHint: {
    fontSize: 13,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  
  // Teaser card
  teaserCard: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 20,
    marginBottom: 24,
    alignItems: 'center',
  },
  teaserTitle: {
    fontSize: 15,
    fontWeight: '500',
    textAlign: 'center',
    marginBottom: 16,
  },
  teaserBody: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    fontStyle: 'italic',
  },
  
  // Pattern Arc
  patternArc: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  arcNode: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 14,
    borderWidth: 1,
  },
  arcNodeText: {
    fontSize: 11,
    fontWeight: '500',
  },
  arcConnector: {
    width: 14,
    height: 2,
    marginHorizontal: 2,
  },
  
  // Actions
  actionsContainer: {
    gap: 12,
  },
  primaryButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '500',
  },
  secondaryButton: {
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
  },
  secondaryButtonText: {
    fontSize: 15,
    fontWeight: '500',
  },
  importHint: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 4,
  },
});
