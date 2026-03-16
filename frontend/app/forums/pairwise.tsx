import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { 
  getForumPulse, 
  ForumPulseMemberCard,
  getPairwiseDynamics,
  PairwiseDynamicsResponse 
} from '../../services/api';

// Helper to parse the pairwise reflection into sections
interface ParsedReflection {
  complement: string | null;
  tension: string | null;
  insight: string | null;
  question: string | null;
}

function parseReflection(text: string): ParsedReflection {
  const result: ParsedReflection = {
    complement: null,
    tension: null,
    insight: null,
    question: null
  };

  // Extract question
  const questionMatch = text.match(/\[QUESTION\]\s*([\s\S]*?)$/);
  if (questionMatch) {
    result.question = questionMatch[1].trim();
    text = text.replace(/\[QUESTION\][\s\S]*$/, '');
  }

  // Extract sections
  const complementMatch = text.match(/\[COMPLEMENT\]\s*([\s\S]*?)(?=\[TENSION\]|$)/);
  if (complementMatch) {
    result.complement = complementMatch[1].trim();
  }

  const tensionMatch = text.match(/\[TENSION\]\s*([\s\S]*?)(?=\[INSIGHT\]|$)/);
  if (tensionMatch) {
    result.tension = tensionMatch[1].trim();
  }

  const insightMatch = text.match(/\[INSIGHT\]\s*([\s\S]*?)(?=\[QUESTION\]|$)/);
  if (insightMatch) {
    result.insight = insightMatch[1].trim();
  }

  // If no sections found, use the whole text as complement
  if (!result.complement && !result.tension && !result.insight) {
    result.complement = text.trim();
  }

  return result;
}

