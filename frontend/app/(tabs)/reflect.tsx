import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Keyboard,
  TouchableWithoutFeedback,
  LayoutAnimation,
  UIManager,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { Colors } from '../../constants/colors';
import { useAppStore, storage } from '../../store';
import JournalEntryItem from '../../components/JournalEntryItem';
import MirrorReflectionModal from '../../components/MirrorReflectionModal';
import MirrorChat from '../../components/MirrorChat';
import MicroMirrorCard from '../../components/MicroMirrorCard';
import PhaseMirrorCard from '../../components/PhaseMirrorCard';
import PhaseTagModal from '../../components/PhaseTagModal';
import KeyMomentsSection from '../../components/KeyMomentsSection';
import { createJournalEntry, getJournalEntries, getCombinedTimeline, TimelineItem, updateJournalEntry, deleteJournalEntry } from '../../services/api';
import api from '../../services/api';
import { buildMirrorResponse, getJournalResponse, detectThemeFromText } from '../../services/mirrorResponseEngine';
import { getCurrentPhase, getReversePrompt, getPhaseById } from '../../services/timelinePhaseUtils';
// Task 51: Lunar Decision Journal Components
import LunarDecisionJournalCard, { LunarJournalStatus } from '../../components/journal/LunarDecisionJournalCard';
import LunarTimelineView from '../../components/journal/LunarTimelineView';
import LunarHistoryView from '../../components/journal/LunarHistoryView';
import CycleCompletionModal from '../../components/journal/CycleCompletionModal';
// Task 52: Lunar Gate Timeline
import LunarGateTimeline from '../../components/journal/LunarGateTimeline';
// Task 53: Lunar Decision Wheel
import LunarDecisionWheel from '../../components/journal/LunarDecisionWheel';
// Task 55: Lunar Cycle Synthesis
import LunarCycleSynthesisCard from '../../components/journal/LunarCycleSynthesisCard';
// Leader cards for Reflect tab
import JournalLeaderCard from '../../components/journal/JournalLeaderCard';
// MirrorLeaderCard now integrated directly into MirrorChat with collapse behavior
// Removed Ionicons - using text-based alternatives for web compatibility
import { useDominantTruthForJournal } from '../../hooks/useDominantTruth';

// REFLECT V3 — visible build marker for live deployment verification.
import { BUILD_ID } from '../../constants/buildMarker';


// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// Interface for cached reflections
interface CachedReflection {
  entryId: string;
  journalText: string;
  textHash: string;
}

