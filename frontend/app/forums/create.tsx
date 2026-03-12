import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import * as Clipboard from 'expo-clipboard';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { createForum } from '../../services/api';
import Constants from 'expo-constants';

export default function CreateForumScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [createdForum, setCreatedForum] = useState<{ id: string; invite_token: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCreate = async () => {
    if (!user?.id) return;
    if (!name.trim()) {
      Alert.alert('Name required', 'Please enter a name for your forum.');
      return;
    }
    
    setLoading(true);
    try {
      const forum = await createForum({
        name: name.trim(),
        description: description.trim() || undefined,
        user_id: user.id,
      });
      setCreatedForum({ id: forum.id, invite_token: forum.invite_token });
    } catch (err) {
      console.error('[Forums] Error creating forum:', err);
      Alert.alert('Error', 'Unable to create forum. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getInviteLink = () => {
    if (!createdForum) return '';
    const baseUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || '';
    // For deep linking, we use a web URL that can open the app
    return `${baseUrl}/forums/join/${createdForum.invite_token}`;
  };

  const handleCopyLink = async () => {
    const link = getInviteLink();
    await Clipboard.setStringAsync(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleGoToForum = () => {
    if (createdForum) {
      router.replace(`/forums/${createdForum.id}`);
    }
  };

  const handleBack = () => {
    if (createdForum) {
      router.replace('/forums');
    } else {
      router.back();
    }
  };

  // Success screen after creation
  if (createdForum) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Done</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Forum Created</Text>
          <View style={styles.backButton} />
        </View>

        <View style={styles.successContent}>
          <Text style={styles.successIcon}>✓</Text>
          <Text style={[styles.successTitle, { color: theme.text }]}>
            "{name}" is ready
          </Text>
          <Text style={[styles.successSubtitle, { color: theme.textSecondary }]}>
            Share this link to invite others:
          </Text>

          <View style={[styles.linkBox, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.linkText, { color: theme.text }]} numberOfLines={2}>
              {getInviteLink()}
            </Text>
          </View>

          <TouchableOpacity
            style={[styles.copyButton, { backgroundColor: theme.buttonPrimaryBg }]}
            onPress={handleCopyLink}
          >
            <Text style={[styles.copyButtonText, { color: theme.buttonPrimaryText }]}>
              {copied ? '✓ Copied!' : 'Copy Invite Link'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.goButton, { borderColor: theme.border }]}
            onPress={handleGoToForum}
          >
            <Text style={[styles.goButtonText, { color: theme.text }]}>
              Go to Forum →
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardAvoid}
      >
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Create Forum</Text>
          <View style={styles.backButton} />
        </View>

        <ScrollView
          style={styles.content}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <Text style={[styles.description, { color: theme.textSecondary }]}>
            Create a private space for your group to reflect together.
          </Text>

          <View style={styles.form}>
            <View style={styles.inputGroup}>
              <Text style={[styles.label, { color: theme.text }]}>Forum Name *</Text>
              <TextInput
                style={[styles.input, { 
                  backgroundColor: theme.inputBg, 
                  borderColor: theme.inputBorder,
                  color: theme.text 
                }]}
                placeholder="e.g., Leadership Circle, Retreat Group"
                placeholderTextColor={theme.inputPlaceholder}
                value={name}
                onChangeText={setName}
                maxLength={50}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={[styles.label, { color: theme.text }]}>Description (optional)</Text>
              <TextInput
                style={[styles.textArea, { 
                  backgroundColor: theme.inputBg, 
                  borderColor: theme.inputBorder,
                  color: theme.text 
                }]}
                placeholder="What brings this group together?"
                placeholderTextColor={theme.inputPlaceholder}
                value={description}
                onChangeText={setDescription}
                multiline
                numberOfLines={3}
                maxLength={200}
              />
            </View>
          </View>

          <TouchableOpacity
            style={[
              styles.createButton, 
              { backgroundColor: name.trim() ? theme.buttonPrimaryBg : theme.border }
            ]}
            onPress={handleCreate}
            disabled={loading || !name.trim()}
          >
            {loading ? (
              <ActivityIndicator color={theme.buttonPrimaryText} />
            ) : (
              <Text style={[styles.createButtonText, { color: theme.buttonPrimaryText }]}>
                Create Forum
              </Text>
            )}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardAvoid: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  backButton: {
    width: 60,
  },
  backText: {
    fontSize: 16,
    fontWeight: '500',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  description: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 32,
  },
  form: {
    gap: 24,
    marginBottom: 32,
  },
  inputGroup: {
    gap: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
  },
  input: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    fontSize: 16,
  },
  textArea: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    fontSize: 16,
    minHeight: 100,
    textAlignVertical: 'top',
  },
  createButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  createButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  // Success screen styles
  successContent: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 40,
    alignItems: 'center',
  },
  successIcon: {
    fontSize: 64,
    marginBottom: 24,
    color: '#66BB6A',
  },
  successTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 12,
    textAlign: 'center',
  },
  successSubtitle: {
    fontSize: 15,
    marginBottom: 24,
    textAlign: 'center',
  },
  linkBox: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    width: '100%',
    marginBottom: 16,
  },
  linkText: {
    fontSize: 13,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    textAlign: 'center',
  },
  copyButton: {
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
    marginBottom: 12,
  },
  copyButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  goButton: {
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
    borderWidth: 1,
  },
  goButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
});
