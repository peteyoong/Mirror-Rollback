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

// =============================================================================
// HUMAN UNDERSTANDING HELPER FUNCTIONS
// Transform lens data into FELT, RELATIONAL, ACTIONABLE descriptions
// =============================================================================

const getArchetypeLabel = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const enneaType = lensData.enneagram.core_type;
  
  // Generate archetype based on HD type + Enneagram
  const archetypes: Record<string, Record<number, string>> = {
    'Manifestor': { 1: 'The Principled Initiator', 2: 'The Generous Starter', 3: 'The Driven Pioneer', 4: 'The Creative Catalyst', 5: 'The Strategic Mover', 6: 'The Vigilant Leader', 7: 'The Visionary Igniter', 8: 'The Bold Activator', 9: 'The Peaceful Initiator' },
    'Generator': { 1: 'The Dedicated Builder', 2: 'The Nurturing Worker', 3: 'The Productive Achiever', 4: 'The Soulful Creator', 5: 'The Deep Investigator', 6: 'The Loyal Sustainer', 7: 'The Enthusiastic Doer', 8: 'The Powerful Producer', 9: 'The Steady Anchor' },
    'Manifesting Generator': { 1: 'The Efficient Perfectionist', 2: 'The Multi-talented Helper', 3: 'The Fast Achiever', 4: 'The Expressive Multi-tasker', 5: 'The Quick Learner', 6: 'The Adaptive Problem-solver', 7: 'The Energetic Explorer', 8: 'The Dynamic Force', 9: 'The Versatile Harmonizer' },
    'Projector': { 1: 'The Discerning Guide', 2: 'The Intuitive Counselor', 3: 'The Strategic Advisor', 4: 'The Deep Seer', 5: 'The Wise Observer', 6: 'The Trusted Mentor', 7: 'The Insightful Optimist', 8: 'The Powerful Guide', 9: 'The Gentle Director' },
    'Reflector': { 1: 'The Fair Mirror', 2: 'The Empathic Barometer', 3: 'The Adaptive Mirror', 4: 'The Sensitive Reflector', 5: 'The Observant Mirror', 6: 'The Community Sensor', 7: 'The Joyful Evaluator', 8: 'The Honest Mirror', 9: 'The Peaceful Assessor' },
  };
  
  if (hdType && enneaType && archetypes[hdType]?.[enneaType]) {
    return archetypes[hdType][enneaType];
  }
  
  if (hdType === 'Manifestor') return 'The Initiator';
  if (hdType === 'Generator') return 'The Builder';
  if (hdType === 'Manifesting Generator') return 'The Multi-tasker';
  if (hdType === 'Projector') return 'The Guide';
  if (hdType === 'Reflector') return 'The Mirror';
  return '';
};

// NEW: What it feels like to be WITH them (second person, experiential)
const getWhatItFeelsLike = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const authority = lensData.human_design.authority;
  const enneaType = lensData.enneagram.core_type;
  
  let base = '';
  
  if (hdType === 'Manifestor') {
    base = "You may feel their urgency before you understand it. There's a sense that something wants to move—even if it's not fully clear yet.";
  } else if (hdType === 'Generator') {
    base = "You can feel their energy when they're lit up about something. When they're not, there's a heaviness that's hard to miss.";
  } else if (hdType === 'Manifesting Generator') {
    base = "You might feel like you're in a whirlwind. They move fast, shift gears quickly, and you may wonder how they keep track of it all.";
  } else if (hdType === 'Projector') {
    base = "You may feel seen in a way that's both comforting and exposing. They notice things others miss—including things about you.";
  } else if (hdType === 'Reflector') {
    base = "You may find yourself reflected back. The mood in the room often shows up in how they seem—they're taking in more than they let on.";
  }
  
  // Authority modifier
  if (authority?.includes('Emotional')) {
    base += " Their energy can shift—what feels true to them today may change tomorrow. This isn't inconsistency; it's their process.";
  }
  
  // Enneagram flavor
  if (enneaType === 7) {
    base += " There's often lightness around them, but sometimes you sense something underneath they're not slowing down to feel.";
  } else if (enneaType === 8) {
    base += " You may feel the weight of their presence—protective, intense, sometimes confronting.";
  } else if (enneaType === 4) {
    base += " You might sense depth under the surface, a longing for something real that not everyone sees.";
  } else if (enneaType === 2) {
    base += " You may feel cared for, but also wonder if they're taking care of themselves.";
  } else if (enneaType === 6) {
    base += " You might notice they're scanning for what could go wrong—not out of pessimism, but vigilance.";
  }
  
  return base;
};

