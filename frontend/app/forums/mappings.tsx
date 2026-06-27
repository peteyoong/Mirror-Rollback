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
import { BUILD_ID, BUILD_AT } from '../../constants/buildMarker';
import BetweenYouTodayCard from '../../components/BetweenYouTodayCard';

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

    // Alias `mapping` so legacy inline blocks that reference `mapping`
    // resolve correctly. (renderMappingRow uses the parameter `mapping`;
    // here we use the modal's selected member but expose the same name.)
    const mapping = selectedMember as ForumMemberMapping;

    // Read from 3-layer structure with backward compat fallbacks
    const story = (selectedMember as any).story || { headline: selectedMember.headline, summary: selectedMember.description };
    const patterns = (selectedMember as any).patterns || null;
    const signals = (selectedMember as any).signals || null;
    const hdSignals = signals?.human_design || selectedMember.why_this_happens || [];

    // Relationship Field Architecture v1 — additive
    const field = (selectedMember as any).field || null;
    const useFieldLayout = field?.version === 'relationship-field-v1';
    const amplifiers = field?.amplifiers || {};
    const hasAnyAmplifier = !!(amplifiers.juno || amplifiers.north_node || amplifiers.vertex);

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
                {useFieldLayout ? 'What happens between you' : 'How they map to you'}
              </Text>
            </View>
            <View style={{ width: 40 }} />
          </View>

          <ScrollView 
            style={styles.modalScroll}
            contentContainerStyle={styles.modalContent}
            showsVerticalScrollIndicator={false}
          >
            {/* ============================================================
                BETWEEN YOU TODAY — Relationship Timing Layer v1
                FIRST in the relationship page hierarchy (per product spec
                v1.5.2): today/transits/relationship-weather drive this
                block. KG synthesis may add an optional `undertone` line
                as a subtle subtitle (never replaces the transit body).
                surface marker: between-you-today-first-v1.5.2
                ============================================================ */}
            {user?.id && selectedMember?.member_id && forumId ? (
              <BetweenYouTodayCard
                forumId={forumId as string}
                userId={user.id}
                memberId={selectedMember.member_id}
                memberName={selectedMember.member_name}
                theme={theme}
                undertone={
                  (selectedMember as any)?.relationship_synthesis?.undertone_for_today
                  || (selectedMember as any)?.mapping?.relationship_synthesis?.undertone_for_today
                  || ''
                }
              />
            ) : null}

            {/* ============================================================
                MIRROR KNOWLEDGE GRAPH V1.5 — SYNTHESIS SECOND
                The eloquent holistic relationship story. Renders the
                cross-lens deterministic synthesis below the Today card.
                Falls back silently to the existing legacy lens sections
                below when absent.  Additive only.
                surface marker: relationship-synthesis-second-v1.5.2
                ============================================================ */}
            {(() => {
              const rs: any = (selectedMember as any)?.relationship_synthesis
                || (selectedMember as any)?.mapping?.relationship_synthesis;
              if (!rs || !rs.story) return null;
              const story = rs.story || {};
              const ladder = Array.isArray(rs.evidence_ladder) ? rs.evidence_ladder : [];
              const conf = rs.confidence || {};
              const diag = rs.diagnostics || {};
              const repair: string[] = Array.isArray(story.repair_pathway)
                ? story.repair_pathway
                : story.repair_pathway ? [String(story.repair_pathway)] : [];
              return (
                <View
                  testID="relationship-synthesis-second-v152"
                  style={[styles.themesSection, { backgroundColor: theme.surface,
                                                   borderColor: theme.border,
                                                   borderWidth: 1,
                                                   padding: 16,
                                                   marginBottom: 16,
                                                   borderRadius: 12 }]}
                >
                  <Text style={[styles.patternLabel, { color: theme.textTertiary, marginBottom: 8 }]}>
                    MIRROR SEES
                  </Text>
                  {!!story.headline && (
                    <Text style={[styles.modalTitle, { color: theme.text, marginBottom: 8 }]}>
                      {String(story.headline)}
                    </Text>
                  )}
                  {!!story.summary && (
                    <Text style={[styles.modalSubtitle, { color: theme.textSecondary, marginBottom: 12 }]}>
                      {String(story.summary)}
                    </Text>
                  )}
                  {!!story.current_movement && (
                    <View style={{ marginBottom: 10 }}>
                      <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>CURRENT MOVEMENT</Text>
                      <Text style={[styles.activationText, { color: theme.text }]}>{String(story.current_movement)}</Text>
                    </View>
                  )}
                  {!!story.growth_edge && (
                    <View style={{ marginBottom: 10 }}>
                      <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>GROWTH EDGE</Text>
                      <Text style={[styles.activationText, { color: theme.text }]}>{String(story.growth_edge)}</Text>
                    </View>
                  )}
                  {!!story.shadow_pattern && (
                    <View style={{ marginBottom: 10 }}>
                      <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>SHADOW PATTERN</Text>
                      <Text style={[styles.activationText, { color: theme.text }]}>{String(story.shadow_pattern)}</Text>
                    </View>
                  )}
                  {repair.length > 0 && (
                    <View style={{ marginBottom: 10 }}>
                      <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>REPAIR PATHWAY</Text>
                      {repair.map((line, i) => (
                        <Text key={`rp-${i}`} style={[styles.activationText, { color: theme.text }]}>
                          • {String(line)}
                        </Text>
                      ))}
                    </View>
                  )}
                  {!!story.question_to_ask && (
                    <View style={{ marginBottom: 10 }}>
                      <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>QUESTION TO HOLD</Text>
                      <Text style={[styles.activationText, { color: theme.text, fontStyle: 'italic' }]}>
                        {String(story.question_to_ask)}
                      </Text>
                    </View>
                  )}
                  {(!!conf.label || !!conf.level || diag.provenance_rollup) && (() => {
                    // Humanize lens identifiers everywhere on the page.
                    const LENS_LABELS: Record<string, string> = {
                      human_design: 'Human Design',
                      numerology:   'Numerology',
                      enneagram:    'Enneagram',
                      bazi:         'BaZi',
                      astrology:    'Astrology',
                    };
                    const humanLenses = Array.isArray(diag.lenses_present)
                      ? diag.lenses_present
                          .map((l: string) => LENS_LABELS[l] || String(l).replace(/_/g, ' '))
                          .join(', ')
                      : '';
                    return (
                      <View style={{ marginTop: 8, flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
                        {!!(conf.label || conf.level) && (
                          <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>
                            Confidence: {String(conf.label || conf.level)}
                          </Text>
                        )}
                        {!!humanLenses && (
                          <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>
                            · Lenses: {humanLenses}
                          </Text>
                        )}
                      </View>
                    );
                  })()}
                  {ladder.length > 0 && (
                    <View style={{ marginTop: 12, borderTopWidth: 1, borderTopColor: theme.border, paddingTop: 12 }}>
                      <Text style={[styles.patternLabel, { color: theme.textTertiary, marginBottom: 6 }]}>
                        WHY MIRROR SEES THIS · evidence ladder
                      </Text>
                      {ladder.slice(0, 6).map((entry: any, i: number) => {
                        // v1.5.3 — humanize lens provenance label for user-
                        // facing copy. Map "human_design", "numerology",
                        // "enneagram", "bazi", "astrology" to plain English
                        // and the provenance_status value to a friendly tag.
                        const LENS_LABELS: Record<string, string> = {
                          human_design: 'Human Design',
                          numerology:   'Numerology',
                          enneagram:    'Enneagram',
                          bazi:         'BaZi',
                          astrology:    'Astrology',
                        };
                        const PROV_LABELS: Record<string, string> = {
                          verified: 'verified',
                          suspect:  'review needed',
                          stale:    'review needed',
                          missing:  'review needed',
                          mixed:    'cross-checked',
                          unknown:  '',
                        };
                        const rawLenses = entry?.lens_contributions && typeof entry.lens_contributions === 'object'
                          ? Object.keys(entry.lens_contributions)
                          : [];
                        const lensText = rawLenses
                          .map((l) => LENS_LABELS[l] || l.replace(/_/g, ' '))
                          .join(' + ');
                        const provRaw = typeof entry?.provenance_status === 'string'
                          ? entry.provenance_status.toLowerCase()
                          : '';
                        const provText = PROV_LABELS[provRaw] || '';
                        return (
                          <View key={`evl-${i}`} style={{ marginBottom: 8 }}>
                            <Text style={[styles.activationText, { color: theme.text, fontWeight: '600' }]}>
                              · {String(entry.claim || entry.claim_label || '')}
                            </Text>
                            {!!lensText && (
                              <Text style={[styles.patternLabel, { color: theme.textTertiary, marginLeft: 12 }]}>
                                from {lensText}{provText ? `  ·  ${provText}` : ''}
                              </Text>
                            )}
                          </View>
                        );
                      })}
                    </View>
                  )}
                </View>
              );
            })()}

            {useFieldLayout ? (
              <>
                {/* ============================================================
                    RELATIONSHIP FIELD ARCHITECTURE v1
                    Activation-first synthesis BEFORE evidence.
                    ============================================================ */}

                {/* FIELD PARAGRAPH — the opener, integrates all lenses */}
                <View style={[styles.storyCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                  <Text style={[styles.fieldParagraph, { color: theme.text }]}>
                    {field.field_paragraph}
                  </Text>
                </View>

                {/* ACTIVATION — DETERMINISTIC SINGLE-SURFACE RULE v2.
                    relationship-mapping-activation-single-surface-v2:
                    The Relationship Field paragraph IS the activation surface.
                    Suppress the WHAT ACTIVATES chip when activation is:
                      (a) exactly equal to paragraph (normalized), OR
                      (b) substring-contained either way (normalized), OR
                      (c) Jaccard token overlap ≥ 0.55.
                    Last guard catches near-identical strings that differ by
                    one or two surrounding sentences. */}
                {(() => {
                  const rawPara = field.field_paragraph || '';
                  const rawAct = field.activation || '';
                  if (!rawAct.trim()) {
                    (selectedMember as any).__diagActivationSurface = 'paragraph-only';
                    return null;
                  }
                  if (!rawPara.trim()) {
                    // No paragraph → activation is the ONLY surface; render it
                    (selectedMember as any).__diagActivationSurface = 'chip-only (no paragraph)';
                    return (
                      <View
                        style={[
                          styles.activationChip,
                          { backgroundColor: (theme.accent || '#8B5CF6') + '12', borderColor: (theme.accent || '#8B5CF6') + '40' },
                        ]}
                      >
                        <Text style={[styles.activationLabel, { color: theme.accent || '#8B5CF6' }]}>
                          WHAT ACTIVATES
                        </Text>
                        <Text style={[styles.activationText, { color: theme.text }]}>
                          {field.activation}
                        </Text>
                      </View>
                    );
                  }
                  const norm = (s: string) =>
                    s.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
                  const para = norm(rawPara);
                  const act = norm(rawAct);
                  const exact = para === act;
                  const containedAinB = para.length > 0 && act.length > 0 && para.includes(act);
                  const containedBinA = para.length > 0 && act.length > 0 && act.includes(para);
                  // Jaccard token overlap as last guard
                  const tokens = (s: string) =>
                    new Set(s.split(/\s+/).filter(t => t.length > 3));
                  const tA = tokens(para);
                  const tB = tokens(act);
                  let inter = 0;
                  tA.forEach(t => { if (tB.has(t)) inter++; });
                  const union = new Set([...tA, ...tB]).size || 1;
                  const jaccard = inter / union;
                  const highOverlap = jaccard >= 0.55;
                  const isDuplicate = exact || containedAinB || containedBinA || highOverlap;
                  (selectedMember as any).__diagActivationSurface = isDuplicate
                    ? `paragraph-only (chip suppressed; jaccard=${jaccard.toFixed(2)})`
                    : `paragraph + chip (jaccard=${jaccard.toFixed(2)})`;
                  if (isDuplicate) {
                    if (typeof window !== 'undefined' && (window as any).__mirrorActivationDupLogged !== mapping?.member_id) {
                      (window as any).__mirrorActivationDupLogged = mapping?.member_id;
                      // eslint-disable-next-line no-console
                      console.log('[RelationshipMappingV2-UI] WHAT ACTIVATES chip suppressed', {
                        member: mapping?.member_name,
                        exact, containedAinB, containedBinA, jaccard,
                        build_marker: 'relationship-mapping-activation-single-surface-v2',
                      });
                    }
                    return null;
                  }
                  return (
                    <View
                      style={[
                        styles.activationChip,
                        { backgroundColor: (theme.accent || '#8B5CF6') + '12', borderColor: (theme.accent || '#8B5CF6') + '40' },
                      ]}
                    >
                      <Text style={[styles.activationLabel, { color: theme.accent || '#8B5CF6' }]}>
                        WHAT ACTIVATES
                      </Text>
                      <Text style={[styles.activationText, { color: theme.text }]}>
                        {field.activation}
                      </Text>
                    </View>
                  );
                })()}

                {/* THEMES — clustered cards, each contains its own friction in-line */}
                {Array.isArray(field.themes) && field.themes.length > 0 && (
                  <View style={styles.themesSection}>
                    <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>
                      WHAT LIVES BETWEEN YOU
                    </Text>
                    {field.themes.map((theme_: any, idx: number) => (
                      <View
                        key={`theme-${idx}`}
                        style={[
                          styles.themeCard,
                          { backgroundColor: theme.surface, borderColor: theme.border },
                        ]}
                      >
                        <Text style={[styles.themeLabel, { color: theme.text }]}>
                          {theme_.label}
                        </Text>
                        <Text style={[styles.themeWhatLivesHere, { color: theme.textSecondary }]}>
                          {theme_.what_lives_here}
                        </Text>
                        {theme_.friction_inside_it && (
                          <Text style={[styles.themeFriction, { color: theme.textTertiary }]}>
                            <Text style={{ color: theme.accent || '#8B5CF6' }}>↳ </Text>
                            {theme_.friction_inside_it}
                          </Text>
                        )}
                      </View>
                    ))}
                  </View>
                )}

                {/* GIFT OF THIS CONNECTION — dedicated, always present */}
                {field.gift_of_this_connection && (
                  <View
                    style={[
                      styles.giftCard,
                      {
                        backgroundColor: theme.surface,
                        borderColor: (theme.accent || '#8B5CF6') + '50',
                      },
                    ]}
                  >
                    <Text style={[styles.giftLabel, { color: theme.accent || '#8B5CF6' }]}>
                      ✦ GIFT OF THIS CONNECTION
                    </Text>
                    <Text style={[styles.giftText, { color: theme.text }]}>
                      {field.gift_of_this_connection}
                    </Text>
                  </View>
                )}

                {/* AMPLIFIERS — only when at least one is non-null. Subtle, framed as
                    "significance amplifiers", never as fate/soulmate language. */}
                {hasAnyAmplifier && (
                  <View style={styles.amplifiersSection}>
                    <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>
                      WHY THE STAKES FEEL HIGHER
                    </Text>
                    {amplifiers.juno && (
                      <View style={styles.amplifierRow}>
                        <Text style={[styles.amplifierPip, { color: theme.textTertiary }]}>·</Text>
                        <Text style={[styles.amplifierText, { color: theme.textSecondary }]}>
                          {amplifiers.juno}
                        </Text>
                      </View>
                    )}
                    {amplifiers.north_node && (
                      <View style={styles.amplifierRow}>
                        <Text style={[styles.amplifierPip, { color: theme.textTertiary }]}>·</Text>
                        <Text style={[styles.amplifierText, { color: theme.textSecondary }]}>
                          {amplifiers.north_node}
                        </Text>
                      </View>
                    )}
                    {amplifiers.vertex && (
                      <View style={styles.amplifierRow}>
                        <Text style={[styles.amplifierPip, { color: theme.textTertiary }]}>·</Text>
                        <Text style={[styles.amplifierText, { color: theme.textSecondary }]}>
                          {amplifiers.vertex}
                        </Text>
                      </View>
                    )}
                  </View>
                )}
              </>
            ) : (
              <>
                {/* ============================================================
                    LEGACY 3-LAYER LAYOUT — unchanged fallback path.
                    Renders when mapping.field is absent OR not v1.
                    ============================================================ */}

                {/* LAYER 1: STORY */}
                <View style={[styles.storyCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                  <Text style={[styles.storyHeadline, { color: theme.text }]}>
                    {story.headline}
                  </Text>
                  <Text style={[styles.storySummary, { color: theme.textSecondary }]}>
                    {story.summary}
                  </Text>
                </View>

                {/* LAYER 2: PATTERNS */}
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
              </>
            )}

            {/* ──────────────────────────────────────────────────────── */}
            {/* V2 ASTROLOGICAL DYNAMICS has been MOVED into the         */}
            {/* "Why this is so strong" accordion below, alongside       */}
            {/* Design Connections, Enneagram Dynamics, and Elemental    */}
            {/* (BaZi) Dynamics. relationship-mapping-astrology-in-accordion */}
            {/* ──────────────────────────────────────────────────────── */}

            {/* ================================================ */}
            {/* LAYER 3: SIGNALS (Collapsible proof layer)       */}
            {/* "Why this is so strong" — opens when ANY lens has  */}
            {/* content: HD channels, V2 astrology, Enneagram,     */}
            {/* BaZi, or Numerology.                               */}
            {/* relationship-mapping-accordion-multi-lens          */}
            {/* ================================================ */}
            {(() => {
              const v2 = (selectedMember as any)?.astrology_dynamics;
              const hasV2Astro =
                !!(v2 && (v2.body || v2.headline) &&
                  (typeof v2.body === 'string' ? v2.body.trim().length > 0 : !!v2.headline));
              const legacy = signals?.astrology;
              const legacyHidden = !!(legacy && (legacy as any).legacy_hidden_due_to_v2);
              const hasLegacyAstro =
                !!legacy &&
                !legacyHidden &&
                (legacy.attraction?.length > 0 ||
                  legacy.tension?.length > 0 ||
                  legacy.growth?.length > 0);
              const hasEnneagram =
                !!signals?.enneagram && Object.keys(signals.enneagram).length > 0;
              const hasBazi =
                !!signals?.bazi && Object.keys(signals.bazi).length > 0;
              const hasNumerology =
                !!signals?.numerology && (signals.numerology.themes?.length || 0) > 0;
              const hasAnySignal =
                hdSignals.length > 0 || hasV2Astro || hasLegacyAstro ||
                hasEnneagram || hasBazi || hasNumerology;

              if (!hasAnySignal) return null;

              return (
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
                      size={20}
                      color={theme.textTertiary}
                    />
                  </TouchableOpacity>

                  {showWhyExpanded && (
                    <View style={styles.whyContent}>
                      {/* HD RELATIONSHIP NARRATIVE BLOCKS (v1.5.2)
                          Renders type/authority/profile/definition/centers/
                          electromagnetic/compromise/practical above the
                          channel cards so HD drill-down has real narrative,
                          not just channel boxes.
                          marker: hd-relationship-narrative-blocks-v1.5.2 */}
                      {(() => {
                        const hdField = (signals as any)?.human_design_field;
                        const blocks = hdField?.narrative_blocks;
                        if (!blocks || typeof blocks !== 'object') return null;
                        const renderBlock = (label: string, head: string | undefined, body: string | undefined, watch?: string | undefined, details?: string[]) => {
                          if (!head && !body) return null;
                          return (
                            <View key={label} style={{ marginBottom: 14 }}>
                              <Text style={[styles.patternLabel, { color: theme.textTertiary, marginBottom: 4 }]}>
                                {label}{head ? ` · ${head}` : ''}
                              </Text>
                              {!!body && (
                                <Text style={[styles.activationText, { color: theme.text, lineHeight: 21 }]}>
                                  {body}
                                </Text>
                              )}
                              {!!watch && (
                                <Text style={[styles.activationText, { color: theme.textSecondary, marginTop: 4, fontStyle: 'italic', lineHeight: 20 }]}>
                                  Watch: {watch}
                                </Text>
                              )}
                              {Array.isArray(details) && details.length > 0 && (
                                <View style={{ marginTop: 6 }}>
                                  {details.map((d, i) => (
                                    <Text key={`d-${i}`} style={[styles.activationText, { color: theme.textSecondary, marginLeft: 8 }]}>
                                      · {d}
                                    </Text>
                                  ))}
                                </View>
                              )}
                            </View>
                          );
                        };
                        const ch = blocks.channels || {};
                        return (
                          <View testID="hd-relationship-narrative-blocks" style={{ marginBottom: 12 }}>
                            <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                              HUMAN DESIGN — RELATIONSHIP DYNAMICS
                            </Text>
                            {renderBlock('TYPE ENGAGEMENT', blocks.type_pair_engagement?.headline, blocks.type_pair_engagement?.summary)}
                            {!!blocks.type_pair_engagement?.field_overview && (
                              <Text style={[styles.activationText, { color: theme.textSecondary, marginTop: -8, marginBottom: 14, lineHeight: 20 }]}>
                                {blocks.type_pair_engagement.field_overview}
                              </Text>
                            )}
                            {renderBlock('AUTHORITY · DECISION RHYTHM', blocks.authority_rhythm?.headline, blocks.authority_rhythm?.summary)}
                            {renderBlock('PROFILE INTERACTION', blocks.profile_interaction?.headline, blocks.profile_interaction?.summary, blocks.profile_interaction?.watch)}
                            {renderBlock('DEFINITION DYNAMICS', blocks.definition_dynamics?.headline, blocks.definition_dynamics?.summary, blocks.definition_dynamics?.watch)}
                            {renderBlock('CENTER CONDITIONING', undefined, blocks.centers_conditioning?.summary, blocks.centers_conditioning?.watch, blocks.centers_conditioning?.details)}
                            {/* CHANNELS DYNAMICS — counts + narratives */}
                            {!!(ch.electromagnetic?.summary || ch.compromise?.summary || ch.dominance?.summary || ch.companion?.summary) && (
                              <View style={{ marginBottom: 14 }}>
                                <Text style={[styles.patternLabel, { color: theme.textTertiary, marginBottom: 4 }]}>
                                  CHANNEL DYNAMICS
                                </Text>
                                {!!ch.electromagnetic?.summary && (
                                  <Text style={[styles.activationText, { color: theme.text, marginTop: 4, lineHeight: 21 }]}>
                                    ⟡ {ch.electromagnetic.summary}
                                  </Text>
                                )}
                                {!!ch.compromise?.summary && (
                                  <Text style={[styles.activationText, { color: theme.text, marginTop: 4, lineHeight: 21 }]}>
                                    ⊘ {ch.compromise.summary}
                                  </Text>
                                )}
                                {!!ch.dominance?.summary && (
                                  <Text style={[styles.activationText, { color: theme.text, marginTop: 4, lineHeight: 21 }]}>
                                    ▣ {ch.dominance.summary}
                                  </Text>
                                )}
                                {!!ch.companion?.summary && (
                                  <Text style={[styles.activationText, { color: theme.text, marginTop: 4, lineHeight: 21 }]}>
                                    = {ch.companion.summary}
                                  </Text>
                                )}
                              </View>
                            )}
                            {/* PRACTICAL — how to engage them */}
                            {(blocks.practical_guidance?.repair_first?.length || blocks.practical_guidance?.growth_edge) && (
                              <View style={{ marginBottom: 8 }}>
                                <Text style={[styles.patternLabel, { color: theme.textTertiary, marginBottom: 4 }]}>
                                  HOW TO ENGAGE
                                </Text>
                                {!!blocks.practical_guidance?.summary && (
                                  <Text style={[styles.activationText, { color: theme.textSecondary, marginBottom: 4, lineHeight: 20 }]}>
                                    {blocks.practical_guidance.summary}
                                  </Text>
                                )}
                                {Array.isArray(blocks.practical_guidance?.repair_first) && blocks.practical_guidance.repair_first.map((r: string, i: number) => (
                                  <Text key={`pr-${i}`} style={[styles.activationText, { color: theme.text, marginTop: 2, lineHeight: 21 }]}>
                                    • {r}
                                  </Text>
                                ))}
                                {!!blocks.practical_guidance?.growth_edge && (
                                  <Text style={[styles.activationText, { color: theme.textSecondary, marginTop: 6, fontStyle: 'italic', lineHeight: 20 }]}>
                                    Growth edge: {blocks.practical_guidance.growth_edge}
                                  </Text>
                                )}
                              </View>
                            )}
                          </View>
                        );
                      })()}

                      {/* HD CHANNELS — only when HD signals present */}
                      {hdSignals.length > 0 && (
                        <>
                          <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                            COMPLETED CHANNELS
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
                              {/* PER-CHANNEL NARRATIVE (v1.5.2) — gift / tension / practical use.
                                  Renders only when channel.narrative is present. */}
                              {channel.narrative && (
                                <View testID={`channel-narrative-${channel.channel}`} style={{ marginTop: 10, paddingTop: 10, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: theme.border }}>
                                  {!!channel.narrative.gift && (
                                    <View style={{ marginBottom: 6 }}>
                                      <Text style={[styles.patternLabel, { color: '#81C784' }]}>GIFT</Text>
                                      <Text style={[styles.activationText, { color: theme.text, lineHeight: 20 }]}>
                                        {channel.narrative.gift}
                                      </Text>
                                    </View>
                                  )}
                                  {!!channel.narrative.tension && (
                                    <View style={{ marginBottom: 6 }}>
                                      <Text style={[styles.patternLabel, { color: '#CF6679' }]}>TENSION TO WATCH</Text>
                                      <Text style={[styles.activationText, { color: theme.text, lineHeight: 20 }]}>
                                        {channel.narrative.tension}
                                      </Text>
                                    </View>
                                  )}
                                  {!!channel.narrative.practical_use && (
                                    <View>
                                      <Text style={[styles.patternLabel, { color: '#90CAF9' }]}>PRACTICAL USE</Text>
                                      <Text style={[styles.activationText, { color: theme.text, lineHeight: 20 }]}>
                                        {channel.narrative.practical_use}
                                      </Text>
                                    </View>
                                  )}
                                </View>
                              )}
                            </View>
                          ))}
                        </>
                      )}

                    {/* ASTROLOGICAL DYNAMICS — V2 preferred, legacy fallback.
                        relationship-mapping-astrology-in-accordion */}
                    {(() => {
                      const v2 = mapping?.astrology_dynamics;
                      const v2Has =
                        v2 && (v2.headline || v2.body) &&
                        (typeof v2.body === 'string' ? v2.body.trim().length > 0 : false);
                      const legacy = signals?.astrology;
                      const legacyHidden = !!(legacy && (legacy as any).legacy_hidden_due_to_v2);
                      const legacyHas =
                        legacy &&
                        (legacy.attraction?.length > 0 ||
                          legacy.tension?.length > 0 ||
                          legacy.growth?.length > 0);

                      if (typeof window !== 'undefined' && (window as any).__mirrorAstroLoggedInner !== mapping?.member_id) {
                        (window as any).__mirrorAstroLoggedInner = mapping?.member_id;
                        // eslint-disable-next-line no-console
                        console.log('[RelationshipMappingV2-UI] in-accordion astrology decision', {
                          member: mapping?.member_name,
                          v2_has: !!v2Has,
                          legacy_has: !!legacyHas,
                          legacy_hidden_due_to_v2: legacyHidden,
                          decision: v2Has
                            ? 'render-v2-in-accordion'
                            : legacyHas && !legacyHidden
                              ? 'render-legacy-fallback'
                              : 'render-nothing',
                          build_marker: 'relationship-mapping-astrology-in-accordion',
                        });
                      }

                      // Preferred: V2 deep card rendered INSIDE the accordion
                      if (v2Has) {
                        return (
                          <View style={styles.lensSection}>
                            <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                              ASTROLOGICAL DYNAMICS
                            </Text>
                            {v2.headline ? (
                              <Text
                                style={{
                                  color: theme.text,
                                  fontSize: 15,
                                  lineHeight: 22,
                                  fontWeight: '600',
                                  marginBottom: 8,
                                }}
                              >
                                {v2.headline}
                              </Text>
                            ) : null}
                            {v2.body ? (
                              <Text
                                style={{
                                  color: theme.textSecondary,
                                  fontSize: 14,
                                  lineHeight: 22,
                                }}
                              >
                                {v2.body}
                              </Text>
                            ) : null}
                            {Array.isArray(v2.supporting_signals) && v2.supporting_signals.length > 0 ? (
                              <View style={{ marginTop: 10 }}>
                                <Text style={[styles.signalsNote, { color: theme.textTertiary, fontSize: 11 }]}>
                                  WHY THIS IS SHOWING UP
                                </Text>
                                {v2.supporting_signals.slice(0, 6).map((sig: string, i: number) => (
                                  <View key={`v2sup-acc-${i}`} style={styles.lensSignalRow}>
                                    <Text style={[styles.lensSignalIcon, { color: '#D4A574' }]}>·</Text>
                                    <Text style={[styles.lensSignalText, { color: theme.textTertiary, fontSize: 12 }]}>
                                      {sig}
                                    </Text>
                                  </View>
                                ))}
                              </View>
                            ) : null}
                            {/* relationship-mapping-deep-astrology-v2.1 — advanced-object corroboration tray.
                                These are advanced-body signals (Juno / Vertex / Anti-Vertex / Chiron /
                                Lilith / Fortune / Spirit) attached BELOW the core Sun/Moon/IC evidence
                                so the user feels the read got deeper without becoming technical. */}
                            {Array.isArray((v2 as any).advanced_supporting_signals) &&
                             (v2 as any).advanced_supporting_signals.length > 0 ? (
                              <View style={{ marginTop: 14 }}>
                                <Text style={[styles.signalsNote, { color: theme.textTertiary, fontSize: 11 }]}>
                                  WHY THE STAKES FEEL HIGHER
                                </Text>
                                {((v2 as any).advanced_supporting_signals as string[])
                                  .slice(0, 8)
                                  .map((sig: string, i: number) => (
                                    <View key={`v2adv-acc-${i}`} style={styles.lensSignalRow}>
                                      <Text style={[styles.lensSignalIcon, { color: '#9B7CC8' }]}>·</Text>
                                      <Text style={[styles.lensSignalText, { color: theme.textTertiary, fontSize: 12 }]}>
                                        {sig}
                                      </Text>
                                    </View>
                                  ))}
                              </View>
                            ) : null}
                          </View>
                        );
                      }

                      // No V2 and legacy was explicitly hidden → render nothing.
                      if (legacyHidden) return null;

                      if (legacyHas) {
                        return (
                          <View style={styles.lensSection}>
                            <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                              ASTROLOGICAL DYNAMICS
                            </Text>
                            {legacy.attraction?.map((item: string, i: number) => (
                              <View key={`aa-${i}`} style={styles.lensSignalRow}>
                                <Text style={[styles.lensSignalIcon, { color: '#D4A574' }]}>✦</Text>
                                <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                              </View>
                            ))}
                            {legacy.tension?.map((item: string, i: number) => (
                              <View key={`at-${i}`} style={styles.lensSignalRow}>
                                <Text style={[styles.lensSignalIcon, { color: '#CF6679' }]}>⚡</Text>
                                <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                              </View>
                            ))}
                            {legacy.growth?.map((item: string, i: number) => (
                              <View key={`ag-${i}`} style={styles.lensSignalRow}>
                                <Text style={[styles.lensSignalIcon, { color: '#81C784' }]}>↑</Text>
                                <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                              </View>
                            ))}
                          </View>
                        );
                      }
                      // EMPTY-STATE DIAGNOSTIC — never silently render nothing.
                      // Surface the reason so the user can see WHY astrology
                      // didn't produce signals (usually role!=spouse → V10
                      // didn't fire, AND legacy has no content for this pair).
                      const rel = (mapping as any)?.debug?.relationship_context || {};
                      const roleStr = rel.relationship_role || 'unknown';
                      const srcStr = rel.role_source || 'unknown';
                      return (
                        <View style={styles.lensSection}>
                          <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                            ASTROLOGICAL DYNAMICS
                          </Text>
                          <Text
                            style={{
                              color: theme.textTertiary,
                              fontSize: 12,
                              fontStyle: 'italic',
                              lineHeight: 18,
                              marginTop: 4,
                            }}
                          >
                            No deterministic astrology signals were generated
                            for this pairing (role: {roleStr} · src: {srcStr}).
                            Astrological dynamics are produced when both
                            charts are available and the relationship role is
                            mapped explicitly.
                          </Text>
                        </View>
                      );
                    })()}

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

                    {/* NUMEROLOGY V2 CARD — Mirror Language fields (v2-lite)
                        Renders core_dynamic / natural_strength / growth_edge /
                        shadow_pattern / repair_pathway PROMINENTLY before the
                        legacy "themes" list. marker: numerology-v2-card-v1.5.2 */}
                    {(() => {
                      const v2c = (signals as any)?.numerology?.v2_card;
                      if (!v2c || typeof v2c !== 'object') return null;
                      const SECTIONS: Array<{ key: string; label: string }> = [
                        { key: 'core_dynamic',     label: 'Core Dynamic' },
                        { key: 'natural_strength', label: 'Natural Strength' },
                        { key: 'growth_edge',      label: 'Growth Edge' },
                        { key: 'shadow_pattern',   label: 'Shadow Pattern' },
                        { key: 'repair_pathway',   label: 'Repair Pathway' },
                      ];
                      const anyText = SECTIONS.some(
                        s => typeof v2c[s.key] === 'string' && v2c[s.key].trim().length > 0,
                      );
                      if (!anyText) return null;
                      return (
                        <View testID="numerology-v2-card-v152" style={styles.lensSection}>
                          <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                            NUMBER RESONANCE — RELATIONSHIP STORY
                          </Text>
                          {SECTIONS.map(({ key, label }) => {
                            const body = v2c[key];
                            if (typeof body !== 'string' || body.trim().length === 0) return null;
                            return (
                              <View key={`nv2-${key}`} style={{ marginTop: 10 }}>
                                <Text style={[styles.lensSignalText, { color: theme.text, fontWeight: '600', marginBottom: 4 }]}>
                                  {label}
                                </Text>
                                <Text style={[styles.lensSignalText, { color: theme.textSecondary, lineHeight: 20 }]}>
                                  {body}
                                </Text>
                              </View>
                            );
                          })}
                        </View>
                      );
                    })()}

                    {/* NUMEROLOGY SIGNALS (only if present) */}
                    {signals?.numerology && signals.numerology.themes?.length > 0 && (
                      <View style={styles.lensSection}>
                        <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                          NUMBER RESONANCE — themes
                        </Text>
                        {signals.numerology.themes.map((item: string, i: number) => (
                          <View key={`nt-${i}`} style={styles.lensSignalRow}>
                            <Text style={[styles.lensSignalIcon, { color: '#90CAF9' }]}>◇</Text>
                            <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{item}</Text>
                          </View>
                        ))}
                      </View>
                    )}

                    {/* BAZI ANIMAL NARRATIVE — grounded zodiac story (v1.5.2)
                        Three blocks: pair_dynamic / inner_dynamic / triad_signal.
                        Renders above the v2 narrative card.
                        marker: bazi-animal-narrative-v1.5.2 */}
                    {(() => {
                      const an = (signals as any)?.bazi?.animal_narrative;
                      if (!an || typeof an !== 'object') return null;
                      const pair  = an.pair_dynamic;
                      const inner = an.inner_dynamic;
                      const triad = an.triad_signal;
                      const hasAny =
                        (pair && pair.summary) ||
                        (inner && inner.summary) ||
                        (triad && triad.summary);
                      if (!hasAny) return null;
                      return (
                        <View testID="bazi-animal-narrative-v152" style={styles.lensSection}>
                          <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                            BAZI ANIMAL DYNAMICS
                          </Text>
                          {!!(pair && pair.summary) && (
                            <View style={{ marginTop: 10 }}>
                              <Text style={[styles.lensSignalText, { color: theme.text, fontWeight: '600', marginBottom: 4 }]}>
                                Pair Dynamic{pair.tone ? `  ·  ${String(pair.tone).replace('-', ' ')}` : ''}
                              </Text>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary, lineHeight: 20 }]}>
                                {pair.summary}
                              </Text>
                            </View>
                          )}
                          {!!(inner && inner.summary) && (
                            <View style={{ marginTop: 10 }}>
                              <Text style={[styles.lensSignalText, { color: theme.text, fontWeight: '600', marginBottom: 4 }]}>
                                Inner Dynamic
                              </Text>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary, lineHeight: 20 }]}>
                                {inner.summary}
                              </Text>
                            </View>
                          )}
                          {!!(triad && triad.summary) && (
                            <View style={{ marginTop: 10 }}>
                              <Text style={[styles.lensSignalText, { color: theme.text, fontWeight: '600', marginBottom: 4 }]}>
                                Triad Signal{triad.element ? `  ·  ${triad.element}` : ''}
                              </Text>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary, lineHeight: 20 }]}>
                                {triad.summary}
                              </Text>
                            </View>
                          )}
                        </View>
                      );
                    })()}

                    {/* BAZI DYNAMICS — narrative card (5 sections) */}
                    {/* relationship-mapping-bazi-narrative-v1                */}
                    {/* Renders ABOVE Elemental Dynamics so users land on the */}
                    {/* interpretation layer first; Elemental Dynamics stays  */}
                    {/* below as the proof/evidence layer.                    */}
                    {(() => {
                      const baziDyn: any =
                        (selectedMember as any)?.bazi_dynamics ||
                        signals?.bazi?.v2_card ||
                        null;
                      if (!baziDyn || typeof baziDyn !== 'object') return null;
                      const SECTIONS: Array<{ key: string; label: string }> = [
                        { key: 'core_dynamic',     label: 'Core Dynamic' },
                        { key: 'what_strengthens', label: 'What Strengthens This Relationship' },
                        { key: 'growth_edge',      label: 'Growth Edge' },
                        { key: 'shadow_pattern',   label: 'Shadow Pattern' },
                        { key: 'why_matters',      label: 'Why This Relationship Matters' },
                        { key: 'what_bazi_sees',   label: 'What BaZi Sees Here' },
                      ];
                      const anyText = SECTIONS.some(
                        s => typeof baziDyn[s.key] === 'string' && baziDyn[s.key].trim().length > 0,
                      );
                      if (!anyText) return null;
                      return (
                        <View style={styles.lensSection}>
                          <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                            BAZI DYNAMICS
                          </Text>
                          {SECTIONS.map(({ key, label }) => {
                            const body = baziDyn[key];
                            if (typeof body !== 'string' || body.trim().length === 0) return null;
                            return (
                              <View key={`bzd-${key}`} style={{ marginTop: 10 }}>
                                <Text style={[styles.lensSignalText, { color: theme.text, fontWeight: '600', marginBottom: 4 }]}>
                                  {label}
                                </Text>
                                <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>
                                  {body}
                                </Text>
                              </View>
                            );
                          })}
                        </View>
                      );
                    })()}

                    {/* BAZI EVIDENCE LAYER v2 — 4 grouped cards beneath wisdom layer */}
                    {/* MARKER: bazi-evidence-layer-v2                                       */}
                    {(() => {
                      const baziSig: any = signals?.bazi;
                      if (!baziSig || typeof baziSig !== 'object' || Object.keys(baziSig).length === 0) return null;
                      const diag = baziSig.diagnostics || null;
                      const support: string[] = baziSig.support || [];
                      const growth:  string[] = baziSig.growth  || [];
                      const tension: string[] = baziSig.tension || [];
                      // legacy fallback: if no diagnostics, render the original flat list
                      if (!diag) {
                        return (
                          <View style={styles.lensSection}>
                            <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>ELEMENTAL DYNAMICS — Evidence</Text>
                            {support.map((it, i) => (<View key={`bs-${i}`} style={styles.lensSignalRow}><Text style={[styles.lensSignalIcon, { color: '#81C784' }]}>+</Text><Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{it}</Text></View>))}
                            {tension.map((it, i) => (<View key={`bt-${i}`} style={styles.lensSignalRow}><Text style={[styles.lensSignalIcon, { color: '#CF6679' }]}>−</Text><Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{it}</Text></View>))}
                            {growth.map((it, i) => (<View key={`bg-${i}`} style={styles.lensSignalRow}><Text style={[styles.lensSignalIcon, { color: '#90CAF9' }]}>↑</Text><Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{it}</Text></View>))}
                          </View>
                        );
                      }
                      // Dynamic import deferred to top of file — use require to avoid hoist issues here.
                      // eslint-disable-next-line @typescript-eslint/no-var-requires
                      const EL = require('../../services/bazi/evidenceLabels');
                      const cycle = diag.cycle || 'unknown';
                      const elA = diag.element_a || '?';
                      const elB = diag.element_b || '?';
                      const animA = diag.animal_a || '';
                      const animB = diag.animal_b || '';
                      const animRel = diag.animal_relation || 'unknown';
                      const nameA = user?.name || 'You';
                      const nameB = selectedMember?.member_name || 'Them';
                      const flowRows = EL.buildFlowRows(cycle, elA, elB, nameA, nameB);
                      const flowHeader = EL.flowHeaderForCycle(cycle);
                      const geo = EL.geometryArrow(cycle, elA, elB);
                      const animLabel = (animA && animB) ? EL.animalRelationLabel(animRel, animA, animB) : null;
                      const growthSub = EL.growthTriggerSubtitle(animRel);

                      const card = {
                        backgroundColor: theme.cardSurface || theme.surface || 'rgba(255,255,255,0.03)',
                        borderColor: theme.border, borderWidth: StyleSheet.hairlineWidth,
                        borderRadius: 10, padding: 12, marginTop: 10,
                      };
                      const tinyHeader = { fontSize: 11, fontWeight: '700' as const, letterSpacing: 1.0 };
                      const labelText  = { fontSize: 13, fontWeight: '600' as const, marginBottom: 2 };

                      return (
                        <View style={styles.lensSection}>
                          <Text style={[styles.signalsNote, { color: theme.textTertiary }]}>
                            ELEMENTAL DYNAMICS — Evidence
                          </Text>

                          {/* 1. ELEMENTAL STRUCTURE */}
                          <View style={card}>
                            <Text style={[tinyHeader, { color: theme.textTertiary, marginBottom: 8 }]}>1 · ELEMENTAL STRUCTURE</Text>
                            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 }}>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{nameA}</Text>
                              <Text style={[styles.lensSignalText, { color: theme.text, fontWeight: '600' }]}>{elA}</Text>
                            </View>
                            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 }}>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>{nameB}</Text>
                              <Text style={[styles.lensSignalText, { color: theme.text, fontWeight: '600' }]}>{elB}</Text>
                            </View>
                            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 }}>
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>Relationship Geometry</Text>
                              <Text style={[styles.lensSignalText, { color: theme.text, fontWeight: '600' }]}>{geo}</Text>
                            </View>
                            <Text style={[labelText, { color: theme.textTertiary }]}>{flowHeader}</Text>
                            {flowRows.length === 0 ? (
                              <Text style={[styles.lensSignalText, { color: theme.textSecondary, fontStyle: 'italic' }]}>
                                No automatic cycle — flow is built by agreement.
                              </Text>
                            ) : flowRows.map((r: any, i: number) => (
                              <View key={`fr-${i}`} style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 2 }}>
                                <Text style={[styles.lensSignalText, { color: theme.textSecondary, flexShrink: 1 }]} numberOfLines={2}>{r.left}</Text>
                                <Text style={[styles.lensSignalText, { color: theme.textTertiary, paddingHorizontal: 6 }]}>→</Text>
                                <Text style={[styles.lensSignalText, { color: theme.textSecondary, flexShrink: 1, textAlign: 'right' }]} numberOfLines={2}>{r.right}</Text>
                              </View>
                            ))}
                            {animLabel ? (
                              <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 10 }}>
                                <Text style={[styles.lensSignalText, { color: theme.textSecondary }]}>Year Animals</Text>
                                <Text style={[styles.lensSignalText, { color: theme.text }]}>{animLabel}</Text>
                              </View>
                            ) : null}
                          </View>

                          {/* 2. WHAT STRENGTHENS THE FLOW */}
                          {support.length > 0 ? (
                            <View style={card}>
                              <Text style={[tinyHeader, { color: theme.textTertiary, marginBottom: 8 }]}>2 · WHAT STRENGTHENS THE FLOW</Text>
                              {support.map((item: string, i: number) => (
                                <View key={`ev-s-${i}`} style={{ marginBottom: 8 }}>
                                  <View style={{ flexDirection: 'row' }}>
                                    <Text style={[styles.lensSignalIcon, { color: '#81C784' }]}>✓</Text>
                                    <Text style={[labelText, { color: theme.text, flexShrink: 1 }]}>{EL.labelFor(cycle, 'strengthen', i)}</Text>
                                  </View>
                                  <Text style={[styles.lensSignalText, { color: theme.textSecondary, paddingLeft: 18 }]}>{item}</Text>
                                </View>
                              ))}
                            </View>
                          ) : null}

                          {/* 3. GROWTH TRIGGER */}
                          {growth.length > 0 ? (
                            <View style={card}>
                              <Text style={[tinyHeader, { color: theme.textTertiary, marginBottom: 8 }]}>3 · GROWTH TRIGGER</Text>
                              {animA && animB ? (
                                <Text style={[labelText, { color: theme.text, marginBottom: 4 }]}>↑  {animA}  ↔  {animB}</Text>
                              ) : null}
                              <Text style={[styles.lensSignalText, { color: theme.textTertiary, fontStyle: 'italic', marginBottom: 8 }]}>{growthSub}</Text>
                              {growth.map((item: string, i: number) => (
                                <View key={`ev-g-${i}`} style={{ marginBottom: 8 }}>
                                  <View style={{ flexDirection: 'row' }}>
                                    <Text style={[styles.lensSignalIcon, { color: '#90CAF9' }]}>↑</Text>
                                    <Text style={[labelText, { color: theme.text, flexShrink: 1 }]}>{EL.labelFor(cycle, 'growth', i)}</Text>
                                  </View>
                                  <Text style={[styles.lensSignalText, { color: theme.textSecondary, paddingLeft: 18 }]}>{item}</Text>
                                </View>
                              ))}
                            </View>
                          ) : null}

                          {/* 4. SHADOW SIGNAL — hidden when tension is empty */}
                          {tension.length > 0 ? (
                            <View style={card}>
                              <Text style={[tinyHeader, { color: theme.textTertiary, marginBottom: 8 }]}>4 · SHADOW SIGNAL</Text>
                              {tension.map((item: string, i: number) => (
                                <View key={`ev-t-${i}`} style={{ marginBottom: 8 }}>
                                  <View style={{ flexDirection: 'row' }}>
                                    <Text style={[styles.lensSignalIcon, { color: '#CF6679' }]}>⚠</Text>
                                    <Text style={[labelText, { color: theme.text, flexShrink: 1 }]}>{EL.labelFor(cycle, 'shadow', i)}</Text>
                                  </View>
                                  <Text style={[styles.lensSignalText, { color: theme.textSecondary, paddingLeft: 18 }]}>{item}</Text>
                                </View>
                              ))}
                            </View>
                          ) : null}
                        </View>
                      );
                    })()}
                  </View>
                )}
              </View>
              );
            })()}

            {/* ───────────────────────────────────────────────── */}
            {/* RELATIONSHIP DIAGNOSTICS FOOTER — always visible   */}
            {/* relationship-mapping-diagnostics-footer-v1         */}
            {/* ───────────────────────────────────────────────── */}
            {(() => {
              const rel = (selectedMember as any)?.debug?.relationship_context || {};
              const v2 = (selectedMember as any)?.astrology_dynamics;
              const v2Has =
                !!(v2 && (v2.headline || (typeof v2.body === 'string' && v2.body.trim().length > 0)));
              const legacy = (selectedMember as any)?.signals?.astrology || {};
              const legacyHidden = !!legacy.legacy_hidden_due_to_v2;
              const activationSurface =
                (selectedMember as any).__diagActivationSurface || 'unknown';
              const role = rel.relationship_role || 'none';
              return (
                <View style={[styles.diagFooter, { borderTopColor: theme.border, backgroundColor: (theme.surfaceLight || theme.surface) + '80' }]}>
                  <Text style={[styles.diagFooterTitle, { color: theme.textTertiary }]}>
                    RELATIONSHIP DIAGNOSTICS
                  </Text>
                  <View style={styles.diagFooterRow}>
                    <Text style={[styles.diagFooterKey, { color: theme.textTertiary }]}>role</Text>
                    <Text style={[styles.diagFooterVal, { color: theme.textSecondary }]}>
                      {role}{rel.role_source ? `  ·  src:${rel.role_source}` : ''}
                    </Text>
                  </View>
                  <View style={styles.diagFooterRow}>
                    <Text style={[styles.diagFooterKey, { color: theme.textTertiary }]}>astrology_v2</Text>
                    <Text style={[styles.diagFooterVal, { color: v2Has ? '#81C784' : '#CF6679' }]}>
                      {v2Has ? 'rendered' : 'missing'}
                    </Text>
                  </View>
                  <View style={styles.diagFooterRow}>
                    <Text style={[styles.diagFooterKey, { color: theme.textTertiary }]}>legacy_hidden</Text>
                    <Text style={[styles.diagFooterVal, { color: legacyHidden ? '#81C784' : theme.textSecondary }]}>
                      {legacyHidden ? 'true' : 'false'}
                    </Text>
                  </View>
                  <View style={styles.diagFooterRow}>
                    <Text style={[styles.diagFooterKey, { color: theme.textTertiary }]}>duplicate_suppression</Text>
                    <Text style={[styles.diagFooterVal, { color: theme.textSecondary }]}>
                      {activationSurface}
                    </Text>
                  </View>
                </View>
              );
            })()}

            {/* BUILD MARKER — for deploy verification */}
            <Text style={[styles.buildMarker, { color: theme.textTertiary }]}>
              build · {BUILD_ID} · {BUILD_AT}
            </Text>
            <Text style={[styles.buildMarker, { color: theme.textTertiary, opacity: 0.55 }]}>
              relationship-mapping-diagnostics-footer-v1
              {(() => {
                const role = mapping?.debug?.relationship_context?.relationship_role;
                const hasV2 = !!mapping?.astrology_dynamics?.body;
                return role ? ` · role:${role}${hasV2 ? ' · v2:on' : ''}` : '';
              })()}
            </Text>

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

          {/* BUILD MARKER — for deploy verification */}
          <Text style={[styles.buildMarker, { color: theme.textTertiary }]}>
            build · {BUILD_ID} · {BUILD_AT}
          </Text>

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
  buildMarker: {
    fontSize: 10,
    textAlign: 'center',
    marginTop: 16,
    marginBottom: 8,
    opacity: 0.6,
    letterSpacing: 0.4,
  },
  diagFooter: {
    marginTop: 24,
    paddingTop: 12,
    paddingHorizontal: 12,
    paddingBottom: 12,
    borderTopWidth: 1,
    borderRadius: 8,
  },
  diagFooterTitle: {
    fontSize: 10,
    letterSpacing: 1.5,
    fontWeight: '600',
    marginBottom: 8,
  },
  diagFooterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingVertical: 3,
  },
  diagFooterKey: {
    fontSize: 11,
    fontFamily: 'monospace',
    flex: 0,
    minWidth: 140,
  },
  diagFooterVal: {
    fontSize: 11,
    fontFamily: 'monospace',
    flex: 1,
    textAlign: 'right',
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

  // ============================================================
  // Relationship Field Architecture v1 — additive styles
  // ============================================================
  fieldParagraph: {
    fontSize: 18,
    lineHeight: 32,
    fontWeight: '500',
  },
  activationChip: {
    paddingVertical: 14,
    paddingHorizontal: 18,
    borderRadius: 14,
    borderWidth: 1,
    marginBottom: 28,
  },
  activationLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 8,
  },
  activationText: {
    fontSize: 16,
    lineHeight: 26,
    fontWeight: '500',
  },
  themesSection: {
    marginBottom: 24,
  },
  themeCard: {
    padding: 18,
    borderRadius: 14,
    borderWidth: 1,
    marginBottom: 14,
  },
  themeLabel: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 8,
  },
  themeWhatLivesHere: {
    fontSize: 16,
    lineHeight: 28,
    marginBottom: 10,
  },
  themeFriction: {
    fontSize: 14,
    lineHeight: 24,
    fontStyle: 'italic',
    marginTop: 4,
  },
  giftCard: {
    padding: 18,
    borderRadius: 14,
    borderWidth: 1.5,
    marginBottom: 28,
  },
  giftLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 10,
  },
  giftText: {
    fontSize: 16,
    lineHeight: 28,
    fontWeight: '500',
  },
  amplifiersSection: {
    marginBottom: 20,
  },
  amplifierRow: {
    flexDirection: 'row',
    marginBottom: 12,
    paddingRight: 8,
  },
  amplifierPip: {
    fontSize: 18,
    marginRight: 10,
    marginTop: 2,
    width: 14,
    textAlign: 'center',
  },
  amplifierText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 24,
    fontStyle: 'italic',
  },
});
