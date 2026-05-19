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

// ---------------------------------------------------------------------------
// PERSON STORY — deterministic synthesis (individual-maps-v1)
// ---------------------------------------------------------------------------
// Six grounded sections that tell the user *who this person actually is*
// and how that lands on them — written in Mirror's recognition-first voice.
// Inputs available at v1:
//   * relationship_type     (drives the "relationship clue" line)
//   * enneagram_type        (when set, sharpens core pattern + shadow)
//   * birth_date / time     (drives an Astrology-light overlay)
//   * full_birth_name       (numerology hint)
//
// No LLM yet — kept deterministic so it always renders the same on every
// device, and never leaks generic coaching copy.
// ---------------------------------------------------------------------------

type PersonStory = {
  core: string;            // Core pattern — who they are at the centre
  movement: string;        // How they tend to move through life
  feel: string;            // How they may feel to be around
  need: string;            // What they may need from others
  shadow: string;          // Shadow / pressure pattern
  relationship_clue: string; // Relationship clue for me (this person ↔ me)
};

// Enneagram-driven core. The mapping is intentionally compact — we tell
// the truth of the type rather than a sanitised version.
const ENNEAGRAM_CORE: Record<string, Omit<PersonStory, 'relationship_clue'>> = {
  '1': {
    core: 'A self that organises around getting it right. Standards live in the body, not just the head.',
    movement: 'They move carefully, hold themselves to a higher line than they hold others to — and notice every detail that misses.',
    feel: 'Steady, principled, sometimes quietly tense. There is often an inner critic working in the background you can almost hear.',
    need: 'Permission to be human. Less correction, more recognition for the work they\'re already doing on themselves.',
    shadow: 'Under pressure: rigidity, resentment, a controlled tone that hides anger. The body holds what the mouth refuses to say.',
  },
  '2': {
    core: 'A self that knows itself most clearly through being needed. Love is felt as usefulness.',
    movement: 'They lean in, anticipate, give before being asked. Their attention is almost always pointed at someone else.',
    feel: 'Warm, attuned, generous — sometimes so close it crosses a line you didn\'t mark.',
    need: 'To be loved for who they are, not just what they do. Permission to have needs without earning them first.',
    shadow: 'Under pressure: covert demand, martyrdom, the bill arriving for help you never asked for.',
  },
  '3': {
    core: 'A self built around performance. Worth and image are tightly bound — and the image is usually polished.',
    movement: 'They optimise, deliver, shape-shift to win the room. Goals are met; the person inside the goals is harder to find.',
    feel: 'Capable, charismatic, slightly armoured. The realness sometimes only shows up when the wins stop.',
    need: 'A relationship where they can be unimpressive and still be loved. Slowness without it meaning failure.',
    shadow: 'Under pressure: image-management, deflection, a quiet contempt for whoever sees through the polish.',
  },
  '4': {
    core: 'A self that locates identity in feeling and depth. What\'s missing tends to feel more vivid than what\'s here.',
    movement: 'They move toward intensity, toward the felt edge — and away from anything that feels generic.',
    feel: 'Textured, emotionally rich, sometimes far away. Pulled toward the longing more than the having.',
    need: 'To be met without being fixed. Steadiness that doesn\'t mistake their depth for drama.',
    shadow: 'Under pressure: envy, withdrawal, a story of being uniquely uncared-for that quietly recruits you.',
  },
  '5': {
    core: 'A self that protects its inner resources by stepping back. Knowing replaces touching.',
    movement: 'They observe before engaging, conserve energy, prefer competence in a small field over chaos in a big one.',
    feel: 'Cool, considered, sometimes far behind glass. Presence is real but rationed.',
    need: 'Space without it being taken as rejection. Permission to come back at their own pace.',
    shadow: 'Under pressure: detachment, hoarding (time, knowledge, affection), a quiet contempt for emotional demand.',
  },
  '6': {
    core: 'A self organised around safety and trust — and around the thinking that keeps testing both.',
    movement: 'They scan for what could go wrong, run the scenarios, then commit fully once trust is real.',
    feel: 'Loyal, vigilant, sometimes braced. Their anxiety is often working in service of you, not against you.',
    need: 'A relationship where doubts can be named out loud without being treated as betrayal.',
    shadow: 'Under pressure: reactivity, testing, projecting threat onto a person who is actually safe.',
  },
  '7': {
    core: 'A self that moves toward options, possibility, momentum. Pain is real — and there is usually a plan around it.',
    movement: 'They reframe fast, jump tracks, generate ideas faster than they can finish them.',
    feel: 'Bright, energising, sometimes hard to pin down. The depth is real but it tends to keep moving.',
    need: 'A field that can hold them through the heavy thing without trying to cheer it away.',
    shadow: 'Under pressure: escape, scattering, a sudden coldness when something tries to make them stay with hard feeling.',
  },
  '8': {
    core: 'A self organised around strength, agency, and not being controlled. Tenderness lives underneath, well-guarded.',
    movement: 'They move directly, take up space, make decisions early and protect their people loudly.',
    feel: 'Big, present, unmistakable. Safety with them is real — and so is the size of their no.',
    need: 'Someone who can meet their intensity without collapsing or matching it. Truth-telling, not management.',
    shadow: 'Under pressure: domination, blunt force, a refusal of vulnerability that turns the room cold.',
  },
  '9': {
    core: 'A self organised around inner peace. Their own preferences are often the last thing they notice.',
    movement: 'They blend, accommodate, find the middle path — and quietly disappear from their own life if no one notices.',
    feel: 'Easy, calming, steady. The cost of that ease is rarely visible from the outside.',
    need: 'To be asked, specifically, what they actually want — and to be waited for while they find the answer.',
    shadow: 'Under pressure: stubborn passivity, fog, a slow withdrawal that looks like agreement.',
  },
};

