import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  Modal,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { api } from '../../src/services/api';
import { COLORS, SPACING, BORDER_RADIUS } from '../../src/constants/theme';

interface JournalEntry {
  id: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export default function Journal() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [currentEntry, setCurrentEntry] = useState<JournalEntry | null>(null);
  const [entryContent, setEntryContent] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchEntries = useCallback(async () => {
    try {
      const response = await api.get('/journal');
      setEntries(response.data);
    } catch (error) {
      console.error('Failed to fetch journal entries:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchEntries();
  };

  const openNewEntry = () => {
    setCurrentEntry(null);
    setEntryContent('');
    setModalVisible(true);
  };

  const openEditEntry = (entry: JournalEntry) => {
    setCurrentEntry(entry);
    setEntryContent(entry.content);
    setModalVisible(true);
  };

  const saveEntry = async () => {
    if (!entryContent.trim()) {
      Alert.alert('Please write something before saving');
      return;
    }

    setSaving(true);
    try {
      if (currentEntry) {
        await api.put(`/journal/${currentEntry.id}`, { content: entryContent });
      } else {
        await api.post('/journal', { content: entryContent });
      }
      setModalVisible(false);
      fetchEntries();
    } catch (error) {
      Alert.alert('Error', 'Failed to save entry');
    } finally {
      setSaving(false);
    }
  };

  const deleteEntry = async (entryId: string) => {
    Alert.alert(
      'Delete Entry',
      'Are you sure you want to delete this reflection?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/journal/${entryId}`);
              fetchEntries();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete entry');
            }
          },
        },
      ]
    );
  };

  const renderEntry = ({ item }: { item: JournalEntry }) => (
    <TouchableOpacity
      style={styles.entryCard}
      onPress={() => openEditEntry(item)}
      onLongPress={() => deleteEntry(item.id)}
    >
      <Text style={styles.entryDate}>
        {format(new Date(item.created_at), 'EEEE, MMMM d, yyyy')}
      </Text>
      <Text style={styles.entryPreview} numberOfLines={3}>
        {item.content}
      </Text>
    </TouchableOpacity>
  );

  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      <Ionicons name="book-outline" size={48} color={COLORS.border} />
      <Text style={styles.emptyTitle}>Your journal awaits</Text>
      <Text style={styles.emptySubtitle}>
        Start capturing your reflections and thoughts
      </Text>
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.accent} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Journal</Text>
        <TouchableOpacity style={styles.addButton} onPress={openNewEntry}>
          <Ionicons name="add" size={28} color={COLORS.accent} />
        </TouchableOpacity>
      </View>

      <FlatList
        data={entries}
        keyExtractor={(item) => item.id}
        renderItem={renderEntry}
        contentContainerStyle={[
          styles.listContent,
          entries.length === 0 && styles.emptyListContent,
        ]}
        ListEmptyComponent={renderEmpty}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={COLORS.accent}
          />
        }
      />

      <Modal
        visible={modalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setModalVisible(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.modalKeyboard}
          >
            <View style={styles.modalHeader}>
              <TouchableOpacity
                onPress={() => setModalVisible(false)}
                style={styles.modalCloseButton}
              >
                <Text style={styles.modalCloseText}>Cancel</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>
                {currentEntry ? 'Edit Entry' : 'New Entry'}
              </Text>
              <TouchableOpacity
                onPress={saveEntry}
                disabled={saving}
                style={styles.modalSaveButton}
              >
                {saving ? (
                  <ActivityIndicator size="small" color={COLORS.accent} />
                ) : (
                  <Text style={styles.modalSaveText}>Save</Text>
                )}
              </TouchableOpacity>
            </View>

            <View style={styles.modalDateContainer}>
              <Text style={styles.modalDate}>
                {format(new Date(), 'EEEE, MMMM d, yyyy')}
              </Text>
            </View>

            <TextInput
              style={styles.modalInput}
              multiline
              placeholder="What's on your mind?"
              placeholderTextColor={COLORS.secondary}
              value={entryContent}
              onChangeText={setEntryContent}
              autoFocus
              textAlignVertical="top"
            />
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
  },
  title: {
    fontSize: 28,
    fontWeight: '300',
    color: COLORS.primary,
  },
  addButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    padding: SPACING.lg,
    paddingBottom: SPACING.xxl,
  },
  emptyListContent: {
    flexGrow: 1,
  },
  entryCard: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 4,
    elevation: 1,
  },
  entryDate: {
    fontSize: 12,
    color: COLORS.secondary,
    marginBottom: SPACING.sm,
  },
  entryPreview: {
    fontSize: 16,
    color: COLORS.primary,
    lineHeight: 24,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SPACING.xl,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '300',
    color: COLORS.primary,
    marginTop: SPACING.lg,
  },
  emptySubtitle: {
    fontSize: 14,
    color: COLORS.secondary,
    textAlign: 'center',
    marginTop: SPACING.sm,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  modalKeyboard: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  modalCloseButton: {
    width: 60,
  },
  modalCloseText: {
    color: COLORS.secondary,
    fontSize: 16,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: COLORS.primary,
  },
  modalSaveButton: {
    width: 60,
    alignItems: 'flex-end',
  },
  modalSaveText: {
    color: COLORS.accent,
    fontSize: 16,
    fontWeight: '600',
  },
  modalDateContainer: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
  },
  modalDate: {
    fontSize: 14,
    color: COLORS.secondary,
  },
  modalInput: {
    flex: 1,
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.md,
    fontSize: 18,
    color: COLORS.primary,
    lineHeight: 28,
  },
});
