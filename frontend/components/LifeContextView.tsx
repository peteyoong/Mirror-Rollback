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
} from '../services/api';
import { LifelineTimeline } from './lifeline';
import PeopleLens from './PeopleLens';
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

  // Load synthesis when the active context is one of the synthesis domains
  useEffect(() => {
    if (isSynthesisDomain(activeContext)) {
      loadSynthesis(activeContext);
    }
  }, [activeContext, loadSynthesis]);

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
  const renderSynthesisBlock = (synth: LifeSynthesisResponse | null) => {
    if (!synth) return null;
    const ds = synth.domain_synthesis;
    const rows: Array<{ label: string; body: string | null | undefined }> = [
      { label: "The Pattern You're In", body: ds?.pattern },
      { label: 'Default Tension', body: ds?.default_tension },
      { label: 'Distortion Under Pressure', body: ds?.distortion_under_pressure },
      { label: 'What This Pattern Needs', body: ds?.what_this_pattern_needs },
    ];
    return (
      <View style={styles.synthStack}>
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

  // Lifeline tab unchanged
  const renderLifelineTab = () => <LifelineTimeline userId={userId} />;

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
      <ScrollView
        style={styles.scrollContainer}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={handleRefresh} tintColor={theme.textTertiary} />
        }
      >
        {renderSynthesisBlock(synth)}

        {/* Relationships: keep People list below synthesis as clearly subordinate */}
        {domain === 'relationships' ? (
          <View style={styles.subordinateSection}>
            <Text style={[styles.subordinateLabel, { color: theme.textTertiary }]}>Your People</Text>
            {renderPeopleTabBody()}
          </View>
        ) : null}

        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: theme.textTertiary }]}>
            This isn&apos;t a rule. It&apos;s a pattern you can notice and work with.
          </Text>
        </View>
      </ScrollView>
    );
  };

  // Render role card globally above sub-tabs for synthesis domains — this
  // makes it the anchor of the Life tab, not just another accordion.
  const topRoleCard =
    isSynthesisDomain(activeContext)
      ? synthCache[activeContext]?.role_card || null
      : null;
  const topRoleLoading =
    isSynthesisDomain(activeContext) ? synthLoading[activeContext] && !topRoleCard : false;

  // Suppress the theme-unused warning and keep the conditional prepared for future use.
  void isDark;

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Anchor: The Role You're In — above the sub-tabs */}
      {isSynthesisDomain(activeContext) ? (
        <View style={styles.anchorWrap}>
          <RoleCard data={topRoleCard} loading={topRoleLoading} />
        </View>
      ) : null}

      {renderContextTabs()}

      {activeContext === 'lifeline' && renderLifelineTab()}
      {isSynthesisDomain(activeContext) && renderSynthesisTab(activeContext)}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  anchorWrap: {
    paddingTop: 8,
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
