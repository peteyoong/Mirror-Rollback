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
import { createJournalEntry, getJournalEntries } from '../../services/api';
import api from '../../services/api';
import { Ionicons } from '@expo/vector-icons';

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

// Interface for timeline events
interface TimelineEvent {
  created_at_iso: string;
  inferred_state: string;
  confidence: number;
  themes: string[];
  tension: string | null;
  event_type: string;
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

// Format relative time
function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

// Format state for display
function formatState(state: string): string {
  const labels: Record<string, string> = {
    'grounding': 'Grounding',
    'stabilizing': 'Stabilizing',
    'exploring': 'Exploring',
    'integrating': 'Integrating',
    'unclear': 'In flux',
  };
  return labels[state] || state;
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

type ViewMode = 'journal' | 'mirror' | 'timeline';

export default function JournalScreen() {
  const { user, chart, journalEntries, setJournalEntries, addJournalEntry } = useAppStore();
  const { theme, isDark } = useTheme();
  const params = useLocalSearchParams<{ view?: string; fromKeystone?: string }>();
  const [viewMode, setViewMode] = useState<ViewMode>('journal');
  const [newEntry, setNewEntry] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef<TextInput>(null);
  
  // Mirror Reflection Modal state
  const [reflectionModalVisible, setReflectionModalVisible] = useState(false);
  const [selectedJournalText, setSelectedJournalText] = useState('');
  const [selectedEntryId, setSelectedEntryId] = useState<string | null>(null);
  
  // Cache of reflections per entry
  const [reflectionCache, setReflectionCache] = useState<Map<string, CachedReflection>>(new Map());

  // Timeline state
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [isLoadingTimeline, setIsLoadingTimeline] = useState(false);
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);

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

  useEffect(() => {
    loadEntries();
  }, []);

  // Load timeline when switching to timeline view
  useEffect(() => {
    if (viewMode === 'timeline' && user) {
      loadTimeline();
    }
  }, [viewMode, user]);

  const loadTimeline = async () => {
    if (!user) return;
    
    setIsLoadingTimeline(true);
    try {
      const response = await api.get(`/timeline/${user.id}?days=7`);
      setTimelineEvents(response.data.events || []);
    } catch (err) {
      console.error('Load timeline error:', err);
    } finally {
      setIsLoadingTimeline(false);
    }
  };

  const toggleEventExpanded = (eventId: string) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpandedEventId(expandedEventId === eventId ? null : eventId);
  };

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

