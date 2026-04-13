import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Modal,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { 
  getForumMemberMappings, 
  ForumMemberMapping,
  ChannelCompletion,
} from '../../services/api';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function ForumMappingsScreen() {
  const { theme, isDark } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const { forumId, forumName } = useLocalSearchParams();

  const [mappings, setMappings] = useState<ForumMemberMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMember, setSelectedMember] = useState<ForumMemberMapping | null>(null);
  const [showWhyExpanded, setShowWhyExpanded] = useState(false);

  useEffect(() => {
    if (user?.id && forumId) {
      fetchMappings();
    }
  }, [user?.id, forumId]);

  const fetchMappings = async () => {
    if (!user?.id || !forumId) return;

    setLoading(true);
    setError(null);
    
    try {
      const response = await getForumMemberMappings(forumId as string, user.id);
      if (response.success) {
        setMappings(response.mappings);
      } else {
        setError(response.error || 'Failed to load mappings');
      }
    } catch (err) {
      console.error('[Mappings] Error:', err);
      setError('Unable to load member mappings');
    } finally {
      setLoading(false);
    }
  };

  const handleMemberPress = (mapping: ForumMemberMapping) => {
    setSelectedMember(mapping);
    setShowWhyExpanded(false);
  };

  const handleCloseModal = () => {
    setSelectedMember(null);
    setShowWhyExpanded(false);
  };

  // Render a single mapping row in the list
  const renderMappingRow = (mapping: ForumMemberMapping) => (
    <TouchableOpacity
      key={mapping.member_id}
      style={[styles.mappingRow, { backgroundColor: theme.surface, borderColor: theme.border }]}
      onPress={() => handleMemberPress(mapping)}
      activeOpacity={0.7}
    >
      <View style={styles.mappingContent}>
        {/* Member Name */}
        <Text style={[styles.memberName, { color: theme.text }]}>
          {mapping.member_name}
        </Text>
        
        {/* Headline - scannable in under 10 seconds */}
        <Text style={[styles.headline, { color: theme.textSecondary }]}>
          {mapping.headline}
        </Text>
        
        {/* Watch-out line - short, actionable */}
        <Text style={[styles.watchOut, { color: theme.textTertiary }]}>
          {mapping.what_to_watch.split('.')[0]}
        </Text>
      </View>
      
      <Ionicons name="chevron-forward" size={20} color={theme.textTertiary} />
    </TouchableOpacity>
  );

  // Render the detail modal - V2 3-Layer Architecture
  const renderDetailModal = () => {
    if (!selectedMember) return null;

    // Read from 3-layer structure with backward compat fallbacks
    const story = (selectedMember as any).story || { headline: selectedMember.headline, summary: selectedMember.description };
    const patterns = (selectedMember as any).patterns || null;
    const signals = (selectedMember as any).signals || null;
    const hdSignals = signals?.human_design || selectedMember.why_this_happens || [];

    return (
      <Modal
        visible={!!selectedMember}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={handleCloseModal}
      >
        <SafeAreaView style={[styles.modalContainer, { backgroundColor: theme.background }]}>
          {/* Header */}
          <View style={[styles.modalHeader, { borderBottomColor: theme.border }]}>
            <TouchableOpacity onPress={handleCloseModal} style={styles.closeButton}>
              <Ionicons name="close" size={24} color={theme.text} />
            </TouchableOpacity>
            <View style={styles.modalTitleContainer}>
              <Text style={[styles.modalTitle, { color: theme.text }]}>
                {selectedMember.member_name}
              </Text>
              <Text style={[styles.modalSubtitle, { color: theme.textSecondary }]}>
                How they map to you
              </Text>
            </View>
            <View style={{ width: 40 }} />
          </View>

          <ScrollView 
            style={styles.modalScroll}
            contentContainerStyle={styles.modalContent}
            showsVerticalScrollIndicator={false}
          >
            {/* ================================================ */}
            {/* LAYER 1: STORY                                   */}
            {/* Emotional hook — feels like "this is us"         */}
            {/* ================================================ */}
            <View style={[styles.storyCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.storyHeadline, { color: theme.text }]}>
                {story.headline}
              </Text>
              <Text style={[styles.storySummary, { color: theme.textSecondary }]}>
                {story.summary}
              </Text>
            </View>

            {/* ================================================ */}
            {/* LAYER 2: PATTERNS                                */}
            {/* Behavioral — "this is EXACTLY what happens"      */}
            {/* ================================================ */}
            
            {/* What Happens Between You */}
            {patterns?.what_happens && patterns.what_happens.length > 0 && (
              <View style={styles.patternSection}>
                <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>
                  WHAT HAPPENS BETWEEN YOU
                </Text>
                {patterns.what_happens.map((item: string, i: number) => (
                  <View key={`wh-${i}`} style={styles.patternBulletRow}>
                    <Text style={[styles.patternBulletDash, { color: theme.textTertiary }]}>›</Text>
                    <Text style={[styles.patternBulletText, { color: theme.textSecondary }]}>
                      {item}
                    </Text>
                  </View>
                ))}
              </View>
            )}

            {/* Where Friction Shows Up */}
            {patterns?.tensions && patterns.tensions.length > 0 && (
              <View style={styles.patternSection}>
                <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>
                  WHERE FRICTION SHOWS UP
                </Text>
                {patterns.tensions.map((item: string, i: number) => (
                  <View key={`fr-${i}`} style={styles.patternBulletRow}>
                    <Text style={[styles.patternBulletDash, { color: theme.textTertiary }]}>⚡</Text>
                    <Text style={[styles.patternBulletText, { color: theme.textSecondary }]}>
                      {item}
                    </Text>
                  </View>
                ))}
              </View>
            )}

            {/* What You Give Each Other */}
            {patterns?.gifts && patterns.gifts.length > 0 && (
              <View style={[styles.giftSection, { borderLeftColor: (theme.accent || '#8B5CF6') + '50' }]}>
                <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>
                  WHAT YOU GIVE EACH OTHER
                </Text>
                {patterns.gifts.map((item: string, i: number) => (
                  <View key={`gf-${i}`} style={styles.patternBulletRow}>
                    <Text style={[styles.patternBulletDash, { color: theme.textTertiary }]}>✦</Text>
                    <Text style={[styles.patternBulletText, { color: theme.textSecondary }]}>
                      {item}
                    </Text>
                  </View>
                ))}
              </View>
            )}

            {/* ================================================ */}
            {/* LAYER 3: SIGNALS (Collapsible proof layer)       */}
            {/* "Why this is so strong" — HD channels + future   */}
            {/* ================================================ */}
            {hdSignals.length > 0 && (
              <View style={styles.signalsSection}>
                <TouchableOpacity
                  style={[styles.signalsToggle, { borderColor: theme.border }]}
                  onPress={() => setShowWhyExpanded(!showWhyExpanded)}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.signalsToggleText, { color: theme.textSecondary }]}>
                    {showWhyExpanded ? 'Hide what drives this' : 'Why this is so strong'}
                  </Text>
                  <Ionicons
                    name={showWhyExpanded ? "chevron-up" : "chevron-down"}
                    size={16}
                    color={theme.textTertiary}
                  />
                </TouchableOpacity>

                {showWhyExpanded && (
                  <View style={styles.whyContent}>
                    <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                      DESIGN CONNECTIONS
                    </Text>
                    {hdSignals.map((channel: any, index: number) => (
                      <View 
                        key={channel.channel} 
                        style={[
                          styles.channelCard, 
                          { backgroundColor: theme.surface, borderColor: theme.border }
                        ]}
                      >
                        {/* Translation line — plain language */}
                        {channel.translation && (
                          <Text style={[styles.channelTranslation, { color: theme.text }]}>
                            {channel.translation}
                          </Text>
                        )}
                        <View style={styles.channelGates}>
                          <View style={[styles.gateBox, { borderColor: theme.border }]}>
                            <Text style={[styles.gateLabel, { color: theme.textTertiary }]}>You</Text>
                            <Text style={[styles.gateNumber, { color: theme.text }]}>
                              Gate {channel.your_gate}
                            </Text>
                          </View>
                          <View style={styles.channelConnector}>
                            <View style={[styles.connectorLine, { backgroundColor: theme.border }]} />
                            <Text style={[styles.channelId, { color: theme.textSecondary }]}>
                              {channel.channel}
                            </Text>
                            <View style={[styles.connectorLine, { backgroundColor: theme.border }]} />
                          </View>
                          <View style={[styles.gateBox, { borderColor: theme.border }]}>
                            <Text style={[styles.gateLabel, { color: theme.textTertiary }]}>They</Text>
                            <Text style={[styles.gateNumber, { color: theme.text }]}>
                              Gate {channel.their_gate}
                            </Text>
                          </View>
                        </View>
                        <View style={styles.channelInfo}>
                          <Text style={[styles.channelName, { color: theme.text }]}>
                            Channel of {channel.name}
                          </Text>
                          <Text style={[styles.channelTheme, { color: theme.textSecondary }]}>
                            {channel.theme}
                          </Text>
                        </View>
                      </View>
                    ))}

                    {/* ASTROLOGY SIGNALS */}
                    {signals?.astrology && (
                      (signals.astrology.attraction?.length > 0 || signals.astrology.tension?.length > 0 || signals.astrology.growth?.length > 0) && (
                        <View style={styles.lensSection}>
                          <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                            ASTROLOGICAL DYNAMICS
                          </Text>
                          {signals.astrology.attraction?.map((item: string, i: number) => (
                            <View key={`aa-${i}`} style={styles.lensSignalRow}>
                              <Text style={[styles.lensSignalIcon, { color: '#D4A574' }]}>✦</Text>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                            </View>
                          ))}
                          {signals.astrology.tension?.map((item: string, i: number) => (
                            <View key={`at-${i}`} style={styles.lensSignalRow}>
                              <Text style={[styles.lensSignalIcon, { color: '#CF6679' }]}>⚡</Text>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                            </View>
                          ))}
                          {signals.astrology.growth?.map((item: string, i: number) => (
                            <View key={`ag-${i}`} style={styles.lensSignalRow}>
                              <Text style={[styles.lensSignalIcon, { color: '#81C784' }]}>↑</Text>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                            </View>
                          ))}
                        </View>
                      )
                    )}

                    {/* ENNEAGRAM SIGNALS */}
                    {signals?.enneagram && (
                      (signals.enneagram.how_you_help_them?.length > 0 || signals.enneagram.how_they_help_you?.length > 0) && (
                        <View style={styles.lensSection}>
                          <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                            GROWTH GIFTS
                          </Text>
                          {signals.enneagram.how_you_help_them?.map((item: string, i: number) => (
                            <View key={`eyt-${i}`} style={styles.lensSignalRow}>
                              <Text style={[styles.lensSignalIcon, { color: '#CE93D8' }]}>→</Text>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                            </View>
                          ))}
                          {signals.enneagram.how_they_help_you?.map((item: string, i: number) => (
                            <View key={`ety-${i}`} style={styles.lensSignalRow}>
                              <Text style={[styles.lensSignalIcon, { color: '#CE93D8' }]}>←</Text>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                            </View>
                          ))}
                          {signals.enneagram.friction_pattern?.map((item: string, i: number) => (
                            <View key={`efp-${i}`} style={styles.lensSignalRow}>
                              <Text style={[styles.lensSignalIcon, { color: '#CF6679' }]}>⚡</Text>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                            </View>
                          ))}
                        </View>
                      )
                    )}

                    {/* NUMEROLOGY SIGNALS (only if present) */}
                    {signals?.numerology && signals.numerology.themes?.length > 0 && (
                      <View style={styles.lensSection}>
                        <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                          NUMBER RESONANCE
                        </Text>
                        {signals.numerology.themes.map((item: string, i: number) => (
                          <View key={`nt-${i}`} style={styles.lensSignalRow}>
                            <Text style={[styles.lensSignalIcon, { color: '#90CAF9' }]}>◇</Text>
                            <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                          </View>
                        ))}
                      </View>
                    )}

                    {/* BAZI SIGNALS (only if present) */}
                    {signals?.bazi && (
                      (signals.bazi.support?.length > 0 || signals.bazi.tension?.length > 0) && (
                        <View style={styles.lensSection}>
                          <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                            ELEMENTAL DYNAMICS
                          </Text>
                          {signals.bazi.support?.map((item: string, i: number) => (
                            <View key={`bs-${i}`} style={styles.lensSignalRow}>
                              <Text style={[styles.lensSignalIcon, { color: '#81C784' }]}>+</Text>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                            </View>
                          ))}
                          {signals.bazi.tension?.map((item: string, i: number) => (
                            <View key={`bt-${i}`} style={styles.lensSignalRow}>
                              <Text style={[styles.lensSignalIcon, { color: '#CF6679' }]}>−</Text>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                            </View>
                          ))}
                          {signals.bazi.growth?.map((item: string, i: number) => (
                            <View key={`bg-${i}`} style={styles.lensSignalRow}>
                              <Text style={[styles.lensSignalIcon, { color: '#90CAF9' }]}>↑</Text>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                            </View>
                          ))}
                        </View>
                      )
                    )}
                  </View>
                )}
              </View>
            )}

            {/* Spacer for bottom */}
            <View style={{ height: 40 }} />
          </ScrollView>
        </SafeAreaView>
      </Modal>
    );
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: theme.border }]}>
        <TouchableOpacity 
          onPress={() => router.back()} 
          style={styles.backButton}
        >
          <Ionicons name="arrow-back" size={24} color={theme.text} />
        </TouchableOpacity>
        <View style={styles.headerTitleContainer}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            How they map to me
          </Text>
          {forumName && (
            <Text style={[styles.headerSubtitle, { color: theme.textTertiary }]}>
              {forumName}
            </Text>
          )}
        </View>
        <View style={{ width: 40 }} />
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={theme.textSecondary} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Computing connections...
          </Text>
        </View>
      ) : error ? (
        <View style={styles.centered}>
          <Ionicons name="alert-circle-outline" size={48} color={theme.textTertiary} />
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
          <TouchableOpacity 
            style={[styles.retryButton, { borderColor: theme.border }]}
            onPress={fetchMappings}
          >
            <Text style={[styles.retryText, { color: theme.text }]}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : mappings.length === 0 ? (
        <View style={styles.centered}>
          <Ionicons name="people-outline" size={48} color={theme.textTertiary} />
          <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
            No forum members to map
          </Text>
        </View>
      ) : (
        <ScrollView 
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Intro text */}
          <Text style={[styles.introText, { color: theme.textTertiary }]}>
            How each person in your forum energetically connects with you
          </Text>

          {/* Mappings list */}
          {mappings.map(renderMappingRow)}

          {/* Footer spacer */}
          <View style={{ height: 100 }} />
        </ScrollView>
      )}

      {/* Detail Modal */}
      {renderDetailModal()}
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
    borderBottomWidth: 1,
  },
  backButton: {
    padding: 8,
    marginRight: 8,
  },
  headerTitleContainer: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  headerSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
  },
  errorText: {
    marginTop: 12,
    fontSize: 14,
    textAlign: 'center',
  },
  emptyText: {
    marginTop: 12,
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
    paddingVertical: 10,
    paddingHorizontal: 24,
    borderRadius: 20,
    borderWidth: 1,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  introText: {
    fontSize: 13,
    fontStyle: 'italic',
    marginBottom: 16,
    lineHeight: 18,
  },
  mappingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
    borderWidth: 1,
  },
  mappingContent: {
    flex: 1,
    marginRight: 12,
  },
  memberName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  headline: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 4,
  },
  watchOut: {
    fontSize: 12,
    fontStyle: 'italic',
  },
  // Modal styles
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  closeButton: {
    padding: 8,
  },
  modalTitleContainer: {
    flex: 1,
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  modalSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  modalScroll: {
    flex: 1,
  },
  modalContent: {
    padding: 20,
  },
  section: {
    marginBottom: 24,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
    lineHeight: 24,
  },
  sectionText: {
    fontSize: 15,
    lineHeight: 22,
  },
  // V2 3-Layer Styles
  storyCard: {
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    marginBottom: 24,
  },
  storyHeadline: {
    fontSize: 20,
    fontWeight: '600',
    lineHeight: 28,
    marginBottom: 12,
  },
  storySummary: {
    fontSize: 15,
    lineHeight: 23,
  },
  patternSection: {
    marginBottom: 20,
  },
  patternLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 12,
  },
  patternBulletRow: {
    flexDirection: 'row',
    marginBottom: 10,
    paddingRight: 8,
  },
  patternBulletDash: {
    fontSize: 14,
    marginRight: 10,
    marginTop: 1,
    width: 16,
    textAlign: 'center',
  },
  patternBulletText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 21,
  },
  giftSection: {
    paddingLeft: 14,
    borderLeftWidth: 3,
    marginBottom: 20,
  },
  signalsSection: {
    marginTop: 8,
  },
  signalsToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 12,
  },
  signalsToggleText: {
    fontSize: 14,
    fontWeight: '500',
  },
  signalsNote: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  expandableHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  whyContent: {
    marginTop: 16,
  },
  channelCard: {
    padding: 16,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 12,
  },
  channelGates: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  gateBox: {
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    minWidth: 80,
  },
  gateLabel: {
    fontSize: 10,
    fontWeight: '500',
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  gateNumber: {
    fontSize: 14,
    fontWeight: '600',
  },
  channelConnector: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  connectorLine: {
    height: 1,
    width: 12,
  },
  channelId: {
    fontSize: 11,
    fontWeight: '600',
    marginHorizontal: 4,
  },
  channelInfo: {
    alignItems: 'center',
  },
  channelTranslation: {
    fontSize: 14,
    fontWeight: '500',
    lineHeight: 20,
    marginBottom: 12,
    fontStyle: 'italic',
  },
  lensSection: {
    marginTop: 20,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(128,128,128,0.15)',
  },
  lensSignalRow: {
    flexDirection: 'row',
    marginBottom: 10,
    paddingRight: 8,
  },
  lensSignalIcon: {
    fontSize: 13,
    marginRight: 10,
    marginTop: 2,
    width: 16,
    textAlign: 'center',
  },
  lensSignalText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
  },
  channelName: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  channelTheme: {
    fontSize: 13,
    fontStyle: 'italic',
    textAlign: 'center',
    lineHeight: 18,
  },
});
