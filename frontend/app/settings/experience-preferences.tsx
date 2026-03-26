/**
 * Experience Preferences Screen
 * 
 * Allows users to edit their MirrorProfile preferences
 * without retaking the full onboarding questionnaire.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useExperienceControls } from '../../hooks/useExperienceControls';
import ExperienceSummaryCard from '../../components/ExperienceSummaryCard';
import {
  PrimaryGoal,
  UncertaintyStyle,
  DesiredDepth,
  SupportStyle,
  CurrentSelfState,
} from '../../types/mirror-profile';

// Option configurations for each preference
const PREFERENCE_OPTIONS = {
  primary_goal: {
    title: 'What do you want Mirror to focus on?',
    options: [
      { value: 'self_understanding', label: 'Self-understanding' },
      { value: 'emotional_clarity', label: 'Emotional clarity' },
      { value: 'perspective_during_change', label: 'Perspective during change' },
      { value: 'quiet_reflection', label: 'Quiet reflection' },
      { value: 'not_sure', label: "I'm not sure yet" },
    ] as { value: PrimaryGoal; label: string }[],
  },
  desired_depth: {
    title: 'How deep should we go?',
    options: [
      { value: 'light_grounding', label: 'Light and grounding' },
      { value: 'thoughtful_simple', label: 'Thoughtful but simple' },
      { value: 'deep_exploratory', label: 'Deep and exploratory' },
      { value: 'slow_step_by_step', label: 'Slowly, step by step' },
      { value: 'not_sure', label: "I'm not sure" },
    ] as { value: DesiredDepth; label: string }[],
  },
  support_style: {
    title: 'What helps you reflect?',
    options: [
      { value: 'gentle_questions', label: 'Gentle questions' },
      { value: 'clear_perspectives', label: 'Clear perspectives' },
      { value: 'emotional_reassurance', label: 'Emotional reassurance' },
      { value: 'practical_grounding', label: 'Practical grounding' },
      { value: 'dont_reflect_much', label: "I don't reflect much" },
    ] as { value: SupportStyle; label: string }[],
  },
  uncertainty_style: {
    title: 'How do you relate to uncertainty?',
    options: [
      { value: 'meaning', label: 'I look for meaning' },
      { value: 'stability', label: 'I look for stability' },
      { value: 'exploration', label: 'I explore perspectives' },
      { value: 'discomfort', label: 'I feel uncomfortable with it' },
      { value: 'depends', label: 'It depends' },
    ] as { value: UncertaintyStyle; label: string }[],
  },
  current_self_state: {
    title: 'Where are you right now?',
    options: [
      { value: 'steady_grounded', label: 'Steady and grounded' },
      { value: 'curious_reflective', label: 'Curious and reflective' },
      { value: 'uncertain_searching', label: 'Uncertain or searching' },
      { value: 'overwhelmed_stuck', label: 'Overwhelmed or stuck' },
      { value: 'hard_to_say', label: 'Hard to say right now' },
    ] as { value: CurrentSelfState; label: string }[],
  },
};

type PreferenceKey = keyof typeof PREFERENCE_OPTIONS;

export default function ExperiencePreferences() {
  const router = useRouter();
  const { theme } = useTheme();
  const { profile, summary, updateProfile, isLoading } = useExperienceControls();
  
  const [expandedSection, setExpandedSection] = useState<PreferenceKey | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const handleSelectOption = async (key: PreferenceKey, value: any) => {
    setIsSaving(true);
    try {
      await updateProfile({ [key]: value });
      setExpandedSection(null);
    } catch (error) {
      console.error('[ExperiencePreferences] Failed to save:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const getCurrentValueLabel = (key: PreferenceKey): string => {
    const currentValue = profile[key];
    const option = PREFERENCE_OPTIONS[key].options.find(o => o.value === currentValue);
    return option?.label || 'Not set';
  };

  if (isLoading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={theme.isDark ? 'light' : 'dark'} />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.textTertiary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <StatusBar style={theme.isDark ? 'light' : 'dark'} />
      
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: theme.border }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Text style={[styles.backText, { color: theme.textSecondary }]}>← Back</Text>
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Experience Preferences</Text>
        <View style={styles.headerSpacer} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Current Summary */}
        <ExperienceSummaryCard summary={summary} />

        {/* Preference Sections */}
        <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
          ADJUST YOUR PREFERENCES
        </Text>

        {(Object.keys(PREFERENCE_OPTIONS) as PreferenceKey[]).map((key) => {
          const config = PREFERENCE_OPTIONS[key];
          const isExpanded = expandedSection === key;
          
          return (
            <View key={key} style={[styles.preferenceSection, { borderColor: theme.border }]}>
              <TouchableOpacity
                style={styles.preferenceHeader}
                onPress={() => setExpandedSection(isExpanded ? null : key)}
                activeOpacity={0.7}
              >
                <View style={styles.preferenceInfo}>
                  <Text style={[styles.preferenceTitle, { color: theme.text }]}>
                    {config.title}
                  </Text>
                  <Text style={[styles.preferenceValue, { color: theme.textSecondary }]}>
                    {getCurrentValueLabel(key)}
                  </Text>
                </View>
                <Text style={[styles.expandIcon, { color: theme.textTertiary }]}>
                  {isExpanded ? '▲' : '▼'}
                </Text>
              </TouchableOpacity>

              {isExpanded && (
                <View style={styles.optionsContainer}>
                  {config.options.map((option) => {
                    const isSelected = profile[key] === option.value;
                    return (
                      <TouchableOpacity
                        key={option.value}
                        style={[
                          styles.option,
                          { borderColor: isSelected ? theme.accent : theme.border },
                          isSelected && { backgroundColor: theme.accent + '15' },
                        ]}
                        onPress={() => handleSelectOption(key, option.value)}
                        activeOpacity={0.7}
                        disabled={isSaving}
                      >
                        <Text
                          style={[
                            styles.optionText,
                            { color: isSelected ? theme.text : theme.textSecondary },
                          ]}
                        >
                          {option.label}
                        </Text>
                        {isSelected && (
                          <Text style={[styles.checkmark, { color: theme.accent }]}>✓</Text>
                        )}
                      </TouchableOpacity>
                    );
                  })}
                </View>
              )}
            </View>
          );
        })}

        {/* Footer note */}
        <Text style={[styles.footerNote, { color: theme.textTertiary }]}>
          These preferences shape how Mirror responds to you—the tone, depth, and focus of what you see. They don't change the underlying data or calculations.
        </Text>
        
        <View style={styles.bottomPadding} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  backButton: {
    padding: 4,
  },
  backText: {
    fontSize: 16,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  headerSpacer: {
    width: 60,
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 20,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 12,
    marginTop: 8,
  },
  preferenceSection: {
    borderWidth: 1,
    borderRadius: 12,
    marginBottom: 12,
    overflow: 'hidden',
  },
  preferenceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  preferenceInfo: {
    flex: 1,
    gap: 4,
  },
  preferenceTitle: {
    fontSize: 15,
    fontWeight: '500',
  },
  preferenceValue: {
    fontSize: 13,
  },
  expandIcon: {
    fontSize: 12,
    marginLeft: 12,
  },
  optionsContainer: {
    paddingHorizontal: 12,
    paddingBottom: 12,
    gap: 8,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
  },
  optionText: {
    fontSize: 14,
  },
  checkmark: {
    fontSize: 16,
    fontWeight: '600',
  },
  footerNote: {
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
    marginTop: 24,
    paddingHorizontal: 20,
    fontStyle: 'italic',
  },
  bottomPadding: {
    height: 40,
  },
});
