import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import * as Clipboard from 'expo-clipboard';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { getForum, getSharedReflections, ForumReflection, getForumExercise } from '../../services/api';
import Constants from 'expo-constants';

export default function ForumHomeScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const forumId = id as string;
  
  const [forum, setForum] = useState<any | null>(null);
  const [reflections, setReflections] = useState<ForumReflection[]>([]);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [expandedReflection, setExpandedReflection] = useState<string | null>(null);

  const fetchData = useCallback(async (showRefresh = false) => {
    if (!user?.id || !forumId) return;
    
    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    
    try {
      const [forumData, reflectionsData, exerciseData] = await Promise.all([
        getForum(forumId, user.id),
        getSharedReflections(forumId, user.id),
        getForumExercise(forumId, user.id),
      ]);
      setForum(forumData);
      setReflections(reflectionsData.reflections);
      setHasSubmitted(exerciseData.has_submitted);
      setError(null);
    } catch (err: any) {
      console.error('[Forum] Error fetching data:', err);
      if (err.response?.status === 403) {
        setError('You are not a member of this forum');
      } else {
        setError('Unable to load forum');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.id, forumId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleBack = () => {
    router.push('/forums');
  };

  const handleBeginReflection = () => {
    router.push(`/forums/exercise?forumId=${forumId}`);
  };

  const handleCopyInvite = async () => {
    if (!forum?.invite_token) return;
    const baseUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || '';
    const link = `${baseUrl}/forums/join/${forum.invite_token}`;
    await Clipboard.setStringAsync(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleReflection = (id: string) => {
    setExpandedReflection(expandedReflection === id ? null : id);
  };

  const getPreviewText = (text: string, maxLength: number = 120) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Loading forum...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Forum</Text>
          <View style={styles.backButton} />
        </View>
        <View style={styles.errorContainer}>
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
          <TouchableOpacity onPress={() => fetchData()}>
            <Text style={[styles.retryText, { color: theme.accent }]}>Try Again</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBack} style={styles.backButton}>
          <Text style={[styles.backText, { color: theme.accent }]}>← Forums</Text>
        </TouchableOpacity>
        <View style={styles.headerRight}>
          <TouchableOpacity onPress={handleCopyInvite} style={styles.inviteButton}>
            <Text style={[styles.inviteButtonText, { color: theme.accent }]}>
              {copied ? '✓ Copied' : 'Invite'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => fetchData(true)}
            tintColor={theme.textSecondary}
          />
        }
      >
        {/* Forum Info */}
        <View style={styles.forumInfo}>
          <Text style={[styles.forumName, { color: theme.text }]}>{forum?.name}</Text>
          <Text style={[styles.forumMeta, { color: theme.textTertiary }]}>
            {forum?.member_count} {forum?.member_count === 1 ? 'member' : 'members'}
          </Text>
          {forum?.description && (
            <Text style={[styles.forumDescription, { color: theme.textSecondary }]}>
              {forum.description}
            </Text>
          )}
        </View>

        {/* Current Exercise Card */}
        {forum?.active_exercise && (
          <View style={[styles.exerciseCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <View style={styles.exerciseHeader}>
              <Text style={[styles.exerciseLabel, { color: theme.textTertiary }]}>CURRENT EXERCISE</Text>
            </View>
            <Text style={[styles.exerciseTitle, { color: theme.text }]}>
              {forum.active_exercise.title}
            </Text>
            <Text style={[styles.exerciseDescription, { color: theme.textSecondary }]}>
              {forum.active_exercise.description}
            </Text>
            
            <TouchableOpacity
              style={[styles.beginButton, { backgroundColor: theme.buttonPrimaryBg }]}
              onPress={handleBeginReflection}
            >
              <Text style={[styles.beginButtonText, { color: theme.buttonPrimaryText }]}>
                {hasSubmitted ? 'Edit Reflection' : 'Begin Reflection'}
              </Text>
            </TouchableOpacity>
            
            {hasSubmitted && (
              <Text style={[styles.submittedNote, { color: theme.success }]}>
                ✓ You've submitted a reflection
              </Text>
            )}
          </View>
        )}

        {/* Shared Reflections */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Shared Reflections</Text>
          
          {reflections.length === 0 ? (
            <View style={[styles.emptyReflections, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={styles.emptyIcon}>✎</Text>
              <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
                No reflections shared yet.
              </Text>
              <Text style={[styles.emptySubtext, { color: theme.textTertiary }]}>
                Be the first to share your reflection with the group.
              </Text>
            </View>
          ) : (
            <View style={styles.reflectionsList}>
              {reflections.map((reflection) => {
                const isExpanded = expandedReflection === reflection.id;
                return (
                  <TouchableOpacity
                    key={reflection.id}
                    style={[styles.reflectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
                    onPress={() => toggleReflection(reflection.id)}
                    activeOpacity={0.8}
                  >
                    <View style={styles.reflectionHeader}>
                      <Text style={[styles.reflectionAuthor, { color: theme.text }]}>
                        {reflection.user_name}
                      </Text>
                      <Text style={[styles.reflectionDomain, { color: theme.accent }]}>
                        {reflection.domain_name}
                      </Text>
                    </View>
                    <Text style={[styles.reflectionText, { color: theme.textSecondary }]}>
                      {isExpanded ? reflection.reflection_text : getPreviewText(reflection.reflection_text)}
                    </Text>
                    {reflection.reflection_text.length > 120 && (
                      <Text style={[styles.expandHint, { color: theme.textTertiary }]}>
                        {isExpanded ? 'Tap to collapse' : 'Tap to read more'}
                      </Text>
                    )}
                  </TouchableOpacity>
                );
              })}
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  backButton: {
    minWidth: 80,
  },
  backText: {
    fontSize: 16,
    fontWeight: '500',
  },
  headerRight: {
    alignItems: 'flex-end',
  },
  inviteButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  inviteButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 16,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  forumInfo: {
    marginBottom: 24,
  },
  forumName: {
    fontSize: 26,
    fontWeight: '700',
    marginBottom: 4,
  },
  forumMeta: {
    fontSize: 13,
    marginBottom: 8,
  },
  forumDescription: {
    fontSize: 15,
    lineHeight: 22,
  },
  exerciseCard: {
    padding: 20,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 24,
  },
  exerciseHeader: {
    marginBottom: 12,
  },
  exerciseLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
  },
  exerciseTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 8,
  },
  exerciseDescription: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 20,
  },
  beginButton: {
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  beginButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  submittedNote: {
    fontSize: 13,
    textAlign: 'center',
    marginTop: 12,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  emptyReflections: {
    padding: 32,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  emptyIcon: {
    fontSize: 40,
    marginBottom: 12,
    opacity: 0.5,
  },
  emptyText: {
    fontSize: 15,
    textAlign: 'center',
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 13,
    textAlign: 'center',
  },
  reflectionsList: {
    gap: 12,
  },
  reflectionCard: {
    padding: 16,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
  },
  reflectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  reflectionAuthor: {
    fontSize: 15,
    fontWeight: '600',
  },
  reflectionDomain: {
    fontSize: 12,
    fontWeight: '500',
  },
  reflectionText: {
    fontSize: 14,
    lineHeight: 21,
  },
  expandHint: {
    fontSize: 12,
    marginTop: 8,
    fontStyle: 'italic',
  },
});
