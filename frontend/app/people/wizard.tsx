/**
 * Saved People — 5-step full-screen wizard
 * ==========================================
 *
 * Steps:
 *   1. Name + relationship type
 *   2. Birth date
 *   3. Birth time + exact/unknown decision
 *   4. Birth location + exact/unknown decision
 *   5. Review + Save
 *
 * Strict client-side validation mirrors the backend contract:
 *   - birth_date: YYYY-MM-DD valid calendar date — required
 *   - birth_time: HH:MM 24h required ONLY when accuracy="exact"
 *   - birth_location: city + country required ONLY when accuracy="exact"
 * No silent nulls. The wizard refuses to advance past a step until
 * the contract for that step is satisfied.
 *
 * Used for both create (no `id` param) and edit (`?id=…`).
 */

import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useTheme } from '../../contexts/ThemeContext';
import {
  AccuracyFlag,
  createSavedPerson,
  deleteSavedPerson,
  formatRelationshipType,
  friendlyPeopleError,
  getPeopleMeta,
  getSavedPerson,
  precisionLabel,
  PrecisionLevel,
  SavedPerson,
  SavedPersonCreatePayload,
  SavedPersonLocation,
  updateSavedPerson,
} from '../../services/people';
import { useAppStore } from '../../store';

const HINT_COPY =
  'Birth details improve precision. You can mark as unknown and update later.';

const TOTAL_STEPS = 5;

// ---------------------------------------------------------------------------
// Helpers (pure)
// ---------------------------------------------------------------------------

const isValidIsoDate = (s: string): boolean => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return false;
  const [y, m, d] = s.split('-').map(Number);
  if (m < 1 || m > 12 || d < 1 || d > 31) return false;
  const dt = new Date(Date.UTC(y, m - 1, d));
  return (
    dt.getUTCFullYear() === y &&
    dt.getUTCMonth() === m - 1 &&
    dt.getUTCDate() === d
  );
};

const isValid24hTime = (s: string): boolean => /^([01]\d|2[0-3]):([0-5]\d)$/.test(s);

const computePrecision = (
  bta: AccuracyFlag, bla: AccuracyFlag,
): PrecisionLevel => {
  const a = bta === 'exact';
  const b = bla === 'exact';
  if (a && b) return 'high';
  if (a || b) return 'medium';
  return 'low';
};

// ---------------------------------------------------------------------------
// Wizard
// ---------------------------------------------------------------------------

