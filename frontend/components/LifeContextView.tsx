import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import {
  getLifeContext,
  LifeContextResponse,
  LifeContextType,
  getLifeSynthesis,
  LifeSynthesisResponse,
  getLifeEvidence,
  LifeEvidenceResponse,
  getLifeToday,
  LifeTodayResponse,
  getLifePhases,
  LifePhase,
  LifePhaseGap,
} from '../services/api';
import { LifelineTimeline } from './lifeline';
import PeopleLens from './PeopleLens';
import PhaseTimeline from './PhaseTimeline';
import ReflectModal from './ReflectModal';
import AskAboutLifeModal from './AskAboutLifeModal';
import { AskLifeChip } from '../services/api';
import RoleCard from './RoleCard';

interface Props {
  userId: string;
  initialContext?: ExtendedContextType;
  onEventCountChange?: (count: number) => void;
}

// Sub-tab configuration — Lifeline kept; Relationships/Work/Self run on the
// new synthesis engine (Phase 1b).
const CONTEXT_CONFIG = {
  lifeline: {
    icon: 'time-outline' as const,
    label: 'Lifeline',
    description: 'Your story',
  },
  relationships: {
    icon: 'heart-outline' as const,
    label: 'Relationships',
    description: 'How you connect',
  },
  work: {
    icon: 'briefcase-outline' as const,
    label: 'Work',
    description: 'How you create',
  },
  self: {
    icon: 'person-outline' as const,
    label: 'Self',
    description: 'How you grow',
  },
};

type ExtendedContextType = LifeContextType | 'lifeline';

type SynthesisDomain = 'relationships' | 'work' | 'self';

const SYNTH_DOMAINS: ReadonlyArray<SynthesisDomain> = ['relationships', 'work', 'self'];

function isSynthesisDomain(ctx: ExtendedContextType): ctx is SynthesisDomain {
  return (SYNTH_DOMAINS as readonly string[]).includes(ctx);
}

