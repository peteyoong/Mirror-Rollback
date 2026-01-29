import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  ScrollView,
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

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  message_text: string;
  created_at: string;
}

export default function Journal() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [currentEntry, setCurrentEntry] = useState<JournalEntry | null>(null);
  const [entryContent, setEntryContent] = useState('');
  const [saving, setSaving] = useState(false);
  
  // Integrative Chat state
  const [chatModalVisible, setChatModalVisible] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const chatScrollRef = useRef<ScrollView>(null);

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

  // Integrative Chat functions
  const openChat = async () => {
    setChatModalVisible(true);
    await fetchChatHistory();
  };

  const fetchChatHistory = async () => {
    setLoadingChat(true);
    try {
      const response = await api.get('/journal/chat');
      setChatMessages(response.data);
      setTimeout(() => chatScrollRef.current?.scrollToEnd({ animated: false }), 100);
    } catch (error) {
      console.error('Failed to fetch chat history:', error);
    } finally {
      setLoadingChat(false);
    }
  };

  const sendMessage = async () => {
    if (!chatInput.trim() || sendingMessage) return;

    const messageText = chatInput.trim();
    setChatInput('');
    setSendingMessage(true);

    try {
      const response = await api.post('/journal/chat', { message: messageText });
      setChatMessages(prev => [...prev, ...response.data]);
      setTimeout(() => chatScrollRef.current?.scrollToEnd({ animated: true }), 100);
    } catch (error) {
      console.error('Failed to send message:', error);
      Alert.alert('Error', 'Failed to send message. Please try again.');
      setChatInput(messageText);
    } finally {
      setSendingMessage(false);
    }
  };

  const clearChat = async () => {
    Alert.alert(
      'Clear Conversation',
      'This will clear your integrative chat history. Your journal entries will not be affected.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete('/journal/chat');
              setChatMessages([]);
            } catch (error) {
              Alert.alert('Error', 'Failed to clear chat');
            }
          },
        },
      ]
    );
  };

  const renderChatMessage = (message: ChatMessage, index: number) => (
    <View
      key={message.id || index}
      style={[
        styles.chatMessage,
        message.role === 'user' ? styles.chatMessageUser : styles.chatMessageAssistant
      ]}
    >
      <Text style={[
        styles.chatMessageText,
        message.role === 'user' ? styles.chatMessageTextUser : styles.chatMessageTextAssistant
      ]}>
        {message.message_text}
      </Text>
    </View>
  );

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
        <View style={styles.headerButtons}>
          <TouchableOpacity style={styles.headerButton} onPress={openChat}>
            <Ionicons name="chatbubbles-outline" size={24} color={COLORS.accent} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerButton} onPress={openNewEntry}>
            <Ionicons name="add" size={28} color={COLORS.accent} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Integrate Mode Banner */}
      <TouchableOpacity style={styles.chatBanner} onPress={openChat}>
        <View style={styles.chatBannerIcon}>
          <Ionicons name="sparkles" size={20} color={COLORS.accent} />
        </View>
        <View style={styles.chatBannerText}>
          <Text style={styles.chatBannerTitle}>Integrate</Text>
          <Text style={styles.chatBannerSubtitle}>Make sense of your experience over time</Text>
        </View>
        <Ionicons name="chevron-forward" size={20} color={COLORS.secondary} />
      </TouchableOpacity>

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

      {/* Entry Modal */}
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

      {/* Integrative Chat Modal */}
      <Modal
        visible={chatModalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setChatModalVisible(false)}
      >
        <SafeAreaView style={styles.chatModalContainer}>
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.chatModalKeyboard}
          >
            {/* Chat Header */}
            <View style={styles.chatHeader}>
              <TouchableOpacity
                onPress={() => setChatModalVisible(false)}
                style={styles.chatCloseButton}
              >
                <Ionicons name="close" size={24} color={COLORS.primary} />
              </TouchableOpacity>
              <View style={styles.chatTitleContainer}>
                <Text style={styles.chatTitle}>Integrate</Text>
                <Text style={styles.chatSubtitle}>Make sense of your experience over time</Text>
              </View>
              <TouchableOpacity
                onPress={clearChat}
                style={styles.chatClearButton}
              >
                <Ionicons name="trash-outline" size={20} color={COLORS.secondary} />
              </TouchableOpacity>
            </View>

            {/* Chat Messages */}
            <ScrollView
              ref={chatScrollRef}
              style={styles.chatMessagesContainer}
              contentContainerStyle={styles.chatMessagesContent}
            >
              {loadingChat ? (
                <ActivityIndicator size="large" color={COLORS.accent} style={styles.chatLoading} />
              ) : chatMessages.length === 0 ? (
                <View style={styles.chatEmptyContainer}>
                  <Ionicons name="sparkles-outline" size={48} color={COLORS.border} />
                  <Text style={styles.chatEmptyTitle}>Start a conversation</Text>
                  <Text style={styles.chatEmptySubtitle}>
                    I can help you see patterns across your journals, reflections, and framework explorations.
                  </Text>
                  <View style={styles.chatSuggestions}>
                    <Text style={styles.chatSuggestionsTitle}>Try asking:</Text>
                    <TouchableOpacity
                      style={styles.chatSuggestion}
                      onPress={() => setChatInput("What themes have been showing up in my recent reflections?")}
                    >
                      <Text style={styles.chatSuggestionText}>
                        "What themes have been showing up in my recent reflections?"
                      </Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={styles.chatSuggestion}
                      onPress={() => setChatInput("Is there a pattern in what I've been journaling about?")}
                    >
                      <Text style={styles.chatSuggestionText}>
                        "Is there a pattern in what I've been journaling about?"
                      </Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={styles.chatSuggestion}
                      onPress={() => setChatInput("Help me connect the dots across what I've been exploring.")}
                    >
                      <Text style={styles.chatSuggestionText}>
                        "Help me connect the dots across what I've been exploring."
                      </Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ) : (
                chatMessages.map(renderChatMessage)
              )}
              {sendingMessage && (
                <View style={[styles.chatMessage, styles.chatMessageAssistant]}>
                  <ActivityIndicator size="small" color={COLORS.accent} />
                </View>
              )}
            </ScrollView>

            {/* Chat Input */}
            <View style={styles.chatInputContainer}>
              <TextInput
                style={styles.chatInput}
                placeholder="Ask about patterns in your journey..."
                placeholderTextColor={COLORS.secondary}
                value={chatInput}
                onChangeText={setChatInput}
                multiline
                maxLength={1000}
              />
              <TouchableOpacity
                style={[
                  styles.chatSendButton,
                  (!chatInput.trim() || sendingMessage) && styles.chatSendButtonDisabled
                ]}
                onPress={sendMessage}
                disabled={!chatInput.trim() || sendingMessage}
              >
                <Ionicons
                  name="send"
                  size={20}
                  color={chatInput.trim() && !sendingMessage ? COLORS.white : COLORS.secondary}
                />
              </TouchableOpacity>
            </View>
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
  headerButtons: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  // Chat Banner Styles
  chatBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    marginHorizontal: SPACING.lg,
    marginBottom: SPACING.md,
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  chatBannerIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F5F8F3',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  chatBannerText: {
    flex: 1,
  },
  chatBannerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
  },
  chatBannerSubtitle: {
    fontSize: 13,
    color: COLORS.secondary,
    marginTop: 2,
  },
  listContent: {
    padding: SPACING.lg,
    paddingTop: SPACING.sm,
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
  // Chat Modal Styles
  chatModalContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  chatModalKeyboard: {
    flex: 1,
  },
  chatHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: COLORS.white,
  },
  chatCloseButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chatTitleContainer: {
    flex: 1,
    alignItems: 'center',
  },
  chatTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: COLORS.primary,
  },
  chatSubtitle: {
    fontSize: 12,
    color: COLORS.secondary,
    marginTop: 2,
  },
  chatClearButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chatMessagesContainer: {
    flex: 1,
  },
  chatMessagesContent: {
    padding: SPACING.md,
    paddingBottom: SPACING.lg,
  },
  chatLoading: {
    marginTop: SPACING.xl,
  },
  chatEmptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: SPACING.xl,
    paddingTop: SPACING.xxl,
  },
  chatEmptyTitle: {
    fontSize: 20,
    fontWeight: '300',
    color: COLORS.primary,
    marginTop: SPACING.lg,
  },
  chatEmptySubtitle: {
    fontSize: 14,
    color: COLORS.secondary,
    textAlign: 'center',
    marginTop: SPACING.sm,
    lineHeight: 20,
  },
  chatSuggestions: {
    marginTop: SPACING.xl,
    width: '100%',
  },
  chatSuggestionsTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.secondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: SPACING.sm,
  },
  chatSuggestion: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  chatSuggestionText: {
    fontSize: 14,
    color: COLORS.accent,
    fontStyle: 'italic',
  },
  chatMessage: {
    maxWidth: '85%',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.sm,
  },
  chatMessageUser: {
    alignSelf: 'flex-end',
    backgroundColor: COLORS.accent,
  },
  chatMessageAssistant: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  chatMessageText: {
    fontSize: 15,
    lineHeight: 22,
  },
  chatMessageTextUser: {
    color: COLORS.white,
  },
  chatMessageTextAssistant: {
    color: COLORS.primary,
  },
  chatInputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    backgroundColor: COLORS.white,
    gap: SPACING.sm,
  },
  chatInput: {
    flex: 1,
    backgroundColor: COLORS.background,
    borderRadius: BORDER_RADIUS.md,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    fontSize: 15,
    color: COLORS.primary,
    maxHeight: 100,
    minHeight: 40,
  },
  chatSendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.accent,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chatSendButtonDisabled: {
    backgroundColor: COLORS.border,
  },
});
