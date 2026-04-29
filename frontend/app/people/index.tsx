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
      setLoading(false);
      return;
    }
    if (showRefresh) setRefreshing(true);
    else              setLoading(true);
    try {
      const data = await listSavedPeople(user.id);
      setPeople(data.people);
      setError(null);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('[People] list fetch error:', err);
      setError('Unable to load saved people');
    } finally {
      setLoading(false);
      setRefreshing(false);
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
        <Text style={[styles.headerTitle, { color: theme.text }]}>People setup</Text>
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

        {/* Add button */}
        <TouchableOpacity
          style={[styles.addButton, { backgroundColor: theme.buttonPrimaryBg }]}
          onPress={handleAdd}
          activeOpacity={0.85}
          accessibilityRole="button"
          accessibilityLabel="Add a person"
        >
          <Ionicons name="person-add-outline" size={18} color={theme.buttonPrimaryText} />
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
              return (
                <View
                  key={p.id}
                  style={[styles.personCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
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
                      onPress={() => handleEdit(p.id)}
                      hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                      accessibilityRole="button"
                      accessibilityLabel={`Edit ${p.name}`}
                    >
                      <Ionicons name="pencil-outline" size={16} color={theme.text} />
                      <Text style={[styles.editText, { color: theme.text }]}>Edit</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

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