export default function LifeContextView({
  userId,
  initialContext = 'lifeline',
  onEventCountChange: _onEventCountChange,
}: Props) {
  const { theme, isDark } = useTheme();
  const [activeContext, setActiveContext] = useState<ExtendedContextType>(initialContext);

  // Legacy data (kept as fallback for any future needs; not rendered)
  const [_legacyData, setLegacyData] = useState<LifeContextResponse | null>(null);

  // New synthesis state — one entry per domain, lazily hydrated
  const [synthCache, setSynthCache] = useState<Record<SynthesisDomain, LifeSynthesisResponse | null>>({
    relationships: null,
    work: null,
    self: null,
  });
  const [synthLoading, setSynthLoading] = useState<Record<SynthesisDomain, boolean>>({
    relationships: false,
    work: false,
    self: false,
  });
  const [synthError, setSynthError] = useState<Record<SynthesisDomain, string | null>>({
    relationships: null,
    work: null,
    self: null,
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Evidence Layer — lazy-loaded on expand
  const [evidenceExpanded, setEvidenceExpanded] = useState<Record<SynthesisDomain, boolean>>({
    relationships: false,
    work: false,
    self: false,
  });
  const [evidenceCache, setEvidenceCache] = useState<Record<SynthesisDomain, LifeEvidenceResponse | null>>({
    relationships: null,
    work: null,
    self: null,
  });
  const [evidenceLoading, setEvidenceLoading] = useState<Record<SynthesisDomain, boolean>>({
    relationships: false,
    work: false,
    self: false,
  });
  const [evidenceError, setEvidenceError] = useState<Record<SynthesisDomain, string | null>>({
    relationships: null,
    work: null,
    self: null,
  });

  // Today modulation — lazy; same 4 sections re-render with intensity modulation
  const [todayOn, setTodayOn] = useState<Record<SynthesisDomain, boolean>>({
    relationships: false,
    work: false,
    self: false,
  });
  const [todayCache, setTodayCache] = useState<Record<SynthesisDomain, LifeTodayResponse | null>>({
    relationships: null,
    work: null,
    self: null,
  });
  const [todayLoading, setTodayLoading] = useState<Record<SynthesisDomain, boolean>>({
    relationships: false,
    work: false,
    self: false,
  });
  const [todayError, setTodayError] = useState<Record<SynthesisDomain, string | null>>({
    relationships: null,
    work: null,
    self: null,
  });

  // Phase Timeline — one fetch per user, shared across the 3 synthesis tabs.
  const [phases, setPhases] = useState<LifePhase[] | null>(null);
  const [phasesLoading, setPhasesLoading] = useState<boolean>(false);
  const [phaseGap, setPhaseGap] = useState<LifePhaseGap | null>(null);

  // When the Phase Timeline "Add that moment" CTA is tapped we bump this
  // counter; LifelineTimeline picks it up via its `externalAddRequest` prop
  // and opens its Add Event editor with the suggested category prefilled.
  const [lifelineAddRequest, setLifelineAddRequest] = useState<{
    key: number;
    suggestedCategory?: string | null;
    source?: string;
  } | null>(null);

  // Reflect modal — quick thought capture from the Life synthesis stack.
  const [reflectOpen, setReflectOpen] = useState<boolean>(false);
  const [reflectDomain, setReflectDomain] = useState<SynthesisDomain>('self');

  // Ask About My Life modal — conversational interpreter
  const [askOpen, setAskOpen] = useState<boolean>(false);
  const [askInitialChip, setAskInitialChip] = useState<AskLifeChip>('self');

  const loadSynthesis = useCallback(async (
    domain: SynthesisDomain,
    opts?: { force?: boolean }
  ) => {
    const force = !!opts?.force;
    if (!force && synthCache[domain]) return;
    setSynthLoading((s) => ({ ...s, [domain]: true }));
    setSynthError((s) => ({ ...s, [domain]: null }));
    try {
      const resp = await getLifeSynthesis(domain, userId, force);
      setSynthCache((c) => ({ ...c, [domain]: resp }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to load this pattern right now.';
      console.error(`[LifeContextView] synth ${domain} error:`, err);
      setSynthError((s) => ({ ...s, [domain]: msg }));
    } finally {
      setSynthLoading((s) => ({ ...s, [domain]: false }));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  // Evidence loader — fires only when the user expands the accordion
  const loadEvidence = useCallback(async (
    domain: SynthesisDomain,
    opts?: { force?: boolean }
  ) => {
    const force = !!opts?.force;
    if (!force && evidenceCache[domain]) return;
    setEvidenceLoading((s) => ({ ...s, [domain]: true }));
    setEvidenceError((s) => ({ ...s, [domain]: null }));
    try {
      const resp = await getLifeEvidence(domain, userId, force);
      setEvidenceCache((c) => ({ ...c, [domain]: resp }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to load this right now.';
      console.error(`[LifeContextView] evidence ${domain} error:`, err);
      setEvidenceError((s) => ({ ...s, [domain]: msg }));
    } finally {
      setEvidenceLoading((s) => ({ ...s, [domain]: false }));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const toggleEvidence = useCallback((domain: SynthesisDomain) => {
    setEvidenceExpanded((s) => {
      const next = !s[domain];
      if (next && !evidenceCache[domain]) {
        // Fire on first expand
        loadEvidence(domain);
      }
      return { ...s, [domain]: next };
    });
  }, [evidenceCache, loadEvidence]);

  // Today modulation — toggle ON makes the 4 synthesis sections re-render
  // with intensity-aware modulation of the SAME pattern.
  const loadToday = useCallback(async (
    domain: SynthesisDomain,
    opts?: { force?: boolean }
  ) => {
    const force = !!opts?.force;
    if (!force && todayCache[domain]) return;
    setTodayLoading((s) => ({ ...s, [domain]: true }));
    setTodayError((s) => ({ ...s, [domain]: null }));
    try {
      const resp = await getLifeToday(domain, userId, force);
      setTodayCache((c) => ({ ...c, [domain]: resp }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to load today right now.';
      console.error(`[LifeContextView] today ${domain} error:`, err);
      setTodayError((s) => ({ ...s, [domain]: msg }));
    } finally {
      setTodayLoading((s) => ({ ...s, [domain]: false }));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const toggleToday = useCallback((domain: SynthesisDomain) => {
    setTodayOn((s) => {
      const next = !s[domain];
      if (next && !todayCache[domain]) {
        loadToday(domain);
      }
      return { ...s, [domain]: next };
    });
  }, [todayCache, loadToday]);

  // Load synthesis when the active context is one of the synthesis domains
  useEffect(() => {
    if (isSynthesisDomain(activeContext)) {
      loadSynthesis(activeContext);
    }
  }, [activeContext, loadSynthesis]);

  // Anchor pre-fetch: the RoleCard + PhaseTimeline live above the tabs and
  // must be populated even when the user is on the Lifeline sub-tab. We
  // prime the 'self' synthesis once on mount so the role card is ready
  // before the user switches into a synthesis domain.
  useEffect(() => {
    loadSynthesis('self');
  }, [loadSynthesis]);

  // Load phase timeline once when the user first lands on any synthesis tab.
  // Shared across work/relationships/self (same endpoint, user-level).
  const loadPhases = useCallback(async (opts?: { force?: boolean }) => {
    const force = !!opts?.force;
    if (!force && phases) return;
    setPhasesLoading(true);
    try {
      const resp = await getLifePhases(userId, force);
      setPhases(resp.phases || []);
      setPhaseGap(resp.phase_gap || null);
    } catch (err) {
      console.warn('[LifeContextView] phases fetch failed:', err);
      // Silent fail — the UI hides when phases are absent.
      setPhases([]);
      setPhaseGap(null);
    } finally {
      setPhasesLoading(false);
    }
  }, [userId, phases]);

  useEffect(() => {
    if (isSynthesisDomain(activeContext) && phases === null && !phasesLoading) {
      loadPhases();
    }
  }, [activeContext, phases, phasesLoading, loadPhases]);

  // Phases live above the tabs — always load them on mount so the
  // PhaseTimeline renders regardless of the active sub-tab.
  useEffect(() => {
    if (phases === null && !phasesLoading) {
      loadPhases();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  // Phase Timeline CTA — "Add that moment"
  // 1. Switches the sub-tab to Lifeline so the user lands exactly where
  //    the new event will live.
  // 2. Bumps `lifelineAddRequest.key` so LifelineTimeline opens its Add
  //    Event editor with the suggested category pre-filled.
  const DOMAIN_TO_CATEGORY: Record<string, string> = {
    work:          'Career',
    relationships: 'Relationships',
    self:          'Identity',
  };
  const handlePhaseAddMoment = useCallback(
    (ctx: { suggested_domain?: string | null }) => {
      const domain = (ctx?.suggested_domain || '').toLowerCase();
      const suggestedCategory = DOMAIN_TO_CATEGORY[domain] || null;
      // Switch to the Lifeline sub-tab so the editor opens in context
      setActiveContext('lifeline');
      // Bump the request — LifelineTimeline consumes this via useEffect
      setLifelineAddRequest(prev => ({
        key: (prev?.key || 0) + 1,
        suggestedCategory,
        source: 'phase_timeline',
      }));
    },
    []
  );

  // Legacy endpoint — only used if we ever need the old Overview/Today/Explore/Reflect
  // content. Currently unused by the UI but kept for potential fallback.
  useEffect(() => {
    if (activeContext === 'lifeline') return;
    if (!isSynthesisDomain(activeContext)) return;
    // (no-op — legacy fetch disabled in P1b)
    void _legacyData;
    void setLegacyData;
    void getLifeContext;
  }, [activeContext, userId]);

  const handleRefresh = async () => {
    if (!isSynthesisDomain(activeContext)) return;
    setIsRefreshing(true);
    try {
      await loadSynthesis(activeContext, { force: true });
    } finally {
      setIsRefreshing(false);
    }
  };

  const renderContextTabs = () => (
    <View style={[styles.contextTabsContainer, { backgroundColor: theme.background, borderBottomColor: theme.border }]}>
      {(Object.keys(CONTEXT_CONFIG) as ExtendedContextType[]).map((ctx) => {
        const config = CONTEXT_CONFIG[ctx];
        const isActive = activeContext === ctx;
        return (
          <TouchableOpacity
            key={ctx}
            style={styles.contextTab}
            onPress={() => setActiveContext(ctx)}
            activeOpacity={0.7}
          >
            <Ionicons
              name={config.icon}
              size={20}
              color={isActive ? theme.text : theme.textTertiary}
            />
            <Text style={[styles.contextTabLabel, { color: isActive ? theme.text : theme.textTertiary }]}>
              {config.label}
            </Text>
            {isActive && <View style={[styles.contextTabIndicator, { backgroundColor: theme.accent }]} />}
          </TouchableOpacity>
        );
      })}
    </View>
  );

  // Phase 1b synthesis rendering — strict section labels, no softening.
  // Phase 2 additions: a subordinate Today toggle that swaps in the
  // intensity-modulated version of the same 4 sections.
  const renderSynthesisBlock = (synth: LifeSynthesisResponse | null, domain: SynthesisDomain) => {
    if (!synth) return null;
    const ds = synth.domain_synthesis;
    const today = todayCache[domain];
    const on = todayOn[domain];
    const loading = todayLoading[domain];

    // Use today values when toggled on and loaded; otherwise base synthesis
    const source = on && today ? {
      pattern: today.pattern,
      default_tension: today.default_tension,
      distortion_under_pressure: today.distortion_under_pressure,
      what_this_pattern_needs: today.what_this_pattern_needs,
    } : ds;

    const intensityLabel = today?.intensity_level;
    const intensityColor =
      intensityLabel === 'high'   ? '#e08c3a' :
      intensityLabel === 'medium' ? theme.accent :
                                    theme.textTertiary;

    const rows: Array<{ label: string; body: string | null | undefined }> = [
      { label: "The Pattern You're In", body: source?.pattern },
      { label: 'Default Tension', body: source?.default_tension },
      { label: 'Distortion Under Pressure', body: source?.distortion_under_pressure },
      { label: 'What This Pattern Needs', body: source?.what_this_pattern_needs },
    ];

    return (
      <View style={styles.synthStack}>
        {/* Today toggle — subordinate to the synthesis, never competing */}
        <TouchableOpacity
          style={[styles.todayToggle, {
            backgroundColor: on ? theme.accent + '15' : theme.surface,
            borderColor: on ? theme.accent + '60' : theme.border,
          }]}
          onPress={() => toggleToday(domain)}
          activeOpacity={0.8}
        >
          <View style={styles.todayToggleLeft}>
            <Ionicons
              name={on ? 'sunny' : 'sunny-outline'}
              size={14}
              color={on ? theme.accent : theme.textTertiary}
            />
            <Text style={[styles.todayToggleLabel, {
              color: on ? theme.accent : theme.textTertiary,
            }]}>
              {on ? 'Showing today' : 'How this pattern is showing up today'}
            </Text>
          </View>
          {on && loading ? (
            <ActivityIndicator size="small" color={theme.accent} />
          ) : on && intensityLabel ? (
            <Text style={[styles.todayIntensity, { color: intensityColor }]}>
              {intensityLabel.toUpperCase()}
            </Text>
          ) : (
            <Ionicons name="chevron-forward" size={14} color={theme.textTertiary} />
          )}
        </TouchableOpacity>

        {rows.map((row) => {
          if (!row.body) return null;
          return (
            <View
              key={row.label}
              style={[styles.synthSection, { backgroundColor: theme.surface, borderColor: theme.border }]}
            >
              <Text style={[styles.synthLabel, { color: theme.textTertiary }]}>{row.label}</Text>
              <Text style={[styles.synthBody, { color: theme.text }]}>{row.body}</Text>
            </View>
          );
        })}
      </View>
    );
  };

  // Evidence expander — "Why this is showing up"
  const renderEvidenceExpander = (domain: SynthesisDomain) => {
    const expanded = evidenceExpanded[domain];
    const ev = evidenceCache[domain];
    const loading = evidenceLoading[domain];
    const err = evidenceError[domain];

    return (
      <View style={styles.evidenceWrap}>
        <TouchableOpacity
          style={[
            styles.evidenceHeader,
            { backgroundColor: theme.surface, borderColor: theme.border },
          ]}
          onPress={() => toggleEvidence(domain)}
          activeOpacity={0.7}
        >
          <Text style={[styles.evidenceHeaderLabel, { color: theme.textTertiary }]}>
            Why this is showing up
          </Text>
          <Ionicons
            name={expanded ? 'chevron-up' : 'chevron-down'}
            size={16}
            color={theme.textTertiary}
          />
        </TouchableOpacity>

        {expanded ? (
          <View style={[styles.evidenceBody, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            {loading && !ev ? (
              <View style={styles.evidenceLoading}>
                <ActivityIndicator size="small" color={theme.textTertiary} />
                <Text style={[styles.evidenceLoadingText, { color: theme.textTertiary }]}>
                  Finding the signals…
                </Text>
              </View>
            ) : err && !ev ? (
              <Text style={[styles.evidenceError, { color: theme.textSecondary }]}>{err}</Text>
            ) : ev && Array.isArray(ev.evidence) && ev.evidence.length > 0 ? (
              <View style={styles.evidenceList}>
                {ev.evidence.map((item, i) => (
                  <View key={`${domain}-ev-${i}`} style={styles.evidenceItem}>
                    <Text style={[styles.evidenceTitle, { color: theme.text }]}>
                      {item.title}
                    </Text>
                    <Text style={[styles.evidenceExplanation, { color: theme.textSecondary }]}>
                      {item.explanation}
                    </Text>
                  </View>
                ))}
              </View>
            ) : (
              <Text style={[styles.evidenceError, { color: theme.textTertiary }]}>
                No strong signals available yet.
              </Text>
            )}
          </View>
        ) : null}
      </View>
    );
  };
  const renderLifelineTab = () => (
    <View>
      {/* PhaseTimeline now lives inside Lifeline — it is part of the
          story experience, not a global anchor across all tabs. */}
      <View style={styles.phaseTimelineWrap}>
        <PhaseTimeline
          phases={phases}
          phaseGap={phaseGap}
          loading={phasesLoading && (phases === null || phases.length === 0)}
          onAddMoment={handlePhaseAddMoment}
        />
      </View>
      <LifelineTimeline
        userId={userId}
        externalAddRequest={lifelineAddRequest}
        embedded
      />
    </View>
  );

  // People tab — kept AS SUBORDINATE under the synthesis on Relationships
  const renderPeopleTabBody = () => (
    <PeopleLens
      userId={userId}
      theme={{
        background: theme.background,
        surface: theme.surface,
        text: theme.text,
        textSecondary: theme.textSecondary,
        textTertiary: theme.textTertiary,
        accent: theme.accent,
        border: theme.border,
      }}
    />
  );

  const renderSynthesisTab = (domain: SynthesisDomain) => {
    const synth = synthCache[domain];
    const loading = synthLoading[domain];
    const err = synthError[domain];

    // Show loader only when nothing is cached yet
    if (loading && !synth) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.textTertiary} />
          <Text style={[styles.loadingText, { color: theme.text }]}>Reading the pattern…</Text>
          <Text style={[styles.loadingSubtext, { color: theme.textTertiary }]}>One moment.</Text>
        </View>
      );
    }

    if (err && !synth) {
      return (
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={44} color={theme.textTertiary} />
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>{err}</Text>
          <TouchableOpacity
            style={[styles.retryButton, { backgroundColor: theme.surface, borderColor: theme.border }]}
            onPress={() => loadSynthesis(domain, { force: true })}
          >
            <Text style={[styles.retryButtonText, { color: theme.text }]}>Try Again</Text>
          </TouchableOpacity>
        </View>
      );
    }

    return (
      <View style={styles.synthTabBody}>
        {renderSynthesisBlock(synth, domain)}

        {/* Reflect — quick thought capture (NOT a Lifeline event) */}
        <TouchableOpacity
          activeOpacity={0.7}
          onPress={() => {
            setReflectDomain(domain);
            setReflectOpen(true);
          }}
          hitSlop={6}
          style={[
            styles.reflectBtn,
            { borderColor: theme.border },
          ]}
        >
          <Text style={[styles.reflectBtnText, { color: theme.text }]}>
            ✨ Reflect
          </Text>
        </TouchableOpacity>

        {/* Why this is showing up — lazy-loaded evidence expander */}
        {synth ? renderEvidenceExpander(domain) : null}

        {/* NOTE: The "People in your life" / Add Person block was removed
            from this tab. People mapping happens elsewhere (Forum / People
            setup) where birth data can be properly captured. */}

        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: theme.textTertiary }]}>
            This isn&apos;t a rule. It&apos;s a pattern you can notice and work with.
          </Text>
        </View>
      </View>
    );
  };

  // Render role card globally above sub-tabs — must be visible on EVERY
  // tab, including Lifeline. Falls back across cached domains so the card
  // still shows even if the user has only loaded one synthesis tab.
  const topRoleCard =
    (isSynthesisDomain(activeContext) ? synthCache[activeContext]?.role_card : null) ||
    synthCache.self?.role_card ||
    synthCache.work?.role_card ||
    synthCache.relationships?.role_card ||
    null;
  const topRoleLoading =
    !topRoleCard && (
      synthLoading.self ||
      synthLoading.work ||
      synthLoading.relationships ||
      (isSynthesisDomain(activeContext) && synthLoading[activeContext])
    );

  // Suppress the theme-unused warning and keep the conditional prepared for future use.
  void isDark;

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <ScrollView
        style={styles.outerScroll}
        contentContainerStyle={styles.outerScrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        refreshControl={
          isSynthesisDomain(activeContext) ? (
            <RefreshControl
              refreshing={isRefreshing}
              onRefresh={handleRefresh}
              tintColor={theme.textTertiary}
            />
          ) : undefined
        }
      >
        {/* Anchor block — RoleCard + Ask + PhaseTimeline.
            Renders unconditionally so the user always has the role
            context, the conversational entry point, and the phase
            timeline visible regardless of the active sub-tab. */}
        <View style={styles.anchorWrap}>
          <RoleCard data={topRoleCard} loading={topRoleLoading} />

          {/* Ask About My Life — conversational entry point */}
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => {
              const chip: AskLifeChip = isSynthesisDomain(activeContext)
                ? (activeContext as AskLifeChip)
                : 'self';
              setAskInitialChip(chip);
              setAskOpen(true);
            }}
            style={[
              styles.askPill,
              { backgroundColor: theme.text },
            ]}
            hitSlop={6}
          >
            <Text style={[styles.askPillText, { color: theme.background }]}>
              💬 Ask about my life
            </Text>
          </TouchableOpacity>
        </View>

        {renderContextTabs()}

        {activeContext === 'lifeline' && renderLifelineTab()}
        {isSynthesisDomain(activeContext) && renderSynthesisTab(activeContext)}
      </ScrollView>

      {/* Reflect modal — mounted once, opened from any synthesis tab.
          Uses the current phase (from the Phase Timeline data) to enrich
          the saved reflection with phase_label and pattern_hint. */}
      <ReflectModal
        visible={reflectOpen}
        onClose={() => setReflectOpen(false)}
        userId={userId}
        domain={reflectDomain}
        phaseLabel={
          (phases || []).find(p => p.is_current)?.label || null
        }
        patternHint={
          (phases || []).find(p => p.is_current)?.pattern_expression || null
        }
      />

      {/* Ask About My Life — full-screen conversational modal */}
      <AskAboutLifeModal
        visible={askOpen}
        onClose={() => setAskOpen(false)}
        userId={userId}
        initialDomain={askInitialChip}
        phaseLabel={
          (phases || []).find(p => p.is_current)?.label || null
        }
        patternHint={
          (phases || []).find(p => p.is_current)?.pattern_expression || null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  outerScroll: {
    flex: 1,
  },
  outerScrollContent: {
    flexGrow: 1,
    paddingBottom: 160,
  },
  anchorWrap: {
    paddingTop: 8,
  },
  phaseTimelineWrap: {
    maxHeight: 220,
    overflow: 'hidden',
  },
  synthTabBody: {
    paddingTop: 4,
    paddingBottom: 16,
  },
  contextTabsContainer: {
    flexDirection: 'row',
    borderBottomWidth: StyleSheet.hairlineWidth,
    paddingHorizontal: 8,
  },
  contextTab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    gap: 4,
    position: 'relative',
  },
  contextTabLabel: {
    fontSize: 12,
    fontWeight: '500',
  },
  contextTabIndicator: {
    position: 'absolute',
    bottom: 0,
    height: 2,
    width: 28,
    borderRadius: 1,
  },
  scrollContainer: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 80,
    paddingTop: 4,
  },
  // Loading / error
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    gap: 12,
  },
  loadingText: {
    fontSize: 16,
    marginTop: 8,
  },
  loadingSubtext: {
    fontSize: 13,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    gap: 16,
  },
  errorText: {
    fontSize: 15,
    textAlign: 'center',
  },
  retryButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
  },
  retryButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  // Synthesis block
  synthStack: {
    paddingHorizontal: 16,
    gap: 10,
  },
  synthSection: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  synthLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  synthBody: {
    fontSize: 15,
    lineHeight: 23,
  },
  // Subordinate block (People inside Relationships)
  subordinateSection: {
    marginTop: 24,
    paddingTop: 12,
    paddingHorizontal: 0,
  },
  subordinateLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  // Evidence expander — "Why this is showing up"
  evidenceWrap: {
    marginTop: 14,
    paddingHorizontal: 16,
  },
  evidenceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
  },
  evidenceHeaderLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  evidenceBody: {
    marginTop: 6,
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
  },
  evidenceLoading: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  evidenceLoadingText: {
    fontSize: 13,
  },
  evidenceError: {
    fontSize: 13,
  },
  evidenceList: {
    gap: 14,
  },
  evidenceItem: {
    gap: 4,
  },
  evidenceTitle: {
    fontSize: 14,
    fontWeight: '600',
    lineHeight: 20,
  },
  evidenceExplanation: {
    fontSize: 13,
    lineHeight: 20,
  },
  // Footer
  footer: {
    paddingHorizontal: 24,
    paddingVertical: 24,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  // Reflect button — quick thought-capture CTA at the bottom of the
  // synthesis stack (above the "Why this is showing up" expander).
  reflectBtn: {
    alignSelf: 'center',
    marginTop: 18,
    marginBottom: 4,
    paddingHorizontal: 22,
    paddingVertical: 10,
    borderRadius: 22,
    borderWidth: StyleSheet.hairlineWidth,
  },
  reflectBtnText: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  // Ask About My Life — primary CTA pill below the role card
  askPill: {
    alignSelf: 'center',
    marginTop: 12,
    paddingHorizontal: 22,
    paddingVertical: 10,
    borderRadius: 22,
  },
  askPillText: {
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  // Today toggle — subordinate bar above the synthesis stack
  todayToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 2,
  },
  todayToggleLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flex: 1,
  },
  todayToggleLabel: {
    fontSize: 12,
    fontWeight: '500',
    flex: 1,
  },
  todayIntensity: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
  },
  // Kept so legacy references compile if referenced elsewhere
  headerContainer: {
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.text,
  },
  contextDescription: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginTop: 4,
  },
  sectionsContainer: {
    padding: 16,
  },
  sectionContainer: {
    marginBottom: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  sectionContent: {
    paddingTop: 8,
  },
  sectionBody: {
    fontSize: 14,
    lineHeight: 22,
    color: Colors.text,
  },
});
