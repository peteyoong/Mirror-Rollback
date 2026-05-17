/**
 * Relationship Profile page — v0.1.
 *
 * Lives at `/people/[id]`. This is the one-to-one private relational
 * mirror for a saved person. It is INTENTIONALLY NOT a forum page —
 * no group dynamics, no live field, no room language.
 *
 * v0.1 design constraints (per product spec, May 2026):
 *   * Lightweight + deterministic synthesis only. No AI prose.
 *   * Tone: recognition-first, grounded, Mirror voice.
 *   * Layout: header card · relationship synthesis · pattern cards ·
 *     "what this is based on" accordion · "enhance profile" panel.
 *   * Optional enhancements (full_birth_name, manual enneagram) are
 *     NEVER required and never block save.
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { useTheme } from '../../contexts/ThemeContext';
import { BUILD_ID } from '../../constants/buildMarker';
import {
  formatRelationshipType,
  friendlyPeopleError,
  getSavedPerson,
  precisionLabel,
  SavedPerson,
  updateSavedPerson,
} from '../../services/people';
import { useAppStore } from '../../store';

// ---------------------------------------------------------------------------
// v0.1 Deterministic synthesis
// ---------------------------------------------------------------------------
// Mapping is intentionally small: precision_level + relationship_type
// generate the "What feels natural / Where friction / What this tends
// to revolve around" lines. No LLM. No personalised birth-chart logic
// yet — that's the next iteration. The lines are written in Mirror's
// recognition-first voice so they feel grounded, not generic.
// ---------------------------------------------------------------------------

type Synthesis = {
  natural: string;
  friction: string;
  revolves: string;
};

const SYNTHESIS_BY_TYPE: Record<string, Synthesis> = {
  partner: {
    natural: 'A shared sense of inner life, a willingness to keep returning even when it feels uncomfortable.',
    friction: 'When one of you starts contracting to keep the peace, the other often feels the silence first.',
    revolves: 'The rhythm of moving close and stepping back. Whether closeness is felt as safety or as pressure on any given week.',
  },
  spouse: {
    natural: 'A long-arc trust that the relationship will hold even when each of you changes shape.',
    friction: 'When one of you starts performing the relationship instead of being in it.',
    revolves: 'Decisions about time, resources, and direction — and whether those decisions feel mutual or arrived at alone.',
  },
  ex_partner: {
    natural: 'A surprising amount of recognition still passes between you — the residue of what was real.',
    friction: 'When you confuse who they were with who they are now, or vice versa.',
    revolves: 'What remains useful between you — and what asks to be acknowledged so it can finally settle.',
  },
  parent: {
    natural: 'A long line of conditioning that shaped how safety, performance and worth feel for you.',
    friction: 'Patterns you inherited that still run when you are tired, stressed or being seen.',
    revolves: 'The work of separating what was theirs from what is yours, without erasing them in the process.',
  },
  child: {
    natural: 'A natural attentiveness to who they are becoming, distinct from who you wanted them to be.',
    friction: 'When your own unfinished business shows up as expectation, pressure or over-protection.',
    revolves: 'Holding presence without holding control. Letting them feel both safe and free.',
  },
  sibling: {
    natural: 'A shared origin story that no one else carries in quite the same way.',
    friction: 'Old roles you both unconsciously slip back into when you spend too much time in the family system.',
    revolves: 'Renegotiating the relationship as adults rather than as the children you both used to be.',
  },
  family_other: {
    natural: 'A shared field of history and obligation — quieter than parent or sibling, but still present.',
    friction: 'When family expectations bleed into your one-on-one with them.',
    revolves: 'How much of the wider family system you each agree to carry, and what you decline to.',
  },
  friend: {
    natural: 'A reliable mutual recognition — they tend to see you accurately even when you don\'t.',
    friction: 'When one of you grows quickly and the other is still relating to who you used to be.',
    revolves: 'The quality of presence between you, not the frequency of contact.',
  },
  close_friend: {
    natural: 'A trust that holds even when months pass between conversations.',
    friction: 'When unspoken needs accumulate and the next conversation has to carry too much.',
    revolves: 'Telling each other the truth before it becomes a story you have to apologise for later.',
  },
  colleague: {
    natural: 'A working alignment around what good looks like and how decisions get made.',
    friction: 'When personal style gets confused with professional judgement.',
    revolves: 'Earning each other\'s default trust so disagreements stay about the work, not about each other.',
  },
  boss: {
    natural: 'A clarity about what they need from you and where the boundaries actually sit.',
    friction: 'When their stress quietly becomes your scope.',
    revolves: 'How visible your work is — and whether that visibility serves you or just protects them.',
  },
  report: {
    natural: 'A felt sense of psychological safety — they can name a problem without needing to manage you first.',
    friction: 'When you confuse coaching them with rescuing them.',
    revolves: 'Their growth, on their timeline, with your honest read of their patterns.',
  },
  client: {
    natural: 'A clear contract about what is being exchanged and on what terms.',
    friction: 'When unspoken expectations on either side stretch the agreement quietly.',
    revolves: 'Whether the work serves their actual need or just the brief they brought you.',
  },
  mentor: {
    natural: 'A field where you can ask the questions you wouldn\'t ask anywhere else.',
    friction: 'When you outgrow the relationship before either of you admits it.',
    revolves: 'What you take seriously from them, and what you have already moved past.',
  },
  mentee: {
    natural: 'A position where your example does more work than your advice.',
    friction: 'When you give them your conclusions before they have done the asking.',
    revolves: 'How much you let them figure out for themselves vs. shortcut.',
  },
  other: {
    natural: 'A specific resonance that doesn\'t fit any standard label — which is often the most useful kind.',
    friction: 'When you try to make this relationship behave like a category it doesn\'t belong to.',
    revolves: 'Whatever you are both quietly trying to learn from being near each other.',
  },
};

const PATTERN_CARDS = [
  {
    key: 'communication',
    title: 'Communication style',
    body: 'Notice whether they default to clarity, warmth, intensity or precision when something matters.',
  },
  {
    key: 'emotional',
    title: 'Emotional style',
    body: 'Notice whether emotions arrive as a wave, a pause, a sharpening, or a quiet leak.',
  },
  {
    key: 'decision',
    title: 'Decision style',
    body: 'Notice whether they decide from gut, from sense-making, from consensus, or from a slow inner read.',
  },
  {
    key: 'pressure',
    title: 'Pressure pattern',
    body: 'Notice what they do when under pressure — and how that differs from who they are when rested.',
  },
];

// ---------------------------------------------------------------------------
// Screen
// ---------------------------------------------------------------------------

export default function RelationshipProfileScreen() {
  const { theme, isDark } = useTheme();
  const router = useRouter();
  const params = useLocalSearchParams<{ id: string }>();
  const personId = String(params.id || '');
  const user = useAppStore((s) => s.user);

  const [person, setPerson] = useState<SavedPerson | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showEvidence, setShowEvidence] = useState(false);

  // Enhance Profile fields — locally edited, saved on demand.
  const [fullBirthName, setFullBirthName] = useState('');
  const [enneagramType, setEnneagramType] = useState('');
  const [savingEnhance, setSavingEnhance] = useState(false);
  const [enhanceMsg, setEnhanceMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!user?.id || !personId) return;
    setLoading(true);
    setError(null);
    try {
      const p = await getSavedPerson(user.id, personId);
      setPerson(p);
      setFullBirthName(p.full_birth_name ?? '');
      setEnneagramType(p.enneagram_type ?? '');
    } catch (e) {
      console.error('[ProfilePage] load error:', e);
      setError(friendlyPeopleError(e));
    } finally {
      setLoading(false);
    }
  }, [user?.id, personId]);

  useEffect(() => { load(); }, [load]);

  const synthesis: Synthesis = useMemo(() => {
    return SYNTHESIS_BY_TYPE[person?.relationship_type ?? 'other'] ?? SYNTHESIS_BY_TYPE.other;
  }, [person?.relationship_type]);

  const availableLenses = useMemo(() => {
    if (!person) return [];
    const lenses: string[] = [];
    // Astrology: needs at least date + (verified location OR exact time)
    if (person.birth_date) lenses.push('Astrology');
    // Human Design needs the same.
    if (person.birth_date && person.birth_time_accuracy === 'exact') {
      lenses.push('Human Design');
    }
    // Numerology: just the birth date is enough at v0.1.
    if (person.birth_date) lenses.push('Numerology');
    // Enneagram: only when user has provided a manual type.
    if (person.enneagram_type) lenses.push('Enneagram');
    return lenses;
  }, [person]);

  const handleSaveEnhance = useCallback(async () => {
    if (!user?.id || !personId) return;
    setSavingEnhance(true);
    setEnhanceMsg(null);
    try {
      const trimmedName = fullBirthName.trim();
      const trimmedEnn = enneagramType.trim();
      const patch: any = {
        full_birth_name: trimmedName.length > 0 ? trimmedName : null,
        enneagram_type: trimmedEnn.length > 0 ? trimmedEnn : null,
        enneagram_source: trimmedEnn.length > 0 ? 'manual' : null,
      };
      const updated = await updateSavedPerson(user.id, personId, patch);
      setPerson(updated);
      setEnhanceMsg('Saved.');
      setTimeout(() => setEnhanceMsg(null), 2000);
    } catch (e) {
      console.error('[ProfilePage] enhance save error:', e);
      Alert.alert('Could not save', friendlyPeopleError(e));
    } finally {
      setSavingEnhance(false);
    }
  }, [user?.id, personId, fullBirthName, enneagramType]);

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.loadingCenter}>
          <ActivityIndicator color={theme.text} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>Loading profile…</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error || !person) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.loadingCenter}>
          <Text style={[styles.errorText, { color: theme.text }]}>
            {error || 'Profile not found.'}
          </Text>
          <TouchableOpacity onPress={load} style={styles.retryButton}>
            <Text style={[styles.retryText, { color: theme.accent }]}>Try again</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const precInfo = precisionLabel(person.precision_level);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 80 : 0}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => router.push(`/people/wizard?id=${personId}` as any)} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Text style={[styles.editText, { color: theme.accent }]}>Edit</Text>
          </TouchableOpacity>
        </View>

        <ScrollView
          style={styles.content}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* A — Snapshot card */}
          <View style={[styles.snapshotCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.personName, { color: theme.text }]}>{person.name}</Text>
            <Text style={[styles.personType, { color: theme.textSecondary }]}>
              {formatRelationshipType(person.relationship_type)}
            </Text>
            <View style={styles.snapshotRows}>
              <SnapshotRow label="Born" value={person.birth_date} theme={theme} />
              <SnapshotRow
                label="Time"
                value={person.birth_time_accuracy === 'exact' ? (person.birth_time || '—') : 'Unknown'}
                theme={theme}
              />
              <SnapshotRow
                label="Place"
                value={
                  person.birth_location_accuracy === 'exact' && person.birth_location
                    ? `${person.birth_location.city}, ${person.birth_location.country}`
                    : 'Unknown'
                }
                theme={theme}
              />
              <SnapshotRow label="Precision" value={precInfo.label} theme={theme} />
            </View>
            {availableLenses.length > 0 && (
              <View style={styles.lensRow}>
                {availableLenses.map((l) => (
                  <View key={l} style={[styles.lensChip, { borderColor: theme.border, backgroundColor: theme.background }]}>
                    <Text style={[styles.lensChipText, { color: theme.textSecondary }]}>{l}</Text>
                  </View>
                ))}
              </View>
            )}
          </View>

          {/* B — Relationship synthesis */}
          <Text style={[styles.sectionTitle, { color: theme.text }]}>How this person maps to you</Text>
          <View style={[styles.synthesisBlock, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <SynthesisRow label="What feels natural" body={synthesis.natural} theme={theme} />
            <SynthesisRow label="Where friction may emerge" body={synthesis.friction} theme={theme} />
            <SynthesisRow label="What this tends to revolve around" body={synthesis.revolves} theme={theme} last />
          </View>

          {/* C — Person pattern cards */}
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Patterns to notice</Text>
          <View style={styles.patternList}>
            {PATTERN_CARDS.map((p) => (
              <View key={p.key} style={[styles.patternCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                <Text style={[styles.patternTitle, { color: theme.text }]}>{p.title}</Text>
                <Text style={[styles.patternBody, { color: theme.textSecondary }]}>{p.body}</Text>
              </View>
            ))}
          </View>

          {/* D — Why this is showing up accordion */}
          <TouchableOpacity
            style={[styles.evidenceToggle, { borderColor: theme.border }]}
            onPress={() => setShowEvidence((v) => !v)}
            activeOpacity={0.7}
          >
            <Text style={[styles.evidenceToggleText, { color: theme.textSecondary }]}>
              {showEvidence ? '▾ ' : '▸ '}What this is based on
            </Text>
          </TouchableOpacity>
          {showEvidence && (
            <View style={[styles.evidencePanel, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <EvidenceLine label="Human Design"
                body={person.birth_time_accuracy === 'exact'
                  ? 'Exact birth time available — energy type and inner authority can be computed.'
                  : 'Birth time unknown — HD type can\'t be locked in without it.'} theme={theme} />
              <EvidenceLine label="Astrology"
                body={person.birth_location_accuracy === 'exact'
                  ? 'Birth date + verified location — sidereal placements available.'
                  : 'Location unverified — placements will be approximate.'} theme={theme} />
              <EvidenceLine label="Numerology"
                body={person.full_birth_name
                  ? `Full birth name on file — deeper number patterns unlocked.`
                  : 'Add full birth name below to unlock deeper number patterns.'} theme={theme} />
              <EvidenceLine label="Enneagram"
                body={person.enneagram_type
                  ? `Manually set to ${person.enneagram_type}. Mirror uses this as a soft hint, not a verdict.`
                  : 'No type set. Add one below if you already know theirs.'} theme={theme} last />
            </View>
          )}

          {/* Enhance Profile */}
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Enhance profile</Text>
          <Text style={[styles.sectionSubtitle, { color: theme.textTertiary }]}>
            Optional. These deepen the read without ever being required.
          </Text>

          <View style={[styles.enhanceBlock, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>Full birth name</Text>
            <TextInput
              style={[styles.input, { borderColor: theme.border, color: theme.text, backgroundColor: theme.background }]}
              value={fullBirthName}
              onChangeText={setFullBirthName}
              placeholder="As on their birth certificate"
              placeholderTextColor={theme.textTertiary}
              autoCapitalize="words"
              autoComplete="off"
              autoCorrect={false}
              maxLength={200}
            />
            <Text style={[styles.fieldHint, { color: theme.textTertiary }]}>
              For richer numerology only. Skip if you don\u2019t know it.
            </Text>

            <Text style={[styles.fieldLabel, { color: theme.textSecondary, marginTop: 16 }]}>Enneagram type</Text>
            <TextInput
              style={[styles.input, { borderColor: theme.border, color: theme.text, backgroundColor: theme.background }]}
              value={enneagramType}
              onChangeText={setEnneagramType}
              placeholder="e.g. 7w8, 3w2, 5w4"
              placeholderTextColor={theme.textTertiary}
              autoCapitalize="none"
              autoComplete="off"
              autoCorrect={false}
              maxLength={10}
            />
            <Text style={[styles.fieldHint, { color: theme.textTertiary }]}>
              Manual only. No assessment required.
            </Text>

            <TouchableOpacity
              onPress={handleSaveEnhance}
              disabled={savingEnhance}
              style={[styles.saveEnhanceBtn, { backgroundColor: theme.buttonPrimaryBg }, savingEnhance && { opacity: 0.6 }]}
              accessibilityRole="button"
              accessibilityLabel="Save enhancement"
            >
              {savingEnhance
                ? <ActivityIndicator color={theme.buttonPrimaryText} />
                : <Text style={[styles.saveEnhanceText, { color: theme.buttonPrimaryText }]}>Save enhancement</Text>}
            </TouchableOpacity>
            {enhanceMsg && (
              <Text style={[styles.enhanceMsg, { color: theme.success ?? '#1f9d55' }]}>{enhanceMsg}</Text>
            )}
          </View>

          {/* Build marker footer — keeps in line with other hotfix screens
              so users on deployed Safari can spot stale bundles. */}
          <Text style={[styles.buildMarker, { color: theme.textTertiary }]}>{BUILD_ID}</Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SnapshotRow({ label, value, theme }: { label: string; value: string; theme: any }) {
  return (
    <View style={styles.snapRow}>
      <Text style={[styles.snapLabel, { color: theme.textTertiary }]}>{label}</Text>
      <Text style={[styles.snapValue, { color: theme.text }]} numberOfLines={1}>{value}</Text>
    </View>
  );
}

function SynthesisRow({ label, body, theme, last }: { label: string; body: string; theme: any; last?: boolean }) {
  return (
    <View style={[styles.synthRow, last ? null : { borderBottomColor: theme.border, borderBottomWidth: StyleSheet.hairlineWidth }]}>
      <Text style={[styles.synthLabel, { color: theme.textTertiary }]}>{label.toUpperCase()}</Text>
      <Text style={[styles.synthBody, { color: theme.text }]}>{body}</Text>
    </View>
  );
}

function EvidenceLine({ label, body, theme, last }: { label: string; body: string; theme: any; last?: boolean }) {
  return (
    <View style={[styles.evidenceRow, last ? null : { borderBottomColor: theme.border, borderBottomWidth: StyleSheet.hairlineWidth }]}>
      <Text style={[styles.evidenceLabel, { color: theme.textSecondary }]}>{label}</Text>
      <Text style={[styles.evidenceBody, { color: theme.textTertiary }]}>{body}</Text>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: { flex: 1 },
  loadingCenter: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10 },
  loadingText: { fontSize: 14 },
  errorText: { fontSize: 15, textAlign: 'center', paddingHorizontal: 24 },
  retryButton: { paddingVertical: 8, paddingHorizontal: 16, marginTop: 8 },
  retryText: { fontSize: 14, fontWeight: '500' },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 8,
  },
  backText: { fontSize: 15, fontWeight: '500' },
  editText: { fontSize: 15, fontWeight: '500' },

  content: { flex: 1 },
  scrollContent: { paddingHorizontal: 20, paddingBottom: 40 },

  snapshotCard: { borderRadius: 14, borderWidth: 1, padding: 16, marginTop: 8, marginBottom: 24 },
  personName: { fontSize: 22, fontWeight: '700', letterSpacing: -0.3 },
  personType: { fontSize: 14, marginTop: 2 },
  snapshotRows: { marginTop: 16, gap: 8 },
  snapRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  snapLabel: { fontSize: 12, fontWeight: '600', letterSpacing: 1, textTransform: 'uppercase' },
  snapValue: { fontSize: 14, flex: 1, textAlign: 'right', marginLeft: 12 },
  lensRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 16 },
  lensChip: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999, borderWidth: 1 },
  lensChipText: { fontSize: 11, fontWeight: '500' },

  sectionTitle: { fontSize: 17, fontWeight: '600', marginBottom: 6, marginTop: 8 },
  sectionSubtitle: { fontSize: 13, marginBottom: 12 },

  synthesisBlock: { borderRadius: 12, borderWidth: 1, paddingHorizontal: 16, marginBottom: 28 },
  synthRow: { paddingVertical: 14 },
  synthLabel: { fontSize: 10, fontWeight: '700', letterSpacing: 1.3, marginBottom: 4 },
  synthBody: { fontSize: 15, lineHeight: 23 },

  patternList: { gap: 10, marginBottom: 24 },
  patternCard: { borderRadius: 12, borderWidth: 1, padding: 14 },
  patternTitle: { fontSize: 14, fontWeight: '600', marginBottom: 4 },
  patternBody: { fontSize: 13, lineHeight: 20 },

  evidenceToggle: { paddingVertical: 10, marginBottom: 8 },
  evidenceToggleText: { fontSize: 14, fontWeight: '500' },
  evidencePanel: { borderRadius: 12, borderWidth: 1, paddingHorizontal: 14, marginBottom: 28 },
  evidenceRow: { paddingVertical: 10 },
  evidenceLabel: { fontSize: 12, fontWeight: '600', marginBottom: 2 },
  evidenceBody: { fontSize: 13, lineHeight: 19 },

  enhanceBlock: { borderRadius: 12, borderWidth: 1, padding: 16, marginBottom: 24 },
  fieldLabel: { fontSize: 13, fontWeight: '500', marginBottom: 6 },
  fieldHint: { fontSize: 11, marginTop: 4 },
  input: {
    borderRadius: 10,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
  },
  saveEnhanceBtn: {
    marginTop: 16,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
  },
  saveEnhanceText: { fontSize: 14, fontWeight: '600' },
  enhanceMsg: { fontSize: 12, marginTop: 8, textAlign: 'center' },

  buildMarker: { fontSize: 10, textAlign: 'center', marginTop: 16, letterSpacing: 0.6 },
});
