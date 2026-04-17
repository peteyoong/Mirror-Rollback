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
  // Renders all 4 lenses natively (HD / Astrology / BaZi / Enneagram) so
  // forum dynamics are scannable without having to open the modal.
  const renderMappingRow = (mapping: ForumMemberMapping) => {
    // V2 3-layer structure with backward-compat fallbacks
    const story = (mapping as any).story || {
      headline: mapping.headline,
      summary: mapping.description,
    };
    const patterns = (mapping as any).patterns || null;
    const signals = (mapping as any).signals || {};

    const hdSignals: any[] = signals.human_design || mapping.why_this_happens || [];
    const astroSignals = signals.astrology || null;
    const baziSignals = signals.bazi || null;
    const enneagramSignals = signals.enneagram || null;

    // Prefer a signal-specific tension line over the generic what_to_watch
    const topTension: string | null =
      (patterns?.tensions && patterns.tensions[0]) ||
      (mapping.what_to_watch ? mapping.what_to_watch.split('.')[0] : null);
    const topGift: string | null =
      (patterns?.gifts && patterns.gifts[0]) ||
      (mapping.what_works ? mapping.what_works.split('.')[0] : null);

    // First astrology attraction (sidereal) line
    const astroAttraction: string | null =
      astroSignals?.attraction && astroSignals.attraction[0]
        ? astroSignals.attraction[0]
        : null;

    // BaZi animal-dynamic line — prefer the one that contains an emoji
    const baziLines: string[] = [
      ...(baziSignals?.support || []),
      ...(baziSignals?.growth || []),
      ...(baziSignals?.tension || []),
    ];
    const animalRegex = /[\u{1F400}-\u{1F43F}\u{1F981}-\u{1F984}\u{1FAE0}-\u{1FAFF}]/u;
    const baziAnimal: string | null =
      baziLines.find((s) => animalRegex.test(s)) || baziLines[0] || null;

    // Enneagram gift-exchange line — what this person gives / needs from you
    const enneagramGift: string | null =
      (enneagramSignals?.how_you_help_them && enneagramSignals.how_you_help_them[0]) ||
      (enneagramSignals?.how_they_help_you && enneagramSignals.how_they_help_you[0]) ||
      null;

    return (
      <TouchableOpacity
        key={mapping.member_id}
        style={[styles.mappingRow, { backgroundColor: theme.surface, borderColor: theme.border }]}
        onPress={() => handleMemberPress(mapping)}
        activeOpacity={0.7}
      >
        <View style={styles.mappingContent}>
          {/* Member Name + channel-count badge */}
          <View style={styles.memberHeaderRow}>
            <Text style={[styles.memberName, { color: theme.text }]}>
              {mapping.member_name}
            </Text>
            {hdSignals.length > 0 && (
              <View
                style={[
                  styles.channelBadge,
                  { backgroundColor: theme.surfaceLight || theme.border, borderColor: theme.border },
                ]}
              >
                <Text style={[styles.channelBadgeText, { color: theme.textSecondary }]}>
                  {hdSignals.length} channel{hdSignals.length === 1 ? '' : 's'}
                </Text>
              </View>
            )}
          </View>

          {/* Headline — signature-driven, unique per member */}
          <Text style={[styles.headline, { color: theme.textSecondary }]}>
            {story.headline}
          </Text>

          {/* 4-LENS NATIVE STRIP — always visible, no modal required */}
          <View style={styles.lensStrip}>
            {/* HD lens */}
            {hdSignals.length > 0 && (
              <View style={styles.lensRow}>
                <View style={[styles.lensPill, { backgroundColor: theme.surfaceLight || theme.border }]}>
                  <Text style={[styles.lensPillText, { color: theme.textSecondary }]}>HD</Text>
                </View>
                <Text
                  style={[styles.lensText, { color: theme.textSecondary }]}
                  numberOfLines={2}
                >
                  {hdSignals[0].translation ||
                    hdSignals[0].name ||
                    `Channel ${hdSignals[0].channel}`}
                </Text>
              </View>
            )}

            {/* Astrology lens */}
            {astroAttraction && (
              <View style={styles.lensRow}>
                <View style={[styles.lensPill, { backgroundColor: theme.surfaceLight || theme.border }]}>
                  <Text style={[styles.lensPillText, { color: theme.textSecondary }]}>Astro</Text>
                </View>
                <Text
                  style={[styles.lensText, { color: theme.textSecondary }]}
                  numberOfLines={2}
                >
                  {astroAttraction}
                </Text>
              </View>
            )}

            {/* BaZi lens (animal dynamic) */}
            {baziAnimal && (
              <View style={styles.lensRow}>
                <View style={[styles.lensPill, { backgroundColor: theme.surfaceLight || theme.border }]}>
                  <Text style={[styles.lensPillText, { color: theme.textSecondary }]}>BaZi</Text>
                </View>
                <Text
                  style={[styles.lensText, { color: theme.textSecondary }]}
                  numberOfLines={2}
                >
                  {baziAnimal}
                </Text>
              </View>
            )}

            {/* Enneagram lens (gift-exchange) */}
            {enneagramGift && (
              <View style={styles.lensRow}>
                <View style={[styles.lensPill, { backgroundColor: theme.surfaceLight || theme.border }]}>
                  <Text style={[styles.lensPillText, { color: theme.textSecondary }]}>Enne</Text>
                </View>
                <Text
                  style={[styles.lensText, { color: theme.textSecondary }]}
                  numberOfLines={2}
                >
                  {enneagramGift}
                </Text>
              </View>
            )}
          </View>

          {/* Tension line — specific, actionable */}
          {topTension && (
            <Text style={[styles.watchOut, { color: theme.textTertiary }]}>
              Watch: {topTension}
            </Text>
          )}
          {topGift && (
            <Text style={[styles.watchOut, { color: theme.textTertiary, marginTop: 2 }]}>
              Gift: {topGift}
            </Text>
          )}
        </View>

        <Ionicons name="chevron-forward" size={20} color={theme.textTertiary} />
      </TouchableOpacity>
    );
  };

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
                    {signals?.enneagram && Object.keys(signals.enneagram).length > 0 ? (
                        <View style={styles.lensSection}>
                          <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                            ENNEAGRAM DYNAMICS
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
                    ) : null}

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

                    {/* BAZI SIGNALS */}
                    {signals?.bazi && Object.keys(signals.bazi).length > 0 ? (
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
                    ) : null}
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
    fontSize: 22,
    fontWeight: '600',
  },
  headerSubtitle: {
    fontSize: 14,
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
    fontSize: 16,
  },
  errorText: {
    marginTop: 12,
    fontSize: 16,
    textAlign: 'center',
  },
  emptyText: {
    marginTop: 12,
    fontSize: 16,
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
    fontSize: 16,
    fontWeight: '500',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  introText: {
    fontSize: 16,
    fontStyle: 'italic',
    marginBottom: 16,
    lineHeight: 31,
  },
  mappingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginBottom: 16,
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
  memberHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  channelBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    borderWidth: 1,
  },
  channelBadgeText: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 0.3,
  },
  headline: {
    fontSize: 16,
    lineHeight: 22,
    marginBottom: 10,
  },
  lensStrip: {
    marginTop: 4,
    marginBottom: 8,
    gap: 6,
  },
  lensRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  lensPill: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    minWidth: 44,
    alignItems: 'center',
  },
  lensPillText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  lensText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
  },
  watchOut: {
    fontSize: 13,
    fontStyle: 'italic',
    lineHeight: 18,
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
    fontSize: 22,
    fontWeight: '600',
  },
  modalSubtitle: {
    fontSize: 14,
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
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 14,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 14,
    lineHeight: 32,
  },
  sectionText: {
    fontSize: 17,
    lineHeight: 30,
  },
  // V2 3-Layer Styles
  storyCard: {
    padding: 22,
    borderRadius: 16,
    borderWidth: 1,
    marginBottom: 28,
  },
  storyHeadline: {
    fontSize: 24,
    fontWeight: '600',
    lineHeight: 32,
    marginBottom: 14,
  },
  storySummary: {
    fontSize: 16,
    lineHeight: 32,
  },
  patternSection: {
    marginBottom: 24,
  },
  patternLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 14,
  },
  patternBulletRow: {
    flexDirection: 'row',
    marginBottom: 14,
    paddingRight: 8,
  },
  patternBulletDash: {
    fontSize: 17,
    marginRight: 10,
    marginTop: 2,
    width: 16,
    textAlign: 'center',
  },
  patternBulletText: {
    flex: 1,
    fontSize: 17,
    lineHeight: 31,
  },
  giftSection: {
    paddingLeft: 16,
    borderLeftWidth: 3,
    marginBottom: 24,
  },
  signalsSection: {
    marginTop: 10,
  },
  signalsToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 16,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 14,
  },
  signalsToggleText: {
    fontSize: 17,
    fontWeight: '500',
  },
  signalsNote: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 14,
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
    marginBottom: 16,
  },
  channelGates: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
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
    fontSize: 14,
    fontWeight: '500',
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  gateNumber: {
    fontSize: 16,
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
    fontSize: 14,
    fontWeight: '600',
    marginHorizontal: 4,
  },
  channelInfo: {
    alignItems: 'center',
  },
  channelTranslation: {
    fontSize: 17,
    fontWeight: '500',
    lineHeight: 30,
    marginBottom: 16,
    fontStyle: 'italic',
  },
  lensSection: {
    marginTop: 24,
    paddingTop: 18,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(128,128,128,0.15)',
  },
  lensSignalRow: {
    flexDirection: 'row',
    marginBottom: 14,
    paddingRight: 8,
  },
  lensSignalIcon: {
    fontSize: 16,
    marginRight: 10,
    marginTop: 2,
    width: 16,
    textAlign: 'center',
  },
  lensSignalText: {
    flex: 1,
    fontSize: 17,
    lineHeight: 31,
  },
  channelName: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 6,
  },
  channelTheme: {
    fontSize: 16,
    fontStyle: 'italic',
    textAlign: 'center',
    lineHeight: 30,
  },
});
