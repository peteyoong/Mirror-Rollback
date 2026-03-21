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
import { useLocalSearchParams } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { Colors } from '../../constants/colors';
import { useAppStore, storage } from '../../store';
import JournalEntryItem from '../../components/JournalEntryItem';
import MirrorReflectionModal from '../../components/MirrorReflectionModal';
import MirrorChat from '../../components/MirrorChat';
import { createJournalEntry, getJournalEntries, getCombinedTimeline, TimelineItem } from '../../services/api';
import api from '../../services/api';
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
import MirrorLeaderCard from '../../components/journal/MirrorLeaderCard';
// Removed Ionicons - using text-based alternatives for web compatibility

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

// ViewMode updated: Timeline removed from UI per product requirements
type ViewMode = 'journal' | 'mirror' | 'lunar' | 'lunar-history';

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

export default function JournalScreen() {
  const { user, chart, journalEntries, setJournalEntries, addJournalEntry } = useAppStore();
  const { theme, isDark } = useTheme();
  const params = useLocalSearchParams<{ 
    view?: string; 
    fromKeystone?: string;
    prefillPrompt?: string;
    journalSource?: string;
    category?: string;
    tensionPair?: string;
  }>();
  const [viewMode, setViewMode] = useState<ViewMode>('journal');
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
      const entries = await getJournalEntries(user.id);
      setJournalEntries(entries);
    } catch (err) {
      console.error('Load entries error:', err);
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
      // Fallback to journal entries only
      setTimelineItems(journalEntries.map(entry => ({
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

    Keyboard.dismiss();
    setIsSubmitting(true);
    setError('');

    try {
      // Include pattern metadata if present
      const metadata = patternMetadata ? {
        journal_source: patternMetadata.journal_source,
        pattern_category: patternMetadata.pattern_category,
        pattern_tension_pair: patternMetadata.pattern_tension_pair,
        prompt_text: patternMetadata.prompt_text
      } : undefined;
      
      const entry = await createJournalEntry(user.id, newEntry.trim(), metadata);
      addJournalEntry(entry);
      setNewEntry('');
      
      // Clear pattern metadata after successful submission
      setPatternMetadata(null);
    } catch (err: any) {
      console.error('Create entry error:', err);
      setError('Unable to save entry. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const dismissKeyboard = () => {
    Keyboard.dismiss();
  };

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

  // Render the mode toggle (Journal | Mirror) - Timeline REMOVED per product requirements
  const renderModeToggle = () => {
    // Check if user is a Reflector based on lunar status
    const isReflector = lunarStatus?.is_reflector === true;
    
    return (
      <View style={styles.modeToggleContainer}>
        <TouchableOpacity
          style={[styles.modeButton, viewMode === 'journal' && styles.modeButtonActive]}
          onPress={() => setViewMode('journal')}
        >
          <Text style={{ fontSize: 14, color: viewMode === 'journal' ? Colors.accent : Colors.textSecondary }}>☰</Text>
          <Text style={[styles.modeButtonText, viewMode === 'journal' && styles.modeButtonTextActive]}>
            Journal
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.modeButton, viewMode === 'mirror' && styles.modeButtonActive]}
          onPress={() => setViewMode('mirror')}
        >
          <Text style={{ fontSize: 14, color: viewMode === 'mirror' ? Colors.accent : Colors.textSecondary }}>✦</Text>
          <Text style={[styles.modeButtonText, viewMode === 'mirror' && styles.modeButtonTextActive]}>
            Mirror
          </Text>
        </TouchableOpacity>
        {/* Task 51: Lunar Journal tab for Reflectors */}
        {isReflector && (
          <TouchableOpacity
            style={[styles.modeButton, (viewMode === 'lunar' || viewMode === 'lunar-history') && styles.modeButtonActive]}
            onPress={() => setViewMode('lunar')}
          >
            <Text style={{ fontSize: 14, color: (viewMode === 'lunar' || viewMode === 'lunar-history') ? '#C0C8D4' : Colors.textSecondary }}>🌙</Text>
            <Text style={[styles.modeButtonText, (viewMode === 'lunar' || viewMode === 'lunar-history') && { color: '#C0C8D4' }]}>
              Lunar
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
                    placeholder="What did you notice today about this decision?"
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
        
        {/* Mirror Leader Card - Emotional framing */}
        <View style={styles.mirrorLeaderCardWrapper}>
          <MirrorLeaderCard />
        </View>
        
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

          {/* Journal Leader Card - Emotional framing */}
          <JournalLeaderCard />

          {/* New Entry Input */}
          <View style={styles.inputSection}>
            <View style={styles.inputContainer}>
              <TextInput
                ref={inputRef}
                style={[styles.input, { backgroundColor: theme.surface, color: theme.text }]}
                value={newEntry}
                onChangeText={(text) => {
                  console.log('[JOURNAL_DEBUG] onChangeText:', text.length, 'chars');
                  setNewEntry(text);
                }}
                onFocus={() => console.log('[JOURNAL_DEBUG] Input FOCUSED')}
                onBlur={() => console.log('[JOURNAL_DEBUG] Input BLURRED')}
                placeholder="What's on your mind?"
                placeholderTextColor={theme.textTertiary}
                multiline
                maxLength={2000}
                editable={!isSubmitting}
                returnKeyType="default"
                blurOnSubmit={false}
              />
              <View style={styles.inputActions}>
                {newEntry.trim().length > 0 && (
                  <TouchableOpacity
                    style={[styles.dismissButton, { backgroundColor: theme.surfaceLight }]}
                    onPress={dismissKeyboard}
                  >
                    <Text style={{ fontSize: 18, color: theme.textSecondary }}>▼</Text>
                  </TouchableOpacity>
                )}
                <TouchableOpacity
                  style={[
                    styles.submitButton,
                    { backgroundColor: theme.text },
                    (!newEntry.trim() || isSubmitting) && styles.submitButtonDisabled,
                  ]}
                  onPress={() => {
                    console.log('[JOURNAL_DEBUG] Submit button pressed, entry length:', newEntry.trim().length);
                    handleSubmit();
                  }}
                  disabled={!newEntry.trim() || isSubmitting}
                >
                  {isSubmitting ? (
                    <ActivityIndicator size="small" color={theme.background} />
                  ) : (
                    <Text style={{ fontSize: 18, color: theme.background }}>✓</Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
              
              {/* Reflect with Mirror button for current entry */}
              {newEntry.trim().length > 20 && (
                <TouchableOpacity 
                  style={[
                    styles.reflectCurrentButton,
                    reflectionModalVisible && styles.reflectButtonDisabled
                  ]}
                  onPress={handleReflectCurrentEntry}
                  disabled={reflectionModalVisible}
                >
                  <Text style={{ fontSize: 14, color: reflectionModalVisible ? Colors.textTertiary : Colors.accent }}>✦</Text>
                  <Text style={[
                    styles.reflectCurrentText,
                    reflectionModalVisible && styles.reflectTextDisabled
                  ]}>Quick Reflect</Text>
                </TouchableOpacity>
              )}
            </View>

            {error && (
              <View style={styles.errorContainer}>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            )}

            {/* Entries List */}
            {isLoading ? (
              <View style={styles.centered}>
                <ActivityIndicator size="large" color={theme.textSecondary} />
              </View>
            ) : journalEntries.length === 0 ? (
              <View style={styles.emptyContainer}>
                <Text style={{ fontSize: 42, color: theme.textTertiary }}>☰</Text>
                <Text style={[styles.emptyText, { color: theme.textSecondary }]}>No entries yet</Text>
                <Text style={[styles.emptySubtext, { color: theme.textTertiary }]}>
                  Start journaling to track your reflections over time.
                </Text>
              </View>
            ) : (
              <FlatList
                data={journalEntries}
                keyExtractor={(item) => item.id}
                renderItem={({ item }) => (
                  <JournalEntryItem
                    content={item.content}
                    created_at={item.created_at}
                    themes={item.themes}
                    onReflect={(content) => handleReflect(item.id, content)}
                    isReflectDisabled={reflectionModalVisible}
                  />
                )}
                contentContainerStyle={styles.listContent}
                showsVerticalScrollIndicator={false}
                keyboardDismissMode="on-drag"
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
  // Mirror Leader Card wrapper
  mirrorLeaderCardWrapper: {
    paddingHorizontal: 24,
    paddingTop: 8,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  // Mode Toggle
  modeToggleContainer: {
    flexDirection: 'row',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 4,
    marginHorizontal: 24,
    marginTop: 16,
    marginBottom: 16,
  },
  modeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: 10,
    gap: 6,
  },
  modeButtonActive: {
    backgroundColor: Colors.accent + '15',
  },
  modeButtonText: {
    fontSize: 14,
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
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.textTertiary,
  },
  inputSection: {
    marginBottom: 24,
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
    fontSize: 15,
    color: Colors.text,
    minHeight: 80,
    maxHeight: 160,
    marginRight: 12,
    textAlignVertical: 'top',
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
    fontSize: 13,
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
    fontSize: 13,
    color: Colors.error,
  },
  listContent: {
    paddingBottom: 120, // Extra padding for PWA banner overlay
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
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
    fontSize: 13,
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
    marginBottom: 12,
  },
  timelineDateDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 10,
  },
  timelineDateLabel: {
    fontSize: 15,
    fontWeight: '600',
    flex: 1,
  },
  timelineEntryCount: {
    fontSize: 12,
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
    marginBottom: 8,
  },
  timelineEntryTime: {
    fontSize: 12,
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
    fontSize: 10,
    fontWeight: '500',
  },
  timelineEntryPreview: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
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
    fontSize: 12,
    fontWeight: '500',
  },
  timelineEmpty: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  timelineEmptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 16,
  },
  timelineEmptySubtext: {
    fontSize: 14,
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 20,
  },
  timelineStartButton: {
    marginTop: 20,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 10,
  },
  timelineStartButtonText: {
    fontSize: 14,
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
    fontSize: 12,
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
    fontSize: 12,
    fontWeight: '500',
  },
  timelineInsightText: {
    fontSize: 15,
    lineHeight: 22,
    fontStyle: 'italic',
    marginBottom: 10,
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
    fontSize: 14,
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
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 6,
  },
  lunarPromptText: {
    fontSize: 14,
    lineHeight: 21,
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
    fontSize: 14,
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
    marginBottom: 8,
    letterSpacing: -0.3,
  },
  lunarIntroText: {
    fontSize: 14,
    lineHeight: 21,
  },
  lunarWheelSection: {
    marginBottom: 16,
    alignItems: 'center',
  },
  lunarWheelInstruction: {
    fontSize: 12,
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
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 10,
  },
  lunarReflectionGateInfo: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 10,
  },
  lunarReflectionGate: {
    fontSize: 15,
    fontWeight: '600',
  },
  lunarReflectionGateTitle: {
    fontSize: 14,
    marginLeft: 4,
  },
  lunarReflectionPrompt: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
  lunarJournalInputSection: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  lunarJournalInputLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 6,
  },
  lunarJournalInputPrompt: {
    fontSize: 13,
    marginBottom: 12,
  },
  lunarJournalInputContainer: {
    gap: 10,
  },
  lunarJournalInput: {
    borderRadius: 10,
    borderWidth: 1,
    padding: 12,
    fontSize: 14,
    lineHeight: 20,
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
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 12,
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
    fontSize: 12,
    fontStyle: 'italic',
    textAlign: 'center',
    lineHeight: 18,
  },
  // ═══════════════════════════════════════════════════════════════════════════
  // Task 63: Decision-First Lunar UX Styles
  // ═══════════════════════════════════════════════════════════════════════════
  decisionsSectionHeader: {
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  decisionsSectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
    letterSpacing: -0.3,
  },
  decisionsSectionSubtitle: {
    fontSize: 13,
    lineHeight: 18,
  },
  decisionCard: {
    borderRadius: 12,
    borderWidth: 1.5,
    padding: 14,
    marginBottom: 12,
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
    fontSize: 14,
    fontWeight: '500',
    lineHeight: 20,
    marginBottom: 4,
  },
  decisionCardDays: {
    fontSize: 12,
  },
  decisionCardBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  decisionCardBadgeText: {
    fontSize: 11,
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
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 8,
  },
  noDecisionsText: {
    fontSize: 13,
    lineHeight: 19,
    textAlign: 'center',
  },
  addDecisionSection: {
    marginBottom: 8,
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
    fontSize: 14,
    fontWeight: '500',
  },
  decisionLimitNote: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginBottom: 16,
  },
  decisionLimitNoteText: {
    fontSize: 12,
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
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 8,
  },
  selectedDecisionTopic: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 6,
    lineHeight: 22,
  },
  selectedDecisionDays: {
    fontSize: 13,
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
    marginBottom: 12,
  },
  todayReflectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  todayGateInfo: {
    flexDirection: 'row',
    alignItems: 'baseline',
    flexWrap: 'wrap',
  },
  todayGateText: {
    fontSize: 14,
  },
  todayGateTitle: {
    fontSize: 13,
    marginLeft: 4,
  },
  todayPrompt: {
    fontSize: 14,
    marginBottom: 12,
    fontStyle: 'italic',
  },
  todayInput: {
    borderRadius: 10,
    borderWidth: 1,
    padding: 12,
    fontSize: 14,
    lineHeight: 20,
    minHeight: 100,
    marginBottom: 12,
  },
  addReflectionButton: {
    borderRadius: 8,
    paddingVertical: 14,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addReflectionButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1A1D24',
  },
  // Task 64: Reflection Timeline Styles
  reflectionTimelineSection: {
    marginBottom: 16,
  },
  reflectionTimelineTitle: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 12,
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
    fontSize: 13,
    fontWeight: '600',
  },
  reflectionEntryGate: {
    fontSize: 12,
  },
  // Task 68: Improved reflection entry card styling
  reflectionEntryCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    marginBottom: 10,
  },
  reflectionEntryMeta: {
    fontSize: 12,
    fontWeight: '500',
    marginBottom: 6,
  },
  reflectionEntryContent: {
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  reflectionEntryDate: {
    fontSize: 12,
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
    fontSize: 13,
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
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 8,
  },
  decisionHeaderTopic: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
    lineHeight: 24,
  },
  decisionHeaderStatus: {
    fontSize: 14,
    marginBottom: 12,
  },
  // Task 68: Improved status row styling
  decisionHeaderStatusRow: {
    marginBottom: 12,
  },
  decisionHeaderStatusDay: {
    fontSize: 15,
    fontWeight: '500',
    marginBottom: 2,
  },
  decisionHeaderStatusPhase: {
    fontSize: 13,
  },
  decisionHeaderDivider: {
    height: 1,
    marginVertical: 12,
  },
  decisionHeaderDescription: {
    fontSize: 13,
    lineHeight: 18,
  },
  noDecisionCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 24,
    alignItems: 'center',
    marginBottom: 16,
  },
  noDecisionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  noDecisionText: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 20,
  },
  instructionCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 16,
  },
  instructionTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 8,
  },
  instructionText: {
    fontSize: 13,
    lineHeight: 18,
  },
  todaysLensCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
    marginBottom: 16,
  },
  todaysLensLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 8,
  },
  todaysLensGate: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  // Task 68: Gate/Line styling
  todaysLensGateRow: {
    marginBottom: 8,
  },
  todaysLensLine: {
    fontSize: 12,
    marginTop: 2,
  },
  todaysLensTheme: {
    fontSize: 14,
    marginBottom: 12,
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
    fontSize: 14,
    marginRight: 8,
    marginTop: 1,
  },
  todaysLensObservation: {
    fontSize: 13,
    lineHeight: 18,
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
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '500',
  },
  reflectionInputCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
    marginBottom: 16,
  },
  reflectionInputLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 12,
  },
  reflectionTextInput: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    fontSize: 15,
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
    fontSize: 15,
    fontWeight: '600',
    color: '#1A1D24',
  },
  lunarWheelSectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 4,
  },
  lunarWheelSectionHint: {
    fontSize: 12,
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
    fontSize: 14,
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
    marginBottom: 12,
  },
  cycleCompletionBannerIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  cycleCompletionBannerText: {
    flex: 1,
  },
  cycleCompletionBannerTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 2,
  },
  cycleCompletionBannerSubtitle: {
    fontSize: 13,
  },
  cycleCompletionBannerButton: {
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cycleCompletionBannerButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1D24',
  },
  cycleCompletionBannerBody: {
    fontSize: 13,
    lineHeight: 18,
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
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 8,
  },
  debugPanelSubtitle: {
    fontSize: 12,
    fontWeight: '600',
    marginTop: 12,
    marginBottom: 4,
  },
  debugPanelText: {
    fontSize: 11,
    fontFamily: 'monospace',
    lineHeight: 16,
  },
});
