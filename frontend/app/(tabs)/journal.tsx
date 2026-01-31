import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Keyboard,
  TouchableWithoutFeedback,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import JournalEntryItem from '../../components/JournalEntryItem';
import ChatBot from '../../components/ChatBot';
import { createJournalEntry, getJournalEntries } from '../../services/api';
import { Ionicons } from '@expo/vector-icons';

export default function JournalScreen() {
  const { user, journalEntries, setJournalEntries, addJournalEntry } = useAppStore();
  const [newEntry, setNewEntry] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadEntries();
  }, []);

  const loadEntries = async () => {
    if (!user) return;

    setIsLoading(true);
    try {
      const entries = await getJournalEntries(user.id);
      setJournalEntries(entries);
    } catch (err) {
      console.error('Load entries error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!user || !newEntry.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setError('');

    try {
      const entry = await createJournalEntry(user.id, newEntry.trim());
      addJournalEntry(entry);
      setNewEntry('');
    } catch (err: any) {
      console.error('Create entry error:', err);
      setError('Unable to save entry. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!user) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.centered}>
          <Text style={styles.errorText}>No user found</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <View style={styles.content}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Journal</Text>
            <Text style={styles.subtitle}>
              A private space for your thoughts and reflections.
            </Text>
          </View>

          {/* New Entry Input */}
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              value={newEntry}
              onChangeText={setNewEntry}
              placeholder="What's on your mind?"
              placeholderTextColor={Colors.textTertiary}
              multiline
              maxLength={2000}
              editable={!isSubmitting}
            />
            <TouchableOpacity
              style={[
                styles.submitButton,
                (!newEntry.trim() || isSubmitting) && styles.submitButtonDisabled,
              ]}
              onPress={handleSubmit}
              disabled={!newEntry.trim() || isSubmitting}
            >
              {isSubmitting ? (
                <ActivityIndicator size="small" color={Colors.background} />
              ) : (
                <Ionicons name="checkmark" size={20} color={Colors.background} />
              )}
            </TouchableOpacity>
          </View>

          {error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {/* Entries List */}
          {isLoading ? (
            <View style={styles.centered}>
              <ActivityIndicator size="large" color={Colors.textSecondary} />
            </View>
          ) : journalEntries.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Ionicons name="book-outline" size={48} color={Colors.textTertiary} />
              <Text style={styles.emptyText}>No entries yet</Text>
              <Text style={styles.emptySubtext}>
                Start journaling to track your reflections over time.
              </Text>
            </View>
          ) : (
            <FlatList
              data={journalEntries}
              keyExtractor={(item) => item.id}
              renderItem={({ item }) => (
                <JournalEntryItem
                  content={item.content}
                  created_at={item.created_at}
                  themes={item.themes}
                />
              )}
              contentContainerStyle={styles.listContent}
              showsVerticalScrollIndicator={false}
            />
          )}
        </View>
      </KeyboardAvoidingView>

      {/* Persistent Chatbot */}
      <ChatBot userId={user.id} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 24,
    paddingBottom: 100,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.textTertiary,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    marginBottom: 24,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    fontSize: 15,
    color: Colors.text,
    minHeight: 80,
    maxHeight: 160,
    marginRight: 12,
    textAlignVertical: 'top',
  },
  submitButton: {
    width: 48,
    height: 48,
    backgroundColor: Colors.text,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  submitButtonDisabled: {
    opacity: 0.4,
  },
  errorContainer: {
    backgroundColor: Colors.error + '20',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 13,
    color: Colors.error,
  },
  listContent: {
    paddingBottom: 24,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginTop: 8,
    maxWidth: 250,
  },
});