// SHORTENED: How they show up (max 2 lines)
const getHowTheyShowUp = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const enneaType = lensData.enneagram.core_type;
  
  if (hdType === 'Manifestor') {
    return "Initiates and moves without waiting for consensus. Acts on internal timing, not external cues.";
  } else if (hdType === 'Generator') {
    return "Shows up with sustainable energy when engaged. Responds to what's in front of them rather than pushing forward.";
  } else if (hdType === 'Manifesting Generator') {
    return "Multi-tracks, moves fast, pivots often. Efficiency over linearity.";
  } else if (hdType === 'Projector') {
    return "Observes before engaging. Offers insight when invited, not before.";
  } else if (hdType === 'Reflector') {
    return "Takes in the group's energy. Reflects back what's really happening.";
  }
  
  return "Shows up authentically based on their inner rhythm.";
};

const getAtTheirBest = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const enneaType = lensData.enneagram.core_type;
  
  let base = '';
  
  if (hdType === 'Manifestor') {
    base = "Clear, decisive, and catalytic. Creates movement when things are stuck. Others feel permission to act.";
  } else if (hdType === 'Generator') {
    base = "Deeply satisfying output. Magnetic presence that draws the right opportunities. The work itself becomes the reward.";
  } else if (hdType === 'Manifesting Generator') {
    base = "Accomplishes what seems impossible. Creates shortcuts others can follow. Brings energy and momentum.";
  } else if (hdType === 'Projector') {
    base = "Sees what's really going on. Guides others to their own clarity. Wisdom that lands when received.";
  } else if (hdType === 'Reflector') {
    base = "Reads the room with uncanny accuracy. Offers perspective that cuts through noise. Reveals truth by reflection.";
  }
  
  return base;
};

// RENAMED: "When things get tense" (situational, not personality-based)
const getWhenThingsGetTense = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const authority = lensData.human_design.authority;
  const enneaType = lensData.enneagram.core_type;
  
  let base = '';
  
  if (hdType === 'Manifestor') {
    base = "When decisions drag or feel unclear, they may push forward anyway—which can feel like pressure to others.";
  } else if (hdType === 'Generator') {
    base = "When forced to commit before feeling a clear response, they may say yes but disengage later. Or push through work that drains them.";
  } else if (hdType === 'Manifesting Generator') {
    base = "When things slow down or require too much waiting, they may skip ahead or abandon ship—leaving others scrambling.";
  } else if (hdType === 'Projector') {
    base = "When their input goes unacknowledged, they may either over-give or withdraw entirely. The bitterness can be quiet but real.";
  } else if (hdType === 'Reflector') {
    base = "When the group energy is off, they absorb it. They may seem checked out or overwhelmed—but they're processing everyone's stuff.";
  }
  
  if (authority?.includes('Emotional') && !base.includes('clarity')) {
    base += " If pushed for fast answers, they may commit to something they'll later need to undo.";
  }
  
  if (enneaType === 9) {
    base += " They may go along with decisions to keep the peace, then quietly resist later.";
  } else if (enneaType === 6) {
    base += " They may voice concerns that sound like resistance—but it's actually loyalty trying to protect the group.";
  }
  
  return base;
};

