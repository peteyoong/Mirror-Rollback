/**
 * PeopleLens V2.0 - Relationships Lens
 * 
 * ARCHITECTURE: One engine, three lenses.
 * 
 * THIS LENS (Life > Relationships):
 * - PRIMARY: User's general relationship pattern (identity-level)
 * - SECONDARY: People in your life (optional)
 * 
 * USER EXPERIENCE:
 * - Immediate value WITHOUT adding anyone
 * - "I understand how I behave in relationships"
 * - Then optionally: "I understand how to be with specific people better"
 * 
 * STRUCTURE:
 * ┌─────────────────────────────────────┐
 * │  YOUR RELATIONSHIP PATTERN          │
 * │  How you show up in connection      │
 * ├─────────────────────────────────────┤
 * │  CORE PATTERN                       │
 * │  DEFAULT TENSION                    │
 * │  GROWTH EDGE (emphasized)           │
 * │  GIFT                               │
 * │  TRY THIS                           │
 * └─────────────────────────────────────┘
 * 
 * ┌─────────────────────────────────────┐
 * │  PEOPLE IN YOUR LIFE (optional)     │
 * │  [List of saved people]             │
 * │  + Add Person                       │
 * └─────────────────────────────────────┘
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Modal,
  Platform,
  ActivityIndicator,
  KeyboardAvoidingView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getRelationshipPattern, RelationshipPatternResponse } from '../services/api';

// Relationship types for people
type RelationshipType = 'partner' | 'family' | 'friend' | 'work' | 'other';

interface Person {
  id: string;
  name: string;
  type: RelationshipType;
  context: string;
  createdAt: string;
}

interface PeopleLensProps {
  userId: string;
  theme: {
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    textTertiary: string;
    accent: string;
    border: string;
  };
}

const RELATIONSHIP_TYPES: { type: RelationshipType; label: string; icon: string }[] = [
  { type: 'partner', label: 'Partner', icon: 'heart' },
  { type: 'family', label: 'Family', icon: 'people' },
  { type: 'friend', label: 'Friend', icon: 'person' },
  { type: 'work', label: 'Work', icon: 'briefcase' },
  { type: 'other', label: 'Other', icon: 'ellipsis-horizontal' },
];

const TYPE_COLORS: Record<RelationshipType, string> = {
  partner: '#E91E63',
  family: '#9C27B0',
  friend: '#2196F3',
  work: '#4CAF50',
  other: '#607D8B',
};

const CONTEXT_SUGGESTIONS = [
  "Takes time to process",
  "Moves fast, decides quickly",
  "Senses the room before acting",
  "Direct communicator",
  "Keeps feelings private",
  "Emotionally open",
  "Needs to know the plan",
  "Goes with the flow",
  "Avoids conflict",
  "Addresses things directly",
];

const PeopleLens: React.FC<PeopleLensProps> = ({ userId, theme }) => {
  const router = useRouter();
  
  // Pattern state (primary)
  const [pattern, setPattern] = useState<RelationshipPatternResponse | null>(null);
  const [patternLoading, setPatternLoading] = useState(true);
  const [patternError, setPatternError] = useState<string | null>(null);
  
  // People state (secondary)
  const [people, setPeople] = useState<Person[]>([]);
  const [peopleLoading, setPeopleLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showPeopleSection, setShowPeopleSection] = useState(true);
  
  // Add person form state
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState<RelationshipType>('friend');
  const [newContext, setNewContext] = useState('');

  const STORAGE_KEY = `@mirror_people_${userId}`;

  useEffect(() => {
    loadPattern();
    loadPeople();
  }, [userId]);

  const loadPattern = async () => {
    try {
      setPatternLoading(true);
      setPatternError(null);
      const data = await getRelationshipPattern(userId);
      setPattern(data);
    } catch (err: any) {
      console.error('[PeopleLens] Error loading pattern:', err);
      setPatternError('Unable to load your relationship pattern');
    } finally {
      setPatternLoading(false);
    }
  };

  const loadPeople = async () => {
    try {
      setPeopleLoading(true);
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      if (stored) {
        setPeople(JSON.parse(stored));
      }
    } catch (err) {
      console.error('[PeopleLens] Error loading people:', err);
    } finally {
      setPeopleLoading(false);
    }
  };

  const savePeople = async (updatedPeople: Person[]) => {
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updatedPeople));
      setPeople(updatedPeople);
    } catch (err) {
      console.error('[PeopleLens] Error saving:', err);
    }
  };

  const handleAddPerson = () => {
    if (!newName.trim()) return;

    const person: Person = {
      id: Date.now().toString(),
      name: newName.trim(),
      type: newType,
      context: newContext.trim(),
      createdAt: new Date().toISOString(),
    };

    savePeople([...people, person]);
    resetForm();
    setShowAddModal(false);
  };

  const handleOpenInsight = (person: Person) => {
    const params = new URLSearchParams({
      name: person.name,
      context: person.context || '',
    });
    router.push(`/relationship-insight?${params}`);
  };

  const resetForm = () => {
    setNewName('');
    setNewType('friend');
    setNewContext('');
  };

  const toggleContextSuggestion = (suggestion: string) => {
    if (newContext.includes(suggestion)) {
      setNewContext(newContext.replace(suggestion, '').replace(/\.\s*\./g, '.').trim());
    } else {
      setNewContext(prev => prev ? `${prev}. ${suggestion}` : suggestion);
    }
  };

  // Split multi-line text
  const splitLines = (text: string): string[] => {
    return text.split('\n').filter(line => line.trim());
  };

  // Render pattern loading state
  if (patternLoading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.accent} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Reading your relationship pattern...
        </Text>
      </View>
    );
  }

  // Render pattern error state
  if (patternError || !pattern) {
    return (
      <View style={[styles.errorContainer, { backgroundColor: theme.background }]}>
        <Ionicons name="alert-circle-outline" size={48} color={theme.textTertiary} />
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {patternError || 'Unable to load pattern'}
        </Text>
        <TouchableOpacity 
          style={[styles.retryButton, { backgroundColor: theme.surface, borderColor: theme.border }]} 
          onPress={loadPattern}
        >
          <Text style={[styles.retryButtonText, { color: theme.text }]}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Render person card
  const renderPersonCard = (person: Person) => {
    const typeColor = TYPE_COLORS[person.type];
    const typeConfig = RELATIONSHIP_TYPES.find(t => t.type === person.type);

    return (
      <TouchableOpacity
        key={person.id}
        style={[styles.personCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
        onPress={() => handleOpenInsight(person)}
        activeOpacity={0.7}
      >
        <View style={styles.personCardContent}>
          <View style={[styles.typeIndicator, { backgroundColor: typeColor + '20' }]}>
            <Ionicons name={typeConfig?.icon as any} size={18} color={typeColor} />
          </View>
          
          <View style={styles.personInfo}>
            <Text style={[styles.personName, { color: theme.text }]}>
              {person.name}
            </Text>
            <Text style={[styles.personType, { color: theme.textTertiary }]}>
              {typeConfig?.label}
            </Text>
          </View>
          
          <Ionicons name="chevron-forward" size={18} color={theme.textTertiary} />
        </View>
      </TouchableOpacity>
    );
  };

  // Render add modal
  const renderAddModal = () => (
    <Modal
      visible={showAddModal}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowAddModal(false)}
    >
      <KeyboardAvoidingView 
        style={[styles.modalContainer, { backgroundColor: theme.background }]}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={styles.modalHeader}>
          <TouchableOpacity onPress={() => { setShowAddModal(false); resetForm(); }}>
            <Text style={[styles.modalCancel, { color: theme.textSecondary }]}>Cancel</Text>
          </TouchableOpacity>
          <Text style={[styles.modalTitle, { color: theme.text }]}>Add Person</Text>
          <TouchableOpacity 
            onPress={handleAddPerson}
            disabled={!newName.trim()}
          >
            <Text style={[
              styles.modalSave, 
              { color: newName.trim() ? theme.accent : theme.textTertiary }
            ]}>
              Save
            </Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.modalContent} showsVerticalScrollIndicator={false}>
          {/* Name input */}
          <View style={styles.inputSection}>
            <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>Name</Text>
            <TextInput
              style={[styles.textInput, { 
                backgroundColor: theme.surface, 
                color: theme.text,
                borderColor: theme.border,
              }]}
              value={newName}
              onChangeText={setNewName}
              placeholder="Their name"
              placeholderTextColor={theme.textTertiary}
              autoFocus
            />
          </View>

          {/* Relationship type */}
          <View style={styles.inputSection}>
            <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>Relationship</Text>
            <View style={styles.typeSelector}>
              {RELATIONSHIP_TYPES.map(({ type, label, icon }) => (
                <TouchableOpacity
                  key={type}
                  style={[
                    styles.typeOption,
                    { 
                      backgroundColor: newType === type ? TYPE_COLORS[type] + '20' : theme.surface,
                      borderColor: newType === type ? TYPE_COLORS[type] : theme.border,
                    }
                  ]}
                  onPress={() => setNewType(type)}
                >
                  <Ionicons 
                    name={icon as any} 
                    size={16} 
                    color={newType === type ? TYPE_COLORS[type] : theme.textSecondary} 
                  />
                  <Text style={[
                    styles.typeOptionText,
                    { color: newType === type ? TYPE_COLORS[type] : theme.textSecondary }
                  ]}>
                    {label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Context */}
          <View style={styles.inputSection}>
            <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>
              How do they operate?
            </Text>
            <Text style={[styles.inputHint, { color: theme.textTertiary }]}>
              This helps generate better insights
            </Text>
            
            <View style={styles.suggestions}>
              {CONTEXT_SUGGESTIONS.map((suggestion) => (
                <TouchableOpacity
                  key={suggestion}
                  style={[
                    styles.suggestionChip,
                    { 
                      backgroundColor: newContext.includes(suggestion) 
                        ? theme.accent + '20' 
                        : theme.surface,
                      borderColor: newContext.includes(suggestion) 
                        ? theme.accent 
                        : theme.border,
                    }
                  ]}
                  onPress={() => toggleContextSuggestion(suggestion)}
                >
                  <Text style={[
                    styles.suggestionText,
                    { color: newContext.includes(suggestion) ? theme.accent : theme.textSecondary }
                  ]}>
                    {suggestion}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <TextInput
              style={[styles.textAreaInput, { 
                backgroundColor: theme.surface, 
                color: theme.text,
                borderColor: theme.border,
              }]}
              value={newContext}
              onChangeText={setNewContext}
              placeholder="Or describe in your own words..."
              placeholderTextColor={theme.textTertiary}
              multiline
              numberOfLines={3}
            />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  );

  return (
    <ScrollView 
      style={[styles.container, { backgroundColor: theme.background }]}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
    >
      {/* ========================================
          PRIMARY: YOUR RELATIONSHIP PATTERN
          ======================================== */}
      <View style={styles.patternSection}>
        <View style={styles.patternHeader}>
          <Text style={[styles.patternTitle, { color: theme.text }]}>
            Your Relationship Pattern
          </Text>
          <Text style={[styles.patternSubtitle, { color: theme.textSecondary }]}>
            How you show up in connection
          </Text>
        </View>

        {/* CORE PATTERN */}
        <View style={[styles.patternCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            CORE PATTERN
          </Text>
          {splitLines(pattern.core_pattern).map((line, idx) => (
            <Text key={idx} style={[styles.patternText, { color: theme.text }]}>
              {line}
            </Text>
          ))}
        </View>

        {/* DEFAULT TENSION */}
        <View style={[styles.patternCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            DEFAULT TENSION
          </Text>
          {splitLines(pattern.default_tension).map((line, idx) => (
            <Text key={idx} style={[styles.patternText, { color: theme.text }]}>
              {line}
            </Text>
          ))}
        </View>

        {/* GROWTH EDGE (emphasized) */}
        <View style={[styles.growthEdgeCard, { borderColor: theme.accent }]}>
          <Text style={[styles.growthEdgeLabel, { color: theme.accent }]}>
            GROWTH EDGE
          </Text>
          {splitLines(pattern.growth_edge).map((line, idx) => (
            <Text key={idx} style={[styles.growthEdgeText, { color: theme.text }]}>
              {line}
            </Text>
          ))}
        </View>

        {/* GIFT */}
        <View style={[styles.giftCard, { backgroundColor: theme.accent + '08' }]}>
          <Text style={[styles.giftLabel, { color: theme.accent }]}>
            GIFT
          </Text>
          {splitLines(pattern.gift).map((line, idx) => (
            <Text key={idx} style={[styles.giftText, { color: theme.text }]}>
              {line}
            </Text>
          ))}
        </View>

        {/* WHAT RELATIONSHIPS ARE TEACHING YOU (NEW) */}
        {pattern.what_teaching && (
          <View style={[styles.teachingCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.teachingLabel, { color: theme.textTertiary }]}>
              WHAT RELATIONSHIPS ARE TEACHING YOU
            </Text>
            {splitLines(pattern.what_teaching).map((line, idx) => (
              <Text key={idx} style={[styles.teachingText, { color: theme.text }]}>
                {line}
              </Text>
            ))}
          </View>
        )}

        {/* TRY THIS */}
        <View style={[styles.tryThisCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.tryThisHeader}>
            <Ionicons name="arrow-forward-circle" size={16} color={theme.accent} />
            <Text style={[styles.tryThisLabel, { color: theme.accent }]}>
              TRY THIS
            </Text>
          </View>
          <Text style={[styles.tryThisText, { color: theme.text }]}>
            {pattern.try_this}
          </Text>
        </View>
      </View>

      {/* ========================================
          SECONDARY: PEOPLE IN YOUR LIFE
          ======================================== */}
      <View style={styles.peopleSection}>
        <TouchableOpacity 
          style={styles.peopleSectionHeader}
          onPress={() => setShowPeopleSection(!showPeopleSection)}
          activeOpacity={0.7}
        >
          <View>
            <Text style={[styles.peopleSectionTitle, { color: theme.text }]}>
              People in your life
            </Text>
            <Text style={[styles.peopleSectionSubtitle, { color: theme.textTertiary }]}>
              Understand specific dynamics
            </Text>
          </View>
          <Ionicons 
            name={showPeopleSection ? 'chevron-up' : 'chevron-down'} 
            size={20} 
            color={theme.textTertiary} 
          />
        </TouchableOpacity>

        {showPeopleSection && (
          <View style={styles.peopleContent}>
            {people.length === 0 ? (
              <View style={[styles.emptyPeople, { borderColor: theme.border }]}>
                <Text style={[styles.emptyPeopleText, { color: theme.textSecondary }]}>
                  Add someone to understand how to be with them
                </Text>
              </View>
            ) : (
              <View style={styles.peopleList}>
                {people.map(renderPersonCard)}
              </View>
            )}
            
            <TouchableOpacity
              style={[styles.addPersonButton, { borderColor: theme.border }]}
              onPress={() => setShowAddModal(true)}
              activeOpacity={0.7}
            >
              <Ionicons name="add" size={18} color={theme.accent} />
              <Text style={[styles.addPersonText, { color: theme.accent }]}>
                Add Person
              </Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* Bottom padding */}
      <View style={styles.bottomPadding} />

      {/* Add modal */}
      {renderAddModal()}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  
  // Loading/Error states
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 17,
    fontStyle: 'italic',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    gap: 16,
  },
  errorText: {
    fontSize: 17,
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 24,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },

  // Pattern section (PRIMARY)
  patternSection: {
    marginBottom: 32,
  },
  patternHeader: {
    marginBottom: 20,
  },
  patternTitle: {
    fontSize: 24,
    fontWeight: '600',
    letterSpacing: -0.3,
    marginBottom: 4,
  },
  patternSubtitle: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  
  // Pattern cards
  patternCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1.2,
    marginBottom: 14,
  },
  patternText: {
    fontSize: 17,
    lineHeight: 31,
    marginBottom: 4,
  },
  
  // Growth Edge (emphasized)
  growthEdgeCard: {
    borderLeftWidth: 3,
    paddingLeft: 16,
    paddingVertical: 16,
    marginBottom: 16,
  },
  growthEdgeLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1.5,
    marginBottom: 16,
  },
  growthEdgeText: {
    fontSize: 16,
    fontWeight: '500',
    lineHeight: 32,
    marginBottom: 6,
  },
  
  // Gift card
  giftCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  giftLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1.2,
    marginBottom: 14,
  },
  giftText: {
    fontSize: 17,
    lineHeight: 31,
    fontStyle: 'italic',
    marginBottom: 4,
  },
  
  // Teaching card (WHAT RELATIONSHIPS ARE TEACHING YOU)
  teachingCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
  },
  teachingLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 16,
  },
  teachingText: {
    fontSize: 17,
    lineHeight: 31,
    marginBottom: 4,
  },
  
  // Try This card
  tryThisCard: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
  },
  tryThisHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 14,
  },
  tryThisLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  tryThisText: {
    fontSize: 17,
    lineHeight: 31,
    fontWeight: '500',
  },

  // People section (SECONDARY)
  peopleSection: {
    paddingTop: 20,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.1)',
  },
  peopleSectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  peopleSectionTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 2,
  },
  peopleSectionSubtitle: {
    fontSize: 16,
  },
  peopleContent: {
    gap: 10,
  },
  
  // Empty state for people
  emptyPeople: {
    padding: 20,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    borderStyle: 'dashed',
    alignItems: 'center',
  },
  emptyPeopleText: {
    fontSize: 16,
    textAlign: 'center',
  },
  
  // People list
  peopleList: {
    gap: 8,
  },
  
  // Person card
  personCard: {
    borderRadius: 10,
    padding: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  personCardContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  typeIndicator: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  personInfo: {
    flex: 1,
  },
  personName: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 2,
  },
  personType: {
    fontSize: 14,
  },
  
  // Add person button
  addPersonButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    borderStyle: 'dashed',
  },
  addPersonText: {
    fontSize: 16,
    fontWeight: '500',
  },

  // Bottom padding
  bottomPadding: {
    height: 100,
  },

  // Modal
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(0,0,0,0.1)',
  },
  modalCancel: {
    fontSize: 16,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  modalSave: {
    fontSize: 16,
    fontWeight: '600',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },

  // Inputs
  inputSection: {
    marginBottom: 24,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 14,
  },
  inputHint: {
    fontSize: 16,
    marginBottom: 16,
  },
  textInput: {
    fontSize: 16,
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
  },
  textAreaInput: {
    fontSize: 16,
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    minHeight: 80,
    textAlignVertical: 'top',
  },

  // Type selector
  typeSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  typeOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    gap: 6,
  },
  typeOptionText: {
    fontSize: 16,
    fontWeight: '500',
  },

  // Suggestions
  suggestions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  suggestionChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 1,
  },
  suggestionText: {
    fontSize: 16,
  },
});

export default PeopleLens;