export default function PairwiseDynamicsScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const { forumId } = useLocalSearchParams();

  const [members, setMembers] = useState<ForumPulseMemberCard[]>([]);
  const [memberA, setMemberA] = useState<ForumPulseMemberCard | null>(null);
  const [memberB, setMemberB] = useState<ForumPulseMemberCard | null>(null);
  const [showMemberAPicker, setShowMemberAPicker] = useState(false);
  const [showMemberBPicker, setShowMemberBPicker] = useState(false);
  const [reflection, setReflection] = useState<PairwiseDynamicsResponse | null>(null);
  const [parsedReflection, setParsedReflection] = useState<ParsedReflection | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMembers, setLoadingMembers] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.id && forumId) {
      fetchMembers();
    }
  }, [user?.id, forumId]);

  const fetchMembers = async () => {
    if (!user?.id || !forumId) return;

    setLoadingMembers(true);
    try {
      const response = await getForumPulse(forumId as string, user.id);
      setMembers(response.member_cards || []);
    } catch (err) {
      console.error('[Pairwise] Error loading members:', err);
    } finally {
      setLoadingMembers(false);
    }
  };

  const handleBack = () => {
    router.back();
  };

  const handleSelectMemberA = (member: ForumPulseMemberCard) => {
    setMemberA(member);
    setShowMemberAPicker(false);
    // Clear existing reflection when selection changes
    setReflection(null);
    setParsedReflection(null);
  };

  const handleSelectMemberB = (member: ForumPulseMemberCard) => {
    setMemberB(member);
    setShowMemberBPicker(false);
    // Clear existing reflection when selection changes
    setReflection(null);
    setParsedReflection(null);
  };

  const handleExplore = async () => {
    if (!user?.id || !forumId || !memberA || !memberB) return;

    setLoading(true);
    setError(null);

    try {
      const response = await getPairwiseDynamics(
        forumId as string,
        user.id,
        memberA.user_id,
        memberB.user_id
      );
      setReflection(response);
      setParsedReflection(parseReflection(response.reflection));
    } catch (err: any) {
      console.error('[Pairwise] Error:', err);
      setError('Unable to generate the reflection. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Filter members for each picker
  const membersForA = members;
  const membersForB = members.filter(m => m.user_id !== memberA?.user_id);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: theme.border }]}>
        <TouchableOpacity onPress={handleBack} style={styles.backButton}>
          <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.content} 
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Title */}
        <View style={styles.titleSection}>
          <Text style={[styles.title, { color: theme.text }]}>Member Dynamics</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Explore how two members' profiles may interact or complement each other
          </Text>
        </View>

        {loadingMembers ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color={theme.accent} />
            <Text style={[styles.loadingText, { color: theme.textTertiary }]}>Loading members...</Text>
          </View>
        ) : members.length < 2 ? (
          <View style={styles.emptyContainer}>
            <Text style={[styles.emptyText, { color: theme.textTertiary }]}>
              This feature requires at least 2 members in the forum.
            </Text>
          </View>
        ) : (
          <>
            {/* Member Selection */}
            <View style={styles.selectionContainer}>
              {/* Member A Picker */}
              <View style={styles.pickerContainer}>
                <Text style={[styles.pickerLabel, { color: theme.textTertiary }]}>MEMBER A</Text>
                <TouchableOpacity
                  style={[styles.pickerButton, { backgroundColor: theme.surface, borderColor: theme.border }]}
                  onPress={() => setShowMemberAPicker(true)}
                >
                  <Text style={[styles.pickerText, { color: memberA ? theme.text : theme.textTertiary }]}>
                    {memberA ? memberA.name : 'Select member...'}
                  </Text>
                  <Ionicons name="chevron-down" size={18} color={theme.textTertiary} />
                </TouchableOpacity>
              </View>

              {/* Connection Symbol */}
              <View style={styles.connectionSymbol}>
                <Text style={[styles.connectionText, { color: theme.accent }]}>↔</Text>
              </View>

              {/* Member B Picker */}
              <View style={styles.pickerContainer}>
                <Text style={[styles.pickerLabel, { color: theme.textTertiary }]}>MEMBER B</Text>
                <TouchableOpacity
                  style={[
                    styles.pickerButton, 
                    { backgroundColor: theme.surface, borderColor: theme.border },
                    !memberA && styles.pickerDisabled
                  ]}
                  onPress={() => memberA && setShowMemberBPicker(true)}
                  disabled={!memberA}
                >
                  <Text style={[styles.pickerText, { color: memberB ? theme.text : theme.textTertiary }]}>
                    {memberB ? memberB.name : 'Select member...'}
                  </Text>
                  <Ionicons name="chevron-down" size={18} color={theme.textTertiary} />
                </TouchableOpacity>
              </View>
            </View>

            {/* Explore Button */}
            <TouchableOpacity
              style={[
                styles.exploreButton,
                { backgroundColor: memberA && memberB ? theme.accent : theme.border }
              ]}
              onPress={handleExplore}
              disabled={!memberA || !memberB || loading}
            >
              {loading ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Text style={[styles.exploreButtonText, { color: '#fff' }]}>
                  Explore Dynamics
                </Text>
              )}
            </TouchableOpacity>

            {/* Error */}
            {error && (
              <View style={[styles.errorContainer, { backgroundColor: theme.error + '15' }]}>
                <Text style={[styles.errorText, { color: theme.error }]}>{error}</Text>
              </View>
            )}

            {/* Reflection Result */}
            {reflection && parsedReflection && (
              <View style={styles.reflectionContainer}>
                {/* Header */}
                <View style={[styles.reflectionHeader, { backgroundColor: theme.accent + '10' }]}>
                  <Text style={[styles.reflectionHeaderText, { color: theme.text }]}>
                    {reflection.member_a.name} ↔ {reflection.member_b.name}
                  </Text>
                </View>

                {/* Complement Section */}
                {parsedReflection.complement && (
                  <View style={[styles.reflectionSection, { backgroundColor: theme.surface }]}>
                    <Text style={[styles.reflectionSectionTitle, { color: theme.text }]}>
                      How they may complement each other
                    </Text>
                    <Text style={[styles.reflectionText, { color: theme.text }]}>
                      {parsedReflection.complement}
                    </Text>
                  </View>
                )}

                {/* Tension Section */}
                {parsedReflection.tension && (
                  <View style={[styles.reflectionSection, { backgroundColor: theme.surface }]}>
                    <Text style={[styles.reflectionSectionTitle, { color: theme.text }]}>
                      Where tensions may arise
                    </Text>
                    <Text style={[styles.reflectionText, { color: theme.text }]}>
                      {parsedReflection.tension}
                    </Text>
                  </View>
                )}

                {/* Insight Section */}
                {parsedReflection.insight && (
                  <View style={[styles.reflectionSection, { backgroundColor: theme.surface }]}>
                    <Text style={[styles.reflectionSectionTitle, { color: theme.text }]}>
                      What they may help each other see
                    </Text>
                    <Text style={[styles.reflectionText, { color: theme.text }]}>
                      {parsedReflection.insight}
                    </Text>
                  </View>
                )}

                {/* Question */}
                {parsedReflection.question && (
                  <View style={[styles.questionSection, { backgroundColor: theme.accent + '10', borderColor: theme.accent + '30' }]}>
                    <Text style={[styles.questionLabel, { color: theme.accent }]}>
                      A question to explore together
                    </Text>
                    <Text style={[styles.questionText, { color: theme.text }]}>
                      {parsedReflection.question}
                    </Text>
                  </View>
                )}
              </View>
            )}

            {/* Member A Picker Dropdown */}
            {showMemberAPicker && (
              <View style={[styles.pickerDropdown, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                <ScrollView style={styles.pickerList}>
                  {membersForA.map((member) => (
                    <TouchableOpacity
                      key={member.user_id}
                      style={[styles.pickerItem, { borderBottomColor: theme.border }]}
                      onPress={() => handleSelectMemberA(member)}
                    >
                      <Text style={[styles.pickerItemName, { color: theme.text }]}>{member.name}</Text>
                      {member.hd_type && (
                        <Text style={[styles.pickerItemType, { color: theme.textTertiary }]}>
                          {member.hd_type}
                        </Text>
                      )}
                    </TouchableOpacity>
                  ))}
                </ScrollView>
                <TouchableOpacity
                  style={[styles.pickerClose, { borderTopColor: theme.border }]}
                  onPress={() => setShowMemberAPicker(false)}
                >
                  <Text style={[styles.pickerCloseText, { color: theme.textSecondary }]}>Cancel</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Member B Picker Dropdown */}
            {showMemberBPicker && (
              <View style={[styles.pickerDropdown, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                <ScrollView style={styles.pickerList}>
                  {membersForB.map((member) => (
                    <TouchableOpacity
                      key={member.user_id}
                      style={[styles.pickerItem, { borderBottomColor: theme.border }]}
                      onPress={() => handleSelectMemberB(member)}
                    >
                      <Text style={[styles.pickerItemName, { color: theme.text }]}>{member.name}</Text>
                      {member.hd_type && (
                        <Text style={[styles.pickerItemType, { color: theme.textTertiary }]}>
                          {member.hd_type}
                        </Text>
                      )}
                    </TouchableOpacity>
                  ))}
                </ScrollView>
                <TouchableOpacity
                  style={[styles.pickerClose, { borderTopColor: theme.border }]}
                  onPress={() => setShowMemberBPicker(false)}
                >
                  <Text style={[styles.pickerCloseText, { color: theme.textSecondary }]}>Cancel</Text>
                </TouchableOpacity>
              </View>
            )}
          </>
        )}

        {/* Footer note */}
        <View style={styles.footerNote}>
          <Text style={[styles.footerNoteText, { color: theme.textTertiary }]}>
            This reflection is meant to support curiosity, not diagnose relationships.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backButton: {
    paddingVertical: 4,
  },
  backText: {
    fontSize: 16,
    fontWeight: '500',
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  titleSection: {
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 40,
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  selectionContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 12,
    marginBottom: 20,
  },
  pickerContainer: {
    flex: 1,
  },
  pickerLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 8,
  },
  pickerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 10,
    borderWidth: 1,
  },
  pickerDisabled: {
    opacity: 0.5,
  },
  pickerText: {
    fontSize: 14,
    flex: 1,
  },
  connectionSymbol: {
    paddingBottom: 12,
  },
  connectionText: {
    fontSize: 20,
    fontWeight: '600',
  },
  exploreButton: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 20,
  },
  exploreButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  errorContainer: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  reflectionContainer: {
    gap: 12,
    marginBottom: 20,
  },
  reflectionHeader: {
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  reflectionHeaderText: {
    fontSize: 16,
    fontWeight: '600',
  },
  reflectionSection: {
    padding: 16,
    borderRadius: 12,
  },
  reflectionSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 10,
  },
  reflectionText: {
    fontSize: 15,
    lineHeight: 23,
  },
  questionSection: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  questionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  questionText: {
    fontSize: 15,
    lineHeight: 23,
    fontStyle: 'italic',
  },
  pickerDropdown: {
    position: 'absolute',
    top: 200,
    left: 20,
    right: 20,
    maxHeight: 300,
    borderRadius: 12,
    borderWidth: 1,
    zIndex: 100,
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
  },
  pickerList: {
    maxHeight: 220,
  },
  pickerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  pickerItemName: {
    fontSize: 15,
    fontWeight: '500',
  },
  pickerItemType: {
    fontSize: 12,
  },
  pickerClose: {
    alignItems: 'center',
    paddingVertical: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  pickerCloseText: {
    fontSize: 14,
    fontWeight: '500',
  },
  footerNote: {
    marginTop: 16,
    paddingHorizontal: 8,
  },
  footerNoteText: {
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
    fontStyle: 'italic',
  },
});
