import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Modal,
  Pressable,
  ScrollView,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useAppStore } from '../store';
import { getUserForums, createJournalEntry, submitForumReflection, Forum } from '../services/api';

// Source metadata interface
export interface ReflectionSource {
  lens: 'patterns' | 'human_design' | 'life' | 'enneagram' | 'astrology' | 'numerology' | 'gene_keys' | 'bazi';
  area?: string;        // e.g., 'relationships', 'work', 'self' for life
  section?: string;     // e.g., 'overview', 'today', 'explore', 'reflect'
  name: string;         // Human-readable name e.g., 'Emotional Authority'
  type?: string;        // e.g., 'authority', 'center', 'gate', 'domain'
  id?: string;          // e.g., gate_1, domain_emotional_landscape
  value?: string;       // Optional value e.g., 'Manifestor'
}

interface UniversalReflectionModalProps {
  visible: boolean;
  onClose: () => void;
  source: ReflectionSource;
  initialPrompt?: string;  // Pre-filled prompt/guidance text
  activeForumId?: string;  // If user came from a forum context
  activeForumName?: string;
}

interface ForumOption {
  id: string;
  name: string;
  selected: boolean;
  isShared: boolean;  // Whether to share publicly in forum
}

export function UniversalReflectionModal({
  visible,
  onClose,
  source,
  initialPrompt,
  activeForumId,
  activeForumName,
}: UniversalReflectionModalProps) {
  const { theme } = useTheme();
  const { user } = useAppStore();
  
  const [reflectionText, setReflectionText] = useState('');
  const [saveToJournal, setSaveToJournal] = useState(true);
  const [forums, setForums] = useState<ForumOption[]>([]);
  const [isLoadingForums, setIsLoadingForums] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load user's forums when modal opens
  useEffect(() => {
    if (visible && user?.id) {
      loadForums();
    }
  }, [visible, user?.id]);

  // Reset state when modal opens
  useEffect(() => {
    if (visible) {
      setReflectionText('');
      setSaveToJournal(true);
      setSaveSuccess(false);
      setError(null);
    }
  }, [visible]);

  const loadForums = async () => {
    if (!user?.id) return;
    setIsLoadingForums(true);
    try {
      const response = await getUserForums(user.id);
      const forumOptions: ForumOption[] = (response.forums || []).map((forum: Forum) => ({
        id: forum.id,
        name: forum.name,
        selected: activeForumId === forum.id, // Pre-select if in forum context
        isShared: false, // Default to private
      }));
      setForums(forumOptions);
    } catch (err) {
      console.error('Failed to load forums:', err);
      setForums([]);
    } finally {
      setIsLoadingForums(false);
    }
  };

  const toggleForum = (forumId: string) => {
    setForums(prev => prev.map(f => 
      f.id === forumId ? { ...f, selected: !f.selected } : f
    ));
  };

  const toggleForumShared = (forumId: string) => {
    setForums(prev => prev.map(f => 
      f.id === forumId ? { ...f, isShared: !f.isShared } : f
    ));
  };

  const getSourceSummary = (): string => {
    const parts = [];
    
    // Lens name
    const lensNames: Record<string, string> = {
      'patterns': 'Patterns',
      'human_design': 'Human Design',
      'life': 'Life',
      'enneagram': 'Enneagram',
      'astrology': 'Astrology',
      'numerology': 'Numerology',
      'gene_keys': 'Gene Keys',
      'bazi': 'BaZi',
    };
    parts.push(lensNames[source?.lens] || source?.lens || 'Unknown');
    
    // Area (for Life)
    if (source?.area) {
      const areaNames: Record<string, string> = {
        'relationships': 'Relationships',
        'work': 'Work',
        'self': 'Self',
      };
      parts.push(areaNames[source.area] || source.area);
    }
    
    // Name
    if (source?.name) {
      parts.push(source.name);
    }
    
    return parts.join(' → ');
  };

  const buildMetadata = () => {
    return {
      source_lens: source?.lens,
      source_area: source?.area,
      source_section: source?.section,
      source_name: source?.name,
      source_type: source?.type,
      source_id: source?.id,
      source_value: source?.value,
      timestamp: new Date().toISOString(),
    };
  };

  const handleSave = async () => {
    if (!user?.id) return;
    if (!reflectionText.trim() && !saveToJournal && forums.filter(f => f.selected).length === 0) {
      setError('Please enter a reflection and select at least one destination.');
      return;
    }
    if (!reflectionText.trim()) {
      setError('Please enter your reflection.');
      return;
    }
    if (!saveToJournal && forums.filter(f => f.selected).length === 0) {
      setError('Please select at least one destination.');
      return;
    }

    setIsSaving(true);
    setError(null);

    const metadata = buildMetadata();
    const selectedForums = forums.filter(f => f.selected);

    try {
      const savePromises: Promise<any>[] = [];

      // Save to journal
      if (saveToJournal) {
        savePromises.push(
          createJournalEntry(user.id, reflectionText, {
            journal_source: `${source?.lens || 'unknown'}_${source?.type || source?.area || 'reflection'}`,
            category: getSourceSummary(),
            ...metadata,
          })
        );
      }

      // Save to selected forums
      for (const forum of selectedForums) {
        savePromises.push(
          submitForumReflection(forum.id, {
            user_id: user.id,
            selected_domain: source?.id || `${source?.lens || 'unknown'}_${source?.type || source?.name || 'reflection'}`,
            reflection_text: reflectionText,
            is_shared: forum.isShared,
          })
        );
      }

      await Promise.all(savePromises);
      setSaveSuccess(true);
      
      // Close after brief success message
      setTimeout(() => {
        onClose();
      }, 1500);

    } catch (err: any) {
      console.error('Failed to save reflection:', err);
      setError('Failed to save reflection. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const selectedForumCount = forums.filter(f => f.selected).length;
  const canSave = reflectionText.trim() && (saveToJournal || selectedForumCount > 0);

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <Pressable style={styles.overlay} onPress={onClose}>
          <Pressable 
            style={[styles.modalContainer, { backgroundColor: theme.surface }]}
            onPress={e => e.stopPropagation()}
          >
            {/* Header */}
            <View style={styles.header}>
              <Text style={[styles.title, { color: theme.text }]}>Reflect</Text>
              <TouchableOpacity onPress={onClose} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                <Ionicons name="close" size={24} color={theme.textTertiary} />
              </TouchableOpacity>
            </View>

            <ScrollView 
              style={styles.scrollContent}
              showsVerticalScrollIndicator={false}
              keyboardShouldPersistTaps="handled"
            >
              {/* Source Summary */}
              <View style={[styles.sourceCard, { backgroundColor: theme.background }]}>
                <Text style={[styles.sourceLabel, { color: theme.textTertiary }]}>Reflecting on</Text>
                <Text style={[styles.sourceName, { color: theme.text }]}>{getSourceSummary()}</Text>
                {source.value && (
                  <Text style={[styles.sourceValue, { color: theme.textSecondary }]}>{source.value}</Text>
                )}
              </View>

              {/* Initial Prompt/Guidance */}
              {initialPrompt && (
                <View style={[styles.promptCard, { backgroundColor: theme.accent + '10', borderColor: theme.accent + '30' }]}>
                  <Ionicons name="sparkles" size={16} color={theme.accent} style={{ marginRight: 8 }} />
                  <Text style={[styles.promptText, { color: theme.textSecondary }]}>{initialPrompt}</Text>
                </View>
              )}

              {/* Reflection Text Input */}
              <View style={styles.inputSection}>
                <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>Your Reflection</Text>
                <TextInput
                  style={[styles.textInput, { 
                    backgroundColor: theme.background, 
                    color: theme.text,
                    borderColor: theme.border,
                  }]}
                  placeholder="What are you noticing? What wants to be expressed?"
                  placeholderTextColor={theme.textTertiary}
                  multiline
                  numberOfLines={5}
                  textAlignVertical="top"
                  value={reflectionText}
                  onChangeText={setReflectionText}
                />
              </View>

              {/* Save Destinations */}
              <View style={styles.destinationsSection}>
                <Text style={[styles.sectionLabel, { color: theme.textSecondary }]}>Save to</Text>
                
                {/* My Journal */}
                <TouchableOpacity 
                  style={[styles.destinationRow, { borderColor: theme.border }]}
                  onPress={() => setSaveToJournal(!saveToJournal)}
                  activeOpacity={0.7}
                >
                  <View style={styles.destinationLeft}>
                    <View style={[
                      styles.checkbox, 
                      { borderColor: theme.border },
                      saveToJournal && { backgroundColor: theme.accent, borderColor: theme.accent }
                    ]}>
                      {saveToJournal && <Ionicons name="checkmark" size={14} color="#fff" />}
                    </View>
                    <Ionicons name="book-outline" size={20} color={theme.textSecondary} />
                    <Text style={[styles.destinationName, { color: theme.text }]}>My Journal</Text>
                  </View>
                  <Text style={[styles.destinationHint, { color: theme.textTertiary }]}>Private</Text>
                </TouchableOpacity>

                {/* Forums */}
                {isLoadingForums ? (
                  <View style={styles.loadingForums}>
                    <ActivityIndicator size="small" color={theme.textTertiary} />
                    <Text style={[styles.loadingText, { color: theme.textTertiary }]}>Loading forums...</Text>
                  </View>
                ) : forums.length > 0 ? (
                  <>
                    <Text style={[styles.forumsLabel, { color: theme.textTertiary }]}>Forums</Text>
                    {forums.map(forum => (
                      <View key={forum.id}>
                        <TouchableOpacity 
                          style={[styles.destinationRow, { borderColor: theme.border }]}
                          onPress={() => toggleForum(forum.id)}
                          activeOpacity={0.7}
                        >
                          <View style={styles.destinationLeft}>
                            <View style={[
                              styles.checkbox, 
                              { borderColor: theme.border },
                              forum.selected && { backgroundColor: theme.accent, borderColor: theme.accent }
                            ]}>
                              {forum.selected && <Ionicons name="checkmark" size={14} color="#fff" />}
                            </View>
                            <Ionicons name="people-outline" size={20} color={theme.textSecondary} />
                            <Text style={[styles.destinationName, { color: theme.text }]}>{forum.name}</Text>
                          </View>
                        </TouchableOpacity>
                        
                        {/* Share toggle when forum is selected */}
                        {forum.selected && (
                          <TouchableOpacity 
                            style={[styles.shareToggle, { backgroundColor: theme.background }]}
                            onPress={() => toggleForumShared(forum.id)}
                            activeOpacity={0.7}
                          >
                            <View style={[
                              styles.toggleTrack, 
                              { backgroundColor: forum.isShared ? theme.accent : theme.border }
                            ]}>
                              <View style={[
                                styles.toggleThumb,
                                { backgroundColor: '#fff' },
                                forum.isShared && styles.toggleThumbActive
                              ]} />
                            </View>
                            <Text style={[styles.shareLabel, { color: theme.textSecondary }]}>
                              {forum.isShared ? 'Shared with forum' : 'Private (only you)'}
                            </Text>
                          </TouchableOpacity>
                        )}
                      </View>
                    ))}
                  </>
                ) : (
                  <TouchableOpacity 
                    style={[styles.noForumsCard, { backgroundColor: theme.background, borderColor: theme.border }]}
                  >
                    <Ionicons name="people-outline" size={20} color={theme.textTertiary} />
                    <Text style={[styles.noForumsText, { color: theme.textTertiary }]}>
                      No forums joined yet
                    </Text>
                  </TouchableOpacity>
                )}
              </View>

              {/* Error Message */}
              {error && (
                <View style={[styles.errorCard, { backgroundColor: '#ff4444' + '15' }]}>
                  <Ionicons name="alert-circle" size={16} color="#ff4444" />
                  <Text style={[styles.errorText, { color: '#ff4444' }]}>{error}</Text>
                </View>
              )}

              {/* Success Message */}
              {saveSuccess && (
                <View style={[styles.successCard, { backgroundColor: theme.accent + '15' }]}>
                  <Ionicons name="checkmark-circle" size={16} color={theme.accent} />
                  <Text style={[styles.successText, { color: theme.accent }]}>Reflection saved!</Text>
                </View>
              )}
            </ScrollView>

            {/* Save Button */}
            <View style={styles.footer}>
              <TouchableOpacity
                style={[
                  styles.saveButton,
                  { backgroundColor: canSave ? theme.accent : theme.border }
                ]}
                onPress={handleSave}
                disabled={!canSave || isSaving || saveSuccess}
                activeOpacity={0.8}
              >
                {isSaving ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <>
                    <Ionicons name="checkmark" size={20} color="#fff" />
                    <Text style={styles.saveButtonText}>
                      {saveSuccess ? 'Saved!' : 'Save Reflection'}
                    </Text>
                  </>
                )}
              </TouchableOpacity>
              
              {/* Summary of destinations */}
              {canSave && !saveSuccess && (
                <Text style={[styles.saveSummary, { color: theme.textTertiary }]}>
                  {saveToJournal && selectedForumCount > 0 
                    ? `Journal + ${selectedForumCount} forum${selectedForumCount > 1 ? 's' : ''}`
                    : saveToJournal 
                      ? 'Journal only'
                      : `${selectedForumCount} forum${selectedForumCount > 1 ? 's' : ''}`
                  }
                </Text>
              )}
            </View>
          </Pressable>
        </Pressable>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  keyboardView: {
    flex: 1,
  },
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
    paddingBottom: Platform.OS === 'ios' ? 34 : 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingBottom: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
  },
  scrollContent: {
    paddingHorizontal: 20,
    flexGrow: 1,
  },
  sourceCard: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  sourceLabel: {
    fontSize: 12,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  sourceName: {
    fontSize: 16,
    fontWeight: '600',
  },
  sourceValue: {
    fontSize: 14,
    marginTop: 4,
  },
  promptCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 16,
  },
  promptText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  inputSection: {
    marginBottom: 20,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    fontSize: 15,
    lineHeight: 22,
    minHeight: 120,
  },
  destinationsSection: {
    marginBottom: 16,
  },
  destinationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 4,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  destinationLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  destinationName: {
    fontSize: 15,
    fontWeight: '500',
  },
  destinationHint: {
    fontSize: 13,
  },
  forumsLabel: {
    fontSize: 12,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: 16,
    marginBottom: 8,
  },
  loadingForums: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 16,
  },
  loadingText: {
    fontSize: 14,
  },
  shareToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 10,
    paddingHorizontal: 38,
    marginBottom: 4,
  },
  toggleTrack: {
    width: 36,
    height: 20,
    borderRadius: 10,
    justifyContent: 'center',
    paddingHorizontal: 2,
  },
  toggleThumb: {
    width: 16,
    height: 16,
    borderRadius: 8,
  },
  toggleThumbActive: {
    alignSelf: 'flex-end',
  },
  shareLabel: {
    fontSize: 13,
  },
  noForumsCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    padding: 16,
    borderRadius: 10,
    borderWidth: 1,
    marginTop: 8,
  },
  noForumsText: {
    fontSize: 14,
  },
  errorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  errorText: {
    fontSize: 14,
    flex: 1,
  },
  successCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  successText: {
    fontSize: 14,
    fontWeight: '500',
  },
  footer: {
    paddingHorizontal: 20,
    paddingTop: 16,
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 16,
    borderRadius: 12,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  saveSummary: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
  },
});

export default UniversalReflectionModal;