// NEW: Where misunderstandings happen (CRITICAL for forum)
const getWhereMisunderstandingsHappen = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const authority = lensData.human_design.authority;
  const enneaType = lensData.enneagram.core_type;
  
  let base = '';
  
  if (hdType === 'Manifestor') {
    base = "They may think they've communicated clearly—others may feel left out of the process. Their 'informing' can feel like announcing.";
  } else if (hdType === 'Generator') {
    base = "Their 'yes' may sound enthusiastic even when it's not fully there. Others may assume commitment that wasn't actually given.";
  } else if (hdType === 'Manifesting Generator') {
    base = "They may skip steps that seem obvious to them—but others need those steps to follow along. Speed can feel like dismissal.";
  } else if (hdType === 'Projector') {
    base = "They may assume their insight is wanted. Others may feel analyzed or advised when they just wanted to be heard.";
  } else if (hdType === 'Reflector') {
    base = "Their shifting opinions may look like indecisiveness. Others may not realize they're reflecting the group's own uncertainty back.";
  }
  
  if (authority?.includes('Emotional')) {
    base += " What they said yesterday may change today—not because they were dishonest, but because clarity moves like a wave.";
  }
  
  if (enneaType === 5) {
    base += " Their silence may be read as disinterest—when they're actually processing deeply.";
  } else if (enneaType === 3) {
    base += " Their efficiency may feel cold. They're often moving toward results faster than others expect.";
  } else if (enneaType === 8) {
    base += " Their directness can land as aggression—even when they're trying to protect.";
  }
  
  return base;
};

// SHARPENED: How to work with them (direct + practical)
const getHowToWorkWith = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const authority = lensData.human_design.authority;
  const enneaType = lensData.enneagram.core_type;
  
  let lines: string[] = [];
  
  if (hdType === 'Manifestor') {
    lines.push("Keep them informed early—not after decisions are made.");
    lines.push("Give them space to reach clarity instead of forcing answers.");
  } else if (hdType === 'Generator') {
    lines.push("Ask yes/no questions instead of open-ended ones.");
    lines.push("Watch their energy—it tells you more than their words.");
  } else if (hdType === 'Manifesting Generator') {
    lines.push("Let them pivot—it's how they find what works.");
    lines.push("Trust their process even when it looks chaotic.");
  } else if (hdType === 'Projector') {
    lines.push("Invite their perspective explicitly. Don't assume they'll offer it.");
    lines.push("Acknowledge their contributions—recognition matters more than you think.");
  } else if (hdType === 'Reflector') {
    lines.push("Give them time for big decisions—a month if possible.");
    lines.push("Ask 'what are you noticing?' to access their insight.");
  }
  
  if (authority?.includes('Emotional')) {
    lines.push("Don't press for immediate decisions. Let them sleep on it.");
  }
  
  if (enneaType === 2) lines.push("Ask what they need—they often forget to say.");
  else if (enneaType === 8) lines.push("Be direct. Don't soften or circle around issues.");
  else if (enneaType === 5) lines.push("Give them prep time. Surprises deplete them.");
  
  return lines.join('\n');
};

