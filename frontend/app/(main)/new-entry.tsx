import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
  ScrollView,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { api } from '../../src/services/api';
import { COLORS, SPACING, BORDER_RADIUS } from '../../src/constants/theme';

export default function NewJournalEntry() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const reflectOnQuestion = params.reflectOn as string || '';
  
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSave = async () => {
    if (!content.trim()) {
      setErrorMessage('Please write something before saving');
      if (Platform.OS !== 'web') {
        Alert.alert('Please write something before saving');
      }
      return;
    }

    setSaving(true);
    setErrorMessage('');
    
    try {
      await api.post('/journal', { content: content.trim() });
      router.replace('/(main)/journal');
    } catch (error: any) {
      console.error('Failed to save journal entry:', error);
      const message = 'Failed to save entry. Please try again.';
      setErrorMessage(message);
      if (Platform.OS !== 'web') {
        Alert.alert('Error', message);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    router.back();
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <View style={styles.header}>
          <TouchableOpacity onPress={handleCancel} style={styles.headerButton}>
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>New Entry</Text>
          <TouchableOpacity
            onPress={handleSave}
            disabled={saving}
            style={styles.headerButton}
          >
            {saving ? (
              <ActivityIndicator size="small" color={COLORS.accent} />
            ) : (
              <Text style={styles.saveText}>Save</Text>
            )}
          </TouchableOpacity>
        </View>

        <ScrollView 
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.dateContainer}>
            <Text style={styles.dateText}>
              {format(new Date(), 'EEEE, MMMM d, yyyy')}
            </Text>
          </View>

          {reflectOnQuestion ? (
            <View style={styles.promptContainer}>
              <Text style={styles.promptLabel}>Today's Reflection</Text>
              <Text style={styles.promptText}>{reflectOnQuestion}</Text>
            </View>
          ) : null}

          {errorMessage ? (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          ) : null}

          <TextInput
            style={styles.textInput}
            multiline
            placeholder="Write your thoughts..."
            placeholderTextColor={COLORS.secondary}
            value={content}
            onChangeText={setContent}
            autoFocus
            textAlignVertical="top"
          />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  keyboardView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  headerButton: {
    minWidth: 60,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: COLORS.primary,
  },
  cancelText: {
    fontSize: 16,
    color: COLORS.secondary,
  },
  saveText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.accent,
    textAlign: 'right',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: SPACING.lg,
    paddingBottom: SPACING.xxl,
  },
  dateContainer: {
    marginBottom: SPACING.md,
  },
  dateText: {
    fontSize: 14,
    color: COLORS.secondary,
  },
  promptContainer: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.accent,
  },
  promptLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.accent,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: SPACING.sm,
  },
  promptText: {
    fontSize: 16,
    color: COLORS.primary,
    lineHeight: 24,
    fontStyle: 'italic',
  },
  errorContainer: {
    backgroundColor: '#FEE2E2',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.md,
  },
  errorText: {
    color: '#DC2626',
    fontSize: 14,
    textAlign: 'center',
  },
  textInput: {
    flex: 1,
    minHeight: 300,
    fontSize: 18,
    color: COLORS.primary,
    lineHeight: 28,
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
  },
});