// Fallback core when no enneagram type is set — based on relationship_type
// so we still feel grounded rather than generic.
const RELATIONSHIP_FALLBACK_CORE: Record<string, Omit<PersonStory, 'relationship_clue'>> = {
  partner: {
    core: 'A self you have studied closely — and one that has studied you back, sometimes more than you realise.',
    movement: 'They show you their full range over time: the version at their best, and the version when something has cost them.',
    feel: 'Familiar, sometimes too familiar — the kind of person whose mood you can read before they speak.',
    need: 'To be seen as the person they are becoming, not only as the person you first chose.',
    shadow: 'Under pressure: the closeness can curdle into watching, scoring, or quiet contracting.',
  },
  spouse: {
    core: 'A self woven into the structure of your daily life — and one whose absence would re-shape the rooms you live in.',
    movement: 'They move with you on the long arc — work, money, family, time — even when neither of you is talking about it.',
    feel: 'Solid, embedded, sometimes invisible because of how present they are.',
    need: 'To be noticed inside the partnership, not just relied on as part of the architecture.',
    shadow: 'Under pressure: performance of the relationship instead of inhabitation of it.',
  },
  ex_partner: {
    core: 'A self that once held a version of you that no one else has held since.',
    movement: 'They move through your memory more than through your present — and the memory is usually older than they are now.',
    feel: 'Charged, layered, sometimes hard to feel cleanly. Real recognition still lives in there.',
    need: 'To be allowed to have changed. To not be frozen in the version of them that hurt you most.',
    shadow: 'Under pressure: a return to the dynamic that ended things, on either side, sometimes without warning.',
  },
  parent: {
    core: 'A self that taught you, before you had words for it, what safety, performance and love feel like.',
    movement: 'They move through their own old loyalties — to their parents, their generation, their fear — even when they\'re with you.',
    feel: 'Foundational, complicated, sometimes still capable of changing the temperature of a room you\'re in.',
    need: 'To be met as a person, not only as a role. To be allowed to be wrong without being erased.',
    shadow: 'Under pressure: the conditioning they passed on shows up — in them, and in you, sometimes at the same time.',
  },
  child: {
    core: 'A self that is still being assembled — and your read of who they are is shaping who they will be.',
    movement: 'They move toward you and away from you in cycles; both are necessary.',
    feel: 'Real, surprising, sometimes a mirror you didn\'t ask for.',
    need: 'Presence without control. To be known as the person they\'re becoming, not the one you hoped for.',
    shadow: 'Under pressure: they absorb your unfinished business and call it their personality.',
  },
  child_minor: {
    core: 'A self that is still being assembled — and your read of who they are is shaping who they will be.',
    movement: 'They move toward you and away from you in cycles; both are necessary.',
    feel: 'Real, surprising, sometimes a mirror you didn\'t ask for.',
    need: 'Presence without control. To be known as the person they\'re becoming, not the one you hoped for.',
    shadow: 'Under pressure: they absorb your unfinished business and call it their personality.',
  },
  sibling: {
    core: 'A self shaped inside the same system that shaped you — but who took a different position in the field.',
    movement: 'They move through the family roles you both grew up inside, even when neither of you wants to.',
    feel: 'Familiar in a way no one else is, sometimes for better, sometimes for worse.',
    need: 'A relationship rebuilt as adults, not as the children you both used to be.',
    shadow: 'Under pressure: old roles snap back, especially in family rooms.',
  },
  family_other: {
    core: 'A self positioned inside a wider family field that carries its own history and expectation.',
    movement: 'They move with one foot in the wider system and one foot in their relationship with you.',
    feel: 'Familiar but partial — the relationship rarely gets all of who they are.',
    need: 'A direct line that isn\'t routed through the rest of the family.',
    shadow: 'Under pressure: the family field decides things between you that you never agreed to.',
  },
  friend: {
    core: 'A self who has chosen you, and been chosen by you, outside of obligation — which is rarer than it sounds.',
    movement: 'They move at their own rhythm, and the friendship survives the gaps between contact.',
    feel: 'Steady, accurate, often more honest about you than your family is.',
    need: 'To be updated as you both grow, not held to who you used to be at each other.',
    shadow: 'Under pressure: drift, projection, or sudden distance that wasn\'t fully named.',
  },
  close_friend: {
    core: 'A self who has stayed — through the version of you that wasn\'t easy to stay through.',
    movement: 'They move close, then give space, then come back; the rhythm is real, not careless.',
    feel: 'Like a person whose presence settles your nervous system before they\'ve said anything.',
    need: 'To be told the truth before it has to be apologised for later.',
    shadow: 'Under pressure: unspoken needs collect and the next conversation has to carry too much.',
  },
  colleague: {
    core: 'A self you see most often in working mode — which is real, but not all of who they are.',
    movement: 'They move through professional structures: roles, deadlines, the politics of the room.',
    feel: 'Capable, recognisable, often more layered than the working version suggests.',
    need: 'To be related to as a person who happens to do this work, not as the work itself.',
    shadow: 'Under pressure: their style of stress becomes confused with their style of judgement.',
  },
  boss: {
    core: 'A self with formal authority over part of your life — and an informal authority that is usually larger than the formal one.',
    movement: 'They move with the constraints of the role: visibility, performance, protecting their own seat.',
    feel: 'Influential, sometimes hard to read because of the asymmetry.',
    need: 'A reliable read from you. Truth told well, not management.',
    shadow: 'Under pressure: their stress quietly becomes your scope.',
  },
  report: {
    core: 'A self developing inside a field you have real influence over — for better and worse.',
    movement: 'They move with one eye on the work and one eye on how you\'re reading them.',
    feel: 'Capable, watchful, sometimes more self-doubting than the surface suggests.',
    need: 'A clear, honest read. Coaching that doesn\'t become rescuing.',
    shadow: 'Under pressure: the relationship slips into performance for you instead of partnership with you.',
  },
  client: {
    core: 'A self meeting you inside a contract — and bringing more than the contract to the table.',
    movement: 'They move with their own pressures, deadlines, and unspoken expectations of you.',
    feel: 'Defined by the work, but rarely only that.',
    need: 'Clarity about what is and isn\'t inside the agreement.',
    shadow: 'Under pressure: scope expands quietly and trust thins by inches.',
  },
  mentor: {
    core: 'A self positioned a few steps ahead of you on a road they have walked.',
    movement: 'They move from earned ground, sometimes with the angle of their own incomplete work still visible.',
    feel: 'Trustworthy on the things they have lived. Less so on the things they only know in theory.',
    need: 'Real questions from you, not just admiration.',
    shadow: 'Under pressure: their model becomes a ceiling instead of a doorway.',
  },
  mentee: {
    core: 'A self standing where you used to stand — and watching you closely whether they admit it or not.',
    movement: 'They move at their pace, not yours, even when you wish they would speed up.',
    feel: 'Hungry, careful, sometimes performing their progress for you.',
    need: 'Space to figure it out, with you holding the shape rather than the answers.',
    shadow: 'Under pressure: they collapse into hero-worship or pre-emptive rebellion.',
  },
  other: {
    core: 'A self that doesn\'t fit a clean label — and that often means the relationship is doing something more specific than the categories allow.',
    movement: 'They move according to whatever the actual thread between you is, not the role.',
    feel: 'Specific, harder to summarise, usually clearer once you stop trying to.',
    need: 'To be related to as themselves, not as a category you\'re trying to fit them into.',
    shadow: 'Under pressure: you reach for a label to manage the relationship, and the label flattens it.',
  },
};

