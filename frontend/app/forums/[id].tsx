import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
  Modal,
  Pressable,
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
  ForumPulseResponse,
  ForumPulseMemberCard,
  getForumMemberLens,
  ForumMemberLensData,
  getPatternDiagnosis,
  PatternDiagnosisResponse
} from '../../services/api';
import ForumChatView from '../../components/ForumChatView';
import Constants from 'expo-constants';

// Types for modal states
interface MemberProfileModal {
  visible: boolean;
  member: ForumPulseMemberCard | null;
  lensData: ForumMemberLensData | null;
  loading: boolean;
}

interface DomainReflectionsModal {
  visible: boolean;
  domainId: string;
  domainName: string;
  reflections: ForumReflection[];
}

interface TypeMembersModal {
  visible: boolean;
  typeName: string;
  members: ForumPulseMemberCard[];
}

interface InsightModal {
  visible: boolean;
  insight: string;
}

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
  
  // Forum Chat state
  const [showForumChat, setShowForumChat] = useState(false);
  const [forumChatInitialMode, setForumChatInitialMode] = useState<'self' | 'member' | 'forum'>('self');
  const [forumChatInitialMember, setForumChatInitialMember] = useState<ForumPulseMemberCard | null>(null);
  
  // Modal states for interactive Forum Pulse
  const [memberModal, setMemberModal] = useState<MemberProfileModal>({ visible: false, member: null, lensData: null, loading: false });
  const [domainModal, setDomainModal] = useState<DomainReflectionsModal>({ visible: false, domainId: '', domainName: '', reflections: [] });
  const [typeModal, setTypeModal] = useState<TypeMembersModal>({ visible: false, typeName: '', members: [] });
  const [insightModal, setInsightModal] = useState<InsightModal>({ visible: false, insight: '' });
  
  // FIX 4: Forum Pattern State
  const [forumPattern, setForumPattern] = useState<PatternDiagnosisResponse | null>(null);
  const [forumPatternLoading, setForumPatternLoading] = useState(false);
  const [showForumPattern, setShowForumPattern] = useState(false);

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
    // Navigate to the Patterns page with forum context
    // This shows the EXACT same Patterns experience as personal Mirror
    router.push(`/forums/patterns?forumId=${forumId}&forumName=${encodeURIComponent(forum?.name || 'Forum')}`);
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

  // =============================================
  // Modal Handlers for Interactive Forum Pulse
  // =============================================
  
  // Open member profile modal and fetch full lens data
  const handleMemberPress = async (member: ForumPulseMemberCard) => {
    if (!user?.id) return;
    
    // Show modal immediately with basic data while loading full lens data
    setMemberModal({ visible: true, member, lensData: null, loading: true });
    
    try {
      const response = await getForumMemberLens(forumId, member.user_id, user.id);
      setMemberModal(prev => ({ 
        ...prev, 
        lensData: response.lens_data, 
        loading: false 
      }));
    } catch (error) {
      console.error('[Forum] Error fetching member lens data:', error);
      setMemberModal(prev => ({ ...prev, loading: false }));
    }
  };
  
  // Open domain reflections modal
  const handleThemePress = (domainId: string, domainName: string) => {
    const domainReflections = reflections.filter(r => r.selected_domain === domainId);
    setDomainModal({ 
      visible: true, 
      domainId, 
      domainName, 
      reflections: domainReflections 
    });
  };
  
  // Open type members modal
  const handleTypePress = (typeName: string) => {
    if (!pulse) return;
    const typeMembers = pulse.member_cards.filter(m => m.hd_type === typeName);
    setTypeModal({ visible: true, typeName, members: typeMembers });
  };
  
  // Open lens insight explanation modal
  const handleInsightPress = () => {
    if (!pulse?.lens_insight) return;
    setInsightModal({ visible: true, insight: pulse.lens_insight });
  };
  
  // Close all modals
  const closeAllModals = () => {
    setMemberModal({ visible: false, member: null, lensData: null, loading: false });
    setDomainModal({ visible: false, domainId: '', domainName: '', reflections: [] });
    setTypeModal({ visible: false, typeName: '', members: [] });
    setInsightModal({ visible: false, insight: '' });
  };

  // Open Forum Chat in member mode with a specific member selected
  const openForumChatWithMember = (member: ForumPulseMemberCard) => {
    closeAllModals();
    setForumChatInitialMode('member');
    setForumChatInitialMember(member);
    setShowForumChat(true);
  };

  // Open Forum Chat in default mode (self)
  const openForumChat = () => {
    setForumChatInitialMode('self');
    setForumChatInitialMember(null);
    setShowForumChat(true);
  };

  // Close Forum Chat and reset initial state
  const closeForumChat = () => {
    setShowForumChat(false);
    setForumChatInitialMode('self');
    setForumChatInitialMember(null);
  };
  
  // FIX 4: Handle forum pattern reveal
  const handleRevealGroupPattern = async () => {
    if (!user?.id) return;
    setForumPatternLoading(true);
    try {
      const response = await getPatternDiagnosis(user.id);
      setForumPattern(response);
      setShowForumPattern(true);
    } catch (err) {
      console.error('[Forum] Pattern load error:', err);
    } finally {
      setForumPatternLoading(false);
    }
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

        {/* FIX 4: Forum Pattern Entry - "What's happening in this room" */}
        <View style={[styles.forumPatternCard, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '25' }]}>
          <Text style={[styles.forumPatternTitle, { color: theme.text }]}>
            What's happening in this room
          </Text>
          <Text style={[styles.forumPatternSub, { color: theme.textSecondary }]}>
            See the pattern shaping this group right now
          </Text>
          
          {!showForumPattern ? (
            <TouchableOpacity
              style={[styles.forumPatternButton, { backgroundColor: theme.accent }]}
              onPress={handleRevealGroupPattern}
              disabled={forumPatternLoading}
            >
              {forumPatternLoading ? (
                <ActivityIndicator size="small" color={theme.textInverse} />
              ) : (
                <Text style={[styles.forumPatternButtonText, { color: theme.textInverse }]}>
                  Reveal group pattern
                </Text>
              )}
            </TouchableOpacity>
          ) : forumPattern ? (
            <View style={styles.forumPatternResult}>
              <Text style={[styles.forumPatternResultTitle, { color: theme.accent }]}>
                {forumPattern.pattern_title}
              </Text>
              <Text style={[styles.forumPatternResultText, { color: theme.text }]}>
                {forumPattern.what_is_happening}
              </Text>
              <Text style={[styles.forumPatternResultWisdom, { color: theme.textSecondary }]}>
                {forumPattern.what_would_be_wise}
              </Text>
              <TouchableOpacity
                style={[styles.forumPatternRefreshBtn, { borderColor: theme.border }]}
                onPress={() => setShowForumPattern(false)}
              >
                <Text style={[styles.forumPatternRefreshText, { color: theme.textTertiary }]}>
                  Hide
                </Text>
              </TouchableOpacity>
            </View>
          ) : null}
        </View>

        {/* Ask Mirror Button */}
        <TouchableOpacity
          style={[styles.askMirrorSection, { backgroundColor: theme.accent + '10', borderColor: theme.accent + '30' }]}
          onPress={openForumChat}
          activeOpacity={0.7}
        >
          <View style={styles.askMirrorContent}>
            <View style={[styles.askMirrorIcon, { backgroundColor: theme.accent + '20' }]}>
              <Text style={{ fontSize: 20 }}>✨</Text>
            </View>
            <View style={styles.askMirrorTextContainer}>
              <Text style={[styles.askMirrorTitle, { color: theme.text }]}>Ask Mirror</Text>
              <Text style={[styles.askMirrorSubtitle, { color: theme.textSecondary }]}>
                Explore yourself, members, or forum dynamics
              </Text>
            </View>
          </View>
          <Text style={[styles.askMirrorArrow, { color: theme.accent }]}>→</Text>
        </TouchableOpacity>

        {/* Forum Story Card */}
        <TouchableOpacity
          style={[styles.forumStoryCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
          onPress={() => router.push({ pathname: '/forums/story', params: { forumId } })}
          activeOpacity={0.7}
        >
          <View style={styles.forumStoryContent}>
            <View style={[styles.forumStoryIcon, { backgroundColor: theme.accent + '15' }]}>
              <Text style={{ fontSize: 20 }}>🌀</Text>
            </View>
            <View style={styles.forumStoryTextContainer}>
              <Text style={[styles.forumStoryTitle, { color: theme.text }]}>Forum Story</Text>
              <Text style={[styles.forumStorySubtitle, { color: theme.textSecondary }]}>
                A reflective view of what this group composition may bring
              </Text>
            </View>
          </View>
          <TouchableOpacity
            style={[styles.forumStoryButton, { backgroundColor: theme.accent + '15' }]}
            onPress={() => router.push({ pathname: '/forums/story', params: { forumId } })}
          >
            <Text style={[styles.forumStoryButtonText, { color: theme.accent }]}>Explore</Text>
          </TouchableOpacity>
        </TouchableOpacity>

        {/* Forum Dynamics Card */}
        <TouchableOpacity
          style={[styles.forumDynamicsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
          onPress={() => router.push({ pathname: '/forums/dynamics', params: { forumId } })}
          activeOpacity={0.7}
        >
          <View style={styles.forumDynamicsContent}>
            <View style={[styles.forumDynamicsIcon, { backgroundColor: theme.accent + '15' }]}>
              <Text style={{ fontSize: 20 }}>🔮</Text>
            </View>
            <View style={styles.forumDynamicsTextContainer}>
              <Text style={[styles.forumDynamicsTitle, { color: theme.text }]}>Forum Dynamics</Text>
              <Text style={[styles.forumDynamicsSubtitle, { color: theme.textSecondary }]}>
                A view of the patterns and diversity within this circle
              </Text>
            </View>
          </View>
          <TouchableOpacity
            style={[styles.forumDynamicsButton, { backgroundColor: theme.accent + '15' }]}
            onPress={() => router.push({ pathname: '/forums/dynamics', params: { forumId } })}
          >
            <Text style={[styles.forumDynamicsButtonText, { color: theme.accent }]}>Explore</Text>
          </TouchableOpacity>
        </TouchableOpacity>

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
                    <TouchableOpacity 
                      key={theme_item.domain_id} 
                      style={[styles.themeTag, { backgroundColor: theme.accent + '15', borderColor: theme.accent + '30' }]}
                      onPress={() => handleThemePress(theme_item.domain_id, theme_item.domain_name)}
                      activeOpacity={0.7}
                    >
                      <Text style={[styles.themeTagText, { color: theme.accent }]}>
                        {theme_item.domain_name}
                      </Text>
                      <Text style={[styles.themeTagCount, { color: theme.textTertiary }]}>
                        {theme_item.count}
                      </Text>
                    </TouchableOpacity>
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
                    <TouchableOpacity 
                      key={type} 
                      style={styles.hdTypeItem}
                      onPress={() => handleTypePress(type)}
                      activeOpacity={0.7}
                    >
                      <Text style={[styles.hdTypeName, { color: theme.textSecondary }]}>{type}</Text>
                      <Text style={[styles.hdTypeCount, { color: theme.text }]}>{count}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            )}
            
            {/* Lens Insight */}
            {pulse.lens_insight && (
              <TouchableOpacity 
                style={[styles.lensInsightBlock, { backgroundColor: theme.accent + '08', borderLeftColor: theme.accent }]}
                onPress={handleInsightPress}
                activeOpacity={0.8}
              >
                <Text style={[styles.lensInsightText, { color: theme.textSecondary }]}>
                  {pulse.lens_insight}
                </Text>
                <Text style={[styles.lensInsightHint, { color: theme.textTertiary }]}>Tap to learn more</Text>
              </TouchableOpacity>
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
                  onPress={() => handleMemberPress(member)}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.memberLensName, { color: theme.text }]}>{member.name}</Text>
                  <View style={styles.memberLensDetails}>
                    {/* HD Type • Profile */}
                    {member.hd_type && (
                      <Text style={[styles.memberLensType, { color: theme.textSecondary }]}>
                        {member.hd_type}
                        {member.hd_profile && ` • ${member.hd_profile}`}
                      </Text>
                    )}
                    {/* Authority */}
                    {member.hd_authority && (
                      <Text style={[styles.memberLensAuthority, { color: theme.textTertiary }]}>
                        {member.hd_authority} Authority
                      </Text>
                    )}
                    {/* Enneagram core */}
                    {member.enneagram_type && (
                      <Text style={[styles.memberLensEnneagram, { color: theme.textTertiary }]}>
                        Enneagram {member.enneagram_type}
                      </Text>
                    )}
                    {/* Active Pattern Domain */}
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

      {/* ============================================
          MODALS - Interactive Forum Pulse Components
          ============================================ */}
      
      {/* Member Lens Profile Modal */}
      <Modal
        visible={memberModal.visible}
        transparent
        animationType="fade"
        onRequestClose={closeAllModals}
      >
        <Pressable style={styles.modalOverlay} onPress={closeAllModals}>
          <Pressable style={[styles.modalContent, styles.modalLarge, { backgroundColor: theme.surface }]} onPress={() => {}}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.text }]}>Member Lens Profile</Text>
              <TouchableOpacity onPress={closeAllModals} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                <Text style={[styles.modalClose, { color: theme.textTertiary }]}>✕</Text>
              </TouchableOpacity>
            </View>
            
            {memberModal.member && (
              <ScrollView style={styles.modalScrollContent} showsVerticalScrollIndicator={false}>
                {/* Header with name */}
                <View style={styles.memberProfileContent}>
                  <View style={[styles.memberProfileAvatar, { backgroundColor: theme.accent + '20' }]}>
                    <Text style={[styles.memberProfileInitial, { color: theme.accent }]}>
                      {memberModal.member.name.charAt(0).toUpperCase()}
                    </Text>
                  </View>
                  <Text style={[styles.memberProfileName, { color: theme.text }]}>
                    {memberModal.member.name}
                  </Text>
                </View>
                
                {memberModal.loading ? (
                  <View style={styles.lensLoadingContainer}>
                    <ActivityIndicator size="small" color={theme.accent} />
                    <Text style={[styles.lensLoadingText, { color: theme.textTertiary }]}>Loading lens data...</Text>
                  </View>
                ) : memberModal.lensData ? (
                  <View style={styles.lensDataContainer}>
                    {/* FIX 6: What this means in real life */}
                    <View style={[styles.realLifeMeaningBox, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
                      <Text style={[styles.realLifeMeaningTitle, { color: theme.accent }]}>
                        What this means in real life
                      </Text>
                      <View style={styles.realLifeMeaningContent}>
                        {memberModal.lensData.human_design.type === 'Manifestor' && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.text }]}>
                            Tends to act quickly, then process after. May not always explain before initiating.
                          </Text>
                        )}
                        {memberModal.lensData.human_design.type === 'Generator' && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.text }]}>
                            Has sustainable energy when engaged. Responds best when asked, not told.
                          </Text>
                        )}
                        {memberModal.lensData.human_design.type === 'Manifesting Generator' && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.text }]}>
                            Fast-moving multi-tasker. May skip steps and come back. Thrives with variety.
                          </Text>
                        )}
                        {memberModal.lensData.human_design.type === 'Projector' && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.text }]}>
                            Sees deeply into others. Works best in bursts. Needs recognition to share.
                          </Text>
                        )}
                        {memberModal.lensData.human_design.type === 'Reflector' && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.text }]}>
                            Mirrors the group's health. Needs time for big decisions. Unusually perceptive.
                          </Text>
                        )}
                        {memberModal.lensData.human_design.authority?.includes('Emotional') && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.textSecondary }]}>
                            Clarity comes over time, not in the moment. Give space for processing.
                          </Text>
                        )}
                        {memberModal.lensData.human_design.authority?.includes('Sacral') && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.textSecondary }]}>
                            Makes decisions through gut response. Yes/no questions work best.
                          </Text>
                        )}
                        {memberModal.lensData.human_design.authority?.includes('Splenic') && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.textSecondary }]}>
                            Trusts instinct in the moment. Knows what's healthy or not instantly.
                          </Text>
                        )}
                        {memberModal.lensData.enneagram.core_type === 1 && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.textSecondary }]}>
                            High standards, notices what could be better. Values doing things right.
                          </Text>
                        )}
                        {memberModal.lensData.enneagram.core_type === 2 && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.textSecondary }]}>
                            Naturally helpful, often anticipates needs before being asked.
                          </Text>
                        )}
                        {memberModal.lensData.enneagram.core_type === 3 && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.textSecondary }]}>
                            Achievement-oriented, adapts to what works. Values being seen as successful.
                          </Text>
                        )}
                        {memberModal.lensData.enneagram.core_type === 4 && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.textSecondary }]}>
                            Drawn to depth and meaning. May feel misunderstood. Values authenticity.
                          </Text>
                        )}
                        {memberModal.lensData.enneagram.core_type === 5 && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.textSecondary }]}>
                            Needs time to observe and understand. Protects energy. Values knowledge.
                          </Text>
                        )}
                        {memberModal.lensData.enneagram.core_type === 6 && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.textSecondary }]}>
                            Anticipates problems, values security. Loyal once trust is established.
                          </Text>
                        )}
                        {memberModal.lensData.enneagram.core_type === 7 && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.textSecondary }]}>
                            Moves toward options and possibilities. Avoids restriction and boredom.
                          </Text>
                        )}
                        {memberModal.lensData.enneagram.core_type === 8 && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.textSecondary }]}>
                            Direct and protective. Takes up space. Values strength and honesty.
                          </Text>
                        )}
                        {memberModal.lensData.enneagram.core_type === 9 && (
                          <Text style={[styles.realLifeMeaningText, { color: theme.textSecondary }]}>
                            Goes with the flow, seeks harmony. May merge with others' agendas.
                          </Text>
                        )}
                      </View>
                    </View>
                    
                    {/* Human Design Section */}
                    {(memberModal.lensData.human_design.type || memberModal.lensData.human_design.authority) && (
                      <View style={[styles.lensSection, { borderTopColor: theme.border }]}>
                        <Text style={[styles.lensSectionTitle, { color: theme.text }]}>Human Design</Text>
                        {memberModal.lensData.human_design.type && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Type</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.human_design.type}</Text>
                          </View>
                        )}
                        {memberModal.lensData.human_design.strategy && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Strategy</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.human_design.strategy}</Text>
                          </View>
                        )}
                        {memberModal.lensData.human_design.authority && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Authority</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.human_design.authority}</Text>
                          </View>
                        )}
                        {memberModal.lensData.human_design.profile && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Profile</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.human_design.profile}</Text>
                          </View>
                        )}
                        {memberModal.lensData.human_design.definition && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Definition</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.human_design.definition}</Text>
                          </View>
                        )}
                        {memberModal.lensData.human_design.incarnation_cross && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Incarnation Cross</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.human_design.incarnation_cross}</Text>
                          </View>
                        )}
                        {memberModal.lensData.human_design.centers_defined.length > 0 && (
                          <View style={styles.lensRowVertical}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Defined Centers</Text>
                            <Text style={[styles.lensValueSmall, { color: theme.text }]}>
                              {memberModal.lensData.human_design.centers_defined.join(', ')}
                            </Text>
                          </View>
                        )}
                        {memberModal.lensData.human_design.centers_undefined.length > 0 && (
                          <View style={styles.lensRowVertical}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Open Centers</Text>
                            <Text style={[styles.lensValueSmall, { color: theme.textSecondary }]}>
                              {memberModal.lensData.human_design.centers_undefined.join(', ')}
                            </Text>
                          </View>
                        )}
                        {memberModal.lensData.human_design.active_channels.length > 0 && (
                          <View style={styles.lensRowVertical}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Key Channels</Text>
                            <Text style={[styles.lensValueSmall, { color: theme.text }]}>
                              {memberModal.lensData.human_design.active_channels.join(' • ')}
                            </Text>
                          </View>
                        )}
                        {memberModal.lensData.human_design.active_gates.length > 0 && (
                          <View style={styles.lensRowVertical}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Key Gates</Text>
                            <Text style={[styles.lensValueSmall, { color: theme.textSecondary }]}>
                              {memberModal.lensData.human_design.active_gates.slice(0, 10).join(', ')}
                            </Text>
                          </View>
                        )}
                      </View>
                    )}
                    
                    {/* Enneagram Section */}
                    {memberModal.lensData.enneagram.core_type && (
                      <View style={[styles.lensSection, { borderTopColor: theme.border }]}>
                        <Text style={[styles.lensSectionTitle, { color: theme.text }]}>Enneagram</Text>
                        <View style={styles.lensRow}>
                          <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Core Type</Text>
                          <Text style={[styles.lensValue, { color: theme.text }]}>Type {memberModal.lensData.enneagram.core_type}</Text>
                        </View>
                        {memberModal.lensData.enneagram.wing && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Wing</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.enneagram.wing}</Text>
                          </View>
                        )}
                        {memberModal.lensData.enneagram.center && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Center</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.enneagram.center}</Text>
                          </View>
                        )}
                        {memberModal.lensData.enneagram.hornevian_group && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Hornevian Group</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.enneagram.hornevian_group}</Text>
                          </View>
                        )}
                        {memberModal.lensData.enneagram.harmonic_group && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Harmonic Group</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.enneagram.harmonic_group}</Text>
                          </View>
                        )}
                        {memberModal.lensData.enneagram.growth_direction && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Growth Direction</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>→ Type {memberModal.lensData.enneagram.growth_direction}</Text>
                          </View>
                        )}
                        {memberModal.lensData.enneagram.stress_direction && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Stress Direction</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>→ Type {memberModal.lensData.enneagram.stress_direction}</Text>
                          </View>
                        )}
                      </View>
                    )}
                    
                    {/* Astrology Section */}
                    {(memberModal.lensData.astrology.sun || memberModal.lensData.astrology.moon || memberModal.lensData.astrology.rising) && (
                      <View style={[styles.lensSection, { borderTopColor: theme.border }]}>
                        <Text style={[styles.lensSectionTitle, { color: theme.text }]}>Astrology</Text>
                        {memberModal.lensData.astrology.sun && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Sun</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.astrology.sun}</Text>
                          </View>
                        )}
                        {memberModal.lensData.astrology.moon && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Moon</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.astrology.moon}</Text>
                          </View>
                        )}
                        {memberModal.lensData.astrology.rising && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Rising</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.astrology.rising}</Text>
                          </View>
                        )}
                        {memberModal.lensData.astrology.dominant_element && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Dominant Element</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.astrology.dominant_element}</Text>
                          </View>
                        )}
                        {memberModal.lensData.astrology.dominant_modality && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Dominant Modality</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>{memberModal.lensData.astrology.dominant_modality}</Text>
                          </View>
                        )}
                      </View>
                    )}
                    
                    {/* Numerology Section */}
                    {memberModal.lensData.numerology.life_path && (
                      <View style={[styles.lensSection, { borderTopColor: theme.border }]}>
                        <Text style={[styles.lensSectionTitle, { color: theme.text }]}>Numerology</Text>
                        <View style={styles.lensRow}>
                          <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Life Path</Text>
                          <Text style={[styles.lensValue, { color: theme.text }]}>
                            {typeof memberModal.lensData.numerology.life_path === 'object' 
                              ? memberModal.lensData.numerology.life_path.number 
                              : memberModal.lensData.numerology.life_path}
                          </Text>
                        </View>
                        {memberModal.lensData.numerology.expression && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Expression</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>
                              {typeof memberModal.lensData.numerology.expression === 'object'
                                ? memberModal.lensData.numerology.expression.number
                                : memberModal.lensData.numerology.expression}
                            </Text>
                          </View>
                        )}
                        {memberModal.lensData.numerology.soul_urge && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Soul Urge</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>
                              {typeof memberModal.lensData.numerology.soul_urge === 'object'
                                ? memberModal.lensData.numerology.soul_urge.number
                                : memberModal.lensData.numerology.soul_urge}
                            </Text>
                          </View>
                        )}
                        {memberModal.lensData.numerology.personality && (
                          <View style={styles.lensRow}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Personality</Text>
                            <Text style={[styles.lensValue, { color: theme.text }]}>
                              {typeof memberModal.lensData.numerology.personality === 'object'
                                ? memberModal.lensData.numerology.personality.number
                                : memberModal.lensData.numerology.personality}
                            </Text>
                          </View>
                        )}
                      </View>
                    )}
                    
                    {/* Patterns Section */}
                    {(memberModal.lensData.patterns.active_domains.length > 0 || 
                      memberModal.lensData.patterns.recurring_domains.length > 0) && (
                      <View style={[styles.lensSection, { borderTopColor: theme.border }]}>
                        <Text style={[styles.lensSectionTitle, { color: theme.text }]}>Patterns</Text>
                        {memberModal.lensData.patterns.active_domains.length > 0 && (
                          <View style={styles.lensRowVertical}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Active Domains</Text>
                            <View style={styles.patternTags}>
                              {memberModal.lensData.patterns.active_domains.map((domain, idx) => (
                                <View key={idx} style={[styles.patternTag, { backgroundColor: theme.accent + '20' }]}>
                                  <Text style={[styles.patternTagText, { color: theme.accent }]}>{domain}</Text>
                                </View>
                              ))}
                            </View>
                          </View>
                        )}
                        {memberModal.lensData.patterns.recurring_domains.length > 0 && (
                          <View style={styles.lensRowVertical}>
                            <Text style={[styles.lensLabel, { color: theme.textTertiary }]}>Recurring Domains</Text>
                            <View style={styles.patternTags}>
                              {memberModal.lensData.patterns.recurring_domains.map((domain, idx) => (
                                <View key={idx} style={[styles.patternTag, { backgroundColor: theme.border }]}>
                                  <Text style={[styles.patternTagText, { color: theme.textSecondary }]}>{domain}</Text>
                                </View>
                              ))}
                            </View>
                          </View>
                        )}
                      </View>
                    )}
                    
                    {/* Ask Mirror Button */}
                    <TouchableOpacity
                      style={[styles.askMirrorButton, { backgroundColor: theme.accent + '15', borderColor: theme.accent + '40' }]}
                      activeOpacity={0.7}
                      onPress={() => {
                        if (memberModal.member) {
                          openForumChatWithMember(memberModal.member);
                        }
                      }}
                    >
                      <Text style={[styles.askMirrorButtonText, { color: theme.accent }]}>
                        Ask Mirror About This Member
                      </Text>
                    </TouchableOpacity>
                  </View>
                ) : (
                  // Fallback to basic data from member card
                  <View style={styles.memberProfileDetails}>
                    {memberModal.member.hd_type && (
                      <View style={styles.profileRow}>
                        <Text style={[styles.profileLabel, { color: theme.textTertiary }]}>Type</Text>
                        <Text style={[styles.profileValue, { color: theme.text }]}>{memberModal.member.hd_type}</Text>
                      </View>
                    )}
                    {memberModal.member.hd_profile && (
                      <View style={styles.profileRow}>
                        <Text style={[styles.profileLabel, { color: theme.textTertiary }]}>Profile</Text>
                        <Text style={[styles.profileValue, { color: theme.text }]}>{memberModal.member.hd_profile}</Text>
                      </View>
                    )}
                    {memberModal.member.hd_authority && (
                      <View style={styles.profileRow}>
                        <Text style={[styles.profileLabel, { color: theme.textTertiary }]}>Authority</Text>
                        <Text style={[styles.profileValue, { color: theme.text }]}>{memberModal.member.hd_authority}</Text>
                      </View>
                    )}
                    {memberModal.member.enneagram_type && (
                      <View style={styles.profileRow}>
                        <Text style={[styles.profileLabel, { color: theme.textTertiary }]}>Enneagram</Text>
                        <Text style={[styles.profileValue, { color: theme.text }]}>Type {memberModal.member.enneagram_type}</Text>
                      </View>
                    )}
                    {memberModal.member.active_pattern && (
                      <View style={styles.profileRow}>
                        <Text style={[styles.profileLabel, { color: theme.textTertiary }]}>Active Pattern</Text>
                        <Text style={[styles.profileValue, { color: theme.accent }]}>{memberModal.member.active_pattern}</Text>
                      </View>
                    )}
                    
                    {!memberModal.member.hd_type && !memberModal.member.enneagram_type && (
                      <Text style={[styles.profileEmpty, { color: theme.textTertiary }]}>
                        This member hasn't set up their profile yet.
                      </Text>
                    )}
                  </View>
                )}
              </ScrollView>
            )}
          </Pressable>
        </Pressable>
      </Modal>

      {/* Domain Reflections Modal */}
      <Modal
        visible={domainModal.visible}
        transparent
        animationType="fade"
        onRequestClose={closeAllModals}
      >
        <Pressable style={styles.modalOverlay} onPress={closeAllModals}>
          <Pressable style={[styles.modalContent, styles.modalLarge, { backgroundColor: theme.surface }]} onPress={() => {}}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.text }]}>{domainModal.domainName}</Text>
              <TouchableOpacity onPress={closeAllModals} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                <Text style={[styles.modalClose, { color: theme.textTertiary }]}>✕</Text>
              </TouchableOpacity>
            </View>
            
            <Text style={[styles.modalSubtitle, { color: theme.textTertiary }]}>
              {domainModal.reflections.length} reflection{domainModal.reflections.length !== 1 ? 's' : ''} shared
            </Text>
            
            <ScrollView style={styles.modalScrollContent} showsVerticalScrollIndicator={false}>
              {domainModal.reflections.length === 0 ? (
                <Text style={[styles.emptyText, { color: theme.textTertiary }]}>
                  No reflections shared in this domain yet.
                </Text>
              ) : (
                domainModal.reflections.map((reflection) => (
                  <View key={reflection.id} style={[styles.modalReflectionCard, { borderBottomColor: theme.border }]}>
                    <Text style={[styles.modalReflectionAuthor, { color: theme.text }]}>
                      {reflection.user_name}
                    </Text>
                    <Text style={[styles.modalReflectionText, { color: theme.textSecondary }]}>
                      {reflection.reflection_text}
                    </Text>
                  </View>
                ))
              )}
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>

      {/* Type Members Modal */}
      <Modal
        visible={typeModal.visible}
        transparent
        animationType="fade"
        onRequestClose={closeAllModals}
      >
        <Pressable style={styles.modalOverlay} onPress={closeAllModals}>
          <Pressable style={[styles.modalContent, { backgroundColor: theme.surface }]} onPress={() => {}}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.text }]}>{typeModal.typeName}s</Text>
              <TouchableOpacity onPress={closeAllModals} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                <Text style={[styles.modalClose, { color: theme.textTertiary }]}>✕</Text>
              </TouchableOpacity>
            </View>
            
            <Text style={[styles.modalSubtitle, { color: theme.textTertiary }]}>
              {typeModal.members.length} member{typeModal.members.length !== 1 ? 's' : ''} with this type
            </Text>
            
            <View style={styles.typeMembersList}>
              {typeModal.members.map((member) => (
                <View key={member.user_id} style={[styles.typeMemberItem, { borderBottomColor: theme.border }]}>
                  <View style={[styles.typeMemberAvatar, { backgroundColor: theme.accent + '20' }]}>
                    <Text style={[styles.typeMemberInitial, { color: theme.accent }]}>
                      {member.name.charAt(0).toUpperCase()}
                    </Text>
                  </View>
                  <View style={styles.typeMemberInfo}>
                    <Text style={[styles.typeMemberName, { color: theme.text }]}>{member.name}</Text>
                    {member.hd_profile && (
                      <Text style={[styles.typeMemberProfile, { color: theme.textTertiary }]}>
                        Profile {member.hd_profile}
                      </Text>
                    )}
                  </View>
                </View>
              ))}
            </View>
          </Pressable>
        </Pressable>
      </Modal>

      {/* Lens Insight Modal */}
      <Modal
        visible={insightModal.visible}
        transparent
        animationType="fade"
        onRequestClose={closeAllModals}
      >
        <Pressable style={styles.modalOverlay} onPress={closeAllModals}>
          <Pressable style={[styles.modalContent, { backgroundColor: theme.surface }]} onPress={() => {}}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.text }]}>Lens Insight</Text>
              <TouchableOpacity onPress={closeAllModals} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                <Text style={[styles.modalClose, { color: theme.textTertiary }]}>✕</Text>
              </TouchableOpacity>
            </View>
            
            <View style={styles.insightContent}>
              <Text style={[styles.insightMainText, { color: theme.text }]}>
                {insightModal.insight}
              </Text>
              
              <View style={[styles.insightNote, { backgroundColor: theme.accent + '08' }]}>
                <Text style={[styles.insightNoteText, { color: theme.textSecondary }]}>
                  This insight is generated based on the lens data shared by forum members. 
                  It reflects tendencies that may be present in the group, not predictions or prescriptions.
                </Text>
              </View>
              
              <Text style={[styles.insightDisclaimer, { color: theme.textTertiary }]}>
                Human Design describes energy patterns. How these show up in practice varies for each person.
              </Text>
            </View>
          </Pressable>
        </Pressable>
      </Modal>

      {/* Forum Chat Full Screen Modal */}
      <Modal
        visible={showForumChat}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={closeForumChat}
      >
        <SafeAreaView style={{ flex: 1, backgroundColor: theme.background }} edges={['top']}>
          <ForumChatView
            forumId={forumId}
            members={pulse?.member_cards || []}
            onClose={closeForumChat}
            initialMode={forumChatInitialMode}
            initialMember={forumChatInitialMember}
          />
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  
  // FIX 4: Forum Pattern Entry Card styles
  forumPatternCard: {
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    marginBottom: 12,
  },
  forumPatternTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 6,
  },
  forumPatternSub: {
    fontSize: 14,
    marginBottom: 14,
  },
  forumPatternButton: {
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  forumPatternButtonText: {
    fontSize: 15,
    fontWeight: '600',
  },
  forumPatternResult: {
    gap: 10,
  },
  forumPatternResultTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  forumPatternResultText: {
    fontSize: 14,
    lineHeight: 21,
  },
  forumPatternResultWisdom: {
    fontSize: 13,
    fontStyle: 'italic',
    lineHeight: 19,
  },
  forumPatternRefreshBtn: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    alignSelf: 'flex-start',
    marginTop: 8,
  },
  forumPatternRefreshText: {
    fontSize: 13,
    fontWeight: '500',
  },
  
  // FIX 6: Real Life Meaning styles
  realLifeMeaningBox: {
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    marginBottom: 16,
  },
  realLifeMeaningTitle: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  realLifeMeaningContent: {
    gap: 6,
  },
  realLifeMeaningText: {
    fontSize: 14,
    lineHeight: 20,
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
  // Ask Mirror Button
  askMirrorSection: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 20,
  },
  askMirrorContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  askMirrorIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  askMirrorTextContainer: {
    flex: 1,
  },
  askMirrorTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  askMirrorSubtitle: {
    fontSize: 13,
  },
  askMirrorArrow: {
    fontSize: 18,
    fontWeight: '600',
    paddingLeft: 8,
  },
  // Forum Story Card
  forumStoryCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  forumStoryContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 12,
  },
  forumStoryIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  forumStoryTextContainer: {
    flex: 1,
  },
  forumStoryTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  forumStorySubtitle: {
    fontSize: 13,
    lineHeight: 18,
  },
  forumStoryButton: {
    alignSelf: 'flex-start',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  forumStoryButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  // Forum Dynamics Card Styles
  forumDynamicsCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  forumDynamicsContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 12,
  },
  forumDynamicsIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  forumDynamicsTextContainer: {
    flex: 1,
  },
  forumDynamicsTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  forumDynamicsSubtitle: {
    fontSize: 13,
    lineHeight: 18,
  },
  forumDynamicsButton: {
    alignSelf: 'flex-start',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  forumDynamicsButtonText: {
    fontSize: 14,
    fontWeight: '600',
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
  memberLensAuthority: {
    fontSize: 12,
  },
  // Lens Data Loading
  lensLoadingContainer: {
    alignItems: 'center',
    paddingVertical: 32,
    gap: 12,
  },
  lensLoadingText: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  // Lens Data Container
  lensDataContainer: {
    paddingTop: 8,
  },
  lensSection: {
    paddingVertical: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    marginTop: 8,
  },
  lensSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  lensRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingVertical: 6,
  },
  lensRowVertical: {
    paddingVertical: 8,
  },
  lensLabel: {
    fontSize: 13,
    flex: 1,
  },
  lensValue: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1.5,
    textAlign: 'right',
  },
  lensValueSmall: {
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4,
  },
  patternTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 8,
  },
  patternTag: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  patternTagText: {
    fontSize: 12,
    fontWeight: '500',
  },
  askMirrorButton: {
    marginTop: 20,
    marginBottom: 8,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
  },
  askMirrorButtonText: {
    fontSize: 15,
    fontWeight: '600',
  },
  askMirrorHint: {
    fontSize: 11,
    marginTop: 4,
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
  
  // ============================================
  // Modal Styles
  // ============================================
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    width: '100%',
    maxWidth: 360,
    borderRadius: 20,
    padding: 20,
    maxHeight: '70%',
  },
  modalLarge: {
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  modalClose: {
    fontSize: 20,
    fontWeight: '300',
    padding: 4,
  },
  modalSubtitle: {
    fontSize: 13,
    marginBottom: 16,
  },
  modalScrollContent: {
    maxHeight: 400,
  },
  
  // Member Profile Modal
  memberProfileContent: {
    alignItems: 'center',
    paddingTop: 8,
  },
  memberProfileAvatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  memberProfileInitial: {
    fontSize: 26,
    fontWeight: '600',
  },
  memberProfileName: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 20,
    textAlign: 'center',
  },
  memberProfileDetails: {
    width: '100%',
    gap: 12,
  },
  profileRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  profileLabel: {
    fontSize: 14,
  },
  profileValue: {
    fontSize: 15,
    fontWeight: '500',
  },
  profileEmpty: {
    fontSize: 14,
    textAlign: 'center',
    marginTop: 16,
    fontStyle: 'italic',
  },
  
  // Domain Reflections Modal
  modalReflectionCard: {
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  modalReflectionAuthor: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 6,
  },
  modalReflectionText: {
    fontSize: 14,
    lineHeight: 20,
  },
  
  // Type Members Modal
  typeMembersList: {
    gap: 4,
  },
  typeMemberItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  typeMemberAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  typeMemberInitial: {
    fontSize: 16,
    fontWeight: '600',
  },
  typeMemberInfo: {
    flex: 1,
  },
  typeMemberName: {
    fontSize: 15,
    fontWeight: '500',
  },
  typeMemberProfile: {
    fontSize: 13,
    marginTop: 2,
  },
  
  // Lens Insight Modal
  insightContent: {
    gap: 16,
  },
  insightMainText: {
    fontSize: 16,
    lineHeight: 24,
  },
  insightNote: {
    padding: 14,
    borderRadius: 12,
  },
  insightNoteText: {
    fontSize: 13,
    lineHeight: 19,
  },
  insightDisclaimer: {
    fontSize: 12,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  
  // Lens Insight Hint
  lensInsightHint: {
    fontSize: 11,
    marginTop: 6,
    fontStyle: 'italic',
  },
});
