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
import { createJournalEntry, getJournalEntries, getCombinedTimeline, TimelineItem } from '../../services/api';
import api from '../../services/api';
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

type ViewMode = 'journal' | 'mirror' | 'timeline';

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

  // Load combined timeline when switching to timeline view
  useEffect(() => {
    if (viewMode === 'timeline' && user) {
      loadCombinedTimeline();
    }
  }, [viewMode, user]);

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

  // Render the mode toggle (Journal | Mirror | Timeline)
  const renderModeToggle = () => (
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
      <TouchableOpacity
        style={[styles.modeButton, viewMode === 'timeline' && styles.modeButtonActive]}
        onPress={() => setViewMode('timeline')}
      >
        <Text style={{ fontSize: 14, color: viewMode === 'timeline' ? Colors.accent : Colors.textSecondary }}>⏱</Text>
        <Text style={[styles.modeButtonText, viewMode === 'timeline' && styles.modeButtonTextActive]}>
          Timeline
        </Text>
      </TouchableOpacity>
    </View>
  );

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

  // Group entries by date for timeline
  const groupEntriesByDate = () => {
    const groups: { [key: string]: typeof journalEntries } = {};
    
    journalEntries.forEach(entry => {
      const date = new Date(entry.created_at);
      const dateKey = date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
      
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(entry);
    });
    
    // Sort groups by date (most recent first)
    const sortedGroups = Object.entries(groups).sort((a, b) => {
      const dateA = new Date(a[1][0].created_at);
      const dateB = new Date(b[1][0].created_at);
      return dateB.getTime() - dateA.getTime();
    });
    
    return sortedGroups;
  };

  // Journal Timeline View - Chronological history of journal entries
  if (viewMode === 'timeline') {
    const groupedEntries = groupEntriesByDate();
    
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        {renderModeToggle()}
        
        <View style={styles.timelineContainer}>
          <View style={styles.timelineHeader}>
            <Text style={[styles.timelineTitle, { color: theme.text }]}>Your Journal History</Text>
            <Text style={[styles.timelineSubtitle, { color: theme.textTertiary }]}>
              A chronological view of your reflections
            </Text>
          </View>
          
          {isLoading ? (
            <View style={styles.centered}>
              <ActivityIndicator size="large" color={theme.textSecondary} />
            </View>
          ) : journalEntries.length === 0 ? (
            <View style={styles.timelineEmpty}>
              <Text style={{ fontSize: 42, color: theme.textTertiary }}>📝</Text>
              <Text style={[styles.timelineEmptyTitle, { color: theme.textSecondary }]}>
                No entries yet
              </Text>
              <Text style={[styles.timelineEmptySubtext, { color: theme.textTertiary }]}>
                Start journaling to see your reflection history here
              </Text>
              <TouchableOpacity
                style={[styles.timelineStartButton, { backgroundColor: theme.accent }]}
                onPress={() => setViewMode('journal')}
              >
                <Text style={[styles.timelineStartButtonText, { color: '#FFFFFF' }]}>
                  Write Your First Entry
                </Text>
              </TouchableOpacity>
            </View>
          ) : (
            <FlatList
              data={groupedEntries}
              keyExtractor={(item) => item[0]}
              showsVerticalScrollIndicator={false}
              contentContainerStyle={styles.timelineList}
              renderItem={({ item: [dateLabel, entries] }) => (
                <View style={styles.timelineDateGroup}>
                  {/* Date Header */}
                  <View style={styles.timelineDateHeader}>
                    <View style={[styles.timelineDateDot, { backgroundColor: theme.accent }]} />
                    <Text style={[styles.timelineDateLabel, { color: theme.text }]}>
                      {dateLabel}
                    </Text>
                    <Text style={[styles.timelineEntryCount, { color: theme.textTertiary }]}>
                      {entries.length} {entries.length === 1 ? 'entry' : 'entries'}
                    </Text>
                  </View>
                  
                  {/* Entries for this date */}
                  <View style={[styles.timelineEntriesLine, { borderLeftColor: theme.border }]}>
                    {entries.map((entry, index) => {
                      const timeInfo = formatTimelineDate(entry.created_at);
                      const preview = entry.content.length > 120 
                        ? entry.content.substring(0, 120).trim() + '...' 
                        : entry.content;
                      
                      return (
                        <View 
                          key={entry.id} 
                          style={[
                            styles.timelineEntryCard,
                            { backgroundColor: theme.surface, borderColor: theme.border }
                          ]}
                        >
                          <View style={styles.timelineEntryHeader}>
                            <Text style={[styles.timelineEntryTime, { color: theme.textTertiary }]}>
                              {timeInfo.time}
                            </Text>
                            {entry.themes && entry.themes.length > 0 && (
                              <View style={styles.timelineThemes}>
                                {entry.themes.slice(0, 2).map((tag, i) => (
                                  <View 
                                    key={i} 
                                    style={[styles.timelineThemeChip, { backgroundColor: theme.accent + '15' }]}
                                  >
                                    <Text style={[styles.timelineThemeText, { color: theme.accent }]}>
                                      {tag}
                                    </Text>
                                  </View>
                                ))}
                              </View>
                            )}
                          </View>
                          
                          <Text 
                            style={[styles.timelineEntryPreview, { color: theme.textSecondary }]}
                            numberOfLines={3}
                          >
                            {preview}
                          </Text>
                          
                          <TouchableOpacity
                            style={[styles.timelineReflectButton, { borderColor: theme.accent + '40' }]}
                            onPress={() => handleReflect(entry.id, entry.content)}
                          >
                            <Text style={{ fontSize: 12, color: theme.accent }}>✦</Text>
                            <Text style={[styles.timelineReflectText, { color: theme.accent }]}>
                              Reflect with Mirror
                            </Text>
                          </TouchableOpacity>
                        </View>
                      );
                    })}
                  </View>
                </View>
              )}
            />
          )}
        </View>
        
        {/* Mirror Reflection Modal */}
        <MirrorReflectionModal
          visible={reflectionModalVisible}
          onClose={handleCloseModal}
          journalText={selectedJournalText}
          chart={chart}
        />
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
        <View style={styles.content}>
          {/* Mode Toggle */}
          {renderModeToggle()}

          {/* Header */}
          <TouchableWithoutFeedback onPress={dismissKeyboard}>
            <View style={styles.header}>
              <Text style={[styles.title, { color: theme.text }]}>Journal</Text>
              <Text style={[styles.subtitle, { color: theme.textTertiary }]}>
                A private space for your thoughts and reflections.
              </Text>
            </View>
          </TouchableWithoutFeedback>

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
});