// Relationship-clue overlay — "what this person is for me, right now".
// This is the line that turns the story from a description of them into a
// reading of the relationship.
const RELATIONSHIP_CLUE: Record<string, string> = {
  partner: 'This relationship asks you to keep choosing presence over performance — even when it would be easier to drift into roles.',
  spouse: 'This is the relationship where your long-arc patterns get the most accurate testing. It will show you what you actually believe about partnership.',
  ex_partner: 'This relationship is finished as a future and unfinished as a teacher. What still surfaces between you is often what is still asking to be acknowledged in you.',
  parent: 'This relationship is part of the system that wrote your nervous system. What runs between you is often older than either of you.',
  child: 'This relationship will keep showing you where you are still working on yourself. They are watching closely.',
  child_minor: 'This relationship will keep showing you where you are still working on yourself. They are watching closely.',
  sibling: 'This relationship is one of the few places you get to renegotiate your original role in the family. That work is slower than it looks.',
  family_other: 'This relationship sits inside a wider field. What you decide to carry from the family system shapes what is actually between you.',
  friend: 'This relationship is voluntary in a way most of your life isn\'t. What you do with that voluntariness is the relationship.',
  close_friend: 'This relationship is a baseline you don\'t notice until it shifts. Tending it directly is rarer than relying on it.',
  colleague: 'This relationship will tell you a lot about what you actually trust about your own work, and what you outsource.',
  boss: 'This relationship sits at the intersection of your work and your nervous system. Both are reading more than you think.',
  report: 'This relationship is one of the cleanest mirrors of how you handle power when you have it.',
  client: 'This relationship will reveal what you do when you want the work and the relationship to stay in agreement, and what you do when they pull apart.',
  mentor: 'This relationship is where you get to test what you take on as truth and what you outgrow.',
  mentee: 'This relationship will show you what you actually believe about how growth works, by what you offer and what you withhold.',
  other: 'This relationship is teaching you something specific that the standard categories can\'t name yet — which is often where the real work lives.',
};