  const handleSubmit = async () => {
    if (!user || !newEntry.trim() || isSubmitting) return;

    Keyboard.dismiss();
    setIsSubmitting(true);
    setError('');

    try {
      const entry = await createJournalEntry(user.id, newEntry.trim());
      addJournalEntry(entry);
      setNewEntry('');
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

  // Render the mode toggle (shared across views)
  const renderModeToggle = () => (
    <View style={styles.modeToggleContainer}>
      <TouchableOpacity
        style={[styles.modeButton, viewMode === 'journal' && styles.modeButtonActive]}
        onPress={() => setViewMode('journal')}
      >
        <Ionicons 
          name="book-outline" 
          size={16} 
          color={viewMode === 'journal' ? Colors.accent : Colors.textSecondary} 
        />
        <Text style={[styles.modeButtonText, viewMode === 'journal' && styles.modeButtonTextActive]}>
          Journal
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.modeButton, viewMode === 'mirror' && styles.modeButtonActive]}
        onPress={() => setViewMode('mirror')}
      >
        <Ionicons 
          name="sparkles" 
          size={16} 
          color={viewMode === 'mirror' ? Colors.accent : Colors.textSecondary} 
        />
        <Text style={[styles.modeButtonText, viewMode === 'mirror' && styles.modeButtonTextActive]}>
          Mirror
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.modeButton, viewMode === 'timeline' && styles.modeButtonActive]}
        onPress={() => setViewMode('timeline')}
      >
        <Ionicons 
          name="time-outline" 
          size={16} 
          color={viewMode === 'timeline' ? Colors.accent : Colors.textSecondary} 
        />
        <Text style={[styles.modeButtonText, viewMode === 'timeline' && styles.modeButtonTextActive]}>
          Timeline
        </Text>
      </TouchableOpacity>
    </View>
  );

  // Render timeline event row
  const renderTimelineEvent = ({ item, index }: { item: TimelineEvent; index: number }) => {
    const eventId = `${item.created_at_iso}-${index}`;
    const isExpanded = expandedEventId === eventId;
    const firstTheme = item.themes[0] || 'Reflection';
    
    return (
      <TouchableOpacity 
        style={styles.timelineRow}
        onPress={() => toggleEventExpanded(eventId)}
        activeOpacity={0.7}
      >
        <View style={styles.timelineHeader}>
          <Text style={styles.timelineTime}>{formatRelativeTime(item.created_at_iso)}</Text>
          <View style={styles.stateChip}>
            <Text style={styles.stateChipText}>{formatState(item.inferred_state)}</Text>
          </View>
          <Ionicons 
            name={isExpanded ? "chevron-up" : "chevron-down"} 
            size={16} 
            color={Colors.textTertiary} 
          />
        </View>
        <Text style={styles.timelineTheme} numberOfLines={isExpanded ? undefined : 1}>
          {firstTheme}
        </Text>
        
        {isExpanded && (
          <View style={styles.timelineDetails}>
            {item.themes[1] && (
              <Text style={styles.timelineSecondTheme}>• {item.themes[1]}</Text>
            )}
            {item.tension && (
              <View style={styles.tensionContainer}>
                <Text style={styles.tensionLabel}>Tension:</Text>
                <Text style={styles.tensionText}>{item.tension}</Text>
              </View>
            )}
            <Text style={styles.confidenceText}>
              Confidence: {Math.round(item.confidence * 100)}%
            </Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  // Timeline View
  if (viewMode === 'timeline') {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        {renderModeToggle()}
        
        <View style={styles.timelineContainer}>
          <View style={styles.timelineHeaderSection}>
            <Text style={styles.timelineTitle}>Last 7 Days</Text>
            <Text style={styles.timelineSubtitle}>Your inner patterns over time</Text>
          </View>
          
          {isLoadingTimeline ? (
            <View style={styles.centered}>
              <ActivityIndicator color={Colors.accent} />
            </View>
          ) : timelineEvents.length === 0 ? (
            <View style={styles.emptyTimeline}>
              <Ionicons name="time-outline" size={48} color={Colors.border} />
              <Text style={styles.emptyTimelineText}>No timeline yet</Text>
              <Text style={styles.emptyTimelineSubtext}>
                Start chatting with Mirror to build your pattern history
              </Text>
            </View>
          ) : (
            <FlatList
              data={timelineEvents}
              keyExtractor={(item, index) => `${item.created_at_iso}-${index}`}
              renderItem={renderTimelineEvent}
              contentContainerStyle={styles.timelineList}
              showsVerticalScrollIndicator={false}
            />
          )}
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
        <TouchableWithoutFeedback onPress={dismissKeyboard}>
          <View style={styles.content}>
            {/* Mode Toggle */}
            {renderModeToggle()}

            {/* Header */}
            <View style={styles.header}>
              <Text style={styles.title}>Journal</Text>
              <Text style={styles.subtitle}>
                A private space for your thoughts and reflections.
              </Text>
            </View>

            {/* New Entry Input */}
            <View style={styles.inputSection}>
              <View style={styles.inputContainer}>
                <TextInput
                  ref={inputRef}
                  style={styles.input}
                  value={newEntry}
                  onChangeText={setNewEntry}
                  placeholder="What's on your mind?"
                  placeholderTextColor={Colors.textTertiary}
                  multiline
                  maxLength={2000}
                  editable={!isSubmitting}
                  returnKeyType="default"
                  blurOnSubmit={false}
                />
                <View style={styles.inputActions}>
                  {newEntry.trim().length > 0 && (
                    <TouchableOpacity
                      style={styles.dismissButton}
                      onPress={dismissKeyboard}
                    >
                      <Ionicons name="chevron-down" size={20} color={Colors.textSecondary} />
                    </TouchableOpacity>
                  )}
                  <TouchableOpacity
                    style={[
                      styles.submitButton,
                      (!newEntry.trim() || isSubmitting) && styles.submitButtonDisabled,
                    ]}
                    onPress={handleSubmit}
                    disabled={!newEntry.trim() || isSubmitting}
                  >
                    {isSubmitting ? (
                      <ActivityIndicator size="small" color={Colors.background} />
                    ) : (
                      <Ionicons name="checkmark" size={20} color={Colors.background} />
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
                  <Ionicons name="sparkles-outline" size={16} color={reflectionModalVisible ? Colors.textTertiary : Colors.accent} />
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
                <ActivityIndicator size="large" color={Colors.textSecondary} />
              </View>
            ) : journalEntries.length === 0 ? (
              <View style={styles.emptyContainer}>
                <Ionicons name="book-outline" size={48} color={Colors.textTertiary} />
                <Text style={styles.emptyText}>No entries yet</Text>
                <Text style={styles.emptySubtext}>
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
        </TouchableWithoutFeedback>
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
    paddingBottom: 24,
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
  // Timeline styles
  timelineContainer: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  timelineHeaderSection: {
    paddingHorizontal: 20,
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
    paddingHorizontal: 16,
    paddingBottom: 32,
  },
  timelineRow: {
    backgroundColor: '#FDFCFA',
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  timelineHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  timelineTime: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginRight: 10,
  },
  stateChip: {
    backgroundColor: Colors.surfaceLight,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    marginRight: 'auto',
  },
  stateChipText: {
    fontSize: 11,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  timelineTheme: {
    fontSize: 14,
    color: Colors.text,
    lineHeight: 20,
  },
  timelineDetails: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  timelineSecondTheme: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginBottom: 8,
  },
  tensionContainer: {
    marginTop: 8,
  },
  tensionLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  tensionText: {
    fontSize: 13,
    color: Colors.text,
    fontStyle: 'italic',
    lineHeight: 18,
  },
  confidenceText: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 10,
    opacity: 0.7,
  },
  emptyTimeline: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyTimelineText: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginTop: 16,
  },
  emptyTimelineSubtext: {
    fontSize: 14,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 20,
  },
});
