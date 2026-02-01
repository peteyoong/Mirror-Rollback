import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity,
  Modal,
  TextInput,
  ActivityIndicator,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Colors } from '../constants/colors';
import { format } from 'date-fns';
import { Ionicons } from '@expo/vector-icons';
import { integrateJournalEntry } from '../services/api';

interface JournalEntryItemProps {
  id: string;
  userId: string;
  content: string;
  created_at: string;
  themes?: string[];
}

export default function JournalEntryItem({
  id,
  userId,
  content,
  created_at,
  themes = [],
}: JournalEntryItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showReflectModal, setShowReflectModal] = useState(false);
  const [userQuestion, setUserQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [reflection, setReflection] = useState<{
    reflection: string;
    perspective?: string;
  } | null>(null);
  const [error, setError] = useState('');

  const formattedDate = format(new Date(created_at), 'MMM d, yyyy');
  const formattedTime = format(new Date(created_at), 'h:mm a');

  const handleReflect = async () => {
    setIsLoading(true);
    setError('');
    setReflection(null);

    try {
      const result = await integrateJournalEntry(
        userId,
        id,
        userQuestion.trim() || undefined
      );
      setReflection(result);
    } catch (err: any) {
      console.error('Reflect error:', err);
      setError('Unable to generate reflection. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const openReflectModal = () => {
    setShowReflectModal(true);
    setUserQuestion('');
    setReflection(null);
    setError('');
  };

  const closeReflectModal = () => {
    setShowReflectModal(false);
    setUserQuestion('');
    setReflection(null);
    setError('');
  };

  return (
    <>
      <TouchableOpacity 
        style={styles.container}
        onPress={() => setIsExpanded(!isExpanded)}
        activeOpacity={0.8}
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.date}>{formattedDate}</Text>
            <Text style={styles.time}>{formattedTime}</Text>
          </View>
          <Ionicons 
            name={isExpanded ? "chevron-up" : "chevron-down"} 
            size={18} 
            color={Colors.textTertiary} 
          />
        </View>
        
        <Text 
          style={styles.content} 
          numberOfLines={isExpanded ? undefined : 3}
        >
          {content}
        </Text>

        {themes.length > 0 && (
          <View style={styles.themesContainer}>
            {themes.map((theme, index) => (
              <View key={index} style={styles.themeTag}>
                <Text style={styles.themeText}>{theme}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Reflect with Mirror button */}
        <TouchableOpacity
          style={styles.reflectButton}
          onPress={(e) => {
            e.stopPropagation();
            openReflectModal();
          }}
          activeOpacity={0.7}
        >
          <Ionicons name="sparkles-outline" size={16} color={Colors.textSecondary} />
          <Text style={styles.reflectButtonText}>Reflect with Mirror</Text>
        </TouchableOpacity>
      </TouchableOpacity>

      {/* Reflection Modal */}
      <Modal
        visible={showReflectModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={closeReflectModal}
      >
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalContainer}
        >
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Reflect with Mirror</Text>
            <TouchableOpacity onPress={closeReflectModal} style={styles.closeButton}>
              <Ionicons name="close" size={24} color={Colors.text} />
            </TouchableOpacity>
          </View>

          <ScrollView 
            style={styles.modalContent}
            contentContainerStyle={styles.modalScrollContent}
            keyboardShouldPersistTaps="handled"
          >
            {/* Original entry preview */}
            <View style={styles.entryPreview}>
              <Text style={styles.previewLabel}>Your entry</Text>
              <Text style={styles.previewText} numberOfLines={4}>
                {content}
              </Text>
            </View>

            {/* Question input (optional) */}
            {!reflection && (
              <View style={styles.questionContainer}>
                <Text style={styles.questionLabel}>
                  What would you like to explore? (optional)
                </Text>
                <TextInput
                  style={styles.questionInput}
                  value={userQuestion}
                  onChangeText={setUserQuestion}
                  placeholder="e.g., What patterns might be at play here?"
                  placeholderTextColor={Colors.textTertiary}
                  multiline
                  maxLength={300}
                  editable={!isLoading}
                />
              </View>
            )}

            {/* Reflect button */}
            {!reflection && (
              <TouchableOpacity
                style={[styles.reflectActionButton, isLoading && styles.buttonDisabled]}
                onPress={handleReflect}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator size="small" color={Colors.background} />
                ) : (
                  <>
                    <Ionicons name="sparkles" size={18} color={Colors.background} />
                    <Text style={styles.reflectActionText}>Reflect</Text>
                  </>
                )}
              </TouchableOpacity>
            )}

            {/* Error */}
            {error && (
              <View style={styles.errorContainer}>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            )}

            {/* Reflection result */}
            {reflection && (
              <View style={styles.reflectionResult}>
                <View style={styles.reflectionHeader}>
                  <Ionicons name="sparkles" size={18} color={Colors.accent} />
                  <Text style={styles.reflectionLabel}>Mirror's reflection</Text>
                </View>
                
                <Text style={styles.reflectionText}>
                  {reflection.reflection}
                </Text>

                {reflection.perspective && (
                  <View style={styles.perspectiveContainer}>
                    <Text style={styles.perspectiveLabel}>Another perspective</Text>
                    <Text style={styles.perspectiveText}>
                      {reflection.perspective}
                    </Text>
                  </View>
                )}

                {/* Ask another question */}
                <TouchableOpacity
                  style={styles.askAnotherButton}
                  onPress={() => {
                    setReflection(null);
                    setUserQuestion('');
                  }}
                >
                  <Ionicons name="chatbubble-outline" size={16} color={Colors.textSecondary} />
                  <Text style={styles.askAnotherText}>Ask another question</Text>
                </TouchableOpacity>
              </View>
            )}
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  date: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  time: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 2,
  },
  content: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.text,
  },
  themesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 12,
  },
  themeTag: {
    backgroundColor: Colors.background,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginRight: 8,
    marginBottom: 8,
  },
  themeText: {
    fontSize: 11,
    color: Colors.textTertiary,
  },
  reflectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    gap: 8,
  },
  reflectButtonText: {
    fontSize: 13,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  // Modal styles
  modalContainer: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
  },
  closeButton: {
    padding: 4,
  },
  modalContent: {
    flex: 1,
  },
  modalScrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  entryPreview: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  previewLabel: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  previewText: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.textSecondary,
  },
  questionContainer: {
    marginBottom: 24,
  },
  questionLabel: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: 12,
  },
  questionInput: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    fontSize: 15,
    color: Colors.text,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  reflectActionButton: {
    backgroundColor: Colors.text,
    borderRadius: 12,
    paddingVertical: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  reflectActionText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.background,
  },
  errorContainer: {
    backgroundColor: Colors.error + '20',
    borderRadius: 8,
    padding: 12,
    marginTop: 16,
  },
  errorText: {
    fontSize: 13,
    color: Colors.error,
    textAlign: 'center',
  },
  reflectionResult: {
    marginTop: 8,
  },
  reflectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  reflectionLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.accent,
  },
  reflectionText: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.text,
  },
  perspectiveContainer: {
    marginTop: 24,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  perspectiveLabel: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  perspectiveText: {
    fontSize: 14,
    lineHeight: 22,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  askAnotherButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 32,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 12,
  },
  askAnotherText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
});
