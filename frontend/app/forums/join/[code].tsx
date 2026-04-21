import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useTheme } from '../../../contexts/ThemeContext';
import { useAppStore } from '../../../store';
import { getForumByInvite, joinForum } from '../../../services/api';

/**
 * Dynamic deep-link handler for shared invite URLs of the form:
 *     /forums/join/{invite_token}
 *
 * When a user taps a shared link, Expo Router routes here with the
 * `code` path parameter. This screen:
 *   1. Loads the forum preview for the token.
 *   2. If the user is already logged in, asks them to confirm and joins.
 *   3. If already a member, redirects straight into the forum.
 *   4. On success, navigates to the forum detail so the forums list
 *      refreshes via useFocusEffect on next visit.
 */
export default function JoinForumByCodeScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const params = useLocalSearchParams<{ code?: string }>();

  // Normalise token: the segment may contain a full URL if a user pastes it,
  // so strip anything that isn't the trailing token.
  const extractToken = (raw: string | undefined): string => {
    if (!raw) return '';
    const decoded = decodeURIComponent(String(raw)).trim();
    const match = decoded.match(/\/forums\/join\/([a-zA-Z0-9_-]+)/);
    if (match) return match[1];
    return decoded;
  };

  const token = extractToken(params.code);

  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [joinError, setJoinError] = useState<string | null>(null);
  const [forumInfo, setForumInfo] = useState<{
    id: string;
    name: string;
    description: string | null;
    member_count: number;
  } | null>(null);
  const didAttemptRef = useRef(false);

  // Load preview on mount
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!token) {
        setLoading(false);
        setError('This invite link is missing a code.');
        return;
      }
      try {
        const info = await getForumByInvite(token);
        if (!cancelled) setForumInfo(info);
      } catch (err: any) {
        console.error('[Forums/Join] preview failed', err?.response?.data || err?.message || err);
        if (!cancelled) {
          const status = err?.response?.status;
          if (status === 404) {
            setError('This invite link is invalid or has expired.');
          } else {
            setError('Unable to load forum. Please check your connection and try again.');
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const handleJoin = async () => {
    if (!token || !forumInfo) return;

    // Require auth — push to welcome if not logged in, preserving intent.
    if (!user?.id) {
      router.replace({
        pathname: '/welcome',
        params: { pendingJoin: token },
      } as any);
      return;
    }

    if (didAttemptRef.current) return;
    didAttemptRef.current = true;
    setJoinError(null);
    setJoining(true);
    try {
      console.log('[Forums/Join] POST /api/forums/join/' + token, { user_id: user.id });
      const result = await joinForum(token, user.id);
      console.log('[Forums/Join] join OK', result);
      // Navigate to forum detail. forums/index refreshes via useFocusEffect.
      // If already_member, we still just take them straight into the forum.
      router.replace(`/forums/${result.forum_id}`);
    } catch (err: any) {
      didAttemptRef.current = false;
      console.error(
        '[Forums/Join] join failed',
        'status=', err?.response?.status,
        'body=', err?.response?.data,
        'message=', err?.message,
      );
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      let msg = 'Unable to join this forum. Please try again.';
      if (status === 404) msg = 'This invite link is no longer valid.';
      else if (status === 400 && detail) msg = String(detail);
      else if (status === 401 || status === 403) msg = 'Please sign in again and try again.';
      else if (err?.message === 'Network Error') {
        msg = 'Could not reach the server. Check your connection and try again.';
      }
      setJoinError(msg);
    } finally {
      setJoining(false);
    }
  };

  const handleGoToForums = () => {
    router.replace('/forums');
  };

  const handleBack = () => {
    if (router.canGoBack()) router.back();
    else router.replace('/forums');
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Looking up invite…
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error || !forumInfo) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Join Forum</Text>
          <View style={styles.backButton} />
        </View>
        <View style={styles.center}>
          <Text style={[styles.errorTitle, { color: theme.text }]}>
            Couldn't open invite
          </Text>
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>
            {error || 'Something went wrong.'}
          </Text>
          <TouchableOpacity
            style={[styles.primaryButton, { backgroundColor: theme.buttonPrimaryBg }]}
            onPress={handleGoToForums}
          >
            <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>
              Go to Forums
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

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
        {joinError ? (
          <View style={styles.errorBanner}>
            <Text style={styles.errorBannerText}>{joinError}</Text>
          </View>
        ) : null}
        <View style={[styles.previewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.previewName, { color: theme.text }]}>
            {forumInfo.name}
          </Text>
          {forumInfo.description ? (
            <Text style={[styles.previewDescription, { color: theme.textSecondary }]}>
              {forumInfo.description}
            </Text>
          ) : null}
          <Text style={[styles.previewMembers, { color: theme.textTertiary }]}>
            {forumInfo.member_count}{' '}
            {forumInfo.member_count === 1 ? 'member' : 'members'}
          </Text>
        </View>

        <Text style={[styles.confirmText, { color: theme.textSecondary }]}>
          You're about to join this forum. You'll be able to participate in reflection exercises and view shared reflections from other members.
        </Text>

        <TouchableOpacity
          style={[styles.primaryButton, { backgroundColor: theme.buttonPrimaryBg }]}
          onPress={handleJoin}
          disabled={joining}
        >
          {joining ? (
            <ActivityIndicator color={theme.buttonPrimaryText} />
          ) : (
            <Text style={[styles.primaryButtonText, { color: theme.buttonPrimaryText }]}>
              {user?.id ? 'Join Forum' : 'Sign in to Join'}
            </Text>
          )}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
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
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
    gap: 12,
  },
  loadingText: { fontSize: 14, marginTop: 12 },
  errorTitle: { fontSize: 18, fontWeight: '600', marginBottom: 4, textAlign: 'center' },
  errorText: { fontSize: 14, lineHeight: 20, textAlign: 'center', marginBottom: 16 },
  previewContent: { flex: 1, paddingHorizontal: 20, paddingTop: 20 },
  previewCard: {
    padding: 24,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 24,
    alignItems: 'center',
  },
  previewName: { fontSize: 22, fontWeight: '600', marginBottom: 8, textAlign: 'center' },
  previewDescription: { fontSize: 15, lineHeight: 22, marginBottom: 12, textAlign: 'center' },
  previewMembers: { fontSize: 13 },
  confirmText: { fontSize: 14, lineHeight: 22, marginBottom: 32, textAlign: 'center' },
  primaryButton: {
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryButtonText: { fontSize: 16, fontWeight: '600' },
  errorBanner: {
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'rgba(220, 50, 50, 0.5)',
    backgroundColor: 'rgba(220, 50, 50, 0.12)',
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 14,
    marginBottom: 16,
  },
  errorBannerText: {
    color: '#ff8080',
    fontSize: 14,
    lineHeight: 20,
  },
});
