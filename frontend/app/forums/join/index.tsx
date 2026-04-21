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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useTheme } from '../../../contexts/ThemeContext';
import { useAppStore } from '../../../store';
import { getForumByInvite, joinForum } from '../../../services/api';

/**
 * Manual "Join Forum" form.
 *
 * Supports three input formats:
 *   1. Raw token       :  cb8cd54847e5
 *   2. Relative path   :  /forums/join/cb8cd54847e5
 *   3. Full URL        :  https://app.example.com/forums/join/cb8cd54847e5
 *
 * Notes:
 *  - We use an INLINE error banner (not Alert.alert) because React Native
 *    Alert is unreliable on React Native Web — it was the root cause of the
 *    silent-failure bug users saw ("spinner briefly, then same page, no
 *    error message").
 *  - Each step emits a diagnostic `[Forums/Join]` console log so we can
 *    trace pasted value → normalised token → API path → response.
 */

type BannerState = { kind: 'error' | 'info' | 'success'; text: string } | null;

export default function JoinForumScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const params = useLocalSearchParams<{ token?: string }>();

  const [inviteLink, setInviteLink] = useState(((params.token as string) || '').trim());
  const [loading, setLoading] = useState(false);
  const [banner, setBanner] = useState<BannerState>(null);
  const [previewForum, setPreviewForum] = useState<{
    id: string;
    name: string;
    description: string | null;
    member_count: number;
    token: string;
  } | null>(null);

  /**
   * Normalise input → the 12-char (or longer) invite token.
   * Handles raw tokens, relative paths, and full URLs with or without
   * query strings / trailing slashes.
   */
  const extractToken = (raw: string): string => {
    if (!raw) return '';
    const trimmed = raw.trim();

    // 1. Try to pull `/forums/join/{token}` from anywhere in the string.
    //    Allow word chars + `-` + `_` just in case the backend ever changes
    //    its token generator.
    const pathMatch = trimmed.match(/\/forums\/join\/([A-Za-z0-9_-]+)/);
    if (pathMatch && pathMatch[1]) return pathMatch[1];

    // 2. If the string parses as a URL, look at its pathname.
    try {
      const asUrl = new URL(trimmed);
      const segs = asUrl.pathname.split('/').filter(Boolean);
      const idx = segs.indexOf('join');
      if (idx !== -1 && segs[idx + 1]) return segs[idx + 1];
      // Fallback: last path segment
      if (segs.length > 0) return segs[segs.length - 1];
    } catch {
      /* not a URL — fall through */
    }

    // 3. Otherwise treat the whole input (stripped of any leading slash) as
    //    the raw token.
    return trimmed.replace(/^\/+/, '').replace(/\/+$/, '');
  };

  const describeError = (err: any, fallback: string): string => {
    const status = err?.response?.status;
    const detail = err?.response?.data?.detail;
    if (status === 404) return 'This invite link is invalid or has expired.';
    if (status === 400 && detail) return String(detail);
    if (status === 401 || status === 403) return 'Please sign in again and try again.';
    if (status && status >= 500) return 'Server error. Please try again in a moment.';
    if (err?.message === 'Network Error') {
      return 'Could not reach the server. Check your connection and try again.';
    }
    return fallback;
  };

  const handlePreview = async () => {
    const original = inviteLink;
    const token = extractToken(inviteLink);

    // Diagnostic logs — visible in browser console on web and in Metro on RN.
    // eslint-disable-next-line no-console
    console.log('[Forums/Join] pasted value =', JSON.stringify(original));
    // eslint-disable-next-line no-console
    console.log('[Forums/Join] normalised token =', JSON.stringify(token));

    if (!token) {
      setBanner({ kind: 'error', text: 'Please paste an invite link or code.' });
      return;
    }

    setBanner(null);
    setLoading(true);
    try {
      // eslint-disable-next-line no-console
      console.log('[Forums/Join] GET /api/forums/invite/' + token);
      const forum = await getForumByInvite(token);
      // eslint-disable-next-line no-console
      console.log('[Forums/Join] preview OK', forum);
      setPreviewForum({ ...forum, token });
    } catch (err: any) {
      // eslint-disable-next-line no-console
      console.error(
        '[Forums/Join] preview failed',
        'status=', err?.response?.status,
        'body=', err?.response?.data,
        'message=', err?.message,
      );
      setBanner({
        kind: 'error',
        text: describeError(err, 'Unable to load forum. Please try again.'),
      });
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async () => {
    if (!previewForum) return;

    if (!user?.id) {
      setBanner({
        kind: 'error',
        text: 'Please sign in before joining a forum.',
      });
      return;
    }

    const token = previewForum.token;
    setBanner(null);
    setLoading(true);
    try {
      // eslint-disable-next-line no-console
      console.log('[Forums/Join] POST /api/forums/join/' + token, { user_id: user.id });
      const result = await joinForum(token, user.id);
      // eslint-disable-next-line no-console
      console.log('[Forums/Join] join OK', result);

      // Success path — even if already_member, take the user into the forum.
      if (result.already_member) {
        setBanner({ kind: 'info', text: "You're already in this forum — taking you there now." });
      }
      // Small pause so the info banner is seen on already_member cases.
      setTimeout(() => {
        router.replace(`/forums/${result.forum_id}`);
      }, result.already_member ? 700 : 0);
    } catch (err: any) {
      // eslint-disable-next-line no-console
      console.error(
        '[Forums/Join] join failed',
        'status=', err?.response?.status,
        'body=', err?.response?.data,
        'message=', err?.message,
      );
      setBanner({
        kind: 'error',
        text: describeError(err, 'Unable to join this forum. Please try again.'),
      });
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (previewForum) {
      setPreviewForum(null);
      setBanner(null);
      return;
    }
    if (router.canGoBack()) router.back();
    else router.replace('/forums');
  };

  const BannerNode = banner
    ? (
      <View
        style={[
          styles.banner,
          {
            backgroundColor:
              banner.kind === 'error'
                ? 'rgba(220, 50, 50, 0.12)'
                : banner.kind === 'success'
                ? 'rgba(50, 180, 100, 0.12)'
                : 'rgba(120, 140, 200, 0.12)',
            borderColor:
              banner.kind === 'error'
                ? 'rgba(220, 50, 50, 0.5)'
                : banner.kind === 'success'
                ? 'rgba(50, 180, 100, 0.5)'
                : 'rgba(120, 140, 200, 0.5)',
          },
        ]}
      >
        <Text
          style={[
            styles.bannerText,
            {
              color:
                banner.kind === 'error'
                  ? '#ff8080'
                  : banner.kind === 'success'
                  ? '#7be0a0'
                  : theme.text,
            },
          ]}
        >
          {banner.text}
        </Text>
      </View>
    )
    : null;

  // ---- PREVIEW SCREEN ----
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
          {BannerNode}
          <View
            style={[
              styles.previewCard,
              { backgroundColor: theme.surface, borderColor: theme.border },
            ]}
          >
            <Text style={[styles.previewName, { color: theme.text }]}>
              {previewForum.name}
            </Text>
            {previewForum.description ? (
              <Text style={[styles.previewDescription, { color: theme.textSecondary }]}>
                {previewForum.description}
              </Text>
            ) : null}
            <Text style={[styles.previewMembers, { color: theme.textTertiary }]}>
              {previewForum.member_count}{' '}
              {previewForum.member_count === 1 ? 'member' : 'members'}
            </Text>
          </View>

          <Text style={[styles.confirmText, { color: theme.textSecondary }]}>
            You're about to join this forum. You'll be able to participate in
            reflection exercises and view shared reflections from other members.
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
                {user?.id ? 'Join Forum' : 'Sign in to Join'}
              </Text>
            )}
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // ---- INPUT SCREEN ----
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

          {BannerNode}

          <View style={styles.inputGroup}>
            <Text style={[styles.label, { color: theme.text }]}>Invite Link or Code</Text>
            <TextInput
              style={[
                styles.input,
                {
                  backgroundColor: theme.inputBg,
                  borderColor: theme.inputBorder,
                  color: theme.text,
                },
              ]}
              placeholder="Paste invite link or code here"
              placeholderTextColor={theme.inputPlaceholder}
              value={inviteLink}
              onChangeText={(t) => {
                setInviteLink(t);
                if (banner) setBanner(null);
              }}
              autoCapitalize="none"
              autoCorrect={false}
              autoComplete="off"
              testID="forum-join-input"
            />
            {/* Debug hint: show the normalised token so users + support can see
                exactly what we'll submit. */}
            {inviteLink.trim().length > 0 ? (
              <Text style={[styles.hint, { color: theme.textTertiary }]}>
                Code to submit: {extractToken(inviteLink) || '(none detected)'}
              </Text>
            ) : null}
          </View>

          <TouchableOpacity
            style={[
              styles.previewButton,
              { backgroundColor: inviteLink.trim() ? theme.buttonPrimaryBg : theme.border },
            ]}
            onPress={handlePreview}
            disabled={loading || !inviteLink.trim()}
            testID="forum-join-continue"
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
  container: { flex: 1 },
  keyboardAvoid: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  backButton: { width: 60 },
  backText: { fontSize: 16, fontWeight: '500' },
  headerTitle: { fontSize: 24, fontWeight: '600' },
  content: { flex: 1, paddingHorizontal: 20, paddingTop: 20 },
  description: { fontSize: 15, lineHeight: 22, marginBottom: 20 },
  inputGroup: { gap: 8, marginBottom: 24 },
  label: { fontSize: 14, fontWeight: '500' },
  input: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    fontSize: 16,
  },
  hint: { fontSize: 12, marginTop: 4 },
  previewButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  previewButtonText: { fontSize: 16, fontWeight: '600' },
  // Preview screen
  previewContent: { flex: 1, paddingHorizontal: 20, paddingTop: 20 },
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
  previewMembers: { fontSize: 13 },
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
  joinButtonText: { fontSize: 16, fontWeight: '600' },
  // Inline banner
  banner: {
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 14,
    marginBottom: 16,
  },
  bannerText: { fontSize: 14, lineHeight: 20 },
});