// NEW: Micro-trigger (1-liner pattern interrupt for real-time awareness)
const getMicroTrigger = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const authority = lensData.human_design.authority;
  const enneaType = lensData.enneagram.core_type;
  
  if (hdType === 'Manifestor') {
    if (enneaType === 7) return "When they suddenly go quiet after proposing something big.";
    if (enneaType === 8) return "When their energy shifts from driving to withdrawing mid-conversation.";
    return "When they stop initiating and start waiting for others to catch up.";
  } else if (hdType === 'Generator') {
    if (enneaType === 9) return "When they agree too easily—without that spark of real engagement.";
    return "When their energy drops mid-task, but they keep pushing anyway.";
  } else if (hdType === 'Manifesting Generator') {
    if (enneaType === 3) return "When they speed past a concern someone else raised—watch if it resurfaces.";
    return "When they suddenly pivot away from something they seemed committed to.";
  } else if (hdType === 'Projector') {
    if (enneaType === 4) return "When they offer insight and no one responds—the silence lands hard.";
    return "When they start over-explaining or advising without being asked.";
  } else if (hdType === 'Reflector') {
    return "When their mood shifts suddenly—something in the group just changed.";
  }
  
  if (authority?.includes('Emotional')) {
    return "When they commit quickly under pressure—check back in a day or two.";
  }
  
  return "When their pattern shifts—pause and ask what's happening.";
};

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
  
  // Member profile state
  const [showPatternSignals, setShowPatternSignals] = useState(false);

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
    // Navigate to the Forum Updates page with forum context
    // This is the new structured update experience
    router.push(`/forums/updates?forumId=${forumId}&forumName=${encodeURIComponent(forum?.name || 'Forum')}`);
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
            HOW THEY MAP TO ME - Channel-completion based mappings
            ============================================ */}
        <TouchableOpacity
          style={[styles.forumDynamicsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
          onPress={() => router.push({ pathname: '/forums/mappings', params: { forumId, forumName: forum?.name } })}
          activeOpacity={0.7}
        >
          <View style={styles.forumDynamicsContent}>
            <View style={[styles.forumDynamicsIcon, { backgroundColor: theme.accent + '15' }]}>
              <Text style={{ fontSize: 20 }}>🔗</Text>
            </View>
            <View style={styles.forumDynamicsTextContainer}>
              <Text style={[styles.forumDynamicsTitle, { color: theme.text }]}>How they map to me</Text>
              <Text style={[styles.forumDynamicsSubtitle, { color: theme.textSecondary }]}>
                See how each member energetically connects with you
              </Text>
            </View>
          </View>
          <TouchableOpacity
            style={[styles.forumDynamicsButton, { backgroundColor: theme.accent + '15' }]}
            onPress={() => router.push({ pathname: '/forums/mappings', params: { forumId, forumName: forum?.name } })}
          >
            <Text style={[styles.forumDynamicsButtonText, { color: theme.accent }]}>View</Text>
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
                {hasSubmitted ? 'Edit Update' : 'Share Forum Update'}
              </Text>
            </TouchableOpacity>
            
            {hasSubmitted && (
              <Text style={[styles.submittedNote, { color: theme.success }]}>
                ✓ You&apos;ve shared an update
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
      
      {/* Member Lens Profile Modal - REDESIGNED for human understanding */}
      <Modal
        visible={memberModal.visible}
        transparent
        animationType="fade"
        onRequestClose={closeAllModals}
      >
        <Pressable style={styles.modalOverlay} onPress={closeAllModals}>
          <Pressable style={[styles.modalContent, styles.modalLarge, { backgroundColor: theme.surface }]} onPress={() => {}}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.text }]}></Text>
              <TouchableOpacity onPress={closeAllModals} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                <Text style={[styles.modalClose, { color: theme.textTertiary }]}>✕</Text>
              </TouchableOpacity>
            </View>
            
            {memberModal.member && (
              <ScrollView style={styles.modalScrollContent} showsVerticalScrollIndicator={false}>
                {/* 1. HEADER - Name + Archetype */}
                <View style={styles.humanProfileHeader}>
                  <View style={[styles.humanProfileAvatar, { backgroundColor: theme.accent + '15' }]}>
                    <Text style={[styles.humanProfileInitial, { color: theme.accent }]}>
                      {memberModal.member.name.charAt(0).toUpperCase()}
                    </Text>
                  </View>
                  <Text style={[styles.humanProfileName, { color: theme.text }]}>
                    {memberModal.member.name}
                  </Text>
                  {memberModal.lensData && (
                    <Text style={[styles.humanProfileArchetype, { color: theme.textSecondary }]}>
                      {getArchetypeLabel(memberModal.lensData)}
                    </Text>
                  )}
                </View>
                
                {memberModal.loading ? (
                  <View style={styles.lensLoadingContainer}>
                    <ActivityIndicator size="small" color={theme.accent} />
                    <Text style={[styles.lensLoadingText, { color: theme.textTertiary }]}>Understanding this person...</Text>
                  </View>
                ) : memberModal.lensData ? (
                  <View style={styles.humanProfileContent}>
                    
                    {/* 2. WHAT IT FEELS LIKE TO BE WITH THEM - NEW TOP PRIORITY */}
                    <View style={[styles.humanSectionFelt, { backgroundColor: theme.accent + '06', borderColor: theme.accent + '20' }]}>
                      <Text style={[styles.humanSectionTitleFelt, { color: theme.accent }]}>What it feels like to be with them</Text>
                      <Text style={[styles.humanSectionTextFelt, { color: theme.text }]}>
                        {getWhatItFeelsLike(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 3. HOW THEY SHOW UP - Shortened */}
                    <View style={[styles.humanSection, { backgroundColor: theme.background, borderColor: theme.border }]}>
                      <Text style={[styles.humanSectionTitle, { color: theme.text }]}>How they show up</Text>
                      <Text style={[styles.humanSectionText, { color: theme.textSecondary }]}>
                        {getHowTheyShowUp(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 4. WHEN THEY'RE AT THEIR BEST */}
                    <View style={[styles.humanSection, { backgroundColor: theme.background, borderColor: theme.border }]}>
                      <Text style={[styles.humanSectionTitle, { color: theme.text }]}>When they're at their best</Text>
                      <Text style={[styles.humanSectionText, { color: theme.textSecondary }]}>
                        {getAtTheirBest(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 5. WHEN THINGS GET TENSE - Renamed, situational */}
                    <View style={[styles.humanSection, { backgroundColor: theme.background, borderColor: theme.border }]}>
                      <Text style={[styles.humanSectionTitle, { color: theme.text }]}>When things get tense</Text>
                      <Text style={[styles.humanSectionText, { color: theme.textSecondary }]}>
                        {getWhenThingsGetTense(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 6. WHERE MISUNDERSTANDINGS HAPPEN - NEW CRITICAL */}
                    <View style={[styles.humanSectionWarning, { backgroundColor: '#FF572208', borderColor: '#FF572225' }]}>
                      <Text style={[styles.humanSectionTitleWarning, { color: '#FF5722' }]}>⚠️ Where misunderstandings happen</Text>
                      <Text style={[styles.humanSectionText, { color: theme.text }]}>
                        {getWhereMisunderstandingsHappen(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 7. HOW TO WORK WITH THEM - Sharpened */}
                    <View style={[styles.humanSectionHighlight, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '25' }]}>
                      <Text style={[styles.humanSectionTitleHighlight, { color: theme.accent }]}>How to work with them</Text>
                      <Text style={[styles.humanSectionTextLines, { color: theme.text }]}>
                        {getHowToWorkWith(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 8. MICRO-TRIGGER - NEW Real-time awareness */}
                    <View style={[styles.microTriggerBox, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                      <Text style={[styles.microTriggerLabel, { color: theme.textTertiary }]}>👁 Watch for this moment:</Text>
                      <Text style={[styles.microTriggerText, { color: theme.text }]}>
                        {getMicroTrigger(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 9. PATTERN SIGNALS - Collapsible */}
                    <TouchableOpacity 
                      style={[styles.patternSignalsToggle, { borderColor: theme.border }]}
                      onPress={() => setShowPatternSignals(!showPatternSignals)}
                      activeOpacity={0.7}
                    >
                      <Text style={[styles.patternSignalsToggleText, { color: theme.textTertiary }]}>
                        Underlying patterns (optional)
                      </Text>
                      <Text style={[styles.patternSignalsChevron, { color: theme.textTertiary }]}>
                        {showPatternSignals ? '▼' : '▶'}
                      </Text>
                    </TouchableOpacity>
                    
                    {showPatternSignals && (
                      <View style={[styles.patternSignalsContent, { backgroundColor: theme.background }]}>
                        <View style={styles.patternSignalsTags}>
                          {memberModal.lensData.human_design.type && (
                            <View style={[styles.patternTag, { backgroundColor: theme.border }]}>
                              <Text style={[styles.patternTagText, { color: theme.textSecondary }]}>
                                {memberModal.lensData.human_design.type}
                              </Text>
                            </View>
                          )}
                          {memberModal.lensData.human_design.authority && (
                            <View style={[styles.patternTag, { backgroundColor: theme.border }]}>
                              <Text style={[styles.patternTagText, { color: theme.textSecondary }]}>
                                {memberModal.lensData.human_design.authority} Authority
                              </Text>
                            </View>
                          )}
                          {memberModal.lensData.enneagram.core_type && (
                            <View style={[styles.patternTag, { backgroundColor: theme.border }]}>
                              <Text style={[styles.patternTagText, { color: theme.textSecondary }]}>
                                Type {memberModal.lensData.enneagram.core_type}
                                {memberModal.lensData.enneagram.wing ? `w${memberModal.lensData.enneagram.wing}` : ''}
                              </Text>
                            </View>
                          )}
                          {memberModal.lensData.astrology.dominant_element && (
                            <View style={[styles.patternTag, { backgroundColor: theme.border }]}>
                              <Text style={[styles.patternTagText, { color: theme.textSecondary }]}>
                                {memberModal.lensData.astrology.dominant_element} dominant
                              </Text>
                            </View>
                          )}
                          {memberModal.lensData.human_design.profile && (
                            <View style={[styles.patternTag, { backgroundColor: theme.border }]}>
                              <Text style={[styles.patternTagText, { color: theme.textSecondary }]}>
                                {memberModal.lensData.human_design.profile} Profile
                              </Text>
                            </View>
                          )}
                        </View>
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
                        Ask Mirror About {memberModal.member.name}
                      </Text>
                    </TouchableOpacity>
                  </View>
                ) : (
                  // Fallback when no lens data
                  <View style={styles.humanProfileContent}>
                    <View style={[styles.humanSection, { backgroundColor: theme.background, borderColor: theme.border }]}>
                      <Text style={[styles.humanSectionText, { color: theme.textSecondary }]}>
                        Lens data not available for this member yet.
                      </Text>
                    </View>
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
  
  // =============================================================================
  // HUMAN UNDERSTANDING MEMBER PROFILE STYLES
  // =============================================================================
  humanProfileHeader: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  humanProfileAvatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  humanProfileInitial: {
    fontSize: 28,
    fontWeight: '600',
  },
  humanProfileName: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 4,
  },
  humanProfileArchetype: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  humanProfileContent: {
    paddingTop: 8,
  },
  
  // NEW: "What it feels like" - Top priority felt section
  humanSectionFelt: {
    borderRadius: 14,
    padding: 18,
    marginBottom: 14,
    borderWidth: 1,
  },
  humanSectionTitleFelt: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 12,
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
  humanSectionTextFelt: {
    fontSize: 16,
    lineHeight: 26,
    fontStyle: 'italic',
  },
  
  humanSection: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
  },
  humanSectionHighlight: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
  },
  humanSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 10,
    letterSpacing: 0.3,
  },
  humanSectionTitleHighlight: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 10,
    letterSpacing: 0.3,
  },
  humanSectionText: {
    fontSize: 15,
    lineHeight: 23,
  },
  patternSignalsToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 4,
    borderTopWidth: StyleSheet.hairlineWidth,
    marginTop: 8,
  },
  patternSignalsToggleText: {
    fontSize: 13,
  },
  patternSignalsChevron: {
    fontSize: 12,
  },
  patternSignalsContent: {
    paddingVertical: 12,
    paddingHorizontal: 4,
  },
  patternSignalsTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  
  // NEW: Warning section (Where misunderstandings happen)
  humanSectionWarning: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
  },
  humanSectionTitleWarning: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 10,
    letterSpacing: 0.3,
  },
  
  // NEW: Text with line breaks for "How to work with them"
  humanSectionTextLines: {
    fontSize: 15,
    lineHeight: 24,
  },
  
  // NEW: Micro-trigger box
  microTriggerBox: {
    borderRadius: 10,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderStyle: 'dashed',
  },
  microTriggerLabel: {
    fontSize: 12,
    fontWeight: '500',
    marginBottom: 6,
  },
  microTriggerText: {
    fontSize: 14,
    lineHeight: 21,
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