export default function PeopleWizardScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const editingId = typeof params.id === 'string' && params.id.length > 0 ? params.id : null;
  const isEditing = Boolean(editingId);

  // ---- form state ---------------------------------------------------------
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [loadingPrefill, setLoadingPrefill] = useState(isEditing);

  const [relationshipTypes, setRelationshipTypes] = useState<string[]>([]);

  // Step 1
  const [name, setName] = useState('');
  const [relType, setRelType] = useState<string>('');

  // Step 2 — birth date as 3 separate inputs (consistent with onboarding)
  const [birthYear, setBirthYear]   = useState('');
  const [birthMonth, setBirthMonth] = useState('');
  const [birthDay, setBirthDay]     = useState('');

  // Step 3 — birth time
  const [btAccuracy, setBtAccuracy] = useState<AccuracyFlag>('exact');
  const [birthHour, setBirthHour]   = useState('');
  const [birthMinute, setBirthMinute] = useState('');
  const [amPm, setAmPm]             = useState<'AM' | 'PM'>('AM');

  // Step 4 — birth location
  const [blAccuracy, setBlAccuracy] = useState<AccuracyFlag>('exact');
  const [city, setCity]       = useState('');
  const [country, setCountry] = useState('');

  // Step-level error
  const [error, setError] = useState<string | null>(null);

  // ----- meta + prefill ----------------------------------------------------
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const meta = await getPeopleMeta();
        if (alive) setRelationshipTypes(meta.relationship_types);
      } catch {
        // Non-fatal — fall back to a sensible canonical subset
        if (alive) setRelationshipTypes([
          'partner','spouse','ex_partner','parent','child','sibling',
          'family_other','friend','close_friend','colleague','boss','report',
          'client','mentor','mentee','other',
        ]);
      }
    })();
    return () => { alive = false; };
  }, []);

  // Hydrate when editing
  useEffect(() => {
    if (!isEditing || !editingId || !user?.id) return;
    let alive = true;
    (async () => {
      try {
        const p: SavedPerson = await getSavedPerson(user.id, editingId);
        if (!alive) return;
        setName(p.name);
        setRelType(p.relationship_type);
        const [y, m, d] = (p.birth_date || '').split('-');
        setBirthYear(y || '');
        setBirthMonth(m || '');
        setBirthDay(d || '');
        setBtAccuracy(p.birth_time_accuracy);
        if (p.birth_time && isValid24hTime(p.birth_time)) {
          let h = parseInt(p.birth_time.slice(0, 2), 10);
          const mm = p.birth_time.slice(3, 5);
          const isPm = h >= 12;
          if (h === 0)        h = 12;
          else if (h > 12)    h -= 12;
          setBirthHour(String(h));
          setBirthMinute(mm);
          setAmPm(isPm ? 'PM' : 'AM');
        }
        setBlAccuracy(p.birth_location_accuracy);
        if (p.birth_location) {
          setCity(p.birth_location.city);
          setCountry(p.birth_location.country);
        }
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('[PeopleWizard] prefill error:', err);
        Alert.alert(
          'Could not load',
          friendlyPeopleError(err),
          [{ text: 'OK', onPress: () => router.back() }],
        );
      } finally {
        if (alive) setLoadingPrefill(false);
      }
    })();
    return () => { alive = false; };
  }, [isEditing, editingId, user?.id, router]);

  // ---- derived data -------------------------------------------------------
  const birthDateIso = useMemo(() => {
    if (!birthYear || !birthMonth || !birthDay) return '';
    return `${birthYear}-${birthMonth.padStart(2, '0')}-${birthDay.padStart(2, '0')}`;
  }, [birthYear, birthMonth, birthDay]);

  const birthTime24h = useMemo(() => {
    if (btAccuracy !== 'exact' || !birthHour || !birthMinute) return null;
    let h = parseInt(birthHour, 10);
    if (Number.isNaN(h)) return null;
    if (amPm === 'PM' && h !== 12) h += 12;
    else if (amPm === 'AM' && h === 12) h = 0;
    const out = `${String(h).padStart(2, '0')}:${birthMinute.padStart(2, '0')}`;
    return isValid24hTime(out) ? out : null;
  }, [btAccuracy, birthHour, birthMinute, amPm]);

  const birthLocationPayload = useMemo<SavedPersonLocation | null>(() => {
    if (blAccuracy !== 'exact') return null;
    if (!city.trim() || !country.trim()) return null;
    return { city: city.trim(), country: country.trim() };
  }, [blAccuracy, city, country]);

  const precision = computePrecision(btAccuracy, blAccuracy);
  const precInfo  = precisionLabel(precision);

  // ---- validation per step ------------------------------------------------
  const validateStep = useCallback((s: number): string | null => {
    if (s === 1) {
      if (!name.trim())    return 'Please enter a name.';
      if (name.trim().length > 120) return 'Name is too long.';
      if (!relType)        return 'Please choose a relationship type.';
    }
    if (s === 2) {
      if (!birthDateIso)   return 'Please enter the full birth date.';
      if (!isValidIsoDate(birthDateIso))
                          return 'Please enter a valid calendar date.';
      const yr = parseInt(birthYear, 10);
      const now = new Date().getUTCFullYear();
      if (yr < 1900 || yr > now)
                          return `Year must be between 1900 and ${now}.`;
    }
    if (s === 3) {
      if (btAccuracy === 'exact') {
        if (!birthHour || !birthMinute)
          return 'Please enter the birth time, or mark it as unknown.';
        if (!birthTime24h)
          return 'That birth time is not valid (use a number 1–12 and minutes 00–59).';
      }
    }
    if (s === 4) {
      if (blAccuracy === 'exact') {
        if (!city.trim() || !country.trim())
          return 'Please enter city and country, or mark location as unknown.';
      }
    }
    return null;
  }, [
    name, relType, birthDateIso, birthYear, btAccuracy, birthHour,
    birthMinute, birthTime24h, blAccuracy, city, country,
  ]);

  const handleNext = () => {
    const e = validateStep(step);
    if (e) {
      setError(e);
      return;
    }
    setError(null);
    setStep((s) => Math.min(TOTAL_STEPS, s + 1));
  };

  const handleBack = () => {
    setError(null);
    if (step <= 1) {
      router.back();
      return;
    }
    setStep((s) => Math.max(1, s - 1));
  };

  // ---- save ---------------------------------------------------------------
  const handleSave = async () => {
    if (!user?.id) {
      setError('No active user. Please log in again.');
      return;
    }
    // Final round-trip validation
    for (let s = 1; s <= 4; s += 1) {
      const e = validateStep(s);
      if (e) {
        setError(e);
        setStep(s);
        return;
      }
    }
    const payload: SavedPersonCreatePayload = {
      name: name.trim(),
      relationship_type: relType,
      birth_date: birthDateIso,
      birth_time: btAccuracy === 'exact' ? birthTime24h : null,
      birth_time_accuracy: btAccuracy,
      birth_location: birthLocationPayload,
      birth_location_accuracy: blAccuracy,
    };
    setSubmitting(true);
    setError(null);
    try {
      if (isEditing && editingId) {
        await updateSavedPerson(user.id, editingId, payload);
      } else {
        await createSavedPerson(user.id, payload);
      }
      router.replace('/people' as any);
    } catch (err) {
      setError(friendlyPeopleError(err));
    } finally {
      setSubmitting(false);
    }
  };

  // ---- delete (edit-only) -------------------------------------------------
  const handleDelete = () => {
    if (!isEditing || !editingId || !user?.id) return;
    Alert.alert(
      'Remove this person?',
      'You can always add them again later.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove', style: 'destructive',
          onPress: async () => {
            setSubmitting(true);
            try {
              await deleteSavedPerson(user.id, editingId);
              router.replace('/people' as any);
            } catch (err) {
              setError(friendlyPeopleError(err));
              setSubmitting(false);
            }
          },
        },
      ],
    );
  };

  // ---- render guards ------------------------------------------------------
  if (loadingPrefill) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Loading…
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  // -------------------------------------------------------------------------
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backBtn} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Ionicons name="chevron-back" size={22} color={theme.text} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            {isEditing ? 'Edit person' : 'Add a person'}
          </Text>
          <View style={styles.backBtn} />
        </View>

        {/* Progress dots */}
        <View style={styles.progressRow}>
          {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
            <View
              key={i}
              style={[
                styles.dot,
                {
                  backgroundColor: i + 1 <= step ? theme.accent : theme.border,
                  width: i + 1 === step ? 24 : 8,
                },
              ]}
            />
          ))}
        </View>
        <Text style={[styles.stepLabel, { color: theme.textTertiary }]}>
          Step {step} of {TOTAL_STEPS}
        </Text>

        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* ========== STEP 1: Name + relationship type ========== */}
          {step === 1 && (
            <View style={styles.stepBlock}>
              <Text style={[styles.stepTitle, { color: theme.text }]}>
                Who are we adding?
              </Text>
              <Text style={[styles.stepHint, { color: theme.textTertiary }]}>{HINT_COPY}</Text>

              <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>Name</Text>
              <TextInput
                style={[styles.input, { borderColor: theme.border, color: theme.text, backgroundColor: theme.surface }]}
                value={name}
                onChangeText={setName}
                placeholder="e.g. Alex"
                placeholderTextColor={theme.textTertiary}
                autoCapitalize="words"
                maxLength={120}
                returnKeyType="next"
              />

              <Text style={[styles.fieldLabel, { color: theme.textSecondary, marginTop: 16 }]}>
                Relationship type
              </Text>
              <View style={styles.chipWrap}>
                {relationshipTypes.map((rt) => {
                  const selected = relType === rt;
                  return (
                    <Pressable
                      key={rt}
                      onPress={() => setRelType(rt)}
                      style={[
                        styles.chip,
                        {
                          borderColor: selected ? theme.accent : theme.border,
                          backgroundColor: selected ? theme.accent : theme.surface,
                        },
                      ]}
                      accessibilityRole="button"
                      accessibilityState={{ selected }}
                    >
                      <Text
                        style={[
                          styles.chipText,
                          { color: selected ? theme.buttonPrimaryText : theme.text },
                        ]}
                      >
                        {formatRelationshipType(rt)}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
            </View>
          )}

          {/* ========== STEP 2: Birth date ========== */}
          {step === 2 && (
            <View style={styles.stepBlock}>
              <Text style={[styles.stepTitle, { color: theme.text }]}>Birth date</Text>
              <Text style={[styles.stepHint, { color: theme.textTertiary }]}>
                A valid calendar date (YYYY · MM · DD).
              </Text>

              <View style={styles.dateRow}>
                <View style={styles.dateField}>
                  <Text style={[styles.dateLabel, { color: theme.textTertiary }]}>Day</Text>
                  <TextInput
                    style={[styles.dateInput, { borderColor: theme.border, color: theme.text, backgroundColor: theme.surface }]}
                    value={birthDay}
                    onChangeText={(t) => setBirthDay(t.replace(/\D/g, '').slice(0, 2))}
                    placeholder="DD"
                    placeholderTextColor={theme.textTertiary}
                    keyboardType="number-pad"
                    maxLength={2}
                  />
                </View>
                <View style={styles.dateField}>
                  <Text style={[styles.dateLabel, { color: theme.textTertiary }]}>Month</Text>
                  <TextInput
                    style={[styles.dateInput, { borderColor: theme.border, color: theme.text, backgroundColor: theme.surface }]}
                    value={birthMonth}
                    onChangeText={(t) => setBirthMonth(t.replace(/\D/g, '').slice(0, 2))}
                    placeholder="MM"
                    placeholderTextColor={theme.textTertiary}
                    keyboardType="number-pad"
                    maxLength={2}
                  />
                </View>
                <View style={[styles.dateField, { flex: 1.4 }]}>
                  <Text style={[styles.dateLabel, { color: theme.textTertiary }]}>Year</Text>
                  <TextInput
                    style={[styles.dateInput, { borderColor: theme.border, color: theme.text, backgroundColor: theme.surface }]}
                    value={birthYear}
                    onChangeText={(t) => setBirthYear(t.replace(/\D/g, '').slice(0, 4))}
                    placeholder="YYYY"
                    placeholderTextColor={theme.textTertiary}
                    keyboardType="number-pad"
                    maxLength={4}
                  />
                </View>
              </View>
            </View>
          )}

          {/* ========== STEP 3: Birth time + accuracy ========== */}
          {step === 3 && (
            <View style={styles.stepBlock}>
              <Text style={[styles.stepTitle, { color: theme.text }]}>Birth time</Text>
              <Text style={[styles.stepHint, { color: theme.textTertiary }]}>{HINT_COPY}</Text>

              <View style={styles.accuracyRow}>
                <AccuracyButton
                  label="I know the time"
                  selected={btAccuracy === 'exact'}
                  onPress={() => setBtAccuracy('exact')}
                  theme={theme}
                />
                <AccuracyButton
                  label="Mark unknown"
                  selected={btAccuracy === 'unknown'}
                  onPress={() => setBtAccuracy('unknown')}
                  theme={theme}
                />
              </View>

              {btAccuracy === 'exact' && (
                <View style={styles.timeRow}>
                  <View style={styles.timeField}>
                    <Text style={[styles.dateLabel, { color: theme.textTertiary }]}>Hour</Text>
                    <TextInput
                      style={[styles.dateInput, { borderColor: theme.border, color: theme.text, backgroundColor: theme.surface }]}
                      value={birthHour}
                      onChangeText={(t) => setBirthHour(t.replace(/\D/g, '').slice(0, 2))}
                      placeholder="HH"
                      placeholderTextColor={theme.textTertiary}
                      keyboardType="number-pad"
                      maxLength={2}
                    />
                  </View>
                  <View style={styles.timeField}>
                    <Text style={[styles.dateLabel, { color: theme.textTertiary }]}>Minute</Text>
                    <TextInput
                      style={[styles.dateInput, { borderColor: theme.border, color: theme.text, backgroundColor: theme.surface }]}
                      value={birthMinute}
                      onChangeText={(t) => setBirthMinute(t.replace(/\D/g, '').slice(0, 2))}
                      placeholder="MM"
                      placeholderTextColor={theme.textTertiary}
                      keyboardType="number-pad"
                      maxLength={2}
                    />
                  </View>
                  <View style={styles.amPmCol}>
                    <Text style={[styles.dateLabel, { color: theme.textTertiary }]}>Period</Text>
                    <View style={styles.amPmGroup}>
                      {(['AM','PM'] as const).map((v) => (
                        <Pressable
                          key={v}
                          onPress={() => setAmPm(v)}
                          style={[
                            styles.amPmBtn,
                            {
                              borderColor: amPm === v ? theme.accent : theme.border,
                              backgroundColor: amPm === v ? theme.accent : theme.surface,
                            },
                          ]}
                        >
                          <Text style={[
                            styles.amPmText,
                            { color: amPm === v ? theme.buttonPrimaryText : theme.text },
                          ]}>{v}</Text>
                        </Pressable>
                      ))}
                    </View>
                  </View>
                </View>
              )}
            </View>
          )}

          {/* ========== STEP 4: Birth location + accuracy ========== */}
          {step === 4 && (
            <View style={styles.stepBlock}>
              <Text style={[styles.stepTitle, { color: theme.text }]}>Birth location</Text>
              <Text style={[styles.stepHint, { color: theme.textTertiary }]}>{HINT_COPY}</Text>

              <View style={styles.accuracyRow}>
                <AccuracyButton
                  label="I know the location"
                  selected={blAccuracy === 'exact'}
                  onPress={() => setBlAccuracy('exact')}
                  theme={theme}
                />
                <AccuracyButton
                  label="Mark unknown"
                  selected={blAccuracy === 'unknown'}
                  onPress={() => setBlAccuracy('unknown')}
                  theme={theme}
                />
              </View>

              {blAccuracy === 'exact' && (
                <>
                  <Text style={[styles.fieldLabel, { color: theme.textSecondary, marginTop: 16 }]}>City</Text>
                  <TextInput
                    style={[styles.input, { borderColor: theme.border, color: theme.text, backgroundColor: theme.surface }]}
                    value={city}
                    onChangeText={setCity}
                    placeholder="e.g. Singapore"
                    placeholderTextColor={theme.textTertiary}
                    autoCapitalize="words"
                    maxLength={120}
                  />
                  <Text style={[styles.fieldLabel, { color: theme.textSecondary, marginTop: 16 }]}>Country</Text>
                  <TextInput
                    style={[styles.input, { borderColor: theme.border, color: theme.text, backgroundColor: theme.surface }]}
                    value={country}
                    onChangeText={setCountry}
                    placeholder="e.g. Singapore"
                    placeholderTextColor={theme.textTertiary}
                    autoCapitalize="words"
                    maxLength={120}
                  />
                </>
              )}
            </View>
          )}

          {/* ========== STEP 5: Review ========== */}
          {step === 5 && (
            <View style={styles.stepBlock}>
              <Text style={[styles.stepTitle, { color: theme.text }]}>Review &amp; save</Text>

              <ReviewRow theme={theme} label="Name"              value={name} onEdit={() => setStep(1)} />
              <ReviewRow theme={theme} label="Relationship"      value={formatRelationshipType(relType)} onEdit={() => setStep(1)} />
              <ReviewRow theme={theme} label="Birth date"        value={birthDateIso} onEdit={() => setStep(2)} />
              <ReviewRow
                theme={theme}
                label="Birth time"
                value={btAccuracy === 'exact'
                  ? (birthTime24h || '—')
                  : 'Marked unknown'}
                onEdit={() => setStep(3)}
              />
              <ReviewRow
                theme={theme}
                label="Birth location"
                value={blAccuracy === 'exact'
                  ? `${city.trim()}, ${country.trim()}`
                  : 'Marked unknown'}
                onEdit={() => setStep(4)}
              />

              <View style={[styles.precisionPanel, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                <Text style={[styles.precisionLabel, { color: theme.textTertiary }]}>Precision</Text>
                <Text style={[styles.precisionValue, { color: theme.text }]}>{precInfo.label}</Text>
                <Text style={[styles.precisionFootnote, { color: theme.textTertiary }]}>
                  Astrology and Human Design lenses use this. You can update later.
                </Text>
              </View>
            </View>
          )}

          {/* Error */}
          {error && (
            <View style={[styles.errorCard, { borderColor: theme.warning ?? '#e2c574', backgroundColor: theme.surface }]}>
              <Text style={[styles.errorText, { color: theme.text }]}>{error}</Text>
            </View>
          )}
        </ScrollView>

        {/* Footer actions */}
        <View style={[styles.footer, { borderTopColor: theme.border, backgroundColor: theme.background }]}>
          {isEditing && step === 5 && (
            <TouchableOpacity
              onPress={handleDelete}
              style={[styles.secondaryBtn, { borderColor: theme.border }]}
              disabled={submitting}
              accessibilityRole="button"
              accessibilityLabel="Remove person"
            >
              <Ionicons name="trash-outline" size={16} color={theme.textSecondary} />
              <Text style={[styles.secondaryBtnText, { color: theme.textSecondary }]}>
                Remove
              </Text>
            </TouchableOpacity>
          )}

          {step < TOTAL_STEPS ? (
            <TouchableOpacity
              onPress={handleNext}
              style={[styles.primaryBtn, { backgroundColor: theme.buttonPrimaryBg }]}
              disabled={submitting}
              accessibilityRole="button"
              accessibilityLabel="Continue"
            >
              <Text style={[styles.primaryBtnText, { color: theme.buttonPrimaryText }]}>
                Continue
              </Text>
              <Ionicons name="chevron-forward" size={18} color={theme.buttonPrimaryText} />
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              onPress={handleSave}
              style={[styles.primaryBtn, { backgroundColor: theme.buttonPrimaryBg }]}
              disabled={submitting}
              accessibilityRole="button"
              accessibilityLabel={isEditing ? 'Save changes' : 'Save person'}
            >
              {submitting ? (
                <ActivityIndicator color={theme.buttonPrimaryText} />
              ) : (
                <>
                  <Text style={[styles.primaryBtnText, { color: theme.buttonPrimaryText }]}>
                    {isEditing ? 'Save changes' : 'Save'}
                  </Text>
                  <Ionicons name="checkmark" size={18} color={theme.buttonPrimaryText} />
                </>
              )}
            </TouchableOpacity>
          )}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// ---------------------------------------------------------------------------
// Subcomponents
// ---------------------------------------------------------------------------

interface AccuracyBtnProps {
  label: string;
  selected: boolean;
  onPress: () => void;
  theme: any;
}

const AccuracyButton: React.FC<AccuracyBtnProps> = ({ label, selected, onPress, theme }) => (
  <Pressable
    onPress={onPress}
    style={[
      styles.accuracyBtn,
      {
        borderColor: selected ? theme.accent : theme.border,
        backgroundColor: selected ? theme.accent : theme.surface,
      },
    ]}
    accessibilityRole="button"
    accessibilityState={{ selected }}
  >
    <Text
      style={[
        styles.accuracyBtnText,
        { color: selected ? theme.buttonPrimaryText : theme.text },
      ]}
    >
      {label}
    </Text>
  </Pressable>
);

interface ReviewRowProps {
  theme: any;
  label: string;
  value: string;
  onEdit: () => void;
}

const ReviewRow: React.FC<ReviewRowProps> = ({ theme, label, value, onEdit }) => (
  <View style={[styles.reviewRow, { borderBottomColor: theme.border }]}>
    <View style={{ flex: 1 }}>
      <Text style={[styles.reviewLabel, { color: theme.textTertiary }]}>{label}</Text>
      <Text style={[styles.reviewValue, { color: theme.text }]} numberOfLines={2}>
        {value || '—'}
      </Text>
    </View>
    <TouchableOpacity onPress={onEdit} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
      <Text style={[styles.reviewEdit, { color: theme.accent }]}>Edit</Text>
    </TouchableOpacity>
  </View>
);

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: { flex: 1 },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 16 },
  loadingText:    { fontSize: 14, fontStyle: 'italic' },
  header: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 10,
  },
  backBtn: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  headerTitle: { fontSize: 18, fontWeight: '600' },
  progressRow: {
    flexDirection: 'row', justifyContent: 'center', alignItems: 'center',
    gap: 6, paddingHorizontal: 20, paddingTop: 4,
  },
  dot: { height: 8, borderRadius: 999 },
  stepLabel: { fontSize: 12, textAlign: 'center', marginTop: 6, marginBottom: 4 },
  scrollContent: { paddingHorizontal: 20, paddingBottom: 24, paddingTop: 16 },
  stepBlock: { gap: 8 },
  stepTitle: { fontSize: 22, fontWeight: '600' },
  stepHint:  { fontSize: 13, lineHeight: 19, marginBottom: 12 },
  fieldLabel: { fontSize: 13, fontWeight: '500' },
  input: {
    minHeight: 48, borderRadius: 12, borderWidth: 1,
    paddingHorizontal: 14, fontSize: 16, marginTop: 6,
  },
  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 },
  chip: {
    paddingHorizontal: 14, paddingVertical: 10,
    borderRadius: 999, borderWidth: 1, minHeight: 40,
    alignItems: 'center', justifyContent: 'center',
  },
  chipText: { fontSize: 13, fontWeight: '500' },
  dateRow: { flexDirection: 'row', gap: 12, marginTop: 12 },
  dateField: { flex: 1 },
  dateLabel: { fontSize: 12, marginBottom: 6 },
  dateInput: {
    minHeight: 48, borderRadius: 12, borderWidth: 1,
    paddingHorizontal: 14, fontSize: 16, textAlign: 'center',
  },
  accuracyRow: { flexDirection: 'row', gap: 10, marginTop: 12 },
  accuracyBtn: {
    flex: 1, paddingVertical: 12, paddingHorizontal: 14,
    borderRadius: 12, borderWidth: 1, alignItems: 'center',
    minHeight: 48, justifyContent: 'center',
  },
  accuracyBtnText: { fontSize: 14, fontWeight: '500', textAlign: 'center' },
  timeRow: { flexDirection: 'row', gap: 12, marginTop: 16 },
  timeField: { flex: 1 },
  amPmCol: { flex: 1 },
  amPmGroup: { flexDirection: 'row', gap: 6 },
  amPmBtn: {
    flex: 1, paddingVertical: 12, borderRadius: 10, borderWidth: 1,
    alignItems: 'center', minHeight: 48, justifyContent: 'center',
  },
  amPmText: { fontSize: 14, fontWeight: '600' },
  reviewRow: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    paddingVertical: 14, borderBottomWidth: 1,
  },
  reviewLabel: { fontSize: 12, marginBottom: 2 },
  reviewValue: { fontSize: 15, fontWeight: '500' },
  reviewEdit:  { fontSize: 14, fontWeight: '600' },
  precisionPanel: {
    marginTop: 24, padding: 16, borderRadius: 12, borderWidth: 1,
  },
  precisionLabel: { fontSize: 12, marginBottom: 4 },
  precisionValue: { fontSize: 16, fontWeight: '600' },
  precisionFootnote: { fontSize: 12, marginTop: 6 },
  errorCard: {
    marginTop: 16, padding: 12, borderRadius: 10, borderWidth: 1,
  },
  errorText: { fontSize: 14 },
  footer: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    paddingHorizontal: 16, paddingVertical: 12, borderTopWidth: 1,
  },
  primaryBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 6, minHeight: 48, borderRadius: 12, paddingHorizontal: 16,
  },
  primaryBtnText: { fontSize: 16, fontWeight: '600' },
  secondaryBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 6, minHeight: 48, borderRadius: 12, borderWidth: 1,
    paddingHorizontal: 16,
  },
  secondaryBtnText: { fontSize: 14, fontWeight: '500' },
});
