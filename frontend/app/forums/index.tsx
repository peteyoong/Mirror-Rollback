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
import { useRouter, useFocusEffect } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { getUserForums, Forum } from '../../services/api';
import { Ionicons } from '@expo/vector-icons';
import {
  listSavedPeople,
  formatRelationshipType,
  precisionLabel,
  SavedPerson,
} from '../../services/people';

export default function ForumsHomeScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  
  const [forums, setForums] = useState<Forum[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Relationship Profiles — surfaced as cards below "Your Forums".
  // These are private 1:1 profiles, intentionally a different visual
  // surface to forums so users don't conflate the two product concepts.
  const [people, setPeople] = useState<SavedPerson[]>([]);

  const fetchForums = useCallback(async (showRefresh = false) => {
    if (!user?.id) return;
    
    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    
    try {
      const [forumsResp, peopleResp] = await Promise.allSettled([
        getUserForums(user.id),
        listSavedPeople(user.id),
      ]);

      if (forumsResp.status === 'fulfilled') {
        setForums(forumsResp.value.forums);
        setError(null);
      } else {
        console.error('[Forums] Error fetching forums:', forumsResp.reason);
        setError('Unable to load forums');
      }

      // Saved-people failure is non-fatal — section just doesn't render.
      if (peopleResp.status === 'fulfilled') {
        setPeople(Array.isArray((peopleResp.value as any)?.people) ? (peopleResp.value as any).people : []);
      } else {
        console.warn('[Forums] saved people fetch failed:', peopleResp.reason);
        setPeople([]);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.id]);

  useEffect(() => {
    fetchForums();
  }, [fetchForums]);

  // Refresh list whenever the forums tab regains focus (e.g., after join).
  useFocusEffect(
    useCallback(() => {
      if (user?.id) {
        fetchForums(false);
      }
    }, [user?.id, fetchForums])
  );

  const handleCreateForum = () => {
    router.push('/forums/create');
  };

  const handleJoinForum = () => {
    router.push('/forums/join');
  };

  const handleOpenPeopleSetup = () => {
    router.push('/people' as any);
  };

  const handleOpenForum = (forumId: string) => {
    router.push(`/forums/${forumId}`);
  };

  const handleBack = () => {
    router.back();
  };

  const handleGoHome = () => {
    router.replace('/(tabs)');
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
        <TouchableOpacity onPress={handleGoHome} style={styles.homeButton} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
          <Ionicons name="home-outline" size={22} color={theme.text} />
        </TouchableOpacity>
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

        {/* ─────────────────────────────────────────────────────────────
            RELATIONSHIP PROFILES — one-to-one private relational
            mirrors. Visually distinct from forums (uses accent border
            + softer card surface) so the two product concepts stay
            mentally separate. Tapping a card opens /people/[id].
            ───────────────────────────────────────────────────────────── */}
        <View style={[styles.section, styles.mappingSection]}>
          <Text style={[styles.mappingSectionLabel, { color: theme.textTertiary }]}>
            Relationship Profiles
          </Text>
          <Text style={[styles.mappingSectionHint, { color: theme.textSecondary }]}>
            One-to-one relational mirrors. Separate from forums.
          </Text>

          {people.length === 0 ? (
            <TouchableOpacity
              style={[styles.mappingCard, { backgroundColor: theme.surface, borderColor: theme.accent + '55' }]}
              onPress={handleOpenPeopleSetup}
              activeOpacity={0.85}
              accessibilityRole="button"
              accessibilityLabel="Add Private Person"
            >
              <View style={styles.peopleSetupRow}>
                <View style={styles.peopleSetupBody}>
                  <Text style={[styles.mappingTitle, { color: theme.text }]}>+ Add Private Person</Text>
                  <Text style={[styles.mappingSub, { color: theme.textSecondary }]} numberOfLines={3}>
                    For people you want to understand privately. They are not forum participants.
                  </Text>
                </View>
              </View>
            </TouchableOpacity>
          ) : (
            <View style={styles.profilesList}>
              {people.map((p) => {
                const pl = precisionLabel(p.precision_level);
                const lenses: string[] = [];
                if (p.birth_date) {
                  lenses.push('Astrology');
                  lenses.push('Numerology');
                }
                if (p.birth_time_accuracy === 'exact') lenses.push('Human Design');
                if (p.enneagram_type) lenses.push('Enneagram');
                return (
                  <TouchableOpacity
                    key={p.id}
                    style={[styles.profileCard, { backgroundColor: theme.surface, borderColor: theme.accent + '55' }]}
                    onPress={() => router.push(`/people/${p.id}` as any)}
                    activeOpacity={0.7}
                  >
                    <View style={styles.profileCardTop}>
                      <Text style={[styles.profileName, { color: theme.text }]} numberOfLines={1}>
                        {p.name}
                      </Text>
                      <Text style={[styles.profilePrecision, { color: theme.textTertiary }]}>
                        {pl.label}
                      </Text>
                    </View>
                    <Text style={[styles.profileType, { color: theme.textSecondary }]}>
                      {formatRelationshipType(p.relationship_type)}
                    </Text>
                    {lenses.length > 0 && (
                      <View style={styles.profileLensRow}>
                        {lenses.map((l) => (
                          <View key={l} style={[styles.profileLensChip, { borderColor: theme.border, backgroundColor: theme.background }]}>
                            <Text style={[styles.profileLensText, { color: theme.textSecondary }]}>{l}</Text>
                          </View>
                        ))}
                      </View>
                    )}
                  </TouchableOpacity>
                );
              })}

              {/* Always show an inline "+ Add another" tap target below
                  the cards so users can grow the list without leaving
                  the forum landing. */}
              <TouchableOpacity
                style={[styles.profileCardAdd, { borderColor: theme.accent + '55' }]}
                onPress={handleOpenPeopleSetup}
                activeOpacity={0.7}
                accessibilityRole="button"
                accessibilityLabel="Add another private person"
              >
                <Text style={[styles.profileCardAddText, { color: theme.accent }]}>
                  + Add another private person
                </Text>
              </TouchableOpacity>
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
  homeButton: {
    width: 60,
    alignItems: 'flex-end',
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
    marginBottom: 16,
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
  peopleSetupCard: {
    marginBottom: 24,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
  },
  peopleSetupRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  peopleSetupIcon: {
    width: 36, height: 36, borderRadius: 999,
    alignItems: 'center', justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.04)',
  },
  peopleSetupBody: { flex: 1, gap: 2 },
  peopleSetupTitle: { fontSize: 15, fontWeight: '600' },
  peopleSetupSub: { fontSize: 12, lineHeight: 17 },

  // ─────────────────────────────────────────────────────────────
  // Relationship Mapping — secondary section placed BELOW "Your
  // Forums". Smaller, muted, with an uppercase section label so it
  // never visually competes with the Create / Join Forum action
  // layer at the top of the screen.
  // ─────────────────────────────────────────────────────────────
  mappingSection: {
    marginTop: 4,
    paddingTop: 8,
  },
  mappingSectionLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  mappingSectionHint: {
    fontSize: 12,
    marginBottom: 12,
    fontStyle: 'italic',
  },
  mappingCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    paddingVertical: 12,
    paddingHorizontal: 14,
  },
  mappingTitle: { fontSize: 14, fontWeight: '500' },
  mappingSub: { fontSize: 12, lineHeight: 17 },

  // ─────────────────────────────────────────────────────────────
  // Relationship Profile cards (May 2026 — relationship-profiles-v0.1).
  // Visually similar to forum cards but with an accent-tinted border
  // so users can immediately see this is a different product surface.
  // ─────────────────────────────────────────────────────────────
  profilesList: { gap: 10 },
  profileCard: {
    borderRadius: 12,
    borderWidth: 1,
    paddingVertical: 12,
    paddingHorizontal: 14,
  },
  profileCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  profileName: { fontSize: 15, fontWeight: '600', flex: 1 },
  profilePrecision: { fontSize: 11, fontWeight: '500', marginLeft: 8 },
  profileType: { fontSize: 12, marginTop: 2 },
  profileLensRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 8 },
  profileLensChip: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
  },
  profileLensText: { fontSize: 10, fontWeight: '500' },
  profileCardAdd: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderStyle: 'dashed',
    paddingVertical: 12,
    alignItems: 'center',
  },
  profileCardAddText: { fontSize: 13, fontWeight: '500' },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 22,
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
    fontSize: 22,
  },
});
