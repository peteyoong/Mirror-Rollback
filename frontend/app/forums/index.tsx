import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { getUserForums, Forum } from '../../services/api';

export default function ForumsHomeScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  
  const [forums, setForums] = useState<Forum[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchForums = useCallback(async (showRefresh = false) => {
    if (!user?.id) return;
    
    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    
    try {
      const response = await getUserForums(user.id);
      setForums(response.forums);
      setError(null);
    } catch (err) {
      console.error('[Forums] Error fetching forums:', err);
      setError('Unable to load forums');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.id]);

  useEffect(() => {
    fetchForums();
  }, [fetchForums]);

  const handleCreateForum = () => {
    router.push('/forums/create');
  };

  const handleJoinForum = () => {
    router.push('/forums/join');
  };

  const handleOpenForum = (forumId: string) => {
    router.push(`/forums/${forumId}`);
  };

  const handleBack = () => {
    router.back();
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Loading forums...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBack} style={styles.backButton}>
          <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Forums</Text>
        <View style={styles.backButton} />
      </View>

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => fetchForums(true)}
            tintColor={theme.textSecondary}
          />
        }
      >
        {/* Description */}
        <Text style={[styles.description, { color: theme.textSecondary }]}>
          Private spaces for trusted reflection. Share insights with a small group and grow together.
        </Text>

        {/* Action Buttons */}
        <View style={styles.actionButtons}>
          <TouchableOpacity
            style={[styles.actionButton, { backgroundColor: theme.buttonPrimaryBg }]}
            onPress={handleCreateForum}
          >
            <Text style={[styles.actionButtonText, { color: theme.buttonPrimaryText }]}>
              + Create Forum
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.actionButtonSecondary, { borderColor: theme.border }]}
            onPress={handleJoinForum}
          >
            <Text style={[styles.actionButtonTextSecondary, { color: theme.text }]}>
              Join Forum
            </Text>
          </TouchableOpacity>
        </View>

        {/* Your Forums Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Your Forums</Text>
          
          {error ? (
            <View style={[styles.emptyState, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.emptyText, { color: theme.textSecondary }]}>{error}</Text>
              <TouchableOpacity onPress={() => fetchForums()}>
                <Text style={[styles.retryText, { color: theme.accent }]}>Try Again</Text>
              </TouchableOpacity>
            </View>
          ) : forums.length === 0 ? (
            <View style={[styles.emptyState, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={styles.emptyIcon}>◎</Text>
              <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
                You're not part of any forums yet.
              </Text>
              <Text style={[styles.emptySubtext, { color: theme.textTertiary }]}>
                Create one or join with an invite link.
              </Text>
            </View>
          ) : (
            <View style={styles.forumsList}>
              {forums.map((forum) => (
                <TouchableOpacity
                  key={forum.id}
                  style={[styles.forumCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
                  onPress={() => handleOpenForum(forum.id)}
                  activeOpacity={0.7}
                >
                  <View style={styles.forumCardHeader}>
                    <Text style={[styles.forumName, { color: theme.text }]} numberOfLines={1}>
                      {forum.name}
                    </Text>
                    <Text style={[styles.forumMembers, { color: theme.textTertiary }]}>
                      {forum.member_count} {forum.member_count === 1 ? 'member' : 'members'}
                    </Text>
                  </View>
                  {forum.description && (
                    <Text style={[styles.forumDescription, { color: theme.textSecondary }]} numberOfLines={2}>
                      {forum.description}
                    </Text>
                  )}
                  <Text style={[styles.forumChevron, { color: theme.textTertiary }]}>→</Text>
                </TouchableOpacity>
              ))}
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
    marginBottom: 24,
  },
  actionButtons: {
    gap: 12,
    marginBottom: 32,
  },
  actionButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  actionButtonSecondary: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
  },
  actionButtonTextSecondary: {
    fontSize: 16,
    fontWeight: '500',
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  emptyState: {
    padding: 32,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
    opacity: 0.5,
  },
  emptyText: {
    fontSize: 15,
    textAlign: 'center',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 13,
    textAlign: 'center',
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
    marginTop: 8,
  },
  forumsList: {
    gap: 12,
  },
  forumCard: {
    padding: 16,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
  },
  forumCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  forumName: {
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  forumMembers: {
    fontSize: 12,
    marginLeft: 12,
  },
  forumDescription: {
    fontSize: 14,
    lineHeight: 20,
  },
  forumChevron: {
    position: 'absolute',
    right: 16,
    top: '50%',
    fontSize: 18,
  },
});
