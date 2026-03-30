/**
 * Experience Preferences Screen (V1)
 * 
 * Premium Mirror-style settings screen.
 * Feels like Mirror's intelligence system, not a settings panel.
 * 
 * USER SHOULD FEEL:
 * "I'm shaping how Mirror meets me"
 * NOT: "I'm configuring software"
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
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { useExperienceControls } from '../../hooks/useExperienceControls';

// =============================================================================
// V1 PREFERENCE OPTIONS - Simple, clear, Mirror-aligned
// =============================================================================

interface PreferenceOption {
  value: string;
  label: string;
  preview: string;  // Short preview of how Mirror will respond
}

const DEPTH_OPTIONS: PreferenceOption[] = [
  { 
    value: 'light', 
    label: 'Light', 
    preview: 'Shorter, sharper. Just enough to notice.' 
  },
  { 
    value: 'balanced', 
    label: 'Balanced', 
    preview: 'Enough to work with. Not overwhelming.' 
  },
  { 
    value: 'deep', 
    label: 'Deep', 
    preview: 'More pattern. More reflection. More time.' 
  },
];

const TONE_OPTIONS: PreferenceOption[] = [
  { 
    value: 'direct', 
    label: 'Direct', 
    preview: "You already know what's off here." 
  },
  { 
    value: 'calm', 
    label: 'Calm', 
    preview: "Take a breath. Something here still doesn't feel settled." 
  },
  { 
    value: 'grounded', 
    label: 'Grounded', 
    preview: "This isn't ready yet. Slow it down." 
  },
  { 
    value: 'confronting', 
    label: 'Confronting', 
    preview: "You're about to do the thing that keeps costing you." 
  },
];

const SUPPORT_OPTIONS: PreferenceOption[] = [
  { 
    value: 'interrupt', 
    label: 'Interrupt me', 
    preview: "Catch the pattern quickly. Don't let me loop." 
  },
  { 
    value: 'work_with', 
    label: 'Help me work with it', 
    preview: 'More practical. Help me move through it.' 
  },
  { 
    value: 'explore', 
    label: 'Let me explore it', 
    preview: 'More depth. More reflection. More space.' 
  },
];

// =============================================================================
// COMPONENT
// =============================================================================

export default function ExperiencePreferences() {
  const router = useRouter();
  const { theme } = useTheme();
  const { profile, updateProfile, isLoading } = useExperienceControls();
  
  // Local state for selections (maps to existing profile fields)
  const [depth, setDepth] = useState<string>('balanced');
  const [tone, setTone] = useState<string>('calm');
  const [supportStyle, setSupportStyle] = useState<string>('work_with');
  const [showSaved, setShowSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // V1: Micro confirmation messages
  const MICRO_CONFIRMATIONS = ["Got it.", "We'll meet you there.", "Adjusted.", "Noted."];
  const [microConfirmation, setMicroConfirmation] = useState<string | null>(null);
  const [tonePreview, setTonePreview] = useState<string | null>(null);

  // Map existing profile to V1 preferences
  useEffect(() => {
    if (profile) {
      // Map desired_depth to V1 depth
      if (profile.desired_depth === 'light_grounding') setDepth('light');
      else if (profile.desired_depth === 'deep_exploratory') setDepth('deep');
      else setDepth('balanced');
      
      // Map support_style to V1 support
      if (profile.support_style === 'clear_perspectives') {
        setTone('direct');
        setSupportStyle('interrupt');
      } else if (profile.support_style === 'practical_grounding') {
        setTone('grounded');
        setSupportStyle('work_with');
      } else if (profile.support_style === 'emotional_reassurance') {
        setTone('calm');
        setSupportStyle('explore');
      } else {
        setTone('calm');
        setSupportStyle('work_with');
      }
    }
  }, [profile]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Map V1 preferences back to existing profile fields
      const desiredDepth = depth === 'light' ? 'light_grounding' 
        : depth === 'deep' ? 'deep_exploratory' 
        : 'thoughtful_simple';
      
      const supportStyleValue = supportStyle === 'interrupt' ? 'clear_perspectives'
        : supportStyle === 'explore' ? 'gentle_questions'
        : 'practical_grounding';
      
      // Also store V1 preferences directly for immediate use
      await updateProfile({
        desired_depth: desiredDepth,
        support_style: supportStyleValue,
        // V1: Store raw preferences for immediate feedback
        v1_tone: tone,
        v1_depth: depth,
        v1_support_style: supportStyle,
      });
      
      // V1: Show micro confirmation
      const randomConfirmation = MICRO_CONFIRMATIONS[Math.floor(Math.random() * MICRO_CONFIRMATIONS.length)];
      setMicroConfirmation(randomConfirmation);
      
      // V1: Show tone preview
      const preview = TONE_OPTIONS.find(o => o.value === tone)?.preview;
      if (preview) {
        setTonePreview(preview);
      }
      
      // Clear after delay
      setTimeout(() => {
        setMicroConfirmation(null);
        setTonePreview(null);
      }, 3000);
      
      setShowSaved(true);
      setTimeout(() => setShowSaved(false), 2000);
    } catch (error) {
      console.error('[ExperiencePreferences] Save error:', error);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={theme.isDark ? 'light' : 'dark'} />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.textTertiary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <StatusBar style={theme.isDark ? 'light' : 'dark'} />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="chevron-back" size={24} color={theme.textSecondary} />
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.content} 
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.contentContainer}
      >
        {/* Title & Intro */}
        <Text style={[styles.title, { color: theme.text }]}>
          Experience Preferences
        </Text>
        <Text style={[styles.intro, { color: theme.textSecondary }]}>
          Shape how Mirror meets you.
        </Text>

        {/* ============================================ */}
        {/* DEPTH */}
        {/* ============================================ */}
        <View style={styles.preferenceGroup}>
          <Text style={[styles.question, { color: theme.text }]}>
            How deep do you want Mirror to go?
          </Text>
          <View style={styles.pillContainer}>
            {DEPTH_OPTIONS.map((option) => {
              const isSelected = depth === option.value;
              return (
                <TouchableOpacity
                  key={option.value}
                  style={[
                    styles.pill,
                    { borderColor: isSelected ? theme.text : theme.border },
                    isSelected && { backgroundColor: theme.text },
                  ]}
                  onPress={() => setDepth(option.value)}
                  activeOpacity={0.7}
                >
                  <Text style={[
                    styles.pillText,
                    { color: isSelected ? theme.background : theme.textSecondary },
                  ]}>
                    {option.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
          {/* Preview */}
          <Text style={[styles.preview, { color: theme.textTertiary }]}>
            {DEPTH_OPTIONS.find(o => o.value === depth)?.preview}
          </Text>
        </View>

        {/* ============================================ */}
        {/* TONE */}
        {/* ============================================ */}
        <View style={styles.preferenceGroup}>
          <Text style={[styles.question, { color: theme.text }]}>
            How should Mirror speak to you?
          </Text>
          <View style={styles.pillContainer}>
            {TONE_OPTIONS.map((option) => {
              const isSelected = tone === option.value;
              return (
                <TouchableOpacity
                  key={option.value}
                  style={[
                    styles.pill,
                    { borderColor: isSelected ? theme.text : theme.border },
                    isSelected && { backgroundColor: theme.text },
                  ]}
                  onPress={() => setTone(option.value)}
                  activeOpacity={0.7}
                >
                  <Text style={[
                    styles.pillText,
                    { color: isSelected ? theme.background : theme.textSecondary },
                  ]}>
                    {option.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
          {/* Preview */}
          <Text style={[styles.preview, { color: theme.textTertiary }]}>
            "{TONE_OPTIONS.find(o => o.value === tone)?.preview}"
          </Text>
        </View>

        {/* ============================================ */}
        {/* SUPPORT STYLE */}
        {/* ============================================ */}
        <View style={styles.preferenceGroup}>
          <Text style={[styles.question, { color: theme.text }]}>
            What helps most when you're stuck?
          </Text>
          <View style={styles.optionList}>
            {SUPPORT_OPTIONS.map((option) => {
              const isSelected = supportStyle === option.value;
              return (
                <TouchableOpacity
                  key={option.value}
                  style={[
                    styles.optionRow,
                    { borderColor: isSelected ? theme.text : theme.border },
                    isSelected && { backgroundColor: 'rgba(128, 128, 128, 0.08)' },
                  ]}
                  onPress={() => setSupportStyle(option.value)}
                  activeOpacity={0.7}
                >
                  <View style={styles.optionContent}>
                    <Text style={[
                      styles.optionLabel,
                      { color: isSelected ? theme.text : theme.textSecondary },
                      isSelected && { fontWeight: '600' },
                    ]}>
                      {option.label}
                    </Text>
                    <Text style={[styles.optionPreview, { color: theme.textTertiary }]}>
                      {option.preview}
                    </Text>
                  </View>
                  {isSelected && (
                    <Ionicons name="checkmark" size={20} color={theme.text} />
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* ============================================ */}
        {/* SAVE / APPLY */}
        {/* ============================================ */}
        <TouchableOpacity
          style={[
            styles.saveButton,
            { backgroundColor: theme.text },
            isSaving && { opacity: 0.7 },
          ]}
          onPress={handleSave}
          disabled={isSaving}
          activeOpacity={0.8}
        >
          {isSaving ? (
            <ActivityIndicator size="small" color={theme.background} />
          ) : showSaved ? (
            <View style={styles.savedRow}>
              <Ionicons name="checkmark" size={18} color={theme.background} />
              <Text style={[styles.saveButtonText, { color: theme.background }]}>
                Saved
              </Text>
            </View>
          ) : (
            <Text style={[styles.saveButtonText, { color: theme.background }]}>
              Save preferences
            </Text>
          )}
        </TouchableOpacity>

        {/* ============================================ */}
        {/* V1: MICRO CONFIRMATION + TONE PREVIEW */}
        {/* ============================================ */}
        {(microConfirmation || tonePreview) && (
          <View style={styles.feedbackContainer}>
            {microConfirmation && (
              <Text style={[styles.microConfirmation, { color: theme.text }]}>
                {microConfirmation}
              </Text>
            )}
            {tonePreview && (
              <Text style={[styles.tonePreview, { color: theme.textSecondary }]}>
                "{tonePreview}"
              </Text>
            )}
          </View>
        )}

        {/* ============================================ */}
        {/* FOOTER */}
        {/* ============================================ */}
        <Text style={[styles.footer, { color: theme.textTertiary }]}>
          You can change this anytime.
        </Text>
        <Text style={[styles.footerSubtle, { color: theme.textTertiary }]}>
          This changes tone and depth - not the truth.
        </Text>

        <View style={styles.bottomPadding} />
      </ScrollView>
    </SafeAreaView>
  );
}

// =============================================================================
// STYLES - Premium, calm, minimal
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  // Header
  header: {
    paddingHorizontal: 8,
    paddingVertical: 8,
  },
  backButton: {
    padding: 8,
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  // Content
  content: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 24,
  },
  
  // Title & Intro
  title: {
    fontSize: 28,
    fontWeight: '700',
    marginTop: 8,
    marginBottom: 8,
  },
  intro: {
    fontSize: 16,
    marginBottom: 40,
  },
  
  // Preference Groups
  preferenceGroup: {
    marginBottom: 40,
  },
  question: {
    fontSize: 17,
    fontWeight: '500',
    marginBottom: 16,
  },
  
  // Pills (for Depth & Tone)
  pillContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 12,
  },
  pill: {
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
  },
  pillText: {
    fontSize: 14,
    fontWeight: '500',
  },
  
  // Preview
  preview: {
    fontSize: 13,
    fontStyle: 'italic',
    lineHeight: 19,
  },
  
  // Option List (for Support Style)
  optionList: {
    gap: 12,
  },
  optionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  optionContent: {
    flex: 1,
    marginRight: 12,
  },
  optionLabel: {
    fontSize: 15,
    marginBottom: 4,
  },
  optionPreview: {
    fontSize: 12,
    lineHeight: 17,
  },
  
  // Save Button
  saveButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
    marginBottom: 24,
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  savedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  
  // V1: Feedback Container
  feedbackContainer: {
    alignItems: 'center',
    paddingVertical: 20,
    gap: 8,
  },
  microConfirmation: {
    fontSize: 15,
    fontWeight: '500',
  },
  tonePreview: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
    paddingHorizontal: 20,
    lineHeight: 20,
  },
  
  // Footer
  footer: {
    fontSize: 13,
    textAlign: 'center',
    marginBottom: 8,
  },
  footerSubtle: {
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
    opacity: 0.7,
  },
  
  bottomPadding: {
    height: 40,
  },
});
