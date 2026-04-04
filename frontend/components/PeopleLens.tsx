/**
 * PeopleLens V1.0
 * 
 * A lens for viewing and understanding the people in your life.
 * NOT just romantic relationships - includes all relationship types.
 * 
 * STRUCTURE:
 * - List of people (name + optional relationship type)
 * - Each person opens a Relationship Insight
 * 
 * RELATIONSHIP TYPES:
 * - Partner, Family, Friend, Work, Other
 * 
 * FINAL STANDARD:
 * User should feel: "I understand how to be with THIS person better"
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

// Relationship types
type RelationshipType = 'partner' | 'family' | 'friend' | 'work' | 'other';

interface Person {
  id: string;
  name: string;
  type: RelationshipType;
  context: string; // How they operate (for insight generation)
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

// Context prompts to help user describe the person
const CONTEXT_PROMPTS = [
  "How do they process things?",
  "How do they communicate?",
  "What's their energy like?",
];

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
  const [people, setPeople] = useState<Person[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null);
  
  // Add person form state
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState<RelationshipType>('friend');
  const [newContext, setNewContext] = useState('');

  const STORAGE_KEY = `@mirror_people_${userId}`;

  useEffect(() => {
    loadPeople();
  }, [userId]);

  const loadPeople = async () => {
    try {
      setIsLoading(true);
      const stored = await AsyncStorage.getItem(STORAGE_KEY);
      if (stored) {
        setPeople(JSON.parse(stored));
      }
    } catch (err) {
      console.error('[PeopleLens] Error loading:', err);
    } finally {
      setIsLoading(false);
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

  const handleDeletePerson = (personId: string) => {
    const updated = people.filter(p => p.id !== personId);
    savePeople(updated);
    setSelectedPerson(null);
  };

  const handleOpenInsight = (person: Person) => {
    // Navigate to relationship insight screen
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

  // Render empty state
  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Ionicons name="people-outline" size={64} color={theme.textTertiary} />
      <Text style={[styles.emptyTitle, { color: theme.text }]}>
        People in your life
      </Text>
      <Text style={[styles.emptySubtitle, { color: theme.textSecondary }]}>
        Add someone to understand how to be with them better
      </Text>
      <TouchableOpacity
        style={[styles.addButtonLarge, { backgroundColor: theme.accent }]}
        onPress={() => setShowAddModal(true)}
      >
        <Ionicons name="add" size={24} color="#fff" />
        <Text style={styles.addButtonLargeText}>Add Person</Text>
      </TouchableOpacity>
    </View>
  );

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
            <Ionicons name={typeConfig?.icon as any} size={20} color={typeColor} />
          </View>
          
          <View style={styles.personInfo}>
            <Text style={[styles.personName, { color: theme.text }]}>
              {person.name}
            </Text>
            <Text style={[styles.personType, { color: theme.textTertiary }]}>
              {typeConfig?.label}
            </Text>
          </View>
          
          <Ionicons name="chevron-forward" size={20} color={theme.textTertiary} />
        </View>
        
        {person.context && (
          <Text 
            style={[styles.personContext, { color: theme.textSecondary }]}
            numberOfLines={1}
          >
            {person.context}
          </Text>
        )}
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
                    size={18} 
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

          {/* Context / How they operate */}
          <View style={styles.inputSection}>
            <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>
              How do they operate?
            </Text>
            <Text style={[styles.inputHint, { color: theme.textTertiary }]}>
              This helps generate better insights
            </Text>
            
            {/* Suggestions */}
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

            {/* Free text input */}
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

  if (isLoading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.accent} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={[styles.title, { color: theme.text }]}>People</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Understand how to be with them
          </Text>
        </View>
        
        {people.length > 0 && (
          <TouchableOpacity
            style={[styles.addButton, { backgroundColor: theme.accent }]}
            onPress={() => setShowAddModal(true)}
          >
            <Ionicons name="add" size={24} color="#fff" />
          </TouchableOpacity>
        )}
      </View>

      {/* People list or empty state */}
      {people.length === 0 ? (
        renderEmptyState()
      ) : (
        <ScrollView 
          style={styles.listContainer}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        >
          {people.map(renderPersonCard)}
        </ScrollView>
      )}

      {/* Add modal */}
      {renderAddModal()}
    </View>
  );
};

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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 12,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 14,
    marginTop: 2,
  },
  addButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.15,
        shadowRadius: 4,
      },
      android: {
        elevation: 3,
      },
    }),
  },

  // Empty state
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginTop: 20,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 32,
  },
  addButtonLarge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
    gap: 8,
  },
  addButtonLargeText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },

  // List
  listContainer: {
    flex: 1,
  },
  listContent: {
    padding: 20,
    paddingTop: 8,
    gap: 12,
  },

  // Person card
  personCard: {
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
  },
  personCardContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  typeIndicator: {
    width: 40,
    height: 40,
    borderRadius: 20,
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
    fontSize: 13,
  },
  personContext: {
    fontSize: 13,
    marginTop: 10,
    fontStyle: 'italic',
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
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  inputHint: {
    fontSize: 13,
    marginBottom: 12,
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
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    gap: 6,
  },
  typeOptionText: {
    fontSize: 14,
    fontWeight: '500',
  },

  // Suggestions
  suggestions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  suggestionChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 1,
  },
  suggestionText: {
    fontSize: 13,
  },
});

export default PeopleLens;
