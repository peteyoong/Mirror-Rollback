/**
 * /forums/[id]/topology — Map your roles (topology-editor-v2)
 * ============================================================
 *
 * Calm list-based editor — NOT a network graph.  Lets the calling
 * forum member declare their own OUTBOUND relationship edges with
 * other members.  For each member they can:
 *   - choose "my role with them" (e.g. mentor, cofounder, sibling)
 *   - optionally pick emotional weight (heavy / moderate / light)
 *   - optionally pick closeness (high / medium / low intimacy)
 *
 * Hierarchy/power_gradient is auto-inferred from the role and
 * intentionally HIDDEN from the user — the editor stays human.
 *
 * Inferred edges remain visible as "inferred" (quietly).  Explicit
 * edges show as "mapped by you".  Edits create explicit edges that
 * override inferred ones at synthesis time.
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  ActivityIndicator,
  Alert,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '../../../contexts/ThemeContext';
import { useAppStore } from '../../../store';
import api from '../../../services/api';
import { BUILD_ID } from '../../../constants/buildMarker';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ForumMember {
  user_id: string;
  // Backend (`/forums/{id}/members`) returns user_name.
  // Older endpoints / draft shapes may use name / display_name / user.name.
  user_name?: string;
  name?: string;
  display_name?: string;
  user?: { name?: string };
}

// Resolve a human-readable name across the various shapes the API has
// returned over time.  Never renders the literal string "Member" — if
// hydration is incomplete we return null and the caller suppresses the
// row until the name arrives.
function resolveMemberName(m: ForumMember | null | undefined): string | null {
  if (!m) return null;
  const candidate =
    m.user_name ||
    m.display_name ||
    m.name ||
    m.user?.name ||
    '';
  const trimmed = String(candidate).trim();
  if (!trimmed) return null;
  // Defensive: legacy seed data sometimes returned "Anonymous" / "Member"
  // as a literal — treat those as unresolved so we show a skeleton instead.
  if (/^(anonymous|member|unknown)$/i.test(trimmed)) return null;
  return trimmed;
}

interface Edge {
  id: string;
  forum_id: string;
  from_user_id: string;
  to_user_id: string;
  role_type: string;
  inferred?: boolean;
  confidence?: string;
  emotional_weight?: string;
  intimacy_level?: string;
}

// Display-name overrides for role chips — keep human, no jargon.
const ROLE_LABEL: Record<string, string> = {
  forum_mate: 'forum mate',
  close_friend: 'close friend',
  spouse: 'spouse',
  former_partner: 'former partner',
  parent: 'parent',
  child: 'child',
  sibling: 'sibling',
  cofounder: 'cofounder',
  manager: 'manager',
  employee: 'employee',
  mentor: 'mentor',
  mentee: 'mentee',
  coach: 'coach',
  coachee: 'coachee',
  advisor: 'advisor',
  collaborator: 'collaborator',
  business_partner: 'business partner',
  investor: 'investor',
  authority_figure: 'authority',
  other: 'other',
};

// The role chip palette (order matters — most-common first).
const ROLE_PALETTE: string[] = [
  'forum_mate', 'close_friend', 'spouse',
  'parent', 'child', 'sibling',
  'cofounder', 'manager', 'employee',
  'mentor', 'mentee', 'coach', 'coachee', 'advisor',
  'collaborator', 'other',
];

const WEIGHT_OPTIONS = ['heavy', 'moderate', 'light'] as const;
const INTIMACY_OPTIONS = ['high', 'medium', 'low'] as const;

// ---------------------------------------------------------------------------
// Screen
// ---------------------------------------------------------------------------

export default function TopologyEditorScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const forumId = String(params.id || '');
  const { user } = useAppStore();
  const userId = user?.id ? String(user.id) : '';

  const [loading, setLoading] = useState(true);
  const [members, setMembers] = useState<ForumMember[]>([]);
  const [outbound, setOutbound] = useState<Edge[]>([]);
  const [saving, setSaving] = useState<string | null>(null); // member id being saved

  // Per-member draft state (selected role + optional facets, not yet saved).
  const [draftRole, setDraftRole] = useState<Record<string, string>>({});
  const [draftWeight, setDraftWeight] = useState<Record<string, string>>({});
  const [draftIntimacy, setDraftIntimacy] = useState<Record<string, string>>({});

  // ── Load members + outbound edges. ───────────────────────────────────
  const reload = useCallback(async () => {
    if (!forumId || !userId) return;
    setLoading(true);
    try {
      const [mResp, tResp] = await Promise.all([
        api.get(`/forums/${forumId}/members?user_id=${userId}`),
        api.get(`/forums/${forumId}/topology/by/${userId}`),
      ]);
      const mlist: ForumMember[] = ((mResp?.data?.members || mResp?.data || []) as ForumMember[])
        .filter((m) => m && m.user_id && String(m.user_id) !== userId);
      setMembers(mlist);
      const out: Edge[] = (tResp?.data?.outbound || []) as Edge[];
      setOutbound(out);
    } catch {
      // Quiet — surface empty UI rather than crashing.
    } finally {
      setLoading(false);
    }
  }, [forumId, userId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  // ── Find the current "best" edge from me → this member. ──────────────
  const edgeFor = (toUserId: string): Edge | null => {
    const explicit = outbound.find(
      (e) => String(e.to_user_id) === String(toUserId) && !e.inferred,
    );
    if (explicit) return explicit;
    const inferred = outbound.find(
      (e) => String(e.to_user_id) === String(toUserId) && e.inferred,
    );
    return inferred || null;
  };

  // ── Save handler. ────────────────────────────────────────────────────
  const onSave = useCallback(
    async (toUserId: string) => {
      const role = draftRole[toUserId];
      if (!role) return;
      setSaving(toUserId);
      try {
        await api.post(`/forums/${forumId}/topology/edge`, {
          from_user_id: userId,
          to_user_id: toUserId,
          role_type: role,
          emotional_weight: draftWeight[toUserId] || null,
          intimacy_level: draftIntimacy[toUserId] || null,
        });
        // Clear draft and reload.
        setDraftRole((p) => ({ ...p, [toUserId]: '' }));
        setDraftWeight((p) => ({ ...p, [toUserId]: '' }));
        setDraftIntimacy((p) => ({ ...p, [toUserId]: '' }));
        await reload();
      } catch (e: any) {
        Alert.alert(
          'Could not save',
          e?.response?.data?.detail || 'Try again in a moment.',
        );
      } finally {
        setSaving(null);
      }
    },
    [draftRole, draftWeight, draftIntimacy, forumId, userId, reload],
  );

  // ── Delete (only explicit edges declared by me). ─────────────────────
  const onDelete = useCallback(
    async (edgeId: string, toUserId: string) => {
      Alert.alert(
        'Clear this mapping?',
        "It'll fall back to whatever can be inferred.",
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Clear',
            style: 'destructive',
            onPress: async () => {
              setSaving(toUserId);
              try {
                await api.delete(
                  `/forums/${forumId}/topology/edge/${edgeId}/by/${userId}`,
                );
                await reload();
              } catch (e: any) {
                Alert.alert(
                  'Could not clear',
                  e?.response?.data?.detail || 'Try again in a moment.',
                );
              } finally {
                setSaving(null);
              }
            },
          },
        ],
      );
    },
    [forumId, userId, reload],
  );

  // ── Render a single member row. ──────────────────────────────────────
  const renderMember = (m: ForumMember) => {
    const name = resolveMemberName(m);
    // Hydration incomplete — suppress this row rather than ever render
    // a fallback like "Member".  Once the name resolves on the next
    // render pass we'll display it.
    if (!name) return null;
    const e = edgeFor(m.user_id);
    const declared = e && !e.inferred;
    const inferred = e && e.inferred;
    const draftSelected = draftRole[m.user_id];

    return (
      <View
        key={m.user_id}
        style={[
          styles.memberCard,
          { backgroundColor: theme.surface, borderColor: theme.border },
        ]}
      >
        <View style={styles.memberHeader}>
          <View style={{ flex: 1 }}>
            <Text style={[styles.memberName, { color: theme.text }]}>{name}</Text>
            {e ? (
              <Text style={[styles.memberSub, { color: theme.textTertiary }]}>
                {declared ? 'mapped by you' : 'inferred'} ·{' '}
                {ROLE_LABEL[e.role_type] || e.role_type}
              </Text>
            ) : (
              <Text style={[styles.memberSub, { color: theme.textTertiary }]}>
                no role yet
              </Text>
            )}
          </View>
          {declared && e?.id && (
            <TouchableOpacity
              onPress={() => onDelete(e.id, m.user_id)}
              hitSlop={6}
              accessibilityRole="button"
              accessibilityLabel="Clear this mapping"
              style={styles.clearBtn}
              disabled={saving === m.user_id}
            >
              <Text style={[styles.clearText, { color: theme.textTertiary }]}>
                Clear
              </Text>
            </TouchableOpacity>
          )}
        </View>

        <Text style={[styles.fieldLabel, { color: theme.textTertiary }]}>
          My role with them
        </Text>
        <View style={styles.chipRow}>
          {ROLE_PALETTE.map((r) => {
            const selected = draftSelected === r || (!draftSelected && e?.role_type === r);
            return (
              <TouchableOpacity
                key={r}
                activeOpacity={0.7}
                onPress={() =>
                  setDraftRole((p) => ({ ...p, [m.user_id]: r }))
                }
                style={[
                  styles.chip,
                  {
                    borderColor: selected ? theme.text : theme.border,
                    backgroundColor: selected ? theme.text : 'transparent',
                  },
                ]}
              >
                <Text
                  style={[
                    styles.chipText,
                    { color: selected ? theme.background : theme.textSecondary },
                  ]}
                >
                  {ROLE_LABEL[r] || r}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <Text style={[styles.fieldLabel, { color: theme.textTertiary, marginTop: 10 }]}>
          Closeness (optional)
        </Text>
        <View style={styles.chipRow}>
          {INTIMACY_OPTIONS.map((opt) => {
            const selected = draftIntimacy[m.user_id] === opt;
            return (
              <TouchableOpacity
                key={opt}
                activeOpacity={0.7}
                onPress={() =>
                  setDraftIntimacy((p) => ({
                    ...p,
                    [m.user_id]: selected ? '' : opt,
                  }))
                }
                style={[
                  styles.chipSm,
                  {
                    borderColor: selected ? theme.text : theme.border,
                    backgroundColor: selected ? theme.text : 'transparent',
                  },
                ]}
              >
                <Text
                  style={[
                    styles.chipSmText,
                    { color: selected ? theme.background : theme.textSecondary },
                  ]}
                >
                  {opt === 'high' ? 'close' : opt === 'medium' ? 'familiar' : 'distant'}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <Text style={[styles.fieldLabel, { color: theme.textTertiary, marginTop: 10 }]}>
          Weight (optional)
        </Text>
        <View style={styles.chipRow}>
          {WEIGHT_OPTIONS.map((opt) => {
            const selected = draftWeight[m.user_id] === opt;
            return (
              <TouchableOpacity
                key={opt}
                activeOpacity={0.7}
                onPress={() =>
                  setDraftWeight((p) => ({
                    ...p,
                    [m.user_id]: selected ? '' : opt,
                  }))
                }
                style={[
                  styles.chipSm,
                  {
                    borderColor: selected ? theme.text : theme.border,
                    backgroundColor: selected ? theme.text : 'transparent',
                  },
                ]}
              >
                <Text
                  style={[
                    styles.chipSmText,
                    { color: selected ? theme.background : theme.textSecondary },
                  ]}
                >
                  {opt}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <TouchableOpacity
          activeOpacity={0.7}
          disabled={!draftSelected || saving === m.user_id}
          onPress={() => onSave(m.user_id)}
          style={[
            styles.saveBtn,
            {
              backgroundColor: draftSelected ? theme.text : 'transparent',
              borderColor: theme.border,
              opacity: !draftSelected || saving === m.user_id ? 0.5 : 1,
            },
          ]}
        >
          {saving === m.user_id ? (
            <ActivityIndicator size="small" color={theme.background} />
          ) : (
            <Text
              style={[
                styles.saveBtnText,
                { color: draftSelected ? theme.background : theme.textTertiary },
              ]}
            >
              {declared ? 'Update mapping' : 'Save mapping'}
            </Text>
          )}
        </TouchableOpacity>
      </View>
    );
  };

  // ── Frame. ───────────────────────────────────────────────────────────
  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.background }]}
      edges={['top']}
    >
      <View style={[styles.header, { borderBottomColor: theme.border }]}>
        <TouchableOpacity
          onPress={() => router.back()}
          hitSlop={16}
          accessibilityRole="button"
          accessibilityLabel="Close and return to forum"
          style={styles.backBtn}
        >
          <Ionicons name="chevron-back" size={22} color={theme.text} />
          <Text style={[styles.backLabel, { color: theme.text }]}>Forum</Text>
        </TouchableOpacity>
        <View style={styles.titleWrap}>
          <Text style={[styles.kicker, { color: theme.textTertiary }]}>
            Topology
          </Text>
          <Text style={[styles.title, { color: theme.text }]}>
            Map your role
          </Text>
        </View>
        <TouchableOpacity
          onPress={() => router.back()}
          hitSlop={16}
          accessibilityRole="button"
          accessibilityLabel="Done"
          style={styles.doneBtn}
        >
          <Text style={[styles.doneText, { color: theme.text }]}>Done</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={[styles.intro, { color: theme.textSecondary }]}>
          For each person in this room, choose how you'd describe your role
          with them. Mappings are directional — what you say about them is
          yours; what they say is theirs.
        </Text>

        {loading ? (
          <ActivityIndicator
            size="small"
            color={theme.textTertiary}
            style={{ marginTop: 32 }}
          />
        ) : members.length === 0 ? (
          <Text style={[styles.empty, { color: theme.textTertiary }]}>
            No other members in this room yet.
          </Text>
        ) : (
          members.map(renderMember)
        )}

        {/* Explicit secondary exit — never let the user feel trapped. */}
        {!loading && members.length > 0 && (
          <TouchableOpacity
            onPress={() => router.back()}
            accessibilityRole="button"
            accessibilityLabel="Done — return to forum"
            style={[styles.doneFooterBtn, { borderColor: theme.border }]}
            activeOpacity={0.8}
          >
            <Text style={[styles.doneFooterText, { color: theme.text }]}>
              Done — back to forum
            </Text>
          </TouchableOpacity>
        )}
      </ScrollView>

      <Text style={[styles.buildBadge, { color: theme.textTertiary }]}>
        {BUILD_ID} · topology-editor-v2
      </Text>
    </SafeAreaView>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backBtn: {
    minWidth: 78,
    height: 44,
    paddingHorizontal: 6,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-start',
  },
  backLabel: {
    fontSize: 15,
    fontWeight: '500',
    marginLeft: 2,
  },
  doneBtn: {
    minWidth: 78,
    height: 44,
    paddingHorizontal: 10,
    alignItems: 'flex-end',
    justifyContent: 'center',
  },
  doneText: {
    fontSize: 15,
    fontWeight: '500',
  },
  doneFooterBtn: {
    marginTop: 18,
    marginHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
    justifyContent: 'center',
  },
  doneFooterText: {
    fontSize: 14.5,
    fontWeight: '500',
    letterSpacing: 0.1,
  },
  titleWrap: { flex: 1, alignItems: 'center' },
  kicker: {
    fontSize: 10.5,
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    fontWeight: '500',
  },
  title: {
    fontSize: 16,
    fontWeight: '500',
    letterSpacing: -0.2,
    marginTop: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 18,
    paddingBottom: 60,
    gap: 14,
  },
  intro: {
    fontSize: 13.5,
    lineHeight: 20,
    marginBottom: 4,
  },
  empty: {
    fontSize: 13,
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 28,
  },

  memberCard: {
    paddingHorizontal: 14,
    paddingVertical: 14,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    gap: 6,
  },
  memberHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  memberName: {
    fontSize: 16,
    fontWeight: '500',
    letterSpacing: -0.2,
  },
  memberSub: {
    fontSize: 11.5,
    marginTop: 2,
    fontStyle: 'italic',
  },
  clearBtn: { paddingHorizontal: 6, paddingVertical: 4 },
  clearText: { fontSize: 12, fontStyle: 'italic' },

  fieldLabel: {
    fontSize: 10.5,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    fontWeight: '500',
    marginTop: 4,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 6,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
  },
  chipText: { fontSize: 12.5, letterSpacing: 0.2 },
  chipSm: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
  },
  chipSmText: { fontSize: 12, letterSpacing: 0.2 },

  saveBtn: {
    marginTop: 12,
    paddingVertical: 11,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
    justifyContent: 'center',
  },
  saveBtnText: { fontSize: 13.5, fontWeight: '500', letterSpacing: 0.2 },

  buildBadge: {
    position: 'absolute',
    bottom: Platform.OS === 'ios' ? 4 : 2,
    right: 12,
    fontSize: 9,
    fontStyle: 'italic',
    opacity: 0.5,
  },
});