// Simple hash function for text comparison
function hashText(text: string): string {
  const normalized = text.trim().toLowerCase().replace(/\s+/g, ' ');
  let hash = 0;
  for (let i = 0; i < normalized.length; i++) {
    const char = normalized.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return hash.toString();
}

// =============================================================================
// JOURNAL ENTRIES NORMALIZER - CRITICAL FIX FOR NON-ARRAY STATE BUG
// =============================================================================
// This helper ensures journalEntries is ALWAYS an array, regardless of what
// the API returns or what gets passed during state updates.
// 
// Known failure modes this prevents:
// 1. API returning {entries: [...]} instead of [...]
// 2. API returning {data: [...]} instead of [...]
// 3. API returning a single object instead of array
// 4. null/undefined from failed requests
// 5. State updater receiving non-array `prev` value
// =============================================================================

interface JournalEntryLike {
  id: string;
  content: string;
  themes?: string[];
  created_at: string;
  [key: string]: any;
}

function normalizeJournalEntries(input: unknown, debugSource?: string): JournalEntryLike[] {
  // DEV LOGGING: Track what shapes are entering the normalizer
  if (__DEV__ && debugSource) {
    console.log(`[JOURNAL_NORMALIZE] Source: ${debugSource}`);
    console.log(`[JOURNAL_NORMALIZE] Input type: ${typeof input}`);
    console.log(`[JOURNAL_NORMALIZE] Is array: ${Array.isArray(input)}`);
    if (input && typeof input === 'object' && !Array.isArray(input)) {
      console.log(`[JOURNAL_NORMALIZE] Object keys: ${Object.keys(input as object).join(', ')}`);
    }
  }

  // Case 1: Already an array - filter to valid entries only
  if (Array.isArray(input)) {
    const filtered = input.filter((item): item is JournalEntryLike => 
      item !== null && 
      item !== undefined && 
      typeof item === 'object' &&
      typeof item.id === 'string' &&
      item.id.length > 0
    );
    if (__DEV__ && debugSource) {
      console.log(`[JOURNAL_NORMALIZE] Result: array with ${filtered.length} valid entries (from ${input.length} total)`);
    }
    return filtered;
  }

  // Case 2: Object with entries array (some APIs wrap arrays)
  if (input && typeof input === 'object') {
    const obj = input as Record<string, unknown>;
    
    // Check for common wrapper patterns
    if (Array.isArray(obj.entries)) {
      if (__DEV__) console.log(`[JOURNAL_NORMALIZE] Found entries wrapper, extracting array`);
      return normalizeJournalEntries(obj.entries, debugSource ? `${debugSource}->entries` : undefined);
    }
    if (Array.isArray(obj.data)) {
      if (__DEV__) console.log(`[JOURNAL_NORMALIZE] Found data wrapper, extracting array`);
      return normalizeJournalEntries(obj.data, debugSource ? `${debugSource}->data` : undefined);
    }
    if (Array.isArray(obj.journal_entries)) {
      if (__DEV__) console.log(`[JOURNAL_NORMALIZE] Found journal_entries wrapper, extracting array`);
      return normalizeJournalEntries(obj.journal_entries, debugSource ? `${debugSource}->journal_entries` : undefined);
    }
    if (Array.isArray(obj.items)) {
      if (__DEV__) console.log(`[JOURNAL_NORMALIZE] Found items wrapper, extracting array`);
      return normalizeJournalEntries(obj.items, debugSource ? `${debugSource}->items` : undefined);
    }

    // Single entry object - wrap in array if it has an id
    if (typeof obj.id === 'string' && obj.id.length > 0 && typeof obj.content === 'string') {
      if (__DEV__) console.log(`[JOURNAL_NORMALIZE] Single entry object detected, wrapping in array`);
      return [obj as JournalEntryLike];
    }
  }

  // Case 3: null, undefined, or invalid - return empty array
  if (__DEV__ && debugSource) {
    console.log(`[JOURNAL_NORMALIZE] Invalid input, returning empty array`);
  }
  return [];
}

// Interface for keystone context (for chat continuation)
interface KeystoneContext {
  date: string;
  title: string;
  keystone: string;
  reflect_question: string;
  micro_affirmation: string;
  tone: string;
  daily_seed: string;
}

// ViewMode updated: Timeline removed from UI per product requirements.
// 'entry' = REFLECT V3 emotional entry point (two intent cards).
// 'journal' = Journal composer + reflection timeline (memory).
// 'mirror' = Mirror Chat (meaning).
// 'lunar' / 'lunar-history' = legacy Reflector tools, accessible
//   from the Journal screen via "View patterns" — no longer top-level.
type ViewMode = 'entry' | 'journal' | 'mirror' | 'lunar' | 'lunar-history';

// =============================================================================
// GATE EXPLANATIONS - Human Design Gate Meanings for Lunar Cycle
// =============================================================================
interface GateExplanation {
  gate: number;
  title: string;
  theme: string;
  observation: string;
  reflectionQuestion: string;
}

const GATE_EXPLANATIONS: { [key: number]: GateExplanation } = {
  1: { gate: 1, title: 'Self-Expression', theme: 'Creative individuality and self-expression.', observation: 'Notice any urges to express yourself authentically around this decision.', reflectionQuestion: 'What unique perspective do I bring to this choice?' },
  2: { gate: 2, title: 'The Direction of Self', theme: 'Receptivity and knowing your own direction.', observation: 'Notice what direction feels natural without forcing.', reflectionQuestion: 'What direction am I naturally drawn to?' },
  3: { gate: 3, title: 'Ordering', theme: 'Innovation through chaos and new beginnings.', observation: 'Notice what needs to be ordered or organized in this decision.', reflectionQuestion: 'What new order wants to emerge?' },
  13: { gate: 13, title: 'The Listener', theme: 'Listening and collecting experiences.', observation: 'Notice what stories or experiences inform this decision.', reflectionQuestion: 'What have I learned from past experiences that applies here?' },
  17: { gate: 17, title: 'Opinions', theme: 'Following and sharing opinions.', observation: 'Notice what opinions you hold about this decision.', reflectionQuestion: 'What opinions am I holding, and are they truly mine?' },
  19: { gate: 19, title: 'Wanting', theme: 'Sensitivity to needs and resources.', observation: 'Notice what you truly need from this decision.', reflectionQuestion: 'What do I genuinely need, versus what do I think I should want?' },
  21: { gate: 21, title: 'The Hunter', theme: 'Control and biting through obstacles.', observation: 'Notice what obstacles stand in the way of this decision.', reflectionQuestion: 'What am I willing to fight for?' },
  22: { gate: 22, title: 'Openness', theme: 'Grace and emotional openness.', observation: 'Notice how emotionally open you feel about this decision.', reflectionQuestion: 'Can I approach this with grace and openness?' },
  25: { gate: 25, title: 'Innocence', theme: 'Universal love and innocence.', observation: 'Notice what feels innocent or pure about this choice.', reflectionQuestion: 'What would I choose if I had no fear?' },
  27: { gate: 27, title: 'Caring', theme: 'Nourishment and caring for others.', observation: 'Notice who else is affected by this decision.', reflectionQuestion: 'How does this decision impact those I care for?' },
  30: { gate: 30, title: 'Feelings', theme: 'Recognition of feelings and desire for new experience.', observation: 'Notice the feelings this decision brings up.', reflectionQuestion: 'What new experiences am I longing for?' },
  36: { gate: 36, title: 'Crisis', theme: 'Emotional exploration through crisis.', observation: 'Notice any sense of crisis or urgency around this decision.', reflectionQuestion: 'Is this truly urgent, or can I wait for clarity?' },
  37: { gate: 37, title: 'Friendship', theme: 'Family and community bonds.', observation: 'Notice how this decision affects your community and relationships.', reflectionQuestion: 'How does this align with my values around family and friendship?' },
  41: { gate: 41, title: 'Contraction', theme: 'Beginning of a new experiential cycle.', observation: 'Notice what desires or imagined experiences arise around this decision.', reflectionQuestion: 'What future experience do I imagine this decision might create?' },
  42: { gate: 42, title: 'Growth', theme: 'Completion and growth through experience.', observation: 'Notice what cycle is completing or growing.', reflectionQuestion: 'What is ready to be completed before I move forward?' },
  49: { gate: 49, title: 'Principles', theme: 'Revolution and principles.', observation: 'Notice what principles guide this decision.', reflectionQuestion: 'What principles am I unwilling to compromise?' },
  51: { gate: 51, title: 'Shock', theme: 'Initiative and shock of the new.', observation: 'Notice what feels shocking or initiating about this choice.', reflectionQuestion: 'Am I ready to initiate something new?' },
  55: { gate: 55, title: 'Spirit', theme: 'Emotional abundance and spirit.', observation: 'Notice the emotional energy around this decision.', reflectionQuestion: 'Does this choice fill my spirit or deplete it?' },
  63: { gate: 63, title: 'Doubt', theme: 'Logical doubt and pressure to know.', observation: 'Notice what doubts arise and whether they serve you.', reflectionQuestion: 'What questions need answering before I can decide?' },
};

// Helper to get gate explanation
const getGateExplanation = (gateNumber: number | null): GateExplanation | null => {
  if (!gateNumber) return null;
  return GATE_EXPLANATIONS[gateNumber] || {
    gate: gateNumber,
    title: `Gate ${gateNumber}`,
    theme: 'A unique perspective in the Human Design system.',
    observation: 'Notice how you feel about this decision today.',
    reflectionQuestion: 'What insights arise as you observe this decision?',
  };
};

// Helper to get cycle phase description
const getCyclePhase = (day: number): string => {
  if (day <= 3) return 'Beginning of observation cycle';
  if (day <= 7) return 'Early observation phase';
  if (day <= 14) return 'First half of cycle';
  if (day <= 21) return 'Deepening observation';
  if (day <= 26) return 'Approaching clarity';
  return 'Cycle completion approaching';
};

// ============================================
// REFLECTOR DECISION JOURNEY LAYER
// ============================================
// Transforms lunar wheel into a lived decision experience
// Mirror Language: calm, reflective, no pressure

interface JourneyPhase {
  label: string;
  hook: string;
  guidance: string;
}

const getJourneyPhase = (day: number): JourneyPhase => {
  // Days 1-9: Taking it in
  if (day <= 9) {
    const hooks = [
      "Right now, you're noticing what feels right—and what doesn't stay that way.",
      "Right now, you're absorbing. Nothing needs to be clear yet.",
      "Right now, you're sensing the edges of this decision. Let them be fuzzy.",
    ];
    return {
      label: "You're still taking this in.",
      hook: hooks[Math.floor(day / 3) % hooks.length],
      guidance: "Nothing is settled yet. That's how it's supposed to be.",
    };
  }
  
  // Days 10-20: Seeing different sides
  if (day <= 20) {
    const hooks = [
      "Right now, you're seeing this from angles you hadn't considered before.",
      "Right now, what felt certain yesterday might feel different today. That's information.",
      "Right now, you're noticing what changes—and what keeps returning.",
    ];
    return {
      label: "You're seeing different sides.",
      hook: hooks[Math.floor((day - 10) / 4) % hooks.length],
      guidance: "What changes matters. What stays consistent matters more.",
    };
  }
  
  // Days 21-28: Clarity forming
  if (day <= 28) {
    const hooks = [
      "Right now, something is becoming clearer. You don't have to name it yet.",
      "Right now, you're approaching the end of the cycle. What has stayed true?",
      "Right now, the pieces are settling. Not forcing—settling.",
    ];
    return {
      label: "Clarity is forming.",
      hook: hooks[Math.floor((day - 21) / 3) % hooks.length],
      guidance: "Notice what stays consistent across different days.",
    };
  }
  
  // Day 29+: Cycle completion
  return {
    label: "You've seen this across a full cycle.",
    hook: "Right now, you have the full picture. Not because you figured it out—because you lived through it.",
    guidance: "Whatever stayed true across this cycle is genuinely yours.",
  };
};

// Daily journal prompt for Reflectors
const getReflectorJournalPrompt = (day: number, topic: string): string => {
  if (day <= 9) {
    return `What felt true today about "${topic}"—and did it stay true?`;
  }
  if (day <= 20) {
    return `How does "${topic}" look different today compared to earlier in the cycle?`;
  }
  if (day <= 28) {
    return `What about "${topic}" has stayed consistent? What keeps changing?`;
  }
  return `Looking back at the full cycle—what do you know now about "${topic}"?`;
};

export default function JournalScreen() {
  const { user, chart, journalEntries, setJournalEntries, addJournalEntry } = useAppStore();
  const { theme, isDark } = useTheme();
  
  // Derive safe entries count for debugging
  const safeEntriesCount = Array.isArray(journalEntries) ? journalEntries.length : 0;
  
  // DEBUG: Log render with journalEntries count
  console.log('[JOURNAL_RENDER] Render triggered. journalEntries count:', safeEntriesCount, 'isArray:', Array.isArray(journalEntries));
  
  const params = useLocalSearchParams<{ 
    view?: string; 
    fromKeystone?: string;
    prefillPrompt?: string;
    journalSource?: string;
    category?: string;
    tensionPair?: string;
  }>();
  const [viewMode, setViewMode] = useState<ViewMode>(
    // REFLECT V3: default to the calm entry chooser.
    // If a deep link asks for a specific sub-view (e.g. journalSource,
    // fromKeystone, prefillPrompt), the existing useEffect below
    // re-routes to 'journal' or 'mirror' as needed.
    'entry'
  );
  const [newEntry, setNewEntry] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef<TextInput>(null);
  
  // Task 51: Lunar Decision Journal state
  const [lunarStatus, setLunarStatus] = useState<LunarJournalStatus | null>(null);
  const [showCycleCompletion, setShowCycleCompletion] = useState(false);
  const [isCreatingLunarEntry, setIsCreatingLunarEntry] = useState(false);
  // Task 52: Lunar timeline data for LunarGateTimeline
  const [lunarTimelineData, setLunarTimelineData] = useState<any>(null);
  // Task 54: Success message for cycle completion
  const [lunarSuccessMessage, setLunarSuccessMessage] = useState<string | null>(null);
  // Task 60: Track if lunar data has been fetched to prevent re-fetch loops
  const [lunarDataFetched, setLunarDataFetched] = useState(false);
  const lunarFetchInProgress = useRef(false);
  // Task 64: Selected decision for multi-decision support
  const [selectedDecisionId, setSelectedDecisionId] = useState<string | null>(null);
  // Task 65: Active decision with full data (single source of truth)
  const [activeDecision, setActiveDecision] = useState<{
    id: string;
    topic: string;
    days_in_cycle: number;
    cycle_start: string;
    entry_count: number;
    entries: any[];
    timeline: any[];
  } | null>(null);
  const [isLoadingDecisionData, setIsLoadingDecisionData] = useState(false);
  
  // Task 70 Fix: Historical entry view state (separate from today state)
  const [selectedHistoricalEntry, setSelectedHistoricalEntry] = useState<{
    cycle_day: number;
    gate: number | null;
    entry_id: string;
  } | null>(null);
  
  // Pattern metadata for journal entries triggered from patterns
  const [patternMetadata, setPatternMetadata] = useState<{
    journal_source?: string;
    pattern_category?: string;
    pattern_tension_pair?: string;
    prompt_text?: string;
  } | null>(null);
  
  // Mirror Reflection Modal state
  const [reflectionModalVisible, setReflectionModalVisible] = useState(false);
  const [selectedJournalText, setSelectedJournalText] = useState('');
  const [selectedEntryId, setSelectedEntryId] = useState<string | null>(null);
  
  // Cache of reflections per entry
  const [reflectionCache, setReflectionCache] = useState<Map<string, CachedReflection>>(new Map());

  // Combined timeline items (journal entries + mirror insights)
  const [timelineItems, setTimelineItems] = useState<TimelineItem[]>([]);
  const [isLoadingTimeline, setIsLoadingTimeline] = useState(false);

  // Keystone context for Mirror Chat continuation
  const [keystoneContext, setKeystoneContext] = useState<KeystoneContext | null>(null);

  // Dominant Truth for Journal prefill (Master Layer Integration)
  const { data: dominantTruthData, isLoading: isDominantTruthLoading, hasPattern: hasDominantPattern } = useDominantTruthForJournal(user?.id);
  const [dominantTruthPrefilled, setDominantTruthPrefilled] = useState(false);

  // Micro-Mirror response state (inline response after journal save)
  const [microMirrorResponse, setMicroMirrorResponse] = useState<string | null>(null);
  const [microMirrorEntryId, setMicroMirrorEntryId] = useState<string | null>(null);
  const [microMirrorVisible, setMicroMirrorVisible] = useState(false);
  
  // Phase Mirror state (Journal ↔ Timeline connection)
  const [phaseMirrorVisible, setPhaseMirrorVisible] = useState(false);
  const [savedPhaseId, setSavedPhaseId] = useState<string | null>(null);
  const [savedPhaseName, setSavedPhaseName] = useState<string | null>(null);
  const [reversePromptText, setReversePromptText] = useState<string | null>(null);
  
  // Phase Tag Modal state (when user taps phase pill on an entry)
  const [phaseTagModalVisible, setPhaseTagModalVisible] = useState(false);
  const [selectedPhaseId, setSelectedPhaseId] = useState<string>('');
  const [selectedPhaseName, setSelectedPhaseName] = useState<string>('');
  const [selectedEntryDate, setSelectedEntryDate] = useState<string>('');
  
  // Post-save highlight state (for newest entry)
  const [highlightedEntryId, setHighlightedEntryId] = useState<string | null>(null);
  const HIGHLIGHT_CLEAR_DELAY = 2500; // Clear after 2.5s (animation is 2s)
  
  // =============================================================================
  // LATEST REFLECTION THREAD STATE
  // =============================================================================
  // This tracks the most recently submitted entry to render it as a connected
  // thread: User Entry → Mirror Response → Pattern Recognition
  // The entry appears ABOVE the feed, attached to Mirror response
  // =============================================================================
  const [latestSubmittedEntry, setLatestSubmittedEntry] = useState<{
    id: string;
    content: string;
    created_at: string;
    themes: string[];
    phase_id?: string;
    phase_name?: string;
    isOptimistic?: boolean;
  } | null>(null);
  
  // "Captured" feedback state (FIX 8)
  const [showCapturedFeedback, setShowCapturedFeedback] = useState(false);
  
  // Pending optimistic entry (for failsafe)
  const [pendingEntryText, setPendingEntryText] = useState<string | null>(null);
  
  // Pattern reinforcement state (post-journal feedback)
  const [patternReinforcement, setPatternReinforcement] = useState<{
    message: string;
    strength: string;
    connects_to_today: boolean;
    route: string | null;
  } | null>(null);
  const [reinforcementEntryId, setReinforcementEntryId] = useState<string | null>(null);
  
  const router = useRouter();

  // Collapsible intro card state (Part 1 & 2) - DEFAULT TO COLLAPSED for write-first UX
  const [introCardExpanded, setIntroCardExpanded] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);
  const [hasTypedInSession, setHasTypedInSession] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);
  const flatListRef = useRef<FlatList>(null);

  // Auto-collapse intro card when user focuses input, types, or scrolls
  const handleInputFocus = () => {
    setInputFocused(true);
    if (introCardExpanded) {
      LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
      setIntroCardExpanded(false);
    }
  };

  const handleInputBlur = () => {
    setInputFocused(false);
  };

  const handleTextChange = (text: string) => {
    setNewEntry(text);
    // Auto-collapse on first character typed
    if (text.length === 1 && !hasTypedInSession) {
      setHasTypedInSession(true);
      if (introCardExpanded) {
        LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
        setIntroCardExpanded(false);
      }
    }
  };

  const handleScroll = (event: any) => {
    // Auto-collapse when user scrolls down past threshold
    const offsetY = event.nativeEvent.contentOffset.y;
    if (offsetY > 50 && introCardExpanded) {
      LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
      setIntroCardExpanded(false);
    }
  };

  const handleToggleIntroCard = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setIntroCardExpanded(!introCardExpanded);
  };

  // Edit and Delete handlers for journal entries
  const handleEditEntry = async (entryId: string, newContent: string) => {
    try {
      const updatedEntry = await updateJournalEntry(entryId, newContent);
      // Update local state - normalize to ensure array safety
      const currentEntries = normalizeJournalEntries(journalEntries, 'handleEditEntry');
      const updatedEntries = currentEntries.map(entry =>
        entry.id === entryId ? { ...entry, content: newContent } : entry
      );
      setJournalEntries(updatedEntries);
      // Also update timeline if visible
      setTimelineItems(prev => prev.map(item =>
        item.id === entryId ? { ...item, content: newContent } : item
      ));
    } catch (error) {
      console.error('[Journal] Edit error:', error);
      throw error; // Let the component handle the error
    }
  };

  const handleDeleteEntry = async (entryId: string) => {
    try {
      await deleteJournalEntry(entryId);
      // Update local state - normalize to ensure array safety
      const currentEntries = normalizeJournalEntries(journalEntries, 'handleDeleteEntry');
      const filteredEntries = currentEntries.filter(entry => entry.id !== entryId);
      setJournalEntries(filteredEntries);
      // Also update timeline
      setTimelineItems(prev => prev.filter(item => item.id !== entryId));
    } catch (error) {
      console.error('[Journal] Delete error:', error);
      throw error;
    }
  };

  // Collapse intro when tapping on entries area
  const handleEntriesAreaPress = () => {
    if (introCardExpanded) {
      LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
      setIntroCardExpanded(false);
    }
  };

  // REFLECT V3 — deep-link handler. If the user arrives at /reflect with
  // any routing param that signals a specific intent (a prefill prompt,
  // a category, a journalSource, an explicit `view`, etc.), bypass the
  // calm entry chooser and route straight into the relevant sub-view so
  // existing call sites keep working without change.
  useEffect(() => {
    if (
      params.view === 'journal' ||
      params.prefillPrompt ||
      params.journalSource ||
      params.category ||
      params.tensionPair
    ) {
      setViewMode('journal');
    } else if (params.view === 'mirror') {
      setViewMode('mirror');
    } else if (params.view === 'lunar') {
      setViewMode('lunar');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.view, params.prefillPrompt, params.journalSource, params.category, params.tensionPair]);


  // Handle deep link from Mirror home (fromKeystone=true)
  useEffect(() => {
    async function loadKeystoneContext() {
      if (params.fromKeystone === 'true' && params.view === 'mirror') {
        // Switch to mirror view
        setViewMode('mirror');
        // Load keystone context from storage
        try {
          const stored = await storage.getItem('pending_keystone_context');
          if (stored) {
            const ctx = JSON.parse(stored) as KeystoneContext;
            setKeystoneContext(ctx);
            console.log('[JournalScreen] Loaded keystone context for continuation');
            
            // Clear the pending context after reading
            await storage.removeItem('pending_keystone_context');
          }
        } catch (e) {
          console.error('[JournalScreen] Failed to load keystone context:', e);
        }
      }
    }
    
    loadKeystoneContext();
  }, [params.fromKeystone, params.view]);

  // Handle prefill from Pattern Pulse or Pattern Graph
  useEffect(() => {
    if (params.prefillPrompt) {
      // Set prefilled content with prompt
      const prefillContent = `Reflection prompt:\n${params.prefillPrompt}\n\nYour reflection:\n`;
      setNewEntry(prefillContent);
      
      // Store pattern metadata for the entry
      setPatternMetadata({
        journal_source: params.journalSource || undefined,
        pattern_category: params.category || undefined,
        pattern_tension_pair: params.tensionPair || undefined,
        prompt_text: params.prefillPrompt
      });
      
      // Focus the input
      setTimeout(() => {
        inputRef.current?.focus();
      }, 300);
    }
  }, [params.prefillPrompt, params.journalSource, params.category, params.tensionPair]);

  useEffect(() => {
    loadEntries();
  }, []);

  // Task 51: Load lunar journal status on mount to detect if user is Reflector
  useEffect(() => {
    const loadLunarStatus = async () => {
      if (!user) return;
      try {
        const response = await api.get(`/lunar-journal/${user.id}/status`);
        if (response.data?.success) {
          setLunarStatus(response.data);
        }
      } catch (err) {
        console.log('[Journal] Could not load lunar status (may not be Reflector)');
      }
    };
    loadLunarStatus();
  }, [user]);

  // Load combined timeline when switching to timeline view
  useEffect(() => {
    if (viewMode === 'timeline' && user) {
      loadCombinedTimeline();
    }
  }, [viewMode, user]);

  // Task 60: Stable callback for lunar status loaded (prevents re-fetch loop)
  // Task 67: REMOVED auto-trigger of cycle completion modal
  // The modal should only open when user explicitly taps "Complete Cycle"
  const handleLunarStatusLoaded = useCallback((status: LunarJournalStatus | null) => {
    console.log('[Lunar] Status loaded:', {
      hasStatus: !!status,
      isNearNewMoon: status?.is_near_new_moon,
      showCycleCompletion: status?.show_cycle_completion,
      hasActiveConsideration: !!status?.active_consideration,
      lunarDay: status?.lunar_day,
    });
    setLunarStatus(status);
    // NOTE: We no longer auto-open the completion modal here.
    // The modal will only open when user taps "Complete Cycle" button.
  }, []);

  // Task 60: Fetch lunar timeline data with proper guards
  const fetchLunarTimeline = useCallback(async () => {
    if (!user || lunarFetchInProgress.current) return;
    
    lunarFetchInProgress.current = true;
    try {
      const response = await api.get(`/lunar-journal/${user.id}/timeline`);
      if (response.data?.success) {
        setLunarTimelineData(response.data);
        setLunarDataFetched(true);
      }
    } catch (err) {
      console.log('[Journal] Error fetching lunar timeline');
    } finally {
      lunarFetchInProgress.current = false;
    }
  }, [user]);

  // Task 60: Load lunar timeline when entering lunar view (only once)
  useEffect(() => {
    if ((viewMode === 'lunar' || viewMode === 'lunar-history') && user && !lunarDataFetched) {
      fetchLunarTimeline();
    }
  }, [viewMode, user, lunarDataFetched, fetchLunarTimeline]);

  // Task 65: Fetch decision-specific data when selection changes
  const fetchDecisionData = useCallback(async (decisionId: string) => {
    if (!user || !decisionId) return;
    
    setIsLoadingDecisionData(true);
    try {
      // Fetch entries specific to this decision
      const entriesRes = await api.get(`/lunar-journal/${user.id}/entries`, {
        params: { consideration_id: decisionId, limit: 50 }
      });
      
      // Find the decision in lunarStatus
      const decision = lunarStatus?.active_considerations?.find((d: any) => d.id === decisionId);
      
      if (decision) {
        // Build timeline from entries grouped by day
        // Note: API returns { success: true, entries: [...] }
        const rawEntries = entriesRes.data?.entries;
        const entries = Array.isArray(rawEntries) ? rawEntries : [];
        const timelineMap: { [key: number]: any[] } = {};
        
        entries.forEach((entry: any) => {
          const day = Math.round(entry.lunar_day || 1);
          if (!timelineMap[day]) {
            timelineMap[day] = [];
          }
          timelineMap[day].push(entry);
        });
        
        const timeline = Object.entries(timelineMap).map(([day, dayEntries]) => ({
          lunar_day: parseInt(day),
          entries: dayEntries,
          entry_count: dayEntries.length,
          gates: [...new Set(dayEntries.map((e: any) => e.moon_gate).filter(Boolean))]
        })).sort((a, b) => a.lunar_day - b.lunar_day);
        
        setActiveDecision({
          id: decision.id,
          topic: decision.topic,
          days_in_cycle: decision.days_in_cycle || 1,
          cycle_start: decision.cycle_start || decision.created_at,
          entry_count: entries.length,
          entries: entries,
          timeline: timeline,
        });
      }
    } catch (err) {
      console.error('[LunarJournal] Error fetching decision data:', err);
    } finally {
      setIsLoadingDecisionData(false);
    }
  }, [user, lunarStatus?.active_considerations]);

  // Task 65: Update activeDecision when selection changes or lunarStatus loads
  // This effect only handles initial load and external changes (not user clicks)
  useEffect(() => {
    // Skip if user has explicitly selected a decision
    if (selectedDecisionId) return;
    
    // Auto-select first decision when lunar status loads
    const decisionId = lunarStatus?.active_consideration?.id 
      || lunarStatus?.active_considerations?.[0]?.id;
    
    if (decisionId && viewMode === 'lunar' && !isLoadingDecisionData) {
      // Only fetch if we don't already have this decision loaded
      if (!activeDecision || activeDecision.id !== decisionId) {
        console.log('[Lunar] Auto-loading first decision:', decisionId);
        fetchDecisionData(decisionId);
      }
    }
  }, [lunarStatus?.active_consideration?.id, lunarStatus?.active_considerations, viewMode, activeDecision, isLoadingDecisionData, fetchDecisionData, selectedDecisionId]);

  // Task 65: Handle explicit user decision selection
  const handleSelectDecision = useCallback(async (decisionId: string) => {
    console.log('[Lunar] User selected decision:', decisionId);
    setSelectedDecisionId(decisionId);
    
    // Clear historical entry view when switching decisions
    setSelectedHistoricalEntry(null);
    
    // Immediately fetch the decision data (don't rely on useEffect)
    if (!isLoadingDecisionData) {
      await fetchDecisionData(decisionId);
    }
  }, [fetchDecisionData, isLoadingDecisionData]);

  // Task 60: Stable callback for creating lunar entry
  // Task 64: Updated to use selectedDecisionId for multi-decision support
  // Task 65: Use activeDecision.id as the source of truth
  const handleCreateLunarEntry = useCallback(async () => {
    if (!newEntry.trim() || !user || isCreatingLunarEntry) return;
    
    // Use activeDecision.id as the single source of truth
    const considerationId = activeDecision?.id || selectedDecisionId || lunarStatus?.active_consideration?.id || null;
    
    setIsCreatingLunarEntry(true);
    try {
      await api.post(`/lunar-journal/${user.id}/entry`, {
        content: newEntry.trim(),
        consideration_id: considerationId,
      });
      
      setNewEntry('');
      Keyboard.dismiss();
      
      // Refresh the lunar status
      const statusRes = await api.get(`/lunar-journal/${user.id}/status`);
      if (statusRes.data?.success) {
        setLunarStatus(statusRes.data);
      }
      
      // Task 65: Refresh activeDecision data to show the new entry
      if (considerationId) {
        await fetchDecisionData(considerationId);
      }
    } catch (err) {
      console.error('[LunarJournal] Error creating entry:', err);
    } finally {
      setIsCreatingLunarEntry(false);
    }
  }, [newEntry, user, isCreatingLunarEntry, activeDecision?.id, selectedDecisionId, lunarStatus?.active_consideration?.id, fetchDecisionData]);

  const loadEntries = async () => {
    if (!user) return;

    setIsLoading(true);
    try {
      const rawResponse = await getJournalEntries(user.id);
      // CRITICAL: Normalize API response before storing in state
      const normalizedEntries = normalizeJournalEntries(rawResponse, 'loadEntries');
      setJournalEntries(normalizedEntries);
    } catch (err) {
      console.error('Load entries error:', err);
      // On error, ensure we don't corrupt state - set to empty array
      setJournalEntries([]);
    } finally {
      setIsLoading(false);
    }
  };

  const loadCombinedTimeline = async () => {
    if (!user) return;
    
    setIsLoadingTimeline(true);
    try {
      const response = await getCombinedTimeline(user.id, 50);
      setTimelineItems(response.items);
    } catch (err) {
      console.error('Load combined timeline error:', err);
      // Fallback to journal entries only - normalize to ensure array
      const safeEntries = normalizeJournalEntries(journalEntries, 'loadCombinedTimeline:fallback');
      setTimelineItems(safeEntries.map(entry => ({
        id: entry.id,
        type: 'journal_entry' as const,
        content: entry.content,
        themes: entry.themes,
        created_at: entry.created_at,
      })));
    } finally {
      setIsLoadingTimeline(false);
    }
  };

  const handleSubmit = async () => {
    if (!user || !newEntry.trim() || isSubmitting) return;

    console.log('[JOURNAL_SAVE] === SUBMIT STARTED ===');
    console.log('[JOURNAL_SAVE] Current journalEntries count:', Array.isArray(journalEntries) ? journalEntries.length : 0);

    Keyboard.dismiss();
    setIsSubmitting(true);
    setError('');

    // Capture the entry text for Micro-Mirror response generation
    const entryText = newEntry.trim();
    
    // FIX 6: Store pending text for failsafe
    setPendingEntryText(entryText);
    
    // Get current timeline phase for auto-tagging
    const currentPhase = getCurrentPhase();
    console.log('[JOURNAL_SAVE] Current timeline phase:', currentPhase.id, currentPhase.name);

    // FIX 1: OPTIMISTIC ENTRY - Create temp entry IMMEDIATELY with FULL SHAPE
    const tempId = `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const optimisticEntry = {
      id: tempId,
      content: entryText,
      created_at: new Date().toISOString(),
      themes: [] as string[],
      phase_id: currentPhase.id,
      phase_name: currentPhase.name,
      status: 'pending' as const,
    };
    
    console.log('[JOURNAL_SAVE] Optimistic entry created:', { id: tempId, content: entryText.substring(0, 30) });
    
    // =============================================================================
    // LATEST REFLECTION THREAD: Set the entry for thread display
    // =============================================================================
    // This makes the user's entry visible as a "Latest Reflection" block
    // ABOVE the journal feed, so it appears connected to the Mirror response
    // =============================================================================
    setLatestSubmittedEntry({
      id: tempId,
      content: entryText,
      created_at: new Date().toISOString(),
      themes: [],
      phase_id: currentPhase.id,
      phase_name: currentPhase.name,
      isOptimistic: true,
    });
    
    // Clear any previous Mirror responses so only new one appears
    setMicroMirrorVisible(false);
    setMicroMirrorResponse(null);
    setPatternReinforcement(null);
    
    // Add optimistic entry to start of list BEFORE API call
    // CRITICAL: Use normalizer to ensure prev is always an array
    setJournalEntries(prev => {
      const validPrev = normalizeJournalEntries(prev, 'handleSubmit:optimistic');
      return [optimisticEntry, ...validPrev];
    });
    
    // FIX 3: Auto-scroll to top to show new entry
    setTimeout(() => {
      flatListRef.current?.scrollToOffset({ offset: 0, animated: true });
    }, 100);
    
    // FIX 8: Show "Captured" feedback
    setShowCapturedFeedback(true);
    setTimeout(() => setShowCapturedFeedback(false), 1500);
    
    // FIX 2: Delay clear input until optimistic entry is rendered
    setTimeout(() => {
      setNewEntry('');
      setPatternMetadata(null);
    }, 150);

    try {
      // Include pattern metadata if present, plus phase data
      const metadata = {
        ...(patternMetadata ? {
          journal_source: patternMetadata.journal_source,
          pattern_category: patternMetadata.pattern_category,
          pattern_tension_pair: patternMetadata.pattern_tension_pair,
          prompt_text: patternMetadata.prompt_text
        } : {}),
        phase_id: currentPhase.id,
        phase_name: currentPhase.name,
      };
      
      console.log('[JOURNAL_SAVE] Calling createJournalEntry API');
      const entry = await createJournalEntry(user.id, entryText, metadata);
      console.log('[JOURNAL_SAVE] API SUCCESS - Entry ID:', entry.id);

      // Replace optimistic entry with real entry - CRITICAL: Use normalizer
      setJournalEntries(prev => {
        const validPrev = normalizeJournalEntries(prev, 'handleSubmit:apiSuccess');
        return validPrev.map(e => {
          if (!e || !e.id) return null;
          return e.id === tempId ? { ...entry, status: undefined } : e;
        }).filter(Boolean) as typeof validPrev;
      });
      
      // =============================================================================
      // LATEST REFLECTION THREAD: Update with real entry data
      // =============================================================================
      setLatestSubmittedEntry(prev => prev ? {
        ...prev,
        id: entry.id,
        themes: entry.themes || [],
        isOptimistic: false,
      } : null);
      
      // Clear pending text on success
      setPendingEntryText(null);
      
      // HIGHLIGHT: Set the newly saved entry as highlighted
      setHighlightedEntryId(entry.id);
      setTimeout(() => setHighlightedEntryId(null), HIGHLIGHT_CLEAR_DELAY);

      // Generate and show Micro-Mirror response
      if (entryText.length >= 10) {
        const response = buildMirrorResponse({
          journalText: entryText,
          dominantTruth: dominantTruthData ? {
            dominantTheme: detectThemeFromText(entryText),
            confidenceScore: 60,
          } : undefined,
          hasHistory: normalizeJournalEntries(journalEntries).length > 0,
          variationSeed: Date.now(),
        });
        
        const { text: journalText } = getJournalResponse(response);
        setMicroMirrorResponse(journalText);
        setMicroMirrorEntryId(entry.id);
        setMicroMirrorVisible(true);
        
        // NO SCROLL HERE - Keep user looking at their entry + Mirror in thread view
        
        // Fetch pattern reinforcement (non-blocking)
        try {
          const reinforcementResponse = await api.get(`/journal/${user.id}/pattern-reinforcement/${entry.id}`);
          if (reinforcementResponse.data?.message && reinforcementResponse.data?.strength !== 'none') {
            setPatternReinforcement(reinforcementResponse.data);
            setReinforcementEntryId(entry.id);
          }
        } catch (err) {
          console.log('[JOURNAL_SAVE] Pattern reinforcement fetch failed');
        }
      }
      
      // Show Phase Mirror card
      setSavedPhaseId(currentPhase.id);
      setSavedPhaseName(currentPhase.name);
      setPhaseMirrorVisible(true);
      
      const reversePrompt = getReversePrompt(currentPhase.id, Date.now());
      setReversePromptText(reversePrompt);

      console.log('[JOURNAL_SAVE] === SUBMIT COMPLETE (SUCCESS) ===');
      
      // Background re-fetch to reconcile - CRITICAL: Normalize before storing
      setTimeout(async () => {
        try {
          const rawFreshEntries = await getJournalEntries(user.id);
          const freshEntries = normalizeJournalEntries(rawFreshEntries, 'handleSubmit:backgroundRefetch');
          const newEntryExists = freshEntries.some((e: any) => e.id === entry.id);
          if (newEntryExists) {
            setJournalEntries(freshEntries);
          }
        } catch (err) {
          console.error('[JOURNAL_SAVE] Background re-fetch failed');
        }
      }, 1000);
    } catch (err: any) {
      console.error('[JOURNAL_SAVE] === SUBMIT FAILED ===', err);
      
      // FIX 6: FAILSAFE - Keep entry visible, mark as "syncing"
      setError("Saved locally. Syncing...");
      
      // Retry after 3 seconds
      setTimeout(async () => {
        if (pendingEntryText) {
          try {
            const metadata = {
              phase_id: currentPhase.id,
              phase_name: currentPhase.name,
            };
            const retryEntry = await createJournalEntry(user.id, pendingEntryText, metadata);
            // CRITICAL: Use normalizer for retry path
            setJournalEntries(prev => {
              const validPrev = normalizeJournalEntries(prev, 'handleSubmit:retry');
              return validPrev.map(e => {
                if (!e || !e.id) return null;
                return e.id === tempId ? { ...retryEntry, status: undefined } : e;
              }).filter(Boolean) as typeof validPrev;
            });
            setError('');
            setPendingEntryText(null);
            console.log('[JOURNAL_SAVE] Retry succeeded');
          } catch (retryErr) {
            console.error('[JOURNAL_SAVE] Retry also failed');
          }
        }
      }, 3000);
    } finally {
      setIsSubmitting(false);
    }
  };

  const dismissKeyboard = () => {
    Keyboard.dismiss();
  };

  // handleReflect must be declared BEFORE handlers that use it
  const handleReflect = useCallback((entryId: string, content: string) => {
    const cached = reflectionCache.get(entryId);
    const currentHash = hashText(content);
    
    if (cached && cached.textHash === currentHash) {
      setSelectedJournalText(cached.journalText);
    } else {
      const newCache = new Map(reflectionCache);
      newCache.set(entryId, {
        entryId,
        journalText: content,
        textHash: currentHash,
      });
      setReflectionCache(newCache);
      setSelectedJournalText(content);
    }
    
    setSelectedEntryId(entryId);
    setReflectionModalVisible(true);
  }, [reflectionCache]);

  // Micro-Mirror action handlers (must come AFTER handleReflect declaration)
  const handleMicroMirrorReflect = useCallback(() => {
    const safeEntries = normalizeJournalEntries(journalEntries);
    if (microMirrorEntryId && safeEntries.length > 0) {
      const entry = safeEntries.find(e => e.id === microMirrorEntryId);
      if (entry) {
        handleReflect(entry.id, entry.content);
      }
    }
  }, [microMirrorEntryId, journalEntries, handleReflect]);

  const handleMicroMirrorAskMirror = useCallback(() => {
    // Navigate to Mirror chat with context
    setViewMode('mirror');
  }, []);

  // Dismiss handler for MicroMirrorCard
  const handleMicroMirrorDismiss = useCallback(() => {
    setMicroMirrorVisible(false);
    setMicroMirrorResponse(null);
    setMicroMirrorEntryId(null);
  }, []);

  // Handle pattern reinforcement tap - routes to relevant screen
  const handlePatternReinforcementTap = useCallback(() => {
    if (!patternReinforcement?.route) return;
    
    if (patternReinforcement.route === 'today_pattern') {
      router.push('/(tabs)');
    } else if (patternReinforcement.route === 'reflect') {
      // Already on reflect, just scroll to top
      scrollViewRef.current?.scrollTo({ y: 0, animated: true });
    }
    
    // Dismiss after tap
    setPatternReinforcement(null);
    setReinforcementEntryId(null);
  }, [patternReinforcement, router]);

  // Auto-dismiss pattern reinforcement after 8 seconds
  useEffect(() => {
    if (patternReinforcement) {
      const timer = setTimeout(() => {
        setPatternReinforcement(null);
        setReinforcementEntryId(null);
      }, 8000);
      return () => clearTimeout(timer);
    }
  }, [patternReinforcement]);

  // Phase Mirror handlers
  const handlePhaseMirrorDismiss = useCallback(() => {
    setPhaseMirrorVisible(false);
    setReversePromptText(null);
  }, []);

  const handleViewTimeline = useCallback(() => {
    // Navigate to the astrology lens Timeline tab with the specific phase to expand
    // Use URL params to tell the Timeline tab which phase to auto-expand
    const phaseToExpand = savedPhaseId || 'q1';
    router.push(`/(tabs)/?lens=astrology&tab=timeline&expandPhase=${phaseToExpand}`);
    setPhaseMirrorVisible(false);
  }, [router, savedPhaseId]);

  // Handler for "Write deeper" CTA in Phase Mirror card
  const handleWriteDeeper = useCallback((prompt: string) => {
    setNewEntry(`${prompt}\n\n`);
    setPhaseMirrorVisible(false);
    setReversePromptText(null);
    // Focus the input
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  }, []);

  // Handler for reverse prompt - prefill journal with the prompt
  const handleReversePrompt = useCallback(() => {
    if (reversePromptText) {
      setNewEntry(`Reflection prompt:\n${reversePromptText}\n\nYour reflection:\n`);
      setPhaseMirrorVisible(false);
      setReversePromptText(null);
      // Focus the input
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  }, [reversePromptText]);

  // Handler for when phase pill is tapped in journal entry
  const handlePhaseTap = useCallback((phaseId: string, phaseName: string, entryDate: string) => {
    setSelectedPhaseId(phaseId);
    setSelectedPhaseName(phaseName);
    setSelectedEntryDate(entryDate);
    setPhaseTagModalVisible(true);
  }, []);

  // Handler for "See related entries" in PhaseTagModal
  const handleSeeRelatedEntries = useCallback((phaseId: string) => {
    setPhaseTagModalVisible(false);
    // Navigate to timeline with that phase expanded
    router.push(`/(tabs)/?lens=astrology&tab=timeline&expandPhase=${phaseId}`);
  }, [router]);

  // Reset Micro-Mirror when new entry is being typed
  useEffect(() => {
    if (newEntry.trim().length > 0 && microMirrorVisible) {
      setMicroMirrorVisible(false);
      setMicroMirrorResponse(null);
      setMicroMirrorEntryId(null);
    }
    // Also reset Phase Mirror when typing
    if (newEntry.trim().length > 0 && phaseMirrorVisible) {
      setPhaseMirrorVisible(false);
      setReversePromptText(null);
    }
  }, [newEntry, microMirrorVisible, phaseMirrorVisible]);

  const handleReflectCurrentEntry = useCallback(() => {
    if (newEntry.trim()) {
      setSelectedEntryId(null);
      setSelectedJournalText(newEntry.trim());
      setReflectionModalVisible(true);
    }
  }, [newEntry]);

  const handleCloseModal = useCallback(() => {
    setReflectionModalVisible(false);
  }, []);

  if (!user) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.centered}>
          <Text style={[styles.errorText, { color: theme.error }]}>No user found</Text>
        </View>
      </SafeAreaView>
    );
  }

  // REFLECT V3: the dense segmented Journal/Mirror/Lunar tab strip has
  // been replaced by the entry chooser + a soft "← Reflect" return
  // link in each sub-view. This function now renders that quieter
  // return link. The Lunar (Reflector) sub-view is still reachable via
  // a "View patterns" link inside Journal — not at the top.
  const renderModeToggle = () => {
    return (
      <View style={styles.softReturnRow}>
        <TouchableOpacity
          onPress={() => setViewMode('entry')}
          style={styles.softReturnButton}
          accessibilityLabel="Back to Reflect"
        >
          <Text style={[styles.softReturnText, { color: theme.textSecondary }]}>
            ← Reflect
          </Text>
        </TouchableOpacity>
        {/* Reflector-only: subtle access to Lunar tools when on Journal */}
        {viewMode === 'journal' && lunarStatus?.is_reflector === true && (
          <TouchableOpacity
            onPress={() => setViewMode('lunar')}
            style={styles.softReturnButton}
            accessibilityLabel="View patterns"
          >
            <Text style={[styles.softReturnText, { color: theme.textTertiary }]}>
              View patterns
            </Text>
          </TouchableOpacity>
        )}
        {(viewMode === 'lunar' || viewMode === 'lunar-history') && (
          <TouchableOpacity
            onPress={() => setViewMode('journal')}
            style={styles.softReturnButton}
            accessibilityLabel="Back to Journal"
          >
            <Text style={[styles.softReturnText, { color: theme.textTertiary }]}>
              ← Journal
            </Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  // Helper to format relative time for timeline
  const formatTimelineDate = (dateStr: string): { date: string; time: string; relative: string } => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / 86400000);
    
    let relative = '';
    if (diffDays === 0) relative = 'Today';
    else if (diffDays === 1) relative = 'Yesterday';
    else if (diffDays < 7) relative = `${diffDays} days ago`;
    else if (diffDays < 30) relative = `${Math.floor(diffDays / 7)} weeks ago`;
    else relative = `${Math.floor(diffDays / 30)} months ago`;
    
    return {
      date: date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
      time: date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
      relative,
    };
  };

  // Group timeline items by date
  const groupTimelineItemsByDate = () => {
    const groups: { [key: string]: TimelineItem[] } = {};
    
    timelineItems.forEach(item => {
      const date = new Date(item.created_at);
      const dateKey = date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
      
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(item);
    });
    
    // Sort groups by date (most recent first)
    const sortedGroups = Object.entries(groups).sort((a, b) => {
      const dateA = new Date(a[1][0].created_at);
      const dateB = new Date(b[1][0].created_at);
      return dateB.getTime() - dateA.getTime();
    });
    
    return sortedGroups;
  };

  // Journal Timeline View - Chronological history of journal entries AND mirror insights
  // Timeline view REMOVED per product requirements - keeping only Journal and Mirror views

  // Task 51: Lunar Journal View (Reflectors Only)
  if (viewMode === 'lunar') {
    // Task 60: All lunar callbacks are now defined at component level to prevent re-fetch loops
    // Task 64: Decision-first tracker UX with multiple decisions support
    // Task 65: Use activeDecision as single source of truth for all lunar components

    // ═══════════════════════════════════════════════════════════════════════════
    // TASK 70 FIX: SINGLE RESOLVED CYCLE STATE OBJECT
    // ═══════════════════════════════════════════════════════════════════════════
    // ALL Lunar UI components MUST read from this single resolved state object.
    // This eliminates inconsistencies between different data sources.
    // ═══════════════════════════════════════════════════════════════════════════
    
    interface ResolvedCycleState {
      decision_id: string | null;
      decision_topic: string | null;
      cycle_start_date: string | null;
      cycle_length: number;
      cycle_day: number;
      phase: 'observation' | 'nearing_completion' | 'completed';
      today_gate: number | null;
      today_line: number | null;
      completion_eligible: boolean;
      completion_reason: string | null;
      source_debug: {
        cycle_day_source: string;
        used_days_in_cycle: number | null;
        used_cycle_start: string | null;
        used_lunar_day: number | null;
        decision_status: string | null;
      };
    }

    // Compute the single resolved cycle state
    const resolvedCycleState: ResolvedCycleState = (() => {
      const CYCLE_LENGTH = 29.53;
      
      // Debug tracking
      const sourceDebug: ResolvedCycleState['source_debug'] = {
        cycle_day_source: 'default',
        used_days_in_cycle: activeDecision?.days_in_cycle || null,
        used_cycle_start: activeDecision?.cycle_start || null,
        used_lunar_day: lunarStatus?.lunar_day || null,
        decision_status: null,
      };
      
      // Find decision status from active_considerations
      const decisionFromList = lunarStatus?.active_considerations?.find(
        (d: any) => d.id === activeDecision?.id
      );
      sourceDebug.decision_status = decisionFromList?.status || activeDecision?.status || null;
      
      // Step 1: Determine cycle_day from the DECISION's perspective
      // Priority: calculated from cycle_start > days_in_cycle > fallback to 1
      let cycle_day = 1;
      
      // BEST: Calculate from decision's cycle_start (most accurate)
      if (activeDecision?.cycle_start) {
        const startDate = new Date(activeDecision.cycle_start);
        const now = new Date();
        const diffMs = now.getTime() - startDate.getTime();
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24)) + 1;
        cycle_day = Math.min(Math.max(diffDays, 1), 30);
        sourceDebug.cycle_day_source = 'calculated_from_cycle_start';
      }
      // FALLBACK: Use days_in_cycle from activeDecision (may be stale)
      else if (activeDecision?.days_in_cycle && activeDecision.days_in_cycle > 0) {
        cycle_day = Math.round(activeDecision.days_in_cycle);
        sourceDebug.cycle_day_source = 'activeDecision.days_in_cycle';
      }
      // LAST RESORT: Default to 1 for new decisions
      else {
        cycle_day = 1;
        sourceDebug.cycle_day_source = 'default_new_decision';
      }
      
      // Step 2: Determine phase based ONLY on cycle_day and explicit completion status
      let phase: ResolvedCycleState['phase'] = 'observation';
      let completion_eligible = false;
      let completion_reason: string | null = null;
      
      // Check if explicitly completed
      const isExplicitlyCompleted = sourceDebug.decision_status === 'completed';
      
      if (isExplicitlyCompleted) {
        phase = 'completed';
        completion_eligible = false; // Already completed
        completion_reason = 'Decision cycle has been completed';
      } else if (cycle_day >= 21) {
        phase = 'nearing_completion';
        completion_eligible = true;
        completion_reason = `Day ${cycle_day} of ~29 - eligible for completion reflection`;
      } else {
        phase = 'observation';
        completion_eligible = false;
        completion_reason = `Day ${cycle_day} - continue observing until Day 21+`;
      }
      
      // Step 3: Get today's gate from lunarStatus (this is global/astronomical, which is correct)
      const today_gate = lunarStatus?.current_gate || null;
      const today_line = lunarStatus?.current_line || null;
      
      return {
        decision_id: activeDecision?.id || null,
        decision_topic: activeDecision?.topic || null,
        cycle_start_date: activeDecision?.cycle_start || null,
        cycle_length: CYCLE_LENGTH,
        cycle_day,
        phase,
        today_gate,
        today_line,
        completion_eligible,
        completion_reason,
        source_debug: sourceDebug,
      };
    })();

    // Log resolved state for debugging
    console.log('[Lunar] Resolved Cycle State:', {
      cycle_day: resolvedCycleState.cycle_day,
      phase: resolvedCycleState.phase,
      completion_eligible: resolvedCycleState.completion_eligible,
      source: resolvedCycleState.source_debug.cycle_day_source,
    });

    // ═══════════════════════════════════════════════════════════════════════════
    // DERIVED VALUES FROM RESOLVED STATE (all UI must use these)
    // ═══════════════════════════════════════════════════════════════════════════
    const gateExplanation = getGateExplanation(resolvedCycleState.today_gate);
    
    // Task 68: Show instruction card only when user has few reflections
    const hasReflections = activeDecision?.entry_count && activeDecision.entry_count > 0;

    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
        >
          <View style={styles.content}>
            {renderModeToggle()}

            <ScrollView 
              style={{ flex: 1 }}
              contentContainerStyle={{ paddingBottom: 120 }}
              showsVerticalScrollIndicator={false}
              keyboardShouldPersistTaps="handled"
            >
              {/* Success Message Banner */}
              {lunarSuccessMessage && (
                <View style={[styles.lunarSuccessBanner, { backgroundColor: 'rgba(129, 199, 132, 0.15)' }]}>
                  <Text style={styles.lunarSuccessText}>✓ {lunarSuccessMessage}</Text>
                </View>
              )}

              {/* ═══════════════════════════════════════════════════════════════
                  DECISION JOURNEY CARD - PRIMARY POSITION
                  Shows current position in the cycle with Mirror Language
                  ═══════════════════════════════════════════════════════════════ */}
              {(() => {
                const journeyPhase = getJourneyPhase(resolvedCycleState.cycle_day);
                const cycleDay = Math.round(resolvedCycleState.cycle_day);
                
                return (
                  <View style={[styles.journeyCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                    {/* Day Position */}
                    <View style={styles.journeyDayRow}>
                      <Text style={styles.journeyDayIcon}>🌙</Text>
                      <Text style={[styles.journeyDayText, { color: theme.text }]}>
                        Day {cycleDay} of 29
                      </Text>
                    </View>
                    
                    {/* Phase Label - The core statement */}
                    <Text style={[styles.journeyPhaseLabel, { color: theme.text }]}>
                      {journeyPhase.label}
                    </Text>
                    
                    {/* Daily Hook - Mirror Language */}
                    <Text style={[styles.journeyHook, { color: theme.textSecondary }]}>
                      {journeyPhase.hook}
                    </Text>
                    
                    {/* Decision Anchor */}
                    {activeDecision ? (
                      <View style={[styles.journeyDecisionAnchor, { borderTopColor: theme.border }]}>
                        <Text style={[styles.journeyDecisionLabel, { color: theme.textTertiary }]}>
                          YOU ARE CURRENTLY CONSIDERING
                        </Text>
                        <Text style={[styles.journeyDecisionTopic, { color: theme.text }]}>
                          "{activeDecision.topic}"
                        </Text>
                      </View>
                    ) : (
                      <TouchableOpacity 
                        style={[styles.journeyStartCta, { borderColor: theme.border }]}
                        onPress={() => {
                          // Scroll to the decision creation section
                        }}
                        activeOpacity={0.7}
                      >
                        <Text style={[styles.journeyStartCtaText, { color: theme.textSecondary }]}>
                          Start a decision to track across your cycle →
                        </Text>
                      </TouchableOpacity>
                    )}
                    
                    {/* Cycle Completion Message */}
                    {cycleDay >= 29 && (
                      <View style={[styles.journeyCompletionBanner, { backgroundColor: 'rgba(192, 200, 212, 0.08)' }]}>
                        <Text style={[styles.journeyCompletionText, { color: theme.text }]}>
                          You've seen this across a full cycle.
                        </Text>
                        <Text style={[styles.journeyCompletionSub, { color: theme.textTertiary }]}>
                          Whatever stayed true is genuinely yours.
                        </Text>
                      </View>
                    )}
                  </View>
                );
              })()}

              {/* ═══════════════════════════════════════════════════════════════
                  SECTION 1: DECISION SELECTOR (Task 68: Improved pill row)
                  ═══════════════════════════════════════════════════════════════ */}
              {lunarStatus?.active_considerations && lunarStatus.active_considerations.length > 1 && (
                <View style={styles.decisionSelectorSection}>
                  <ScrollView 
                    horizontal 
                    showsHorizontalScrollIndicator={false} 
                    style={styles.decisionSelectorScroll}
                    contentContainerStyle={styles.decisionSelectorScrollContent}
                  >
                    {lunarStatus.active_considerations.map((decision: any) => {
                      const isSelected = decision.id === activeDecision?.id;
                      const displayText = decision.topic.length > 28 
                        ? decision.topic.substring(0, 28) + '…' 
                        : decision.topic;
                      return (
                        <TouchableOpacity
                          key={decision.id}
                          style={[
                            styles.decisionSelectorPill,
                            { 
                              backgroundColor: isSelected ? 'rgba(192, 200, 212, 0.25)' : theme.surface,
                              borderColor: isSelected ? '#C0C8D4' : theme.border,
                              borderWidth: isSelected ? 1.5 : 1,
                            },
                          ]}
                          onPress={() => handleSelectDecision(decision.id)}
                          activeOpacity={0.7}
                        >
                          <Text style={[
                            styles.decisionSelectorText,
                            { 
                              color: isSelected ? '#E8EBF0' : theme.textSecondary,
                              fontWeight: isSelected ? '600' : '400',
                            }
                          ]} numberOfLines={1}>
                            {displayText}
                          </Text>
                        </TouchableOpacity>
                      );
                    })}
                  </ScrollView>
                </View>
              )}

              {/* ═══════════════════════════════════════════════════════════════
                  SECTION 2: DECISION HEADER CARD (Primary Focus)
                  Uses resolvedCycleState for all cycle information
                  ═══════════════════════════════════════════════════════════════ */}
              {activeDecision ? (
                <View style={[styles.decisionHeaderCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                  <Text style={[styles.decisionHeaderLabel, { color: '#A8B2C0' }]}>
                    OBSERVING DECISION
                  </Text>
                  <Text style={[styles.decisionHeaderTopic, { color: theme.text }]}>
                    "{activeDecision.topic}"
                  </Text>
                  <View style={styles.decisionHeaderStatusRow}>
                    <Text style={[styles.decisionHeaderStatusDay, { color: theme.text }]}>
                      Day {resolvedCycleState.cycle_day} of your lunar cycle
                    </Text>
                    <Text style={[styles.decisionHeaderStatusPhase, { color: theme.textTertiary }]}>
                      {getCyclePhase(resolvedCycleState.cycle_day)}
                    </Text>
                  </View>
                  <View style={[styles.decisionHeaderDivider, { backgroundColor: theme.border }]} />
                  <Text style={[styles.decisionHeaderDescription, { color: theme.textTertiary }]}>
                    You are observing this decision across a full lunar cycle before making a choice.
                  </Text>
                </View>
              ) : (
                /* No Decision Selected - Show Creation Card */
                <View style={[styles.noDecisionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                  <Text style={{ fontSize: 32, marginBottom: 12 }}>🌙</Text>
                  <Text style={[styles.noDecisionTitle, { color: theme.text }]}>
                    Start Observing a Decision
                  </Text>
                  <Text style={[styles.noDecisionText, { color: theme.textSecondary }]}>
                    Track important decisions across a lunar cycle (~29 days) and observe how your perspective shifts day by day.
                  </Text>
                  <LunarDecisionJournalCard
                    userId={user?.id || ''}
                    onStatusLoaded={handleLunarStatusLoaded}
                    onConsiderationCreated={() => {
                      if (user) {
                        api.get(`/lunar-journal/${user.id}/status`).then(res => {
                          if (res.data?.success) setLunarStatus(res.data);
                        });
                      }
                    }}
                  />
                </View>
              )}

              {/* ═══════════════════════════════════════════════════════════════
                  SECTION 3: CYCLE INSTRUCTION CARD
                  NEW VISIBILITY RULE: Show only if BOTH are true:
                  - entry_count < 2
                  - cycle_day <= 7
                  Hides automatically once user is engaged (past early phase or has reflections)
                  ═══════════════════════════════════════════════════════════════ */}
              {activeDecision && (activeDecision.entry_count || 0) < 2 && resolvedCycleState.cycle_day <= 7 && (
                <View style={[styles.instructionCard, { backgroundColor: 'rgba(192, 200, 212, 0.06)', borderColor: theme.border }]}>
                  <Text style={[styles.instructionTitle, { color: theme.text }]}>
                    How This Works
                  </Text>
                  <Text style={[styles.instructionText, { color: theme.textSecondary }]}>
                    Each day the Moon activates a different Human Design gate, offering a unique lens for viewing your decision. Simply notice how your perspective evolves over the ~29 day cycle.
                  </Text>
                </View>
              )}

              {/* ═══════════════════════════════════════════════════════════════
                  SECTION 4: TODAY'S LENS CARD 
                  Uses resolvedCycleState.today_gate for current gate
                  ═══════════════════════════════════════════════════════════════ */}
              {activeDecision && gateExplanation && (
                <View style={[styles.todaysLensCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                  <Text style={[styles.todaysLensLabel, { color: '#A8B2C0' }]}>
                    TODAY'S LENS
                  </Text>
                  <View style={styles.todaysLensGateRow}>
                    <Text style={[styles.todaysLensGate, { color: theme.text }]}>
                      Gate {resolvedCycleState.today_gate} — {gateExplanation.title}
                    </Text>
                    {resolvedCycleState.today_line && (
                      <Text style={[styles.todaysLensLine, { color: theme.textTertiary }]}>
                        Line {resolvedCycleState.today_line}
                      </Text>
                    )}
                  </View>
                  <Text style={[styles.todaysLensTheme, { color: theme.textSecondary }]}>
                    {gateExplanation.theme}
                  </Text>
                  <View style={[styles.todaysLensDivider, { backgroundColor: theme.border }]} />
                  <View style={styles.todaysLensObservationRow}>
                    <Text style={styles.todaysLensObservationIcon}>💡</Text>
                    <Text style={[styles.todaysLensObservation, { color: theme.textTertiary }]}>
                      {gateExplanation.observation}
                    </Text>
                  </View>
                  <View style={[styles.todaysLensPromptBox, { backgroundColor: 'rgba(192, 200, 212, 0.06)' }]}>
                    <Text style={[styles.todaysLensPromptLabel, { color: '#A8B2C0' }]}>
                      REFLECTION PROMPT
                    </Text>
                    <Text style={[styles.todaysLensPrompt, { color: theme.text }]}>
                      {gateExplanation.reflectionQuestion}
                    </Text>
                  </View>
                </View>
              )}

              {/* ═══════════════════════════════════════════════════════════════
                  SECTION 5: REFLECTION INPUT (Primary Action)
                  ═══════════════════════════════════════════════════════════════ */}
              {activeDecision && (
                <View style={[styles.reflectionInputCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                  <Text style={[styles.reflectionInputLabel, { color: '#A8B2C0' }]}>
                    TODAY'S REFLECTION
                  </Text>
                  <TextInput
                    ref={inputRef}
                    style={[styles.reflectionTextInput, { backgroundColor: theme.background, color: theme.text, borderColor: theme.border }]}
                    value={newEntry}
                    onChangeText={setNewEntry}
                    placeholder={getReflectorJournalPrompt(
                      Math.round(resolvedCycleState.cycle_day),
                      activeDecision.topic
                    )}
                    placeholderTextColor={theme.textTertiary}
                    multiline
                    numberOfLines={5}
                    maxLength={2000}
                    editable={!isCreatingLunarEntry}
                    textAlignVertical="top"
                  />
                  <TouchableOpacity
                    style={[
                      styles.saveReflectionButton,
                      { backgroundColor: newEntry.trim() ? '#C0C8D4' : theme.border },
                      (!newEntry.trim() || isCreatingLunarEntry) && { opacity: 0.5 },
                    ]}
                    onPress={handleCreateLunarEntry}
                    disabled={!newEntry.trim() || isCreatingLunarEntry}
                  >
                    {isCreatingLunarEntry ? (
                      <ActivityIndicator size="small" color="#1A1D24" />
                    ) : (
                      <Text style={styles.saveReflectionButtonText}>Save Reflection</Text>
                    )}
                  </TouchableOpacity>
                </View>
              )}

              {/* ═══════════════════════════════════════════════════════════════
                  SECTION 6: LUNAR WHEEL (History & Navigation Tool)
                  Uses resolvedCycleState for today state
                  cycleProgress is a ratio (0-1), not a percentage
                  ═══════════════════════════════════════════════════════════════ */}
              {activeDecision && (
                <View style={styles.lunarWheelSection}>
                  <Text style={[styles.lunarWheelSectionLabel, { color: '#A8B2C0' }]}>
                    OBSERVATION TIMELINE
                  </Text>
                  <Text style={[styles.lunarWheelSectionHint, { color: theme.textTertiary }]}>
                    Tap any day to view that gate's reflection
                  </Text>
                  <LunarDecisionWheel
                    currentLunarDay={resolvedCycleState.cycle_day}
                    currentGate={resolvedCycleState.today_gate}
                    currentGateTitle={gateExplanation?.title || null}
                    cycleProgress={resolvedCycleState.cycle_day / resolvedCycleState.cycle_length}
                    timeline={activeDecision.timeline || []}
                    activeTopic={activeDecision.topic}
                    onDayPress={(day, entries) => {
                      console.log('[LunarWheel] Day pressed:', day, 'entries:', entries.length);
                      // Set historical view state (does not change today state)
                      if (entries.length > 0) {
                        setSelectedHistoricalEntry({
                          cycle_day: day,
                          gate: entries[0]?.moon_gate || null,
                          entry_id: entries[0]?.id || '',
                        });
                      }
                    }}
                    onAddEntry={() => {
                      inputRef.current?.focus();
                    }}
                  />
                </View>
              )}

              {/* ═══════════════════════════════════════════════════════════════
                  SECTION 7: CYCLE COMPLETION BANNER 
                  CRITICAL FIX: Only shows when resolvedCycleState.completion_eligible === true
                  This means cycle_day >= 21 (nearing_completion phase)
                  HARD RULE: If cycle_day < 21, do NOT render this banner.
                  ═══════════════════════════════════════════════════════════════ */}
              {activeDecision && resolvedCycleState.completion_eligible && (
                <View style={[styles.cycleCompletionBanner, { backgroundColor: 'rgba(192, 200, 212, 0.08)', borderColor: theme.border }]}>
                  <View style={styles.cycleCompletionBannerContent}>
                    <Text style={[styles.cycleCompletionBannerIcon]}>🌑</Text>
                    <View style={styles.cycleCompletionBannerText}>
                      <Text style={[styles.cycleCompletionBannerTitle, { color: theme.text }]}>
                        Cycle nearing completion
                      </Text>
                      <Text style={[styles.cycleCompletionBannerSubtitle, { color: theme.textSecondary }]}>
                        Day {resolvedCycleState.cycle_day} of {resolvedCycleState.cycle_length.toFixed(1)}
                      </Text>
                      <Text style={[styles.cycleCompletionBannerBody, { color: theme.textTertiary }]}>
                        You're approaching the end of this observation cycle.
                      </Text>
                    </View>
                  </View>
                  <TouchableOpacity
                    style={[styles.cycleCompletionBannerButton, { backgroundColor: '#C0C8D4' }]}
                    onPress={() => {
                      console.log('[Lunar] User tapped Complete Cycle button');
                      setShowCycleCompletion(true);
                    }}
                  >
                    <Text style={styles.cycleCompletionBannerButtonText}>Complete Cycle Reflection</Text>
                  </TouchableOpacity>
                </View>
              )}

              {/* ═══════════════════════════════════════════════════════════════
                  SECTION 8: REFLECTION TIMELINE (Task 68: Improved card formatting)
                  ═══════════════════════════════════════════════════════════════ */}
              {activeDecision?.entries && activeDecision.entries.length > 0 && (
                <View style={styles.reflectionTimelineSection}>
                  <Text style={[styles.reflectionTimelineTitle, { color: '#A8B2C0' }]}>
                    YOUR REFLECTIONS
                  </Text>
                  {activeDecision.entries.slice(0, 5).map((entry: any, index: number) => {
                    const entryDate = entry.created_at 
                      ? new Date(entry.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                      : '';
                    return (
                      <View 
                        key={entry.id || index}
                        style={[styles.reflectionEntryCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
                      >
                        <View style={styles.reflectionEntryHeader}>
                          <Text style={[styles.reflectionEntryMeta, { color: theme.textSecondary }]}>
                            Day {Math.round(entry.lunar_day || 1)} • Gate {entry.moon_gate || '—'} • {entryDate}
                          </Text>
                        </View>
                        <Text style={[styles.reflectionEntryContent, { color: theme.text }]} numberOfLines={4}>
                          "{entry.content}"
                        </Text>
                      </View>
                    );
                  })}
                </View>
              )}

              {/* ═══════════════════════════════════════════════════════════════
                  SECTION 9: ADD ANOTHER DECISION
                  ═══════════════════════════════════════════════════════════════ */}
              {activeDecision && (
                <View style={styles.addAnotherSection}>
                  <TouchableOpacity
                    style={[styles.addAnotherButton, { borderColor: theme.border }]}
                    onPress={() => {
                      // TODO: Show modal to add new decision
                    }}
                  >
                    <Text style={[styles.addAnotherButtonText, { color: theme.textSecondary }]}>
                      + Track Another Decision
                    </Text>
                  </TouchableOpacity>
                </View>
              )}

              {/* ═══════════════════════════════════════════════════════════════
                  SECTION 10: LUNAR CYCLE SYNTHESIS
                  Only shows AFTER cycle completion (phase === 'completed')
                  OR when cycle_day >= 29 (full cycle observed)
                  ═══════════════════════════════════════════════════════════════ */}
              {activeDecision && (resolvedCycleState.phase === 'completed' || resolvedCycleState.cycle_day >= 29) && (
                <View style={styles.lunarSynthesisSection}>
                  <LunarCycleSynthesisCard
                    userId={user?.id || ''}
                    considerationId={activeDecision.id}
                    cycleCompleted={resolvedCycleState.phase === 'completed'}
                  />
                </View>
              )}

              {/* ═══════════════════════════════════════════════════════════════
                  DEBUG PANEL (Task 70: Development/QA only)
                  Shows resolved cycle state vs raw inputs for debugging
                  Enable via EXPO_PUBLIC_DEBUG_MIRROR=true
                  ═══════════════════════════════════════════════════════════════ */}
              {process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true' && activeDecision && (
                <View style={[styles.debugPanel, { backgroundColor: 'rgba(255, 165, 0, 0.1)', borderColor: '#FFA500' }]}>
                  <Text style={[styles.debugPanelTitle, { color: '#FFA500' }]}>
                    🐛 DEBUG: Resolved Cycle State
                  </Text>
                  <Text style={[styles.debugPanelText, { color: theme.textSecondary }]}>
                    cycle_day: {resolvedCycleState.cycle_day}{'\n'}
                    phase: {resolvedCycleState.phase}{'\n'}
                    today_gate: {resolvedCycleState.today_gate}{'\n'}
                    completion_eligible: {String(resolvedCycleState.completion_eligible)}{'\n'}
                    completion_reason: {resolvedCycleState.completion_reason}{'\n'}
                    source: {resolvedCycleState.source_debug.cycle_day_source}
                  </Text>
                  <Text style={[styles.debugPanelSubtitle, { color: '#FFA500' }]}>
                    Raw Inputs:
                  </Text>
                  <Text style={[styles.debugPanelText, { color: theme.textSecondary }]}>
                    activeDecision.days_in_cycle: {resolvedCycleState.source_debug.used_days_in_cycle ?? 'null'}{'\n'}
                    activeDecision.cycle_start: {resolvedCycleState.source_debug.used_cycle_start ?? 'null'}{'\n'}
                    lunarStatus.lunar_day: {resolvedCycleState.source_debug.used_lunar_day ?? 'null'}{'\n'}
                    decision_status: {resolvedCycleState.source_debug.decision_status ?? 'null'}
                  </Text>
                </View>
              )}
            </ScrollView>
          </View>
        </KeyboardAvoidingView>

        {/* Cycle Completion Modal */}
        {activeDecision && lunarStatus?.cycle_completion_prompts && (
          <CycleCompletionModal
            visible={showCycleCompletion}
            userId={user?.id || ''}
            considerationId={activeDecision.id}
            considerationTopic={activeDecision.topic}
            cycleCompletionPrompts={lunarStatus.cycle_completion_prompts}
            onClose={() => setShowCycleCompletion(false)}
            onComplete={(message) => {
              console.log('[Journal] Cycle completion success:', message);
              setShowCycleCompletion(false);
              
              if (message) {
                setLunarSuccessMessage(message);
                setTimeout(() => setLunarSuccessMessage(null), 4000);
              }
              
              if (user) {
                Promise.all([
                  api.get(`/lunar-journal/${user.id}/status`),
                  api.get(`/lunar-journal/${user.id}/timeline`)
                ]).then(([statusRes, timelineRes]) => {
                  if (statusRes.data?.success) setLunarStatus(statusRes.data);
                  if (timelineRes.data?.success) setLunarTimelineData(timelineRes.data);
                });
              }
            }}
          />
        )}
      </SafeAreaView>
    );
  }

  // Task 51: Lunar History View (Reflectors Only)
  if (viewMode === 'lunar-history') {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.content}>
          {renderModeToggle()}

          {/* Lunar Sub-navigation */}
          <View style={styles.lunarSubNav}>
            <TouchableOpacity
              style={[styles.lunarSubNavButton]}
              onPress={() => setViewMode('lunar')}
            >
              <Text style={[styles.lunarSubNavText]}>
                Current Cycle
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.lunarSubNavButton, styles.lunarSubNavButtonActive]}
            >
              <Text style={[styles.lunarSubNavText, styles.lunarSubNavTextActive]}>
                History
              </Text>
            </TouchableOpacity>
          </View>

          {/* Lunar History View */}
          <View style={{ flex: 1 }}>
            <LunarHistoryView userId={user?.id || ''} />
          </View>
        </View>
      </SafeAreaView>
    );
  }

  // Mirror Chat View
  if (viewMode === 'mirror') {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        {renderModeToggle()}
        
        {/* Mirror Leader Card now integrated inside MirrorChat with collapse behavior */}
        <MirrorChat
          userId={user.id}
          lens={null}
          placeholder="Say what's real right now…"
          headerTitle="Mirror"
          keystoneContext={keystoneContext}
        />
      </SafeAreaView>
    );
  }

  // ---------------------------------------------------------------------
  // REFLECT V3 — ENTRY CHOOSER
  // ---------------------------------------------------------------------
  // Calm two-card emotional entry point. Replaces the old segmented
  // Journal/Mirror tabs at the top of every Reflect session. Renders
  // ONLY when viewMode === 'entry'. Deep links (prefillPrompt, view=...,
  // fromKeystone=true, etc.) bypass this and route directly into a
  // sub-view via the deep-link useEffect.
  if (viewMode === 'entry') {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.entryScreen}>
          <View style={styles.entryHeader}>
            <Text style={[styles.entryTitle, { color: theme.text }]}>
              Reflect
            </Text>
            <Text style={[styles.entrySubtitle, { color: theme.textSecondary }]}>
              A mirror, not a verdict.
            </Text>
          </View>

          <View style={styles.entryCardsWrap}>
            {/* CARD 1 — JOURNAL (memory) */}
            <TouchableOpacity
              activeOpacity={0.85}
              onPress={() => setViewMode('journal')}
              style={[styles.entryCard, { backgroundColor: theme.surface }]}
              accessibilityLabel="Open Journal"
              accessibilityRole="button"
            >
              <Text style={[styles.entryCardTitle, { color: theme.text }]}>
                Capture what's real
              </Text>
              <Text style={[styles.entryCardSubtitle, { color: theme.textSecondary }]}>
                Build reflection over time.
              </Text>
              <View style={styles.entryCardCtaRow}>
                <Text style={[styles.entryCardCta, { color: theme.text }]}>
                  Write
                </Text>
                <Text style={[styles.entryCardCtaArrow, { color: theme.text }]}>
                  →
                </Text>
              </View>
            </TouchableOpacity>

            {/* CARD 2 — MIRROR CHAT (meaning) */}
            <TouchableOpacity
              activeOpacity={0.85}
              onPress={() => setViewMode('mirror')}
              style={[styles.entryCard, { backgroundColor: theme.surface }]}
              accessibilityLabel="Open Mirror Chat"
              accessibilityRole="button"
            >
              <Text style={[styles.entryCardTitle, { color: theme.text }]}>
                Ask Mirror
              </Text>
              <Text style={[styles.entryCardSubtitle, { color: theme.textSecondary }]}>
                Say what's been sitting with you.
              </Text>
              <View style={styles.entryCardCtaRow}>
                <Text style={[styles.entryCardCta, { color: theme.text }]}>
                  Open Mirror
                </Text>
                <Text style={[styles.entryCardCtaArrow, { color: theme.text }]}>
                  →
                </Text>
              </View>
            </TouchableOpacity>
          </View>

          {/* Always-visible build marker — used to confirm whether a
              given client is running the latest bundle. Subtle bottom
              footer; production users will not notice it. */}
          <View style={styles.buildMarkerFooter}>
            <Text style={[styles.buildMarkerText, { color: theme.textTertiary }]}>
              build · {BUILD_ID}
            </Text>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  // Journal View
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <View style={styles.content}>
          {/* Mode Toggle */}
          {renderModeToggle()}

          {/* ─────────────────────────────────────────────────────────
              REFLECT V4 — Journal redesigned to feel like a private
              notebook. The JournalLeaderCard intro accordion has been
              removed: explanatory copy delays emotional entry and the
              writing surface now dominates the visible viewport.
              An optional, subtle one-line prompt sits ABOVE the
              textarea (only when a dominant truth exists) and is
              dismissible by tapping into the writing surface.
              ───────────────────────────────────────────────────────── */}

          {/* Optional ghost prompt — subtle, single line, dismissible.
              Becomes invisible the moment the user starts typing. */}
          {hasDominantPattern && dominantTruthData && !newEntry.trim() && !dominantTruthPrefilled && (
            <TouchableOpacity
              style={styles.journalGhostPrompt}
              onPress={() => {
                setNewEntry(dominantTruthData.prefill);
                setDominantTruthPrefilled(true);
                inputRef.current?.focus();
              }}
              activeOpacity={0.6}
              accessibilityRole="button"
              accessibilityLabel="Use today's prompt"
            >
              <Text
                style={[styles.journalGhostPromptText, { color: theme.textTertiary }]}
                numberOfLines={1}
                ellipsizeMode="tail"
              >
                {dominantTruthData.question}
              </Text>
            </TouchableOpacity>
          )}

          {/* Primary writing surface — fills the visible viewport */}
          <View style={styles.journalInputSection}>
            <View style={styles.journalInputContainer}>
              <TextInput
                ref={inputRef}
                style={[
                  styles.journalInput,
                  { color: theme.text },
                ]}
                value={newEntry}
                onChangeText={handleTextChange}
                onFocus={handleInputFocus}
                onBlur={handleInputBlur}
                placeholder="What's here right now…"
                placeholderTextColor={theme.textTertiary}
                multiline
                maxLength={4000}
                editable={!isSubmitting}
                returnKeyType="default"
                blurOnSubmit={false}
                textAlignVertical="top"
              />
              {/* Soft, subtle save chip. Only appears once there is
                  content — never competes with the writing surface. */}
              {newEntry.trim().length > 0 && (
                <View style={styles.journalChipRow}>
                  <TouchableOpacity
                    style={[styles.journalDismissChip, { borderColor: theme.border }]}
                    onPress={dismissKeyboard}
                    accessibilityLabel="Hide keyboard"
                  >
                    <Text style={[styles.journalChipText, { color: theme.textSecondary }]}>
                      Hide keyboard
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[
                      styles.journalSaveChip,
                      { backgroundColor: theme.text },
                      isSubmitting && styles.submitButtonDisabled,
                    ]}
                    onPress={handleSubmit}
                    disabled={!newEntry.trim() || isSubmitting}
                    accessibilityLabel="Save entry"
                  >
                    {isSubmitting ? (
                      <ActivityIndicator size="small" color={theme.background} />
                    ) : (
                      <Text style={[styles.journalSaveChipText, { color: theme.background }]}>
                        Save
                      </Text>
                    )}
                  </TouchableOpacity>
                </View>
              )}
            </View>

            {/* Quick Reflect — only after meaningful content */}
            {newEntry.trim().length > 20 && (
              <TouchableOpacity
                style={[
                  styles.reflectCurrentButton,
                  reflectionModalVisible && styles.reflectButtonDisabled,
                ]}
                onPress={handleReflectCurrentEntry}
                disabled={reflectionModalVisible}
              >
                <Text style={{ fontSize: 16, color: reflectionModalVisible ? Colors.textTertiary : Colors.accent }}>✦</Text>
                <Text style={[
                  styles.reflectCurrentText,
                  reflectionModalVisible && styles.reflectTextDisabled,
                ]}>Quick Reflect</Text>
              </TouchableOpacity>
            )}
          </View>

            {error && (
              <View style={styles.errorContainer}>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            )}
            
            {/* FIX 8: "Captured" micro-feedback */}
            {showCapturedFeedback && (
              <View style={[styles.capturedFeedback, { backgroundColor: theme.success + '15' }]}>
                <Text style={[styles.capturedFeedbackText, { color: theme.success }]}>
                  ✓ Captured
                </Text>
              </View>
            )}

            {/* =================================================================
                JOURNAL FEED - ALL CONTENT IN ONE SCROLLABLE FLATLIST
                =================================================================
                The Latest Reflection Thread, Phase Mirror, Recognition cards,
                and older entries are ALL inside the FlatList scroll flow.
                This prevents scroll lock / clipping issues.
                ================================================================= */}
            {isLoading ? (
              <View style={styles.centered}>
                <ActivityIndicator size="large" color={theme.textSecondary} />
              </View>
            ) : (
              <FlatList
                ref={flatListRef}
                data={normalizeJournalEntries(journalEntries, 'FlatList:data').filter(
                  // Exclude the latest submitted entry - it's shown in the thread header
                  item => !latestSubmittedEntry || item.id !== latestSubmittedEntry.id
                )}
                extraData={`${Array.isArray(journalEntries) ? journalEntries.length : 0}-${highlightedEntryId}-${latestSubmittedEntry?.id}-${microMirrorVisible}-${patternReinforcement?.message}`}
                keyExtractor={(item) => item?.id || `fallback_${Math.random()}`}
                ListHeaderComponent={
                  <>
                    {/* LATEST REFLECTION THREAD - Now inside scroll flow */}
                    {latestSubmittedEntry && (
                      <View style={[styles.latestReflectionThread, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                        {/* USER'S ENTRY - Always visible first */}
                        <View style={styles.threadUserEntry}>
                          <View style={styles.threadEntryHeader}>
                            <Text style={[styles.threadLabel, { color: theme.textTertiary }]}>
                              You wrote
                            </Text>
                            {latestSubmittedEntry.isOptimistic && (
                              <Text style={[styles.threadSavingLabel, { color: theme.textTertiary }]}>
                                saving...
                              </Text>
                            )}
                          </View>
                          <Text style={[styles.threadEntryContent, { color: theme.text }]}>
                            {latestSubmittedEntry.content}
                          </Text>
                          {latestSubmittedEntry.phase_name && (
                            <Text style={[styles.threadPhaseTag, { color: theme.textTertiary }]}>
                              {latestSubmittedEntry.phase_name}
                            </Text>
                          )}
                        </View>

                        {/* MIRROR RESPONSE - Directly beneath user entry */}
                        {microMirrorVisible && microMirrorResponse && (
                          <View style={[styles.threadMirrorResponse, { borderTopColor: theme.border }]}>
                            <Text style={[styles.threadLabel, { color: theme.textTertiary }]}>
                              Mirror noticed
                            </Text>
                            <Text style={[styles.threadMirrorText, { color: theme.textSecondary }]}>
                              {microMirrorResponse}
                            </Text>
                            <View style={styles.threadMirrorActions}>
                              <TouchableOpacity
                                style={[styles.threadMirrorAction, { borderColor: theme.border }]}
                                onPress={handleMicroMirrorReflect}
                              >
                                <Text style={[styles.threadMirrorActionText, { color: theme.text }]}>
                                  Reflect deeper
                                </Text>
                              </TouchableOpacity>
                              <TouchableOpacity
                                style={[styles.threadMirrorAction, { borderColor: theme.border }]}
                                onPress={handleMicroMirrorAskMirror}
                              >
                                <Text style={[styles.threadMirrorActionText, { color: theme.text }]}>
                                  Talk to Mirror
                                </Text>
                              </TouchableOpacity>
                            </View>
                          </View>
                        )}

                        {/* PATTERN REINFORCEMENT - Beneath Mirror */}
                        {patternReinforcement && patternReinforcement.message && (
                          <TouchableOpacity
                            style={[styles.threadPatternRecognition, { borderTopColor: theme.border }]}
                            onPress={handlePatternReinforcementTap}
                            activeOpacity={patternReinforcement.route ? 0.7 : 1}
                            disabled={!patternReinforcement.route}
                          >
                            <Text style={[styles.threadLabel, { color: theme.textTertiary }]}>
                              Pattern recognized
                            </Text>
                            <Text style={[styles.threadPatternText, { color: theme.textSecondary }]}>
                              {patternReinforcement.message}
                              {patternReinforcement.route && ' →'}
                            </Text>
                          </TouchableOpacity>
                        )}

                        {/* DISMISS THREAD */}
                        <TouchableOpacity
                          style={styles.threadDismiss}
                          onPress={() => {
                            setLatestSubmittedEntry(null);
                            setMicroMirrorVisible(false);
                            setMicroMirrorResponse(null);
                            setPatternReinforcement(null);
                          }}
                        >
                          <Text style={[styles.threadDismissText, { color: theme.textTertiary }]}>
                            ✕
                          </Text>
                        </TouchableOpacity>
                      </View>
                    )}

                    {/* Phase Mirror Card - Timeline connection (inside scroll flow) */}
                    {phaseMirrorVisible && savedPhaseId && savedPhaseName && (
                      <PhaseMirrorCard
                        phaseId={savedPhaseId}
                        phaseName={savedPhaseName}
                        visible={phaseMirrorVisible}
                        onViewTimeline={handleViewTimeline}
                        onWriteDeeper={handleWriteDeeper}
                        onDismiss={handlePhaseMirrorDismiss}
                      />
                    )}

                    {/* Mini Connection Line - inside scroll flow */}
                    {normalizeJournalEntries(journalEntries).length > 0 && !phaseMirrorVisible && !latestSubmittedEntry && (
                      <Text style={[styles.connectionLine, { color: theme.textTertiary }]}>
                        What you write here may later become patterns you can see.
                      </Text>
                    )}

                    {/* Empty state message when no entries */}
                    {normalizeJournalEntries(journalEntries).length === 0 && !latestSubmittedEntry && (
                      <View style={styles.emptyContainer}>
                        <Text style={{ fontSize: 42, color: theme.textTertiary }}>☰</Text>
                        <Text style={[styles.emptyText, { color: theme.textSecondary }]}>No entries yet</Text>
                        <Text style={[styles.emptySubtext, { color: theme.textTertiary }]}>
                          Start journaling to track your reflections over time.
                        </Text>
                      </View>
                    )}
                  </>
                }
                renderItem={({ item }) => {
                  // HARDEN: Early return if item is invalid
                  if (!item || !item.id) {
                    console.warn('[JOURNAL] Invalid item in FlatList, skipping render');
                    return null;
                  }
                  return (
                    <JournalEntryItem
                      id={item.id}
                      content={item.content}
                      created_at={item.created_at}
                      themes={item.themes}
                      phase_id={item.phase_id}
                      phase_name={item.phase_name}
                      onReflect={(content) => handleReflect(item.id, content)}
                      onEdit={handleEditEntry}
                      onDelete={handleDeleteEntry}
                      onPhaseTap={handlePhaseTap}
                      isReflectDisabled={reflectionModalVisible}
                      isHighlighted={item.id === highlightedEntryId}
                    />
                  );
                }}
                contentContainerStyle={styles.listContent}
                showsVerticalScrollIndicator={false}
                keyboardDismissMode="on-drag"
                onScroll={handleScroll}
                scrollEventThrottle={16}
                onTouchStart={handleEntriesAreaPress}
                ListFooterComponent={
                  <>
                    {/* Key Moments Section - DEMOTED to footer, lower priority */}
                    {normalizeJournalEntries(journalEntries).length >= 2 && (
                      <KeyMomentsSection
                        journalEntries={normalizeJournalEntries(journalEntries)}
                        onMomentPress={(entry) => handleReflect(entry.id, entry.content)}
                        onReflectWithMirror={(entry) => handleReflect(entry.id, entry.content)}
                        maxMoments={3}
                      />
                    )}
                    {/* Bottom spacer to ensure content clears tab bar */}
                    <View style={{ height: 120 }} />
                  </>
                }
                ListEmptyComponent={
                  // Show nothing if we have the thread header visible
                  latestSubmittedEntry ? null : undefined
                }
              />
            )}
          </View>
      </KeyboardAvoidingView>

      {/* Mirror Reflection Modal (Quick Template-based) */}
      <MirrorReflectionModal
        visible={reflectionModalVisible}
        onClose={handleCloseModal}
        journalText={selectedJournalText}
        chart={chart}
      />

      {/* Phase Tag Modal - appears when user taps a phase pill on an entry */}
      <PhaseTagModal
        visible={phaseTagModalVisible}
        phaseId={selectedPhaseId}
        phaseName={selectedPhaseName}
        entryDate={selectedEntryDate}
        onClose={() => setPhaseTagModalVisible(false)}
        onSeeRelated={handleSeeRelatedEntries}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 24,
    paddingTop: 0,
    paddingBottom: 24,
  },
  // ---------------------------------------------------------------------
  // REFLECT V3 — entry chooser & soft return link
  // ---------------------------------------------------------------------
  entryScreen: {
    flex: 1,
    paddingHorizontal: 28,
    paddingTop: 64,
    paddingBottom: 32,
    justifyContent: 'flex-start',
  },
  entryHeader: {
    marginBottom: 56,
  },
  entryTitle: {
    fontSize: 34,
    fontWeight: '300',
    letterSpacing: -0.6,
    marginBottom: 12,
  },
  entrySubtitle: {
    fontSize: 17,
    lineHeight: 24,
    fontWeight: '300',
    opacity: 0.85,
  },
  entryCardsWrap: {
    gap: 16,
  },
  entryCard: {
    paddingHorizontal: 24,
    paddingTop: 28,
    paddingBottom: 24,
    borderRadius: 20,
    // No hard border — relies on a soft surface lift for separation.
  },
  entryCardTitle: {
    fontSize: 22,
    fontWeight: '500',
    letterSpacing: -0.2,
    marginBottom: 6,
  },
  entryCardSubtitle: {
    fontSize: 15,
    lineHeight: 21,
    fontWeight: '300',
    opacity: 0.8,
    marginBottom: 24,
  },
  entryCardCtaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  entryCardCta: {
    fontSize: 15,
    fontWeight: '500',
    letterSpacing: 0.2,
  },
  entryCardCtaArrow: {
    fontSize: 16,
    fontWeight: '400',
    opacity: 0.6,
  },
  softReturnRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 4,
  },
  softReturnButton: {
    paddingVertical: 6,
    paddingHorizontal: 6,
    minHeight: 32,
    justifyContent: 'center',
  },
  softReturnText: {
    fontSize: 14,
    fontWeight: '400',
    letterSpacing: 0.2,
    opacity: 0.85,
  },
  buildMarkerFooter: {
    marginTop: 'auto',
    paddingTop: 24,
    alignItems: 'center',
  },
  buildMarkerText: {
    fontSize: 10,
    letterSpacing: 0.4,
    opacity: 0.4,
    fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }),
  },
  // =============================================================================
  // LATEST REFLECTION THREAD STYLES
  // =============================================================================
  // A unified block showing: User Entry → Mirror Response → Pattern Recognition
  // This creates a threaded conversation feel after submit
  // =============================================================================
  latestReflectionThread: {
    marginHorizontal: 0,
    marginBottom: 16,
    borderRadius: 16,
    borderWidth: 1,
    overflow: 'hidden',
    position: 'relative',
  },
  threadUserEntry: {
    padding: 16,
    paddingBottom: 14,
  },
  threadEntryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  threadLabel: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  threadSavingLabel: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  threadEntryContent: {
    fontSize: 17,
    lineHeight: 30,
  },
  threadPhaseTag: {
    fontSize: 14,
    marginTop: 8,
    fontStyle: 'italic',
  },
  threadMirrorResponse: {
    padding: 16,
    paddingTop: 14,
    borderTopWidth: 1,
  },
  threadMirrorText: {
    fontSize: 16,
    lineHeight: 30,
    fontStyle: 'italic',
    marginTop: 6,
  },
  threadMirrorActions: {
    flexDirection: 'row',
    marginTop: 12,
    gap: 8,
  },
  threadMirrorAction: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 20,
    borderWidth: 1,
  },
  threadMirrorActionText: {
    fontSize: 16,
    fontWeight: '500',
  },
  threadPatternRecognition: {
    padding: 16,
    paddingTop: 14,
    borderTopWidth: 1,
  },
  threadPatternText: {
    fontSize: 16,
    lineHeight: 32,
    marginTop: 4,
    fontStyle: 'italic',
  },
  threadDismiss: {
    position: 'absolute',
    top: 10,
    right: 12,
    padding: 6,
  },
  threadDismissText: {
    fontSize: 16,
    fontWeight: '300',
  },
  // Pattern Reinforcement Card - subtle recognition after journal save
  reinforcementCard: {
    marginHorizontal: 24,
    marginTop: 8,
    marginBottom: 4,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
  },
  reinforcementText: {
    fontSize: 16,
    lineHeight: 31,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  // Mirror Leader Card wrapper
  mirrorLeaderCardWrapper: {
    paddingHorizontal: 24,
    paddingTop: 8,
  },
  // Dominant Truth Prompt Card (Master Layer Integration) - COMPACT VERSION
  dominantTruthPromptCard: {
    marginHorizontal: 24,
    marginBottom: 14, // Reduced from 16
    paddingVertical: 10, // Reduced from 16
    paddingHorizontal: 14,
    borderRadius: 10,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  dominantTruthPromptLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.6,
    color: Colors.accent,
    marginBottom: 3, // Reduced from 8
  },
  dominantTruthPromptQuestion: {
    fontSize: 16, // Reduced from 15
    lineHeight: 31, // Reduced from 22
    fontStyle: 'italic',
    flex: 1,
  },
  dominantTruthPromptCTA: {
    fontSize: 14, // Reduced from 13
    fontWeight: '600',
    marginLeft: 10,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  // Mode Toggle - tighter spacing
  modeToggleContainer: {
    flexDirection: 'row',
    backgroundColor: Colors.surface,
    borderRadius: 10,
    padding: 3,
    marginHorizontal: 24,
    marginTop: 10, // Reduced from 16
    marginBottom: 14, // Reduced from 16
  },
  modeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8, // Reduced from 10
    borderRadius: 8,
    gap: 5,
  },
  modeButtonActive: {
    backgroundColor: Colors.accent + '15',
  },
  modeButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  modeButtonTextActive: {
    color: Colors.accent,
    fontWeight: '600',
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 14,
  },
  subtitle: {
    fontSize: 16,
    color: Colors.textTertiary,
  },
  inputSection: {
    marginBottom: 16, // Reduced from 24 - tighter spacing
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
  },
  input: {
    flex: 1,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    fontSize: 17,
    color: Colors.text,
    minHeight: 120, // Increased from 80 - much larger writing area
    maxHeight: 200, // Increased from 160
    marginRight: 12,
    textAlignVertical: 'top',
  },

  // ─────────────────────────────────────────────────────────────
  // REFLECT V4 — Journal redesign styles (May 2026)
  // ─────────────────────────────────────────────────────────────
  // The writing surface is now the visual anchor of the screen.
  // Chrome is intentionally light: no card background, no border,
  // generous line height. The save / hide-keyboard chips sit below
  // the textarea so the writing area itself is never crowded.
  journalGhostPrompt: {
    paddingHorizontal: 4,
    paddingVertical: 8,
    marginBottom: 4,
  },
  journalGhostPromptText: {
    fontSize: 14,
    fontStyle: 'italic',
    letterSpacing: 0.1,
  },
  journalInputSection: {
    flex: 1,
    marginBottom: 16,
  },
  journalInputContainer: {
    flex: 1,
  },
  journalInput: {
    flex: 1,
    backgroundColor: 'transparent',
    paddingHorizontal: 4,
    paddingVertical: 8,
    fontSize: 19,
    lineHeight: 30,
    minHeight: 280,
    textAlignVertical: 'top',
  },
  journalChipRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: 8,
    marginTop: 12,
  },
  journalDismissChip: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: StyleSheet.hairlineWidth,
  },
  journalSaveChip: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    minWidth: 72,
    alignItems: 'center',
  },
  journalChipText: {
    fontSize: 14,
    fontWeight: '500',
  },
  journalSaveChipText: {
    fontSize: 14,
    fontWeight: '600',
  },
  inputActions: {
    flexDirection: 'column',
    gap: 8,
  },
  dismissButton: {
    width: 48,
    height: 48,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  submitButton: {
    width: 48,
    height: 48,
    backgroundColor: Colors.text,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  submitButtonDisabled: {
    opacity: 0.4,
  },
  reflectCurrentButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 12,
    paddingVertical: 10,
    backgroundColor: Colors.accent + '12',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Colors.accent + '30',
  },
  reflectButtonDisabled: {
    backgroundColor: Colors.surface,
    borderColor: Colors.border,
  },
  reflectCurrentText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.accent,
  },
  reflectTextDisabled: {
    color: Colors.textTertiary,
  },
  errorContainer: {
    backgroundColor: Colors.error + '20',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 16,
    color: Colors.error,
  },
  // FIX 8: Captured feedback styles
  capturedFeedback: {
    marginTop: 8,
    marginBottom: 14,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignSelf: 'center',
  },
  capturedFeedbackText: {
    fontSize: 16,
    fontWeight: '600',
  },
  listContent: {
    paddingBottom: 120, // Extra padding for PWA banner overlay
  },
  // Mini connection line style
  connectionLine: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
    marginBottom: 16,
    marginTop: 4,
  },
  // Reverse Prompt Card styles (Journal ↔ Timeline connection)
  reversePromptCard: {
    marginTop: 10,
    marginBottom: 14,
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
  },
  reversePromptLabel: {
    fontSize: 14,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  reversePromptText: {
    fontSize: 16,
    lineHeight: 25,
    fontStyle: 'italic',
  },
  reversePromptHint: {
    fontSize: 14,
    marginTop: 8,
    fontStyle: 'italic',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyText: {
    fontSize: 22,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 16,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginTop: 8,
    maxWidth: 250,
  },
  // Journal Timeline styles
  timelineContainer: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  timelineHeader: {
    paddingHorizontal: 24,
    paddingTop: 8,
    paddingBottom: 16,
  },
  timelineTitle: {
    fontSize: 22,
    fontWeight: '600',
    color: Colors.text,
    letterSpacing: -0.3,
  },
  timelineSubtitle: {
    fontSize: 16,
    color: Colors.textTertiary,
    marginTop: 4,
    fontStyle: 'italic',
  },
  timelineList: {
    paddingHorizontal: 24,
    paddingBottom: 32,
  },
  timelineDateGroup: {
    marginBottom: 24,
  },
  timelineDateHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  timelineDateDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 10,
  },
  timelineDateLabel: {
    fontSize: 17,
    fontWeight: '600',
    flex: 1,
  },
  timelineEntryCount: {
    fontSize: 14,
  },
  timelineEntriesLine: {
    borderLeftWidth: 2,
    marginLeft: 4,
    paddingLeft: 18,
    gap: 12,
  },
  timelineEntryCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
  },
  timelineEntryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  timelineEntryTime: {
    fontSize: 14,
    fontWeight: '500',
  },
  timelineThemes: {
    flexDirection: 'row',
    gap: 6,
  },
  timelineThemeChip: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
  },
  timelineThemeText: {
    fontSize: 14,
    fontWeight: '500',
  },
  timelineEntryPreview: {
    fontSize: 16,
    lineHeight: 25,
    marginBottom: 16,
  },
  timelineReflectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
  },
  timelineReflectText: {
    fontSize: 14,
    fontWeight: '500',
  },
  timelineEmpty: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  timelineEmptyTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginTop: 16,
  },
  timelineEmptySubtext: {
    fontSize: 16,
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 25,
  },
  timelineStartButton: {
    marginTop: 20,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 10,
  },
  timelineStartButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  // Mirror Insight card styles
  timelineInsightCard: {
    borderWidth: 1,
  },
  insightLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  insightLabel: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  journalLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  journalLabel: {
    fontSize: 14,
    fontWeight: '500',
  },
  timelineInsightText: {
    fontSize: 17,
    lineHeight: 30,
    fontStyle: 'italic',
    marginBottom: 14,
  },
  // Task 51: Lunar Decision Journal Styles
  lunarSubNav: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  lunarSubNavButton: {
    paddingVertical: 6,
    paddingHorizontal: 2,
  },
  lunarSubNavButtonActive: {
    borderBottomWidth: 2,
    borderBottomColor: '#C0C8D4',
  },
  lunarSubNavText: {
    fontSize: 16,
    color: Colors.textSecondary,
  },
  lunarSubNavTextActive: {
    color: '#C0C8D4',
    fontWeight: '600',
  },
  lunarPromptCard: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
    marginBottom: 16,
  },
  lunarPromptLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 6,
  },
  lunarPromptText: {
    fontSize: 16,
    lineHeight: 30,
    fontStyle: 'italic',
  },
  // Task 54: Success banner styles
  lunarSuccessBanner: {
    marginBottom: 16,
    padding: 12,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  lunarSuccessText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#81C784',
  },
  // ═══════════════════════════════════════════════════════════════════════════
  // Task 62: Lunar Tab UX Restructure Styles
  // ═══════════════════════════════════════════════════════════════════════════
  lunarIntroCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  lunarIntroTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 14,
    letterSpacing: -0.3,
  },
  lunarIntroText: {
    fontSize: 16,
    lineHeight: 30,
  },
  lunarWheelSection: {
    marginBottom: 16,
    alignItems: 'center',
  },
  lunarWheelInstruction: {
    fontSize: 14,
    fontStyle: 'italic',
    marginTop: 8,
    textAlign: 'center',
  },
  lunarReflectionCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  lunarReflectionLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 14,
  },
  lunarReflectionGateInfo: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 14,
  },
  lunarReflectionGate: {
    fontSize: 17,
    fontWeight: '600',
  },
  lunarReflectionGateTitle: {
    fontSize: 16,
    marginLeft: 4,
  },
  lunarReflectionPrompt: {
    fontSize: 16,
    lineHeight: 30,
    fontStyle: 'italic',
  },
  lunarJournalInputSection: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  lunarJournalInputLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 6,
  },
  lunarJournalInputPrompt: {
    fontSize: 16,
    marginBottom: 16,
  },
  lunarJournalInputContainer: {
    gap: 10,
  },
  lunarJournalInput: {
    borderRadius: 10,
    borderWidth: 1,
    padding: 12,
    fontSize: 16,
    lineHeight: 25,
    minHeight: 80,
  },
  lunarJournalSubmitButton: {
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 20,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'flex-end',
  },
  lunarTimelineSection: {
    marginBottom: 16,
  },
  lunarTimelineSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  lunarSynthesisSection: {
    marginBottom: 16,
  },
  lunarLimitNote: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 20,
  },
  lunarLimitNoteText: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
    lineHeight: 31,
  },
  // ═══════════════════════════════════════════════════════════════════════════
  // Task 63: Decision-First Lunar UX Styles
  // ═══════════════════════════════════════════════════════════════════════════
  decisionsSectionHeader: {
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  decisionsSectionTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 4,
    letterSpacing: -0.3,
  },
  decisionsSectionSubtitle: {
    fontSize: 16,
    lineHeight: 31,
  },
  decisionCard: {
    borderRadius: 12,
    borderWidth: 1.5,
    padding: 14,
    marginBottom: 16,
  },
  decisionCardActive: {
    borderWidth: 1.5,
  },
  decisionCardContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  decisionCardIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(192, 200, 212, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  decisionCardText: {
    flex: 1,
  },
  decisionCardTopic: {
    fontSize: 16,
    fontWeight: '500',
    lineHeight: 25,
    marginBottom: 4,
  },
  decisionCardDays: {
    fontSize: 14,
  },
  decisionCardBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  decisionCardBadgeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#81C784',
  },
  decisionCardProgress: {
    height: 3,
    borderRadius: 1.5,
    marginTop: 12,
    overflow: 'hidden',
  },
  decisionCardProgressFill: {
    height: '100%',
    backgroundColor: '#C0C8D4',
    borderRadius: 1.5,
  },
  noDecisionsCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 24,
    marginBottom: 16,
    alignItems: 'center',
  },
  noDecisionsTitle: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 14,
  },
  noDecisionsText: {
    fontSize: 16,
    lineHeight: 32,
    textAlign: 'center',
  },
  addDecisionSection: {
    marginBottom: 14,
  },
  simpleAddButton: {
    borderWidth: 1.5,
    borderRadius: 10,
    borderStyle: 'dashed',
    paddingVertical: 14,
    paddingHorizontal: 20,
    alignItems: 'center',
    marginBottom: 16,
  },
  simpleAddButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  decisionLimitNote: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginBottom: 16,
  },
  decisionLimitNoteText: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
    lineHeight: 17,
  },
  selectedDecisionCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  selectedDecisionLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 14,
  },
  selectedDecisionTopic: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 6,
    lineHeight: 30,
  },
  selectedDecisionDays: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  // Task 64: Today's Reflection Card Styles
  todayReflectionCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  todayReflectionHeader: {
    marginBottom: 16,
  },
  todayReflectionTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 4,
  },
  todayGateInfo: {
    flexDirection: 'row',
    alignItems: 'baseline',
    flexWrap: 'wrap',
  },
  todayGateText: {
    fontSize: 16,
  },
  todayGateTitle: {
    fontSize: 16,
    marginLeft: 4,
  },
  todayPrompt: {
    fontSize: 16,
    marginBottom: 16,
    fontStyle: 'italic',
  },
  todayInput: {
    borderRadius: 10,
    borderWidth: 1,
    padding: 12,
    fontSize: 16,
    lineHeight: 25,
    minHeight: 100,
    marginBottom: 16,
  },
  addReflectionButton: {
    borderRadius: 8,
    paddingVertical: 14,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addReflectionButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#1A1D24',
  },
  // Task 64: Reflection Timeline Styles
  reflectionTimelineSection: {
    marginBottom: 16,
  },
  reflectionTimelineTitle: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  reflectionEntry: {
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  reflectionEntryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
    gap: 8,
  },
  reflectionEntryDay: {
    fontSize: 16,
    fontWeight: '600',
  },
  reflectionEntryGate: {
    fontSize: 14,
  },
  // Task 68: Improved reflection entry card styling
  reflectionEntryCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    marginBottom: 14,
  },
  reflectionEntryMeta: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 6,
  },
  reflectionEntryContent: {
    fontSize: 16,
    lineHeight: 25,
    fontStyle: 'italic',
  },
  reflectionEntryDate: {
    fontSize: 14,
  },
  // New styles for restructured lunar view
  decisionSelectorSection: {
    marginBottom: 16,
  },
  decisionSelectorScroll: {
    paddingHorizontal: 4,
  },
  // Task 68: Improved scroll content styling
  decisionSelectorScrollContent: {
    paddingLeft: 16,
    paddingRight: 12,
  },
  decisionSelectorPill: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    marginRight: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  decisionSelectorText: {
    fontSize: 16,
    fontWeight: '500',
  },
  decisionSelectorDot: {
    fontSize: 8,
    fontWeight: '600',
  },
  decisionHeaderCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
    marginBottom: 16,
  },
  decisionHeaderLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 14,
  },
  decisionHeaderTopic: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 14,
    lineHeight: 32,
  },
  decisionHeaderStatus: {
    fontSize: 16,
    marginBottom: 16,
  },
  // Task 68: Improved status row styling
  decisionHeaderStatusRow: {
    marginBottom: 16,
  },
  decisionHeaderStatusDay: {
    fontSize: 17,
    fontWeight: '500',
    marginBottom: 2,
  },
  decisionHeaderStatusPhase: {
    fontSize: 16,
  },
  decisionHeaderDivider: {
    height: 1,
    marginVertical: 12,
  },
  decisionHeaderDescription: {
    fontSize: 16,
    lineHeight: 31,
  },
  noDecisionCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 24,
    alignItems: 'center',
    marginBottom: 16,
  },
  noDecisionTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 14,
    textAlign: 'center',
  },
  noDecisionText: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 25,
    marginBottom: 20,
  },
  instructionCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 16,
  },
  instructionTitle: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 14,
  },
  instructionText: {
    fontSize: 16,
    lineHeight: 31,
  },
  todaysLensCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
    marginBottom: 16,
  },
  todaysLensLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 14,
  },
  todaysLensGate: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  // Task 68: Gate/Line styling
  todaysLensGateRow: {
    marginBottom: 14,
  },
  todaysLensLine: {
    fontSize: 14,
    marginTop: 2,
  },
  todaysLensTheme: {
    fontSize: 16,
    marginBottom: 16,
    fontStyle: 'italic',
  },
  todaysLensDivider: {
    height: 1,
    marginVertical: 12,
  },
  // Task 68: Improved observation row styling
  todaysLensObservationRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  todaysLensObservationIcon: {
    fontSize: 16,
    marginRight: 8,
    marginTop: 1,
  },
  todaysLensObservation: {
    fontSize: 16,
    lineHeight: 31,
    flex: 1,
  },
  todaysLensPromptBox: {
    borderRadius: 8,
    padding: 12,
  },
  todaysLensPromptLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 6,
  },
  todaysLensPrompt: {
    fontSize: 16,
    lineHeight: 31,
    fontWeight: '500',
  },
  reflectionInputCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
    marginBottom: 16,
  },
  reflectionInputLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 16,
  },
  reflectionTextInput: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    fontSize: 17,
    minHeight: 120,
    textAlignVertical: 'top',
    marginBottom: 16,
  },
  saveReflectionButton: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  saveReflectionButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#1A1D24',
  },
  lunarWheelSectionLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 4,
  },
  lunarWheelSectionHint: {
    fontSize: 14,
    marginBottom: 16,
  },
  addAnotherSection: {
    marginTop: 8,
    marginBottom: 16,
  },
  addAnotherButton: {
    borderRadius: 12,
    borderWidth: 1,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addAnotherButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  // Task 67: Cycle Completion Banner styles
  cycleCompletionBanner: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 16,
  },
  cycleCompletionBannerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  cycleCompletionBannerIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  cycleCompletionBannerText: {
    flex: 1,
  },
  cycleCompletionBannerTitle: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 2,
  },
  cycleCompletionBannerSubtitle: {
    fontSize: 16,
  },
  cycleCompletionBannerButton: {
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cycleCompletionBannerButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1A1D24',
  },
  cycleCompletionBannerBody: {
    fontSize: 16,
    lineHeight: 31,
    marginTop: 4,
  },
  // Task 70: Debug Panel styles
  debugPanel: {
    borderRadius: 12,
    borderWidth: 2,
    padding: 16,
    marginBottom: 16,
    marginTop: 8,
  },
  debugPanelTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 14,
  },
  debugPanelSubtitle: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 12,
    marginBottom: 4,
  },
  debugPanelText: {
    fontSize: 14,
    fontFamily: 'monospace',
    lineHeight: 30,
  },
  // ============================================
  // DECISION JOURNEY CARD STYLES
  // ============================================
  journeyCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
    marginBottom: 16,
  },
  journeyDayRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  journeyDayIcon: {
    fontSize: 22,
    marginRight: 8,
  },
  journeyDayText: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  journeyPhaseLabel: {
    fontSize: 24,
    fontWeight: '600',
    lineHeight: 32,
    marginBottom: 16,
  },
  journeyHook: {
    fontSize: 17,
    lineHeight: 32,
    marginBottom: 16,
  },
  journeyDecisionAnchor: {
    paddingTop: 16,
    borderTopWidth: 1,
    marginTop: 4,
  },
  journeyDecisionLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  journeyDecisionTopic: {
    fontSize: 16,
    fontWeight: '500',
    lineHeight: 32,
    fontStyle: 'italic',
  },
  journeyStartCta: {
    borderRadius: 12,
    borderWidth: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
    marginTop: 12,
  },
  journeyStartCtaText: {
    fontSize: 16,
    fontWeight: '500',
  },
  journeyCompletionBanner: {
    borderRadius: 10,
    padding: 16,
    marginTop: 16,
  },
  journeyCompletionText: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 4,
  },
  journeyCompletionSub: {
    fontSize: 16,
    lineHeight: 25,
  },
});
