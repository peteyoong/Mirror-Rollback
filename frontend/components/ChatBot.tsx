import React, { useState } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { Colors } from '../constants/colors';
import { sendChatMessage } from '../services/api';
import { Ionicons } from '@expo/vector-icons';

interface ChatBotProps {
  userId: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatBot({ userId }: ChatBotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage = inputText.trim();
    setInputText('');
    
    // Add user message
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    
    setIsLoading(true);
    try {
      const response = await sendChatMessage(userId, userMessage);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.response },
      ]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: "I'm having trouble connecting. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Chat Toggle Button */}
      <TouchableOpacity
        style={styles.toggleButton}
        onPress={() => setIsOpen(!isOpen)}
        activeOpacity={0.8}
      >
        <Ionicons
          name={isOpen ? 'close' : 'chatbubble-outline'}
          size={24}
          color={Colors.text}
        />
      </TouchableOpacity>

      {/* Chat Window */}
      {isOpen && (
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.chatWindow}
        >
          <View style={styles.chatHeader}>
            <Text style={styles.chatTitle}>Reflective Guide</Text>
          </View>

          <ScrollView
            style={styles.messagesContainer}
            contentContainerStyle={styles.messagesContent}
          >
            {messages.length === 0 && (
              <Text style={styles.emptyText}>
                Ask me anything about your frameworks, or share what's on your mind.
              </Text>
            )}
            {messages.map((msg, index) => {
              // Normalize role - unknown defaults to assistant
              const rawRole = String(msg?.role ?? '').toLowerCase();
              const role = rawRole.includes('user') ? 'user' 
                : rawRole.includes('system') ? 'system' 
                : 'assistant';
              
              const getBubbleStyle = () => {
                if (role === 'user') return styles.userBubble;
                if (role === 'system') return styles.systemBubble;
                return styles.assistantBubble;
              };
              
              const getTextStyle = () => {
                if (role === 'user') return styles.userText;
                if (role === 'system') return styles.systemText;
                return styles.assistantText;
              };
              
              return (
                <View
                  key={index}
                  style={[styles.messageBubble, getBubbleStyle()]}
                >
                  <Text style={[styles.messageText, getTextStyle()]}>
                    {msg.content}
                  </Text>
                </View>
              );
            })}
            {isLoading && (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="small" color={Colors.textSecondary} />
              </View>
            )}
          </ScrollView>

          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              value={inputText}
              onChangeText={setInputText}
              placeholder="Type your message..."
              placeholderTextColor={Colors.textTertiary}
              multiline
              maxLength={500}
              editable={!isLoading}
            />
            <TouchableOpacity
              style={styles.sendButton}
              onPress={handleSend}
              disabled={!inputText.trim() || isLoading}
            >
              <Ionicons
                name="send"
                size={20}
                color={inputText.trim() ? Colors.text : Colors.textTertiary}
              />
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    zIndex: 1000,
  },
  toggleButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  chatWindow: {
    position: 'absolute',
    bottom: 72,
    right: 0,
    width: 320,
    height: 450,
    backgroundColor: Colors.surface,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 12,
    overflow: 'hidden',
  },
  chatHeader: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  chatTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
  },
  emptyText: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginTop: 32,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: Colors.surfaceLight,
  },
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.background,
  },
  messageText: {
    fontSize: 14,
    lineHeight: 20,
  },
  userText: {
    color: Colors.text,
  },
  assistantText: {
    color: Colors.textSecondary,
  },
  loadingContainer: {
    padding: 12,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  input: {
    flex: 1,
    minHeight: 40,
    maxHeight: 80,
    backgroundColor: Colors.background,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginRight: 8,
    color: Colors.text,
    fontSize: 14,
  },
  sendButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
});