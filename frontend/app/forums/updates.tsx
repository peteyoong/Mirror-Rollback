/**
 * Forum Updates Page
 * 
 * Replaces the old "Patterns" forum tool with a structured update experience
 * that captures live human signal for Mirror's pattern engine.
 * 
 * Structure:
 * 1. One-word check-in (7 life areas)
 * 2. Updates in 3 areas (Work, Relationships, Personal)
 * 3. Save + Reflect with Mirror
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Switch,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import api from '../../services/api';

// Check-in areas
const CHECKIN_AREAS = [
  { key: 'mentally', label: 'Mentally', placeholder: 'deep, foggy, sharp...' },
  { key: 'emotionally', label: 'Emotionally', placeholder: 'swinging, calm, raw...' },
  { key: 'relationship', label: 'Relationship', placeholder: 'withdrawn, connected...' },
  { key: 'vocationally', label: 'Vocationally', placeholder: 'consolidating, stuck...' },
  { key: 'spiritually', label: 'Spiritually', placeholder: 'exploring, dry, alive...' },
  { key: 'financially', label: 'Financially', placeholder: 'safer, stretched...' },
  { key: 'physically', label: 'Physically', placeholder: 'pained, strong, tired...' },
];

// Update areas
const UPDATE_AREAS = [
  { key: 'work', label: 'Work', emotionPlaceholder: 'pressure, momentum, doubt...' },
  { key: 'relationships', label: 'Relationships', emotionPlaceholder: 'distance, love, tension...' },
  { key: 'personal', label: 'Personal', emotionPlaceholder: 'rebuilding, grief, hope...' },
];

interface CheckinState {
  mentally: string;
  emotionally: string;
  relationship: string;
  vocationally: string;
  spiritually: string;
  financially: string;
  physically: string;
}

interface UpdateAreaState {
  emotions: string;
  update_text: string;
  add_to_journal: boolean;
}

interface UpdatesState {
  work: UpdateAreaState;
  relationships: UpdateAreaState;
  personal: UpdateAreaState;
}

export default function ForumUpdatesScreen() {
  const { forumId, forumName } = useLocalSearchParams<{ forumId: string; forumName?: string }>();
  const router = useRouter();
  const { theme } = useTheme();
  const user = useAppStore((state) => state.user);
  
  // Form state
  const [checkin, setCheckin] = useState<CheckinState>({
    mentally: '',
    emotionally: '',
    relationship: '',
    vocationally: '',
    spiritually: '',
    financially: '',
    physically: '',
  });
  
  const [updates, setUpdates] = useState<UpdatesState>({
    work: { emotions: '', update_text: '', add_to_journal: false },
    relationships: { emotions: '', update_text: '', add_to_journal: false },
    personal: { emotions: '', update_text: '', add_to_journal: false },
  });
  
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [savedSummary, setSavedSummary] = useState<string[] | null>(null);
  
  // Update check-in field
  const updateCheckin = (key: keyof CheckinState, value: string) => {
    setCheckin(prev => ({ ...prev, [key]: value }));
  };
  
  // Update area field
  const updateAreaField = (
    area: keyof UpdatesState,
    field: keyof UpdateAreaState,
    value: string | boolean
  ) => {
    setUpdates(prev => ({
      ...prev,
      [area]: { ...prev[area], [field]: value }
    }));
  };
  
  // Parse emotions string to array
  const parseEmotions = (emotionStr: string): string[] => {
    return emotionStr
      .split(/[,\s]+/)
      .map(e => e.trim())
      .filter(e => e.length > 0)
      .slice(0, 3);
  };
  
  // Generate summary from saved data
  const generateSummary = (): string[] => {
    const summary: string[] = [];
    
    if (updates.work.emotions || updates.work.update_text) {
      const emotion = parseEmotions(updates.work.emotions)[0] || 'movement';
      summary.push(`${emotion} in work`);
    }
    if (updates.relationships.emotions || updates.relationships.update_text) {
      const emotion = parseEmotions(updates.relationships.emotions)[0] || 'presence';
      summary.push(`${emotion} in relationships`);
    }
    if (updates.personal.emotions || updates.personal.update_text) {
      const emotion = parseEmotions(updates.personal.emotions)[0] || 'processing';
      summary.push(`${emotion} in self`);
    }
    
    return summary;
  };
  
  // Save forum update
  const handleSave = async () => {
    if (!user?.id || !forumId) return;
    
    setIsSaving(true);
    try {
      const payload = {
        forum_id: forumId,
        user_id: user.id,
        one_word_checkin: checkin,
        updates: {
          work: {
            emotions: parseEmotions(updates.work.emotions),
            update_text: updates.work.update_text,
            add_to_journal: updates.work.add_to_journal,
          },
          relationships: {
            emotions: parseEmotions(updates.relationships.emotions),
            update_text: updates.relationships.update_text,
            add_to_journal: updates.relationships.add_to_journal,
          },
          personal: {
            emotions: parseEmotions(updates.personal.emotions),
            update_text: updates.personal.update_text,
            add_to_journal: updates.personal.add_to_journal,
          },
        },
      };
      
      await api.post('/forums/update', payload);
      
      setIsSaved(true);
      setSavedSummary(generateSummary());
    } catch (err) {
      console.error('[ForumUpdates] Save error:', err);
    } finally {
      setIsSaving(false);
    }
  };
  
  // Save and reflect with Mirror
  const handleReflectWithMirror = async () => {
    if (!isSaved) {
      await handleSave();
    }
    
    // Build context for reflection
    const context = buildReflectionContext();
    
    // Navigate to reflection chat with context
    router.push({
      pathname: '/reflection-chat',
      params: {
        prefill: context,
        forumId: forumId,
        source: 'forum_update',
      }
    });
  };
  
  // Build reflection context from update
  const buildReflectionContext = (): string => {
    const parts: string[] = [];
    
    // Add check-in context
    const filledCheckins = Object.entries(checkin)
      .filter(([_, v]) => v.trim())
      .map(([k, v]) => `${k}: ${v}`);
    if (filledCheckins.length > 0) {
      parts.push(`Right now I'm feeling: ${filledCheckins.join(', ')}`);
    }
    
    // Add update context
    if (updates.work.update_text) {
      parts.push(`In work: ${updates.work.update_text}`);
    }
    if (updates.relationships.update_text) {
      parts.push(`In relationships: ${updates.relationships.update_text}`);
    }
    if (updates.personal.update_text) {
      parts.push(`Personally: ${updates.personal.update_text}`);
    }
    
    return parts.join('\n\n');
  };
  
  const handleBack = () => {
    router.back();
  };
  
  // Check if form has any content
  const hasContent = () => {
    const hasCheckin = Object.values(checkin).some(v => v.trim());
    const hasUpdates = Object.values(updates).some(
      u => u.emotions.trim() || u.update_text.trim()
    );
    return hasCheckin || hasUpdates;
  };
  
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Header */}
        <View style={[styles.header, { borderBottomColor: theme.border }]}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Forum Update</Text>
          <View style={styles.headerRight} />
        </View>
        
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Intro */}
          <View style={styles.introSection}>
            <Text style={[styles.introTitle, { color: theme.text }]}>
              {forumName || 'Forum'} Update
            </Text>
            <Text style={[styles.introSubtext, { color: theme.textSecondary }]}>
              Capture what's happening before Mirror reflects it back
            </Text>
          </View>
          
          {/* PART 1: One-Word Check-In */}
          <View style={[styles.sectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>One-word check-in</Text>
            <Text style={[styles.sectionSubtext, { color: theme.textTertiary }]}>
              Quick snapshot — how are you showing up right now?
            </Text>
            
            <View style={styles.checkinGrid}>
              {CHECKIN_AREAS.map((area) => (
                <View key={area.key} style={styles.checkinItem}>
                  <Text style={[styles.checkinLabel, { color: theme.textSecondary }]}>
                    {area.label}
                  </Text>
                  <TextInput
                    style={[styles.checkinInput, { 
                      backgroundColor: theme.background, 
                      color: theme.text,
                      borderColor: theme.border 
                    }]}
                    placeholder={area.placeholder}
                    placeholderTextColor={theme.textTertiary}
                    value={checkin[area.key as keyof CheckinState]}
                    onChangeText={(text) => updateCheckin(area.key as keyof CheckinState, text)}
                    maxLength={30}
                  />
                </View>
              ))}
            </View>
          </View>
          
          {/* PART 2: Updates in 3 Areas */}
          {UPDATE_AREAS.map((area) => (
            <View 
              key={area.key} 
              style={[styles.sectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
            >
              <Text style={[styles.sectionTitle, { color: theme.text }]}>{area.label}</Text>
              
              {/* Emotions */}
              <View style={styles.emotionsRow}>
                <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>
                  3 emotions
                </Text>
                <TextInput
                  style={[styles.emotionsInput, { 
                    backgroundColor: theme.background, 
                    color: theme.text,
                    borderColor: theme.border 
                  }]}
                  placeholder={area.emotionPlaceholder}
                  placeholderTextColor={theme.textTertiary}
                  value={updates[area.key as keyof UpdatesState].emotions}
                  onChangeText={(text) => updateAreaField(area.key as keyof UpdatesState, 'emotions', text)}
                />
              </View>
              
              {/* Update text */}
              <View style={styles.updateTextRow}>
                <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>
                  What's happening
                </Text>
                <TextInput
                  style={[styles.updateTextInput, { 
                    backgroundColor: theme.background, 
                    color: theme.text,
                    borderColor: theme.border 
                  }]}
                  placeholder="Share what's real right now..."
                  placeholderTextColor={theme.textTertiary}
                  value={updates[area.key as keyof UpdatesState].update_text}
                  onChangeText={(text) => updateAreaField(area.key as keyof UpdatesState, 'update_text', text)}
                  multiline
                  numberOfLines={4}
                  textAlignVertical="top"
                />
              </View>
              
              {/* Add to journal toggle */}
              <View style={styles.journalToggleRow}>
                <Text style={[styles.journalToggleLabel, { color: theme.textTertiary }]}>
                  Also add to my journal
                </Text>
                <Switch
                  value={updates[area.key as keyof UpdatesState].add_to_journal}
                  onValueChange={(value) => updateAreaField(area.key as keyof UpdatesState, 'add_to_journal', value)}
                  trackColor={{ false: theme.border, true: theme.accent + '60' }}
                  thumbColor={updates[area.key as keyof UpdatesState].add_to_journal ? theme.accent : theme.textTertiary}
                />
              </View>
            </View>
          ))}
          
          {/* Saved Summary */}
          {isSaved && savedSummary && savedSummary.length > 0 && (
            <View style={[styles.savedSummaryCard, { backgroundColor: theme.accent + '10', borderColor: theme.accent + '30' }]}>
              <Text style={[styles.savedTitle, { color: theme.accent }]}>Saved.</Text>
              <Text style={[styles.savedSubtitle, { color: theme.textSecondary }]}>You're carrying:</Text>
              {savedSummary.map((item, idx) => (
                <Text key={idx} style={[styles.savedItem, { color: theme.text }]}>
                  • {item}
                </Text>
              ))}
            </View>
          )}
          
          {/* PART 3: Action Buttons */}
          <View style={styles.actionsSection}>
            <TouchableOpacity
              style={[styles.primaryButton, { backgroundColor: theme.accent }]}
              onPress={handleSave}
              disabled={isSaving || !hasContent()}
              activeOpacity={0.8}
            >
              {isSaving ? (
                <ActivityIndicator size="small" color={theme.textInverse} />
              ) : (
                <Text style={[styles.primaryButtonText, { color: theme.textInverse }]}>
                  {isSaved ? 'Update Saved' : 'Save Forum Update'}
                </Text>
              )}
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.secondaryButton, { borderColor: theme.accent }]}
              onPress={handleReflectWithMirror}
              disabled={isSaving || !hasContent()}
              activeOpacity={0.8}
            >
              <Text style={[styles.secondaryButtonText, { color: theme.accent }]}>
                Reflect with Mirror
              </Text>
            </TouchableOpacity>
          </View>
          
          {/* Bottom spacing */}
          <View style={{ height: 40 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backButton: {
    minWidth: 80,
  },
  backText: {
    fontSize: 16,
    fontWeight: '500',
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  headerRight: {
    minWidth: 80,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  
  // Intro
  introSection: {
    marginBottom: 20,
  },
  introTitle: {
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 6,
  },
  introSubtext: {
    fontSize: 15,
    lineHeight: 21,
  },
  
  // Section Card
  sectionCard: {
    borderRadius: 14,
    padding: 18,
    marginBottom: 16,
    borderWidth: 1,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 4,
  },
  sectionSubtext: {
    fontSize: 13,
    marginBottom: 16,
  },
  
  // Check-in Grid
  checkinGrid: {
    gap: 12,
  },
  checkinItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  checkinLabel: {
    width: 100,
    fontSize: 14,
    fontWeight: '500',
  },
  checkinInput: {
    flex: 1,
    height: 40,
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 14,
    borderWidth: 1,
  },
  
  // Update Area Fields
  fieldLabel: {
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 8,
  },
  emotionsRow: {
    marginBottom: 14,
  },
  emotionsInput: {
    height: 42,
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 14,
    borderWidth: 1,
  },
  updateTextRow: {
    marginBottom: 12,
  },
  updateTextInput: {
    minHeight: 100,
    borderRadius: 10,
    padding: 12,
    fontSize: 15,
    lineHeight: 22,
    borderWidth: 1,
  },
  journalToggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 8,
  },
  journalToggleLabel: {
    fontSize: 13,
  },
  
  // Saved Summary
  savedSummaryCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
  },
  savedTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 6,
  },
  savedSubtitle: {
    fontSize: 14,
    marginBottom: 8,
  },
  savedItem: {
    fontSize: 14,
    lineHeight: 22,
  },
  
  // Actions
  actionsSection: {
    gap: 12,
    marginTop: 8,
  },
  primaryButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1.5,
  },
  secondaryButtonText: {
    fontSize: 15,
    fontWeight: '600',
  },
});