// The six labelled sections of the Person Story, in render order.
const STORY_SECTIONS: { key: keyof PersonStory; label: string }[] = [
  { key: 'core', label: 'Core pattern' },
  { key: 'movement', label: 'How they tend to move through life' },
  { key: 'feel', label: 'How they may feel to be around' },
  { key: 'need', label: 'What they may need from others' },
  { key: 'shadow', label: 'Shadow / pressure pattern' },
  { key: 'relationship_clue', label: 'Relationship clue for me' },
];

/**
 * Build a PersonStory deterministically from the person + (optional) enneagram.
 * Always returns a complete story; falls back to relationship-type defaults
 * for the core block when no enneagram type is set.
 */
function buildPersonStory(person: SavedPerson): PersonStory {
  const relType = person.relationship_type ?? 'other';
  const ennRaw = (person.enneagram_type ?? '').trim();
  // Pull the leading digit (e.g. "7w8" -> "7") so we tolerate any wing notation.
  const ennKey = ennRaw.match(/^[1-9]/)?.[0];

  const coreBlock =
    (ennKey && ENNEAGRAM_CORE[ennKey])
      ? ENNEAGRAM_CORE[ennKey]
      : (RELATIONSHIP_FALLBACK_CORE[relType] ?? RELATIONSHIP_FALLBACK_CORE.other);

  const clue = RELATIONSHIP_CLUE[relType] ?? RELATIONSHIP_CLUE.other;

  return {
    core: coreBlock.core,
    movement: coreBlock.movement,
    feel: coreBlock.feel,
    need: coreBlock.need,
    shadow: coreBlock.shadow,
    relationship_clue: clue,
  };
}

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

  const story: PersonStory = useMemo(() => {
    if (!person) {
      return {
        core: '', movement: '', feel: '', need: '', shadow: '', relationship_clue: '',
      };
    }
    return buildPersonStory(person);
  }, [person]);

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

          {/* B — PERSON STORY (individual-maps-v1)
              Six grounded, deterministic sections that describe who this
              person actually is — and how that lands on the user.  No
              generic 'notice whether...' copy. */}
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Person story</Text>
          <Text style={[styles.sectionSubtitle, { color: theme.textTertiary }]}>
            A grounded read of who they are and how that lives in your relationship.
          </Text>
          <View style={[styles.synthesisBlock, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            {STORY_SECTIONS.map((s, idx) => (
              <SynthesisRow
                key={s.key}
                label={s.label}
                body={story[s.key]}
                theme={theme}
                last={idx === STORY_SECTIONS.length - 1}
              />
            ))}
          </View>

          {/* Ask about this person — opens a focused chat surface that
              POSTs to /api/mirror/chat with about_person_id, so the
              backend Relational Awareness layer activates. */}
          <TouchableOpacity
            style={[styles.askBtn, { borderColor: theme.accent + '66', backgroundColor: theme.surface }]}
            onPress={() => router.push(`/people/${personId}/chat` as any)}
            activeOpacity={0.7}
            accessibilityRole="button"
            accessibilityLabel={`Ask about ${person.name}`}
          >
            <Text style={[styles.askBtnTitle, { color: theme.text }]}>Ask about {person.name}</Text>
            <Text style={[styles.askBtnSubtitle, { color: theme.textTertiary }]}>
              A private line to Mirror about this person — relational tone, no recruitment.
            </Text>
          </TouchableOpacity>

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

  askBtn: {
    borderRadius: 12,
    borderWidth: 1,
    paddingVertical: 16,
    paddingHorizontal: 16,
    marginBottom: 28,
    alignItems: 'flex-start',
  },
  askBtnTitle: { fontSize: 15, fontWeight: '600', marginBottom: 4 },
  askBtnSubtitle: { fontSize: 12, lineHeight: 17 },

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
