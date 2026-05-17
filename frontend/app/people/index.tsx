/**
 * People setup — list screen (entry point under Forum)
 * ======================================================
 *
 * Lists all saved relationship subjects for the current user. Add /
 * Edit lead into the full-screen 5-step wizard (./wizard).
 *
 * Per spec:
 *   - Lives under Forum > People setup, NOT Life tab.
 *   - List card shows: name + relationship type + precision_level + edit.
 *   - No auto-linking of generic mentions in this phase.
 */

import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useTheme } from '../../contexts/ThemeContext';
import {
  formatRelationshipType,
  listSavedPeople,
  precisionLabel,
  SavedPerson,
} from '../../services/people';
import { useAppStore } from '../../store';

const HINT_COPY =
  'Birth details improve precision. You can mark as unknown and update later.';

export default function PeopleListScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();

  const [people, setPeople]         = useState<SavedPerson[]>([]);
  const [loading, setLoading]       = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError]           = useState<string | null>(null);

  const fetchPeople = useCallback(async (showRefresh = false) => {
    if (!user?.id) {
      // No auth yet — let the higher-level guard show the login prompt
      // (ScrollView + Add button). DO NOT mark this as an error.
      console.log('[People] fetchPeople skipped — no user.id');
      setLoading(false);
      return;
    }
    if (showRefresh) setRefreshing(true);
    else              setLoading(true);
    // P0 hotfix (May 2026): heavy console diagnostics on Safari so we
    // can pinpoint exactly which step fails (auth ID? endpoint? CORS?
    // payload shape? empty list?) when the user reports "Unable to
    // load saved people" on iPhone.
    const endpoint = `/people/${user.id}`;
    console.log('[People] === fetch start ===');
    console.log('[People]   endpoint =', endpoint);
    console.log('[People]   user_id  =', user.id);
    try {
      const data = await listSavedPeople(user.id);
      console.log('[People]   payload type =', typeof data, 'keys =', data ? Object.keys(data) : '(none)');
      // Defensive: treat ANY shape with people=[] as success-empty,
      // not an error. Production was occasionally surfacing the
      // "Unable to load" card simply because a hot-reload returned
      // a partial shape during navigation focus.
      const list = Array.isArray((data as any)?.people) ? (data as any).people : [];
      console.log('[People]   parsed count =', list.length);
      setPeople(list);
      setError(null);
    } catch (err: any) {
      console.error('[People] list fetch error:', err);
      console.error('[People]   status =', err?.response?.status);
      console.error('[People]   data   =', err?.response?.data);
      // 404 from a stale user_id should be treated as "no people"
      // rather than a hard failure — the row simply doesn't exist
      // server-side. This is friendlier than a scary error card and
      // matches the visual contract the user expects.
      if (err?.response?.status === 404) {
        console.warn('[People] treating 404 as empty list');
        setPeople([]);
        setError(null);
      } else {
        setError("Couldn't load saved people. Try again.");
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
      console.log('[People] === fetch end ===');
    }
  }, [user?.id]);

  useFocusEffect(
    useCallback(() => {
      if (user?.id) {
        fetchPeople(false);
      } else {
        setLoading(false);
      }
    }, [user?.id, fetchPeople]),
  );

  const handleAdd = () => {
    router.push('/people/wizard' as any);
  };

  const handleEdit = (personId: string) => {
    router.push({ pathname: '/people/wizard' as any, params: { id: personId } });
  };

  const handleBack = () => router.back();

  // ----- precision pill ----------------------------------------------------
  const precisionPillColor = (
    tone: 'success' | 'warn' | 'muted',
  ): { bg: string; fg: string } => {
    switch (tone) {
      case 'success': return { bg: 'rgba(124,223,161,0.15)', fg: theme.success ?? '#7cdfa1' };
      case 'warn':    return { bg: 'rgba(226,197,116,0.15)', fg: theme.warning ?? '#e2c574' };
      case 'muted':   return { bg: theme.surface,            fg: theme.textSecondary };
    }
  };

  // -------------------------------------------------------------------------
  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Loading saved people…
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBack} style={styles.backButton} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
          <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Individual Maps</Text>
        <View style={styles.backButton} />
      </View>

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => fetchPeople(true)}
            tintColor={theme.textSecondary}
          />
        }
      >
        {/* Lead copy */}
        <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
          The people you save here ground relational reflection.
        </Text>
        <Text style={[styles.hint, { color: theme.textTertiary }]}>{HINT_COPY}</Text>

        {/* Add button — uses a text glyph instead of an Ionicons font
            to avoid the missing-glyph "tofu box" we were seeing on
            Safari iOS when the icon font fails to hydrate. */}
        <TouchableOpacity
          style={[styles.addButton, { backgroundColor: theme.buttonPrimaryBg }]}
          onPress={handleAdd}
          activeOpacity={0.85}
          accessibilityRole="button"
          accessibilityLabel="Add a person"
        >
          <Text style={[styles.addButtonText, { color: theme.buttonPrimaryText, fontSize: 18 }]}>+</Text>
          <Text style={[styles.addButtonText, { color: theme.buttonPrimaryText }]}>
            Add a person
          </Text>
        </TouchableOpacity>

        {/* Error */}
        {error && (
          <View style={[styles.errorCard, { borderColor: theme.border, backgroundColor: theme.surface }]}>
            <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
            <TouchableOpacity onPress={() => fetchPeople()}>
              <Text style={[styles.retryText, { color: theme.accent }]}>Try again</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* List */}
        {!error && people.length === 0 ? (
          <View style={[styles.emptyState, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={styles.emptyIcon}>◎</Text>
            <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
              No people saved yet.
            </Text>
            <Text style={[styles.emptySubtext, { color: theme.textTertiary }]}>
              Add the people whose pattern with you matters most.
            </Text>
          </View>
        ) : (
          <View style={styles.list}>
            {people.map((p) => {
              const pl = precisionLabel(p.precision_level);
              const pillColors = precisionPillColor(pl.tone);
              // Lens availability snapshot — used to render the
              // soft "Add details to unlock" hints inline.
              const hasTime = p.birth_time_accuracy === 'exact';
              const hasLocation = p.birth_location_accuracy === 'exact';
              const hasFullName = !!p.full_birth_name;
              const hasEnneagram = !!p.enneagram_type;
              return (
                <TouchableOpacity
                  key={p.id}
                  style={[styles.personCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
                  activeOpacity={0.7}
                  onPress={() => router.push(`/people/${p.id}` as any)}
                  accessibilityRole="button"
                  accessibilityLabel={`Open ${p.name}'s individual map`}
                >
                  <View style={styles.personRow}>
                    <View style={styles.personMain}>
                      <Text style={[styles.personName, { color: theme.text }]} numberOfLines={1}>
                        {p.name}
                      </Text>
                      <Text style={[styles.personType, { color: theme.textSecondary }]}>
                        {formatRelationshipType(p.relationship_type)}
                      </Text>
                      <View style={[styles.precisionPill, { backgroundColor: pillColors.bg }]}>
                        <Text style={[styles.precisionText, { color: pillColors.fg }]}>
                          {pl.label}
                        </Text>
                      </View>
                    </View>
                    <TouchableOpacity
                      style={[styles.editButton, { borderColor: theme.border }]}
                      onPress={(e) => { e.stopPropagation(); handleEdit(p.id); }}
                      hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                      accessibilityRole="button"
                      accessibilityLabel={`Edit ${p.name}`}
                    >
                      <Text style={[styles.editText, { color: theme.text }]}>Edit</Text>
                    </TouchableOpacity>
                  </View>

                  {/* Lens summary rows — each line tells the user
                      whether the lens is available for this person
                      and, if not, what's needed to unlock it. */}
                  <View style={styles.lensSummary}>
                    <LensSummary
                      label="Astrology"
                      available={!!p.birth_date}
                      hint={p.birth_date ? 'Available' : 'Add date to unlock'}
                      theme={theme}
                    />
                    <LensSummary
                      label="Human Design"
                      available={hasTime && hasLocation}
                      hint={hasTime && hasLocation ? 'Available' : 'Add exact time + verified location to unlock'}
                      theme={theme}
                    />
                    <LensSummary
                      label="BaZi"
                      available={false}
                      hint="Coming soon"
                      theme={theme}
                    />
                    <LensSummary
                      label="Numerology"
                      available={!!p.birth_date || hasFullName}
                      hint={hasFullName ? 'Full name on file' : (p.birth_date ? 'Add full birth name for deeper read' : 'Add date to unlock')}
                      theme={theme}
                    />
                    <LensSummary
                      label="Enneagram"
                      available={hasEnneagram}
                      hint={hasEnneagram ? `Manual: ${p.enneagram_type}` : 'Add details to unlock'}
                      theme={theme}
                    />
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

// Small inline component for the per-lens summary line on each card.
// Available lenses get a quiet check; unavailable lenses say what's
// needed to unlock them so the user knows where to invest details.
function LensSummary({ label, available, hint, theme }: { label: string; available: boolean; hint: string; theme: any }) {
  return (
    <View style={summaryStyles.row}>
      <Text
        style={[
          summaryStyles.label,
          { color: available ? theme.text : theme.textTertiary },
        ]}
      >
        {available ? '✓ ' : '·  '}{label}
      </Text>
      <Text style={[summaryStyles.hint, { color: theme.textTertiary }]} numberOfLines={1}>
        {hint}
      </Text>
    </View>
  );
}

const summaryStyles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  label: { fontSize: 12, fontWeight: '500' },
  hint: { fontSize: 11, marginLeft: 12, flexShrink: 1, textAlign: 'right' },
});

const styles = StyleSheet.create({
  container: { flex: 1 },
  loadingContainer: {
    flex: 1, justifyContent: 'center', alignItems: 'center', gap: 16,
  },
  loadingText: { fontSize: 14, fontStyle: 'italic' },
  header: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20, paddingVertical: 12,
  },
  backButton: { width: 60 },
  backText: { fontSize: 16, fontWeight: '500' },
  headerTitle: { fontSize: 22, fontWeight: '600' },
  content: { flex: 1 },
  scrollContent: { paddingHorizontal: 20, paddingBottom: 40 },
  subtitle: { fontSize: 15, lineHeight: 22, marginTop: 4 },
  hint: { fontSize: 13, lineHeight: 19, marginTop: 8 },
  addButton: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 8, paddingVertical: 14, borderRadius: 14, marginTop: 20,
    minHeight: 48,
  },
  addButtonText: { fontSize: 16, fontWeight: '600' },
  errorCard: {
    marginTop: 24, padding: 16, borderRadius: 12, borderWidth: 1,
    alignItems: 'center', gap: 8,
  },
  errorText: { fontSize: 14 },
  retryText: { fontSize: 14, fontWeight: '600' },
  emptyState: {
    marginTop: 24, padding: 24, borderRadius: 16, borderWidth: 1,
    alignItems: 'center', gap: 8,
  },
  emptyIcon: { fontSize: 36, opacity: 0.7, marginBottom: 4 },
  emptyText: { fontSize: 15, textAlign: 'center' },
  emptySubtext: { fontSize: 13, textAlign: 'center', marginTop: 4 },
  list: { marginTop: 24, gap: 12 },
  personCard: {
    padding: 14, borderRadius: 14, borderWidth: 1,
  },
  personRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  lensSummary: {
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.06)',
    gap: 2,
  },
  personMain: { flex: 1, gap: 4 },
  personName: { fontSize: 16, fontWeight: '600' },
  personType: { fontSize: 13 },
  precisionPill: {
    alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 4,
    borderRadius: 999, marginTop: 4,
  },
  precisionText: { fontSize: 11, fontWeight: '600', letterSpacing: 0.2 },
  editButton: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingVertical: 8, paddingHorizontal: 12,
    borderRadius: 10, borderWidth: 1, minHeight: 36,
  },
  editText: { fontSize: 13, fontWeight: '600' },
});
