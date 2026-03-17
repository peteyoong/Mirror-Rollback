/**
 * LifelineEventEditor
 * 
 * Modal form for creating and editing lifeline events.
 * Supports all event fields with validation.
 * 
 * TASK 59: Separates emotional valence (how good/bad) from significance (how life-shaping)
 * - emotional_valence: 1-10 scale (1 = very difficult, 5 = mixed, 10 = very positive)
 * - significance_score: 1-10 scale (1 = very low, 5 = meaningful, 10 = life-changing)
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../../constants/colors';
import { useTheme } from '../../contexts/ThemeContext';
import { LifelineEvent } from './LifelineEventCard';

const CATEGORIES = [
  'Family',
  'Relationships',
  'Career',
  'Health',
  'Money',
  'Spirituality',
  'Turning Point',
  'Loss',
  'Achievement',
  'Move',
  'Identity',
];

interface Props {
  visible: boolean;
  event?: LifelineEvent | null;
  prefillYear?: number | null;
  onClose: () => void;
  onSave: (eventData: Partial<LifelineEvent>) => Promise<void>;
  onDelete?: (eventId: string) => Promise<void>;
}

export default function LifelineEventEditor({ visible, event, prefillYear, onClose, onSave, onDelete }: Props) {
  const { theme } = useTheme();
  const isEditing = !!event;

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [year, setYear] = useState('');
  const [age, setAge] = useState('');
  const [category, setCategory] = useState('');
  // TASK 59: Separate valence from significance
  const [emotionalValence, setEmotionalValence] = useState(5); // 1-10: 1=very difficult, 5=mixed, 10=very positive
  const [significanceScore, setSignificanceScore] = useState(5); // 1-10: 1=minor, 5=meaningful, 10=life-changing
  const [tags, setTags] = useState('');
  const [privacyLevel, setPrivacyLevel] = useState<'private' | 'shareable'>('private');

  // UI state
  const [isSaving, setIsSaving] = useState(false);
  const [showCategories, setShowCategories] = useState(false);
  const [error, setError] = useState('');

  // Initialize form when event changes
  useEffect(() => {
    if (event) {
      setTitle(event.title || '');
      setDescription(event.description || '');
      setYear(event.year?.toString() || '');
      setAge(event.age?.toString() || '');
      setCategory(event.category || '');
      // TASK 59: Load new fields with backward compatibility
      // emotional_valence: new field (default 5)
      // For old events, derive from emotional_tone if available
      if ((event as any).emotional_valence !== undefined) {
        setEmotionalValence((event as any).emotional_valence);
      } else if (event.emotional_tone) {
        // Map old categorical tone to numeric valence
        const toneToValence: Record<string, number> = {
          'positive': 8,
          'negative': 2,
          'mixed': 5,
          'neutral': 5,
        };
        setEmotionalValence(toneToValence[event.emotional_tone] || 5);
      } else {
        setEmotionalValence(5);
      }
      // significance_score: maps from old impact_score
      setSignificanceScore((event as any).significance_score || event.impact_score || 5);
      setTags(event.tags?.join(', ') || '');
      setPrivacyLevel(event.privacy_level || 'private');
    } else {
      resetForm();
      // If prefillYear is provided (from gap prompt), prefill the year field
      if (prefillYear) {
        setYear(prefillYear.toString());
      }
    }
  }, [event, visible, prefillYear]);

  const resetForm = () => {
    setTitle('');
    setDescription('');
    setYear('');
    setAge('');
    setCategory('');
    setEmotionalValence(5);
    setSignificanceScore(5);
    setTags('');
    setPrivacyLevel('private');
    setError('');
  };

  const handleSave = async () => {
    // Validation
    if (!title.trim()) {
      setError('Please add a title for this moment');
      return;
    }

    const yearNum = year ? parseInt(year, 10) : undefined;
    const ageNum = age ? parseInt(age, 10) : undefined;

    if (year && (isNaN(yearNum!) || yearNum! < 1900 || yearNum! > 2100)) {
      setError('Please enter a valid year (1900-2100)');
      return;
    }

    if (age && (isNaN(ageNum!) || ageNum! < 0 || ageNum! > 120)) {
      setError('Please enter a valid age (0-120)');
      return;
    }

    setError('');
    setIsSaving(true);

    try {
      // TASK 59: Save both emotional_valence and significance_score
      // Also derive emotional_tone from valence for backward compatibility
      const derivedTone = emotionalValence <= 3 ? 'negative' : 
                          emotionalValence <= 6 ? 'mixed' : 
                          emotionalValence >= 7 ? 'positive' : 'neutral';
      
      const eventData: Partial<LifelineEvent> & { 
        emotional_valence?: number; 
        significance_score?: number;
      } = {
        title: title.trim(),
        description: description.trim() || undefined,
        year: yearNum,
        age: ageNum,
        category: category || undefined,
        // Keep emotional_tone for backward compatibility
        emotional_tone: derivedTone as LifelineEvent['emotional_tone'],
        // New fields for Task 59
        emotional_valence: emotionalValence,
        significance_score: significanceScore,
        // Also save as impact_score for backward compatibility
        impact_score: significanceScore,
        tags: tags ? tags.split(',').map(t => t.trim()).filter(Boolean) : [],
        privacy_level: privacyLevel,
      };

      if (isEditing && event?.id) {
        eventData.id = event.id;
      }

      await onSave(eventData);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = () => {
    if (!event?.id || !onDelete) return;

    Alert.alert(
      'Delete moment?',
      'This will remove the moment from your lifeline and update related patterns.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            setIsSaving(true);
            try {
              await onDelete(event.id);
              // onClose is called by the parent after successful delete
            } catch (err: any) {
              setError(err.message || 'Failed to delete');
              setIsSaving(false);
            }
          },
        },
      ]
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView
        style={[styles.container, { backgroundColor: theme.background }]}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Header */}
        <View style={[styles.header, { borderBottomColor: theme.border }]}>
          <TouchableOpacity onPress={onClose} style={styles.headerButton}>
            <Text style={[styles.cancelText, { color: theme.textSecondary }]}>Cancel</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            {isEditing ? 'Edit Moment' : 'Add Moment'}
          </Text>
          <TouchableOpacity
            onPress={handleSave}
            style={styles.headerButton}
            disabled={isSaving}
          >
            {isSaving ? (
              <ActivityIndicator size="small" color={theme.accent} />
            ) : (
              <Text style={[styles.saveText, { color: theme.accent }]}>Save</Text>
            )}
          </TouchableOpacity>
        </View>

        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Error Message */}
          {error ? (
            <View style={[styles.errorBox, { backgroundColor: `${Colors.error}15` }]}>
              <Text style={[styles.errorText, { color: Colors.error }]}>{error}</Text>
            </View>
          ) : null}

          {/* Title */}
          <View style={styles.fieldGroup}>
            <Text style={[styles.label, { color: theme.text }]}>What happened? *</Text>
            <TextInput
              style={[styles.input, { backgroundColor: theme.surface, borderColor: theme.border, color: theme.text }]}
              value={title}
              onChangeText={setTitle}
              placeholder="e.g., Started my first job"
              placeholderTextColor={theme.textTertiary}
              maxLength={100}
            />
          </View>

          {/* Description */}
          <View style={styles.fieldGroup}>
            <Text style={[styles.label, { color: theme.text }]}>More details</Text>
            <TextInput
              style={[styles.textArea, { backgroundColor: theme.surface, borderColor: theme.border, color: theme.text }]}
              value={description}
              onChangeText={setDescription}
              placeholder="What made this moment significant?"
              placeholderTextColor={theme.textTertiary}
              multiline
              numberOfLines={4}
              textAlignVertical="top"
              maxLength={500}
            />
          </View>

          {/* Year / Age */}
          <View style={styles.rowFields}>
            <View style={[styles.fieldGroup, { flex: 1 }]}>
              <Text style={[styles.label, { color: theme.text }]}>Year</Text>
              <TextInput
                style={[styles.input, { backgroundColor: theme.surface, borderColor: theme.border, color: theme.text }]}
                value={year}
                onChangeText={setYear}
                placeholder="2015"
                placeholderTextColor={theme.textTertiary}
                keyboardType="number-pad"
                maxLength={4}
              />
            </View>
            <View style={[styles.fieldGroup, { flex: 1 }]}>
              <Text style={[styles.label, { color: theme.text }]}>Or Age</Text>
              <TextInput
                style={[styles.input, { backgroundColor: theme.surface, borderColor: theme.border, color: theme.text }]}
                value={age}
                onChangeText={setAge}
                placeholder="25"
                placeholderTextColor={theme.textTertiary}
                keyboardType="number-pad"
                maxLength={3}
              />
            </View>
          </View>

          {/* Category */}
          <View style={styles.fieldGroup}>
            <Text style={[styles.label, { color: theme.text }]}>Category</Text>
            <TouchableOpacity
              style={[styles.selectButton, { backgroundColor: theme.surface, borderColor: theme.border }]}
              onPress={() => setShowCategories(!showCategories)}
            >
              <Text style={[styles.selectText, { color: category ? theme.text : theme.textTertiary }]}>
                {category || 'Select category'}
              </Text>
              <Ionicons name={showCategories ? 'chevron-up' : 'chevron-down'} size={18} color={theme.textTertiary} />
            </TouchableOpacity>
            {showCategories && (
              <View style={[styles.optionsList, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                {CATEGORIES.map((cat) => (
                  <TouchableOpacity
                    key={cat}
                    style={[styles.optionItem, category === cat && { backgroundColor: `${theme.accent}15` }]}
                    onPress={() => {
                      setCategory(cat);
                      setShowCategories(false);
                    }}
                  >
                    <Text style={[styles.optionText, { color: theme.text }]}>{cat}</Text>
                    {category === cat && <Ionicons name="checkmark" size={18} color={theme.accent} />}
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>

          {/* Emotional Valence - TASK 59: New scale for how the period felt */}
          <View style={styles.fieldGroup}>
            <Text style={[styles.label, { color: theme.text }]}>How did this period feel overall?</Text>
            <View style={styles.scaleGuidance}>
              <Text style={[styles.scaleGuideText, { color: theme.textTertiary }]}>Very difficult</Text>
              <Text style={[styles.scaleGuideArrow, { color: theme.textTertiary }]}>← 1 · · · · 5 · · · · 10 →</Text>
              <Text style={[styles.scaleGuideText, { color: theme.textTertiary }]}>Very positive</Text>
            </View>
            <View style={styles.scaleRow}>
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((score) => {
                // Color gradient from red (1) through yellow (5) to green (10)
                const getValenceColor = (val: number) => {
                  if (val <= 3) return '#E57373'; // Red - difficult
                  if (val <= 6) return '#FFB74D'; // Orange/Yellow - mixed
                  return '#81C784'; // Green - positive
                };
                const isSelected = emotionalValence === score;
                const scoreColor = getValenceColor(score);
                return (
                  <TouchableOpacity
                    key={score}
                    style={[
                      styles.scaleButton,
                      { borderColor: isSelected ? scoreColor : theme.border },
                      isSelected && { backgroundColor: `${scoreColor}25` },
                    ]}
                    onPress={() => setEmotionalValence(score)}
                  >
                    <Text style={[
                      styles.scaleText, 
                      { color: isSelected ? scoreColor : theme.textSecondary }
                    ]}>
                      {score}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
            <View style={styles.scaleCalibration}>
              <Text style={[styles.calibrationText, { color: theme.textTertiary }]}>1 = Very difficult</Text>
              <Text style={[styles.calibrationText, { color: theme.textTertiary }]}>5 = Mixed / neutral</Text>
              <Text style={[styles.calibrationText, { color: theme.textTertiary }]}>10 = Very positive</Text>
            </View>
          </View>

          {/* Significance Score - TASK 59: New scale for how life-shaping */}
          <View style={styles.fieldGroup}>
            <Text style={[styles.label, { color: theme.text }]}>How much did this shape your life?</Text>
            <View style={styles.scaleGuidance}>
              <Text style={[styles.scaleGuideText, { color: theme.textTertiary }]}>Very low</Text>
              <Text style={[styles.scaleGuideArrow, { color: theme.textTertiary }]}>← 1 · · · · 5 · · · · 10 →</Text>
              <Text style={[styles.scaleGuideText, { color: theme.textTertiary }]}>Very high</Text>
            </View>
            <View style={styles.scaleRow}>
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((score) => {
                const isSelected = significanceScore === score;
                return (
                  <TouchableOpacity
                    key={score}
                    style={[
                      styles.scaleButton,
                      { borderColor: isSelected ? theme.accent : theme.border },
                      isSelected && { backgroundColor: `${theme.accent}20` },
                    ]}
                    onPress={() => setSignificanceScore(score)}
                  >
                    <Text style={[
                      styles.scaleText, 
                      { color: isSelected ? theme.accent : theme.textSecondary }
                    ]}>
                      {score}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
            <View style={styles.scaleCalibration}>
              <Text style={[styles.calibrationText, { color: theme.textTertiary }]}>1 = Very low</Text>
              <Text style={[styles.calibrationText, { color: theme.textTertiary }]}>5 = Meaningful</Text>
              <Text style={[styles.calibrationText, { color: theme.textTertiary }]}>10 = Life-changing</Text>
            </View>
          </View>

          {/* Tags */}
          <View style={styles.fieldGroup}>
            <Text style={[styles.label, { color: theme.text }]}>Tags</Text>
            <TextInput
              style={[styles.input, { backgroundColor: theme.surface, borderColor: theme.border, color: theme.text }]}
              value={tags}
              onChangeText={setTags}
              placeholder="growth, family, milestone (comma-separated)"
              placeholderTextColor={theme.textTertiary}
              autoCapitalize="none"
            />
          </View>

          {/* Privacy */}
          <View style={styles.fieldGroup}>
            <Text style={[styles.label, { color: theme.text }]}>Privacy</Text>
            <View style={styles.privacyRow}>
              <TouchableOpacity
                style={[
                  styles.privacyButton,
                  { borderColor: privacyLevel === 'private' ? theme.accent : theme.border },
                  privacyLevel === 'private' && { backgroundColor: `${theme.accent}15` },
                ]}
                onPress={() => setPrivacyLevel('private')}
              >
                <Ionicons name="lock-closed-outline" size={16} color={privacyLevel === 'private' ? theme.accent : theme.textSecondary} />
                <Text style={[styles.privacyText, { color: privacyLevel === 'private' ? theme.accent : theme.textSecondary }]}>Private</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.privacyButton,
                  { borderColor: privacyLevel === 'shareable' ? theme.accent : theme.border },
                  privacyLevel === 'shareable' && { backgroundColor: `${theme.accent}15` },
                ]}
                onPress={() => setPrivacyLevel('shareable')}
              >
                <Ionicons name="people-outline" size={16} color={privacyLevel === 'shareable' ? theme.accent : theme.textSecondary} />
                <Text style={[styles.privacyText, { color: privacyLevel === 'shareable' ? theme.accent : theme.textSecondary }]}>Shareable</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Delete Button (for editing) */}
          {isEditing && onDelete && (
            <TouchableOpacity
              style={[styles.deleteButton, { borderColor: Colors.error }]}
              onPress={handleDelete}
            >
              <Ionicons name="trash-outline" size={18} color={Colors.error} />
              <Text style={[styles.deleteText, { color: Colors.error }]}>Delete this moment</Text>
            </TouchableOpacity>
          )}

          <View style={styles.bottomSpacer} />
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  headerButton: {
    minWidth: 60,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  cancelText: {
    fontSize: 16,
  },
  saveText: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'right',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  errorBox: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  fieldGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
  },
  textArea: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    minHeight: 100,
  },
  rowFields: {
    flexDirection: 'row',
    gap: 12,
  },
  selectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  selectText: {
    fontSize: 16,
  },
  optionsList: {
    borderWidth: 1,
    borderRadius: 10,
    marginTop: 8,
    overflow: 'hidden',
  },
  optionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  optionText: {
    fontSize: 15,
  },
  toneRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  toneButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 20,
    borderWidth: 1,
    gap: 6,
  },
  toneDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  toneText: {
    fontSize: 13,
    fontWeight: '500',
  },
  // TASK 59: New two-scale rating styles
  scaleRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    justifyContent: 'center',
  },
  scaleGuidance: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
    paddingHorizontal: 2,
  },
  scaleGuideText: {
    fontSize: 11,
    fontWeight: '500',
  },
  scaleGuideArrow: {
    fontSize: 10,
    letterSpacing: 0.5,
    fontWeight: '400',
  },
  scaleCalibration: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
    paddingHorizontal: 2,
  },
  scaleButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scaleText: {
    fontSize: 13,
    fontWeight: '600',
  },
  // Keep old impact styles for backward compatibility
  impactRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  impactGuidance: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
    paddingHorizontal: 2,
  },
  impactGuideText: {
    fontSize: 12,
    fontWeight: '500',
  },
  impactGuideArrow: {
    fontSize: 11,
    letterSpacing: 0.5,
  },
  impactCalibration: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
    paddingHorizontal: 2,
  },
  calibrationText: {
    fontSize: 11,
  },
  // Task 54: Success banner styles
  lunarSuccessBanner: {
    marginBottom: 16,
    padding: 12,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  lunarSuccessText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#81C784',
  },
  impactButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  impactText: {
    fontSize: 13,
    fontWeight: '500',
  },
  privacyRow: {
    flexDirection: 'row',
    gap: 12,
  },
  privacyButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 10,
    borderWidth: 1,
    gap: 8,
  },
  privacyText: {
    fontSize: 14,
    fontWeight: '500',
  },
  deleteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginTop: 20,
    gap: 8,
  },
  deleteText: {
    fontSize: 15,
    fontWeight: '500',
  },
  bottomSpacer: {
    height: 40,
  },
});
