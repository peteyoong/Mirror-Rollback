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
import { useRouter, useLocalSearchParams } from 'expo-router';
import * as Clipboard from 'expo-clipboard';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { useForumContext } from '../../contexts/ForumContext';
import { 
  getForum, 
  getSharedReflections, 
  ForumReflection, 
  getForumExercise, 
  getForumMembers, 
  ForumMember,
  getForumPulse,
  ForumPulseResponse
} from '../../services/api';
import Constants from 'expo-constants';

export default function ForumHomeScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const forumId = id as string;
  const { setForumContext, clearForumContext } = useForumContext();
  
  const [forum, setForum] = useState<any | null>(null);
  const [reflections, setReflections] = useState<ForumReflection[]>([]);
  const [members, setMembers] = useState<ForumMember[]>([]);
  const [pulse, setPulse] = useState<ForumPulseResponse | null>(null);
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
      const [forumData, reflectionsData, exerciseData, membersData, pulseData] = await Promise.all([
        getForum(forumId, user.id),
        getSharedReflections(forumId, user.id),
        getForumExercise(forumId, user.id),
        getForumMembers(forumId, user.id),
        getForumPulse(forumId, user.id),
      ]);
      setForum(forumData);
      setReflections(reflectionsData.reflections);
      setHasSubmitted(exerciseData.has_submitted);
      setMembers(membersData.members);
      setPulse(pulseData);
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
    clearForumContext();
    router.push('/forums');
  };

  const handleBeginReflection = () => {
    router.push(`/forums/exercise?forumId=${forumId}`);
  };

  const handleMyMirrorProfile = () => {
    // Set forum context before navigating to Mirror
    if (forum) {
      setForumContext({
        forumId: forumId,
        forumName: forum.name,
        exerciseId: forum.active_exercise?.id || null,
        exerciseTitle: forum.active_exercise?.title || null,
      });
    }
    // Navigate to the Lenses tab where user can browse their insights
    router.push('/(tabs)/lenses');
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

  // Get first name for display
  const getFirstName = (fullName: string) => {
    return fullName.split(' ')[0];
  };

  // Handle member card press - navigate to their Mirror profile
  const handleMemberPress = (memberId: string) => {
    // For now, we could show a modal with member info
    // In future, this could navigate to a read-only view of their profile
    console.log('[Forum] Member card pressed:', memberId);
    // TODO: Navigate to member's public profile when implemented
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
          {forum?.description && (
            <Text style={[styles.forumDescription, { color: theme.textSecondary }]}>
              {forum.description}
            </Text>
          )}
        </View>

        {/* Members Quick List */}
        <View style={[styles.membersSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.membersTitle, { color: theme.textTertiary }]}>
            {members.length} {members.length === 1 ? 'MEMBER' : 'MEMBERS'}
          </Text>
          <View style={styles.membersList}>
            {members.slice(0, 5).map((member, index) => (
              <View key={member.user_id} style={styles.memberItem}>
                <View style={[styles.memberAvatar, { backgroundColor: theme.accent + '20' }]}>
                  <Text style={[styles.memberInitial, { color: theme.accent }]}>
                    {member.user_name.charAt(0).toUpperCase()}
                  </Text>
                </View>
                <Text style={[styles.memberName, { color: theme.text }]}>
                  {getFirstName(member.user_name)}
                  {member.role === 'owner' && (
                    <Text style={[styles.memberRole, { color: theme.textTertiary }]}> • host</Text>
                  )}
                </Text>
              </View>
            ))}
          </View>
        </View>

        {/* ============================================
            FORUM PULSE - Collective Patterns & Lens Dynamics
            ============================================ */}
        {pulse && (
          <View style={[styles.pulseSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.pulseSectionTitle, { color: theme.text }]}>Forum Pulse</Text>
            
            {/* Exploring Themes */}
            {pulse.exploring_themes.length > 0 && (
              <View style={styles.pulseBlock}>
                <Text style={[styles.pulseBlockLabel, { color: theme.textTertiary }]}>EXPLORING THEMES</Text>
                <View style={styles.themeTags}>
                  {pulse.exploring_themes.map((theme_item, index) => (
                    <View 
                      key={theme_item.domain_id} 
                      style={[styles.themeTag, { backgroundColor: theme.accent + '15', borderColor: theme.accent + '30' }]}
                    >
                      <Text style={[styles.themeTagText, { color: theme.accent }]}>
                        {theme_item.domain_name}
                      </Text>
                      <Text style={[styles.themeTagCount, { color: theme.textTertiary }]}>
                        {theme_item.count}
                      </Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
            
            {/* Activity Summary */}
            <View style={styles.pulseBlock}>
              <Text style={[styles.pulseBlockLabel, { color: theme.textTertiary }]}>ACTIVITY (7 DAYS)</Text>
              <View style={styles.activityStats}>
                <View style={styles.statItem}>
                  <Text style={[styles.statNumber, { color: theme.text }]}>
                    {pulse.activity_summary.reflections_7d}
                  </Text>
                  <Text style={[styles.statLabel, { color: theme.textTertiary }]}>reflections</Text>
                </View>
                <View style={[styles.statDivider, { backgroundColor: theme.border }]} />
                <View style={styles.statItem}>
                  <Text style={[styles.statNumber, { color: theme.text }]}>
                    {pulse.activity_summary.active_members_7d}
                  </Text>
                  <Text style={[styles.statLabel, { color: theme.textTertiary }]}>active</Text>
                </View>
                {pulse.activity_summary.most_active_domain && (
                  <>
                    <View style={[styles.statDivider, { backgroundColor: theme.border }]} />
                    <View style={[styles.statItem, { flex: 2 }]}>
                      <Text style={[styles.statNumber, { color: theme.accent, fontSize: 13 }]} numberOfLines={1}>
                        {pulse.activity_summary.most_active_domain}
                      </Text>
                      <Text style={[styles.statLabel, { color: theme.textTertiary }]}>most active</Text>
                    </View>
                  </>
                )}
              </View>
            </View>
            
            {/* Group Energy (HD Types) */}
            {Object.keys(pulse.group_energy).length > 0 && (
              <View style={styles.pulseBlock}>
                <Text style={[styles.pulseBlockLabel, { color: theme.textTertiary }]}>GROUP ENERGY</Text>
                <View style={styles.hdTypesGrid}>
                  {Object.entries(pulse.group_energy).map(([type, count]) => (
                    <View key={type} style={styles.hdTypeItem}>
                      <Text style={[styles.hdTypeName, { color: theme.textSecondary }]}>{type}</Text>
                      <Text style={[styles.hdTypeCount, { color: theme.text }]}>{count}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
            
            {/* Lens Insight */}
            {pulse.lens_insight && (
              <View style={[styles.lensInsightBlock, { backgroundColor: theme.accent + '08', borderLeftColor: theme.accent }]}>
                <Text style={[styles.lensInsightText, { color: theme.textSecondary }]}>
                  {pulse.lens_insight}
                </Text>
              </View>
            )}
          </View>
        )}

        {/* Member Lens Cards */}
        {pulse && pulse.member_cards.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>Members</Text>
            <View style={styles.memberCardsGrid}>
              {pulse.member_cards.map((member) => (
                <TouchableOpacity 
                  key={member.user_id}
                  style={[styles.memberLensCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
                  onPress={() => handleMemberPress(member.user_id)}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.memberLensName, { color: theme.text }]}>{member.name}</Text>
                  <View style={styles.memberLensDetails}>
                    {member.hd_type && (
                      <Text style={[styles.memberLensType, { color: theme.textSecondary }]}>
                        {member.hd_type}
                        {member.hd_profile && ` • ${member.hd_profile}`}
                      </Text>
                    )}
                    {member.enneagram_type && (
                      <Text style={[styles.memberLensEnneagram, { color: theme.textTertiary }]}>
                        Enneagram {member.enneagram_type}
                      </Text>
                    )}
                    {member.active_pattern && (
                      <Text style={[styles.memberLensActive, { color: theme.accent }]}>
                        Active: {member.active_pattern}
                      </Text>
                    )}
                    {!member.hd_type && !member.enneagram_type && (
                      <Text style={[styles.memberLensEmpty, { color: theme.textTertiary }]}>
                        Profile not set up yet
                      </Text>
                    )}
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        {/* My Mirror Profile Card */}
        <TouchableOpacity
          style={[styles.mirrorProfileCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
          onPress={handleMyMirrorProfile}
          activeOpacity={0.7}
        >
          <View style={styles.mirrorProfileContent}>
            <Text style={[styles.mirrorProfileIcon, { color: theme.accent }]}>◎</Text>
            <View style={styles.mirrorProfileText}>
              <Text style={[styles.mirrorProfileTitle, { color: theme.text }]}>My Mirror Profile</Text>
              <Text style={[styles.mirrorProfileSubtitle, { color: theme.textTertiary }]}>
                Access your lenses and insights
              </Text>
            </View>
          </View>
          <Text style={[styles.mirrorProfileChevron, { color: theme.textTertiary }]}>›</Text>
        </TouchableOpacity>

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
                ✓ You&apos;ve submitted a reflection
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
                        {getFirstName(reflection.user_name)}
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
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
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
    marginBottom: 16,
  },
  forumName: {
    fontSize: 26,
    fontWeight: '700',
    marginBottom: 4,
  },
  forumDescription: {
    fontSize: 15,
    lineHeight: 22,
  },
  // Members Quick List
  membersSection: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
  },
  membersTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 12,
  },
  membersList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  memberItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  memberAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  memberInitial: {
    fontSize: 14,
    fontWeight: '600',
  },
  memberName: {
    fontSize: 14,
    fontWeight: '500',
  },
  memberRole: {
    fontSize: 12,
    fontStyle: 'italic',
  },
  // Forum Pulse Styles
  pulseSection: {
    padding: 20,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 20,
  },
  pulseSectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  pulseBlock: {
    marginBottom: 16,
  },
  pulseBlockLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 8,
  },
  themeTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  themeTag: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    gap: 6,
  },
  themeTagText: {
    fontSize: 13,
    fontWeight: '500',
  },
  themeTagCount: {
    fontSize: 12,
    fontWeight: '600',
  },
  activityStats: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 2,
  },
  statLabel: {
    fontSize: 11,
    fontWeight: '500',
    textAlign: 'center',
  },
  statDivider: {
    width: 1,
    height: 32,
  },
  hdTypesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  hdTypeItem: {
    alignItems: 'center',
    minWidth: 60,
  },
  hdTypeName: {
    fontSize: 12,
    fontWeight: '500',
    marginBottom: 2,
  },
  hdTypeCount: {
    fontSize: 16,
    fontWeight: '700',
  },
  lensInsightBlock: {
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    marginTop: 4,
  },
  lensInsightText: {
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  // Member Lens Cards
  memberCardsGrid: {
    gap: 12,
  },
  memberLensCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  memberLensName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  memberLensDetails: {
    gap: 4,
  },
  memberLensType: {
    fontSize: 14,
    fontWeight: '500',
  },
  memberLensEnneagram: {
    fontSize: 13,
  },
  memberLensActive: {
    fontSize: 13,
    fontWeight: '500',
  },
  memberLensEmpty: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  // My Mirror Profile Card
  mirrorProfileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  mirrorProfileContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  mirrorProfileIcon: {
    fontSize: 28,
    marginRight: 14,
  },
  mirrorProfileText: {
    flex: 1,
  },
  mirrorProfileTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  mirrorProfileSubtitle: {
    fontSize: 13,
  },
  mirrorProfileChevron: {
    fontSize: 24,
    marginLeft: 8,
  },
  // Exercise Card
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
