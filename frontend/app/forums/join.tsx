import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { getForumByInvite, joinForum } from '../../services/api';

export default function JoinForumScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const params = useLocalSearchParams();
  
  // Support pre-filled invite token from deep link
  const [inviteLink, setInviteLink] = useState((params.token as string) || '');
  const [loading, setLoading] = useState(false);
  const [previewForum, setPreviewForum] = useState<{
    id: string;
    name: string;
    description: string | null;
    member_count: number;
  } | null>(null);

  const extractToken = (input: string): string => {
    // Extract token from full URL or just use the input if it's the token
    const match = input.match(/\/forums\/join\/([a-zA-Z0-9]+)/);
    if (match) return match[1];
    // Check if it's a bare token (alphanumeric, 12 chars)
    if (/^[a-zA-Z0-9]{12}$/.test(input.trim())) return input.trim();
    return input.trim();
  };

  const handlePreview = async () => {
    const token = extractToken(inviteLink);
    if (!token) {
      Alert.alert('Invalid link', 'Please enter a valid invite link or code.');
      return;
    }
    
    setLoading(true);
    try {
      const forum = await getForumByInvite(token);
      setPreviewForum({ ...forum, token } as any);
    } catch (err: any) {
      console.error('[Forums] Error getting forum preview:', err);
      Alert.alert('Invalid link', 'This invite link is not valid or has expired.');
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async () => {
    if (!user?.id || !previewForum) return;
    
    const token = extractToken(inviteLink);
    setLoading(true);
    try {
      const result = await joinForum(token, user.id);
      if (result.already_member) {
        Alert.alert('Already a member', 'You are already a member of this forum.');
      }
      router.replace(`/forums/${result.forum_id}`);
    } catch (err) {
      console.error('[Forums] Error joining forum:', err);
      Alert.alert('Error', 'Unable to join forum. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (previewForum) {
      setPreviewForum(null);
    } else {
      router.back();
    }
  };

  // Preview confirmation screen
  if (previewForum) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Join Forum</Text>
          <View style={styles.backButton} />
        </View>

        <View style={styles.previewContent}>
          <View style={[styles.previewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.previewName, { color: theme.text }]}>
              {previewForum.name}
            </Text>
            {previewForum.description && (
              <Text style={[styles.previewDescription, { color: theme.textSecondary }]}>
                {previewForum.description}
              </Text>
            )}
            <Text style={[styles.previewMembers, { color: theme.textTertiary }]}>
              {previewForum.member_count} {previewForum.member_count === 1 ? 'member' : 'members'}
            </Text>
          </View>

          <Text style={[styles.confirmText, { color: theme.textSecondary }]}>
            You're about to join this forum. You'll be able to participate in reflection exercises and view shared reflections from other members.
          </Text>

          <TouchableOpacity
            style={[styles.joinButton, { backgroundColor: theme.buttonPrimaryBg }]}
            onPress={handleJoin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color={theme.buttonPrimaryText} />
            ) : (
              <Text style={[styles.joinButtonText, { color: theme.buttonPrimaryText }]}>
                Join Forum
              </Text>
            )}
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
          <Text style={[styles.headerTitle, { color: theme.text }]}>Join Forum</Text>
          <View style={styles.backButton} />
        </View>

        <View style={styles.content}>
          <Text style={[styles.description, { color: theme.textSecondary }]}>
            Enter the invite link or code shared with you to join a forum.
          </Text>

          <View style={styles.inputGroup}>
            <Text style={[styles.label, { color: theme.text }]}>Invite Link or Code</Text>
            <TextInput
              style={[styles.input, { 
                backgroundColor: theme.inputBg, 
                borderColor: theme.inputBorder,
                color: theme.text 
              }]}
              placeholder="Paste invite link or code here"
              placeholderTextColor={theme.inputPlaceholder}
              value={inviteLink}
              onChangeText={setInviteLink}
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>

          <TouchableOpacity
            style={[
              styles.previewButton, 
              { backgroundColor: inviteLink.trim() ? theme.buttonPrimaryBg : theme.border }
            ]}
            onPress={handlePreview}
            disabled={loading || !inviteLink.trim()}
          >
            {loading ? (
              <ActivityIndicator color={theme.buttonPrimaryText} />
            ) : (
              <Text style={[styles.previewButtonText, { color: theme.buttonPrimaryText }]}>
                Continue
              </Text>
            )}
          </TouchableOpacity>
        </View>
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
    fontSize: 24,
    fontWeight: '600',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  description: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 32,
  },
  inputGroup: {
    gap: 8,
    marginBottom: 32,
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
  previewButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  previewButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  // Preview screen styles
  previewContent: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  previewCard: {
    padding: 24,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 24,
    alignItems: 'center',
  },
  previewName: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  previewDescription: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 12,
    textAlign: 'center',
  },
  previewMembers: {
    fontSize: 13,
  },
  confirmText: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 32,
    textAlign: 'center',
  },
  joinButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  joinButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
});
