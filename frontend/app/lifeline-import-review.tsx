/**
 * Lifeline Import Review Screen (Task 44 - Updated)
 * 
 * A review and confirmation flow for imported lifeline data.
 * Users can review, edit, and confirm extracted events before saving.
 * 
 * CRITICAL: No placeholder/demo data shown without real upload.
 * Shows clear file source and extraction state.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Modal,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useAppStore } from '../store';
import api from '../services/api';

// =============================================================================
// TYPES
// =============================================================================

interface ExtractedEvent {
  id: string;
  year: number | null;
  title: string;
  description: string;
  category?: string;
  impact_score?: number;
  emotional_tone?: string;
  confidence?: number;
  selected: boolean;
}

// Available categories
const CATEGORIES = [
  'Turning Point',
  'Career',
  'Relationships',
  'Family',
  'Identity',
  'Achievement',
  'Loss',
  'Move',
  'Health',
  'Spirituality',
  'Money',
  'Other',
];

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function LifelineImportReviewScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const { user } = useAppStore();
  const params = useLocalSearchParams();
  
  // State
  const [events, setEvents] = useState<ExtractedEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editingEvent, setEditingEvent] = useState<ExtractedEvent | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  
  // Import source info from params
  const sourceFilename = params.sourceFilename as string | undefined;
  const isRealImport = params.isRealImport === 'true';
  const extractedCountParam = params.extractedCount as string | undefined;
  const importSourceId = params.importSourceId as string | undefined;
  const alreadyImported = params.alreadyImported === 'true';
  
  // Debug logging helper
  const debugLog = (message: string, data?: any) => {
    console.log(`[ImportReview] ${message}`, data || '');
  };
  
  // Initialize events from params - NO DEMO DATA
  useEffect(() => {
    debugLog('Initializing with params', { 
      hasExtractedEvents: !!params.extractedEvents,
      sourceFilename,
      isRealImport,
      extractedCount: extractedCountParam
    });
    
    // Only load events if we have real extracted data from an upload
    if (params.extractedEvents && isRealImport) {
      try {
        const parsed = JSON.parse(params.extractedEvents as string);
        debugLog('Parsed events:', { count: parsed.length, events: parsed });
        
        setEvents(parsed.map((e: any, idx: number) => ({
          ...e,
          id: e.id || `extracted-${idx}`,
          selected: true,
          impact_score: e.impact_score || 5,
        })));
      } catch (err) {
        debugLog('Failed to parse extracted events:', err);
        // Don't show demo data - show empty state instead
        setEvents([]);
      }
    } else {
      // No real import data - show empty state
      debugLog('No real import data - showing empty state');
      setEvents([]);
    }
    
    setLoading(false);
  }, [params.extractedEvents, isRealImport]);
  
  // Selection handlers
  const toggleEventSelection = (id: string) => {
    setEvents(events.map(e => 
      e.id === id ? { ...e, selected: !e.selected } : e
    ));
  };
  
  const selectAll = () => {
    setEvents(events.map(e => ({ ...e, selected: true })));
  };
  
  const deselectAll = () => {
    setEvents(events.map(e => ({ ...e, selected: false })));
  };
  
  // Delete handler
  const deleteEvent = (id: string) => {
    Alert.alert(
      'Remove Event',
      'Are you sure you want to remove this event from the import?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Remove', 
          style: 'destructive',
          onPress: () => setEvents(events.filter(e => e.id !== id))
        },
      ]
    );
  };
  
  // Edit handlers
  const openEditModal = (event: ExtractedEvent) => {
    setEditingEvent({ ...event });
    setShowEditModal(true);
  };
  
  const saveEventEdit = () => {
    if (!editingEvent) return;
    
    setEvents(events.map(e => 
      e.id === editingEvent.id ? editingEvent : e
    ));
    setShowEditModal(false);
    setEditingEvent(null);
  };
  
  // State for tracking failed events for retry
  const [failedEvents, setFailedEvents] = useState<ExtractedEvent[]>([]);
  
  // Save selected events to Lifeline using new v2 architecture
  const saveSelectedEvents = async () => {
    // Debug: confirm tap is firing (visible in Safari Web Inspector / Metro logs)
    console.log('[ImportReview] saveSelectedEvents TAPPED', {
      hasUser: !!user?.id,
      userId: user?.id,
      eventCount: events.length,
      importSourceId,
    });

    if (!user?.id) {
      Alert.alert('Not signed in', 'Please log in to save events. (If you are logged in, try refreshing the page.)');
      return;
    }
    
    const selectedEvents = events.filter(e => e.selected);
    
    if (selectedEvents.length === 0) {
      Alert.alert('No Events Selected', 'Please select at least one event to add to your Lifeline.');
      return;
    }
    
    debugLog('Starting save with v2 architecture:', { 
      count: selectedEvents.length,
      importSourceId,
      alreadyImported 
    });
    setSaving(true);
    setFailedEvents([]);
    
    try {
      // Use the new v2 confirm-import endpoint if we have an import source ID
      if (importSourceId) {
        debugLog('Using v2 confirm-import endpoint');
        
        const response = await api.post(`/lifeline/confirm-import/${importSourceId}?auto_merge_exact=true`);
        
        debugLog('Confirm import response:', response.data);
        
        if (response.data.success) {
          const stats = response.data.stats || {};
          const newCount = stats.new_canonical || 0;
          const matchedCount = stats.exact_matches || 0;
          const needsReviewCount = stats.needs_review || 0;
          
          let message = `Added ${newCount} new moment${newCount !== 1 ? 's' : ''} to your Lifeline.`;
          if (matchedCount > 0) {
            message += ` ${matchedCount} matched existing entries.`;
          }
          if (needsReviewCount > 0) {
            message += ` ${needsReviewCount} potential duplicates to review later.`;
          }
          
          Alert.alert(
            'Import Complete',
            message,
            [
              {
                text: 'View Lifeline',
                onPress: () => router.replace('/(tabs)/life'),
              },
            ]
          );
        } else {
          throw new Error(response.data.message || 'Import confirmation failed');
        }
      } else {
        // Fallback to legacy direct-save method for backwards compatibility
        debugLog('Falling back to legacy direct-save method');
        await saveLegacyMethod(selectedEvents);
      }
    } catch (err: any) {
      console.error('[ImportReview] Save error:', err);
      const status = err?.response?.status;
      const apiMsg = err?.response?.data?.detail || err?.response?.data?.message;
      let friendly = err?.message || 'Failed to save events. Please try again.';
      if (status === 404) {
        friendly = 'The import endpoint is missing on the server. Your deployment may be out of sync — please redeploy, then try again.';
      } else if (status === 502 || status === 503 || err?.code === 'ERR_NETWORK') {
        friendly = 'Could not reach the server (502/network). Please wait 30 seconds and try again. If it persists, redeploy the app.';
      } else if (status >= 500) {
        friendly = `Server error (${status}). ${apiMsg || 'Please try again shortly.'}`;
      } else if (apiMsg) {
        friendly = apiMsg;
      }
      Alert.alert(
        'Import Failed',
        friendly,
        [
          { text: 'OK' },
          {
            text: 'View Lifeline anyway',
            onPress: () => router.replace('/(tabs)/life'),
          },
        ],
      );
    } finally {
      setSaving(false);
    }
  };
  
  // Legacy save method for backwards compatibility
  const saveLegacyMethod = async (selectedEvents: ExtractedEvent[]) => {
    debugLog('Starting legacy bulk save:', { count: selectedEvents.length });
    
    // Create save promises for all events
    const savePromises = selectedEvents.map(async (event) => {
      try {
        await api.post('/lifeline/event', {
          user_id: user!.id,
          title: event.title,
          year: event.year,
          description: event.description,
          category: event.category || 'Turning Point',
          impact_score: event.impact_score || 5,
          emotional_tone: event.emotional_tone || 'neutral',
          tags: [],
        });
        debugLog('Saved event:', event.title);
        return { success: true, event };
      } catch (err: any) {
        console.error('[ImportReview] Failed to save event:', event.title, err);
        return { success: false, event, error: err };
      }
    });
    
    // Wait for all saves to complete (success or failure)
    const results = await Promise.allSettled(savePromises);
    
    // Count successes and failures
    let savedCount = 0;
    let errorCount = 0;
    const failed: ExtractedEvent[] = [];
    
    results.forEach((result) => {
      if (result.status === 'fulfilled') {
        if (result.value.success) {
          savedCount++;
        } else {
          errorCount++;
          failed.push(result.value.event);
        }
      } else {
        // Promise rejected (shouldn't happen with our try/catch, but just in case)
        errorCount++;
      }
    });
    
    setFailedEvents(failed);
    
    debugLog('Legacy bulk save complete:', { savedCount, errorCount, failedCount: failed.length });
    
    // Always show result and navigate
    if (errorCount === 0) {
      // Full success - navigate immediately
      Alert.alert(
        'Import Complete',
        `Successfully added ${savedCount} moment${savedCount !== 1 ? 's' : ''} to your Lifeline.`,
        [
          {
            text: 'View Lifeline',
            onPress: () => router.replace('/(tabs)/life'),
          },
        ]
      );
    } else if (savedCount > 0) {
      // Partial success - allow retry or continue
      Alert.alert(
        'Import Partially Complete',
        `Added ${savedCount} moment${savedCount !== 1 ? 's' : ''}, but ${errorCount} failed to save.`,
        [
          {
            text: 'Retry Failed',
            onPress: () => retryFailedEvents(failed),
          },
          {
            text: 'Continue to Lifeline',
            onPress: () => router.replace('/(tabs)/life'),
            style: 'cancel',
          },
        ]
      );
    } else {
      // Complete failure - allow retry or go back
      Alert.alert(
        'Import Failed',
        'All moments failed to save. Please check your connection and try again.',
        [
          {
            text: 'Retry',
            onPress: () => retryFailedEvents(failed),
          },
          {
            text: 'Go Back',
            onPress: navigateBack,
            style: 'cancel',
          },
        ]
      );
    }
  };
  
  // Retry failed events
  const retryFailedEvents = async (eventsToRetry: ExtractedEvent[]) => {
    if (!user?.id || eventsToRetry.length === 0) return;
    
    debugLog('Retrying failed events:', { count: eventsToRetry.length });
    setSaving(true);
    
    const savePromises = eventsToRetry.map(async (event) => {
      try {
        await api.post('/lifeline/event', {
          user_id: user.id,
          title: event.title,
          year: event.year,
          description: event.description,
          category: event.category || 'Turning Point',
          impact_score: event.impact_score || 5,
          emotional_tone: event.emotional_tone || 'neutral',
          tags: [],
        });
        return { success: true, event };
      } catch (err) {
        return { success: false, event };
      }
    });
    
    const results = await Promise.allSettled(savePromises);
    
    let savedCount = 0;
    const stillFailed: ExtractedEvent[] = [];
    
    results.forEach((result) => {
      if (result.status === 'fulfilled' && result.value.success) {
        savedCount++;
      } else if (result.status === 'fulfilled') {
        stillFailed.push(result.value.event);
      }
    });
    
    setSaving(false);
    setFailedEvents(stillFailed);
    
    debugLog('Retry complete:', { savedCount, stillFailed: stillFailed.length });
    
    if (stillFailed.length === 0) {
      Alert.alert(
        'Retry Successful',
        `All ${savedCount} remaining moment${savedCount !== 1 ? 's were' : ' was'} saved.`,
        [
          {
            text: 'View Lifeline',
            onPress: () => router.replace('/(tabs)/life'),
          },
        ]
      );
    } else {
      Alert.alert(
        'Some Moments Still Failed',
        `Saved ${savedCount}, but ${stillFailed.length} still failed.`,
        [
          {
            text: 'Continue to Lifeline',
            onPress: () => router.replace('/(tabs)/life'),
          },
        ]
      );
    }
  };
  
  // Cancel import - safe navigation back
  const handleCancel = () => {
    debugLog('Cancel pressed');
    
    if (events.length > 0 && events.some(e => e.selected)) {
      Alert.alert(
        'Cancel Import',
        'Are you sure you want to cancel? Selected events will not be saved.',
        [
          { text: 'Keep Reviewing', style: 'cancel' },
          { 
            text: 'Cancel Import', 
            style: 'destructive',
            onPress: navigateBack,
          },
        ]
      );
    } else {
      navigateBack();
    }
  };
  
  // Safe navigation back - always works
  const navigateBack = () => {
    debugLog('Navigating back');
    // Try to go back, fallback to Life tab if can't
    if (router.canGoBack()) {
      router.back();
    } else {
      router.replace('/(tabs)/life');
    }
  };
  
  // Navigate to upload screen
  const goToUpload = () => {
    debugLog('Navigating to upload screen');
    router.push('/lifeline-upload');
  };
  
  // Navigate to manual entry (Life tab)
  const goToManualEntry = () => {
    debugLog('Navigating to manual entry');
    router.replace('/(tabs)/life');
  };
  
  // Counts
  const selectedCount = events.filter(e => e.selected).length;
  const totalCount = events.length;
  
  // =============================================================================
  // RENDER: LOADING STATE
  // =============================================================================
  
  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Processing your file...
          </Text>
        </View>
      </SafeAreaView>
    );
  }
  
  // =============================================================================
  // RENDER: EMPTY/NO DATA STATE (Critical - Task 44 Part 5)
  // =============================================================================
  
  if (events.length === 0) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        {/* Header with Cancel */}
        <View style={styles.header}>
          <TouchableOpacity onPress={navigateBack} style={styles.cancelButton}>
            <Text style={[styles.cancelButtonText, { color: theme.textSecondary }]}>Cancel</Text>
          </TouchableOpacity>
          <View style={styles.headerCenter} />
          <View style={styles.headerRight} />
        </View>
        
        <View style={styles.emptyContainer}>
          <View style={[styles.emptyIconCircle, { backgroundColor: `${theme.textTertiary}15` }]}>
            <Ionicons name="document-text-outline" size={48} color={theme.textTertiary} />
          </View>
          
          <Text style={[styles.emptyTitle, { color: theme.text }]}>
            No imported moments yet
          </Text>
          
          <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
            {sourceFilename 
              ? `We couldn't extract enough moments from "${sourceFilename}". Try a different file or add moments manually.`
              : 'Upload a file to extract turning points, or add moments manually.'
            }
          </Text>
          
          <View style={styles.emptyActions}>
            <TouchableOpacity
              style={[styles.emptyButton, { backgroundColor: theme.accent }]}
              onPress={goToUpload}
            >
              <Ionicons name="folder-open-outline" size={20} color="#FFFFFF" />
              <Text style={styles.emptyButtonText}>Choose a file</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.emptyButtonSecondary, { borderColor: theme.border }]}
              onPress={goToManualEntry}
            >
              <Text style={[styles.emptyButtonSecondaryText, { color: theme.text }]}>
                Add moments manually
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.backLink}
              onPress={navigateBack}
            >
              <Text style={[styles.backLinkText, { color: theme.textTertiary }]}>
                Back
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </SafeAreaView>
    );
  }
  
  // =============================================================================
  // RENDER: MAIN REVIEW SCREEN
  // =============================================================================
  
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleCancel} style={styles.cancelButton}>
          <Text style={[styles.cancelButtonText, { color: theme.textSecondary }]}>Cancel</Text>
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={[styles.selectedCount, { color: theme.accent }]}>
            {selectedCount} of {totalCount} selected
          </Text>
        </View>
        <TouchableOpacity
          onPress={() => {
            Alert.alert(
              'Leave without importing?',
              'Your selection will be discarded. Continue?',
              [
                { text: 'Keep reviewing', style: 'cancel' },
                { text: 'Go to Lifeline', onPress: () => router.replace('/(tabs)/life') },
              ],
            );
          }}
          style={styles.homeButton}
          accessibilityLabel="Home"
        >
          <Ionicons name="home-outline" size={22} color={theme.textSecondary} />
        </TouchableOpacity>
      </View>
      
      {/* Title Section */}
      <View style={styles.titleSection}>
        <Text style={[styles.title, { color: theme.text }]}>
          Review extracted moments
        </Text>
        <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
          Select the ones you want to add to your Lifeline.
        </Text>
      </View>
      
      {/* File Source Indicator (Task 44 Part 3) */}
      {sourceFilename && (
        <View style={[styles.sourceCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.sourceInfo}>
            <Ionicons name="document-attach-outline" size={18} color={theme.textSecondary} />
            <View style={styles.sourceTextContainer}>
              <Text style={[styles.sourceLabel, { color: theme.textTertiary }]}>IMPORTED FROM</Text>
              <Text style={[styles.sourceFilename, { color: theme.text }]} numberOfLines={1}>
                {sourceFilename}
              </Text>
            </View>
          </View>
          <View style={[styles.extractedBadge, { backgroundColor: `${theme.accent}15` }]}>
            <Text style={[styles.extractedBadgeText, { color: theme.accent }]}>
              {totalCount} moment{totalCount !== 1 ? 's' : ''} extracted
            </Text>
          </View>
        </View>
      )}
      
      {/* Selection Controls */}
      <View style={[styles.selectionControls, { borderColor: theme.border }]}>
        <TouchableOpacity onPress={selectAll} style={styles.selectionButton}>
          <Text style={[styles.selectionButtonText, { color: theme.accent }]}>Select All</Text>
        </TouchableOpacity>
        <View style={[styles.selectionDivider, { backgroundColor: theme.border }]} />
        <TouchableOpacity onPress={deselectAll} style={styles.selectionButton}>
          <Text style={[styles.selectionButtonText, { color: theme.textSecondary }]}>Deselect All</Text>
        </TouchableOpacity>
      </View>
      
      {/* Event List */}
      <ScrollView 
        style={styles.eventList}
        contentContainerStyle={styles.eventListContent}
        showsVerticalScrollIndicator={false}
      >
        {events.map((event) => (
          <View 
            key={event.id}
            style={[
              styles.eventCard,
              { 
                backgroundColor: theme.cardBackground,
                borderColor: event.selected ? theme.accent : theme.border,
                borderWidth: event.selected ? 2 : 1,
              }
            ]}
          >
            {/* Selection Checkbox */}
            <TouchableOpacity
              style={styles.checkboxContainer}
              onPress={() => toggleEventSelection(event.id)}
            >
              <View style={[
                styles.checkbox,
                { borderColor: event.selected ? theme.accent : theme.border },
                event.selected && { backgroundColor: theme.accent }
              ]}>
                {event.selected && <Text style={styles.checkmark}>✓</Text>}
              </View>
            </TouchableOpacity>
            
            {/* Event Content */}
            <View style={styles.eventContent}>
              <View style={styles.eventHeader}>
                {event.year && (
                  <Text style={[styles.eventYear, { color: theme.accent }]}>
                    {event.year}
                  </Text>
                )}
                {event.category && (
                  <View style={[styles.categoryBadge, { backgroundColor: theme.border }]}>
                    <Text style={[styles.categoryText, { color: theme.textSecondary }]}>
                      {event.category}
                    </Text>
                  </View>
                )}
              </View>
              
              <Text style={[styles.eventTitle, { color: theme.text }]}>
                {event.title || 'Untitled moment'}
              </Text>
              
              {event.description && (
                <Text 
                  style={[styles.eventDescription, { color: theme.textSecondary }]}
                  numberOfLines={2}
                >
                  {event.description}
                </Text>
              )}
              
              {event.confidence && event.confidence < 0.8 && (
                <Text style={[styles.confidenceWarning, { color: theme.warning || '#F59E0B' }]}>
                  ⚠ Low confidence - please verify
                </Text>
              )}
            </View>
            
            {/* Action Buttons */}
            <View style={styles.eventActions}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => openEditModal(event)}
              >
                <Text style={[styles.actionButtonText, { color: theme.accent }]}>Edit</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => deleteEvent(event.id)}
              >
                <Text style={[styles.actionButtonText, { color: theme.error || '#EF4444' }]}>Remove</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))}
        
        {/* Bottom spacing */}
        <View style={{ height: 140 }} />
      </ScrollView>
      
      {/* Bottom Actions (Task 44 Part 4 - Exit paths) */}
      <View style={[styles.bottomActions, { backgroundColor: theme.background, borderTopColor: theme.border }]}>
        <TouchableOpacity
          style={[
            styles.primaryButton,
            { backgroundColor: theme.accent },
            selectedCount === 0 && styles.disabledButton
          ]}
          onPress={saveSelectedEvents}
          disabled={saving || selectedCount === 0}
        >
          {saving ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={styles.primaryButtonText}>
              Add {selectedCount} moment{selectedCount !== 1 ? 's' : ''} to Lifeline
            </Text>
          )}
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.secondaryButton}
          onPress={handleCancel}
        >
          <Text style={[styles.secondaryButtonText, { color: theme.textSecondary }]}>
            Cancel Import
          </Text>
        </TouchableOpacity>
      </View>
      
      {/* Edit Modal */}
      <Modal
        visible={showEditModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowEditModal(false)}
      >
        <SafeAreaView style={[styles.modalContainer, { backgroundColor: theme.background }]}>
          <KeyboardAvoidingView 
            style={styles.modalContent}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          >
            {/* Modal Header */}
            <View style={[styles.modalHeader, { borderBottomColor: theme.border }]}>
              <TouchableOpacity onPress={() => setShowEditModal(false)}>
                <Text style={[styles.modalCancel, { color: theme.textSecondary }]}>Cancel</Text>
              </TouchableOpacity>
              <Text style={[styles.modalTitle, { color: theme.text }]}>Edit Moment</Text>
              <TouchableOpacity onPress={saveEventEdit}>
                <Text style={[styles.modalSave, { color: theme.accent }]}>Save</Text>
              </TouchableOpacity>
            </View>
            
            {/* Modal Body */}
            <ScrollView style={styles.modalBody} showsVerticalScrollIndicator={false}>
              {/* Title */}
              <View style={styles.fieldGroup}>
                <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>Title *</Text>
                <TextInput
                  style={[styles.textInput, { backgroundColor: theme.cardBackground, color: theme.text, borderColor: theme.border }]}
                  value={editingEvent?.title || ''}
                  onChangeText={(text) => setEditingEvent(e => e ? { ...e, title: text } : null)}
                  placeholder="What happened?"
                  placeholderTextColor={theme.textTertiary}
                />
              </View>
              
              {/* Year */}
              <View style={styles.fieldGroup}>
                <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>Year</Text>
                <TextInput
                  style={[styles.textInput, { backgroundColor: theme.cardBackground, color: theme.text, borderColor: theme.border }]}
                  value={editingEvent?.year?.toString() || ''}
                  onChangeText={(text) => setEditingEvent(e => e ? { ...e, year: parseInt(text) || null } : null)}
                  placeholder="e.g., 2020"
                  placeholderTextColor={theme.textTertiary}
                  keyboardType="number-pad"
                />
              </View>
              
              {/* Description */}
              <View style={styles.fieldGroup}>
                <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>Description</Text>
                <TextInput
                  style={[styles.textInputMulti, { backgroundColor: theme.cardBackground, color: theme.text, borderColor: theme.border }]}
                  value={editingEvent?.description || ''}
                  onChangeText={(text) => setEditingEvent(e => e ? { ...e, description: text } : null)}
                  placeholder="What made this moment significant?"
                  placeholderTextColor={theme.textTertiary}
                  multiline
                  numberOfLines={4}
                  textAlignVertical="top"
                />
              </View>
              
              {/* Category */}
              <View style={styles.fieldGroup}>
                <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>Category</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoryScroll}>
                  {CATEGORIES.map((cat) => (
                    <TouchableOpacity
                      key={cat}
                      style={[
                        styles.categoryOption,
                        { borderColor: theme.border },
                        editingEvent?.category === cat && { backgroundColor: theme.accent, borderColor: theme.accent }
                      ]}
                      onPress={() => setEditingEvent(e => e ? { ...e, category: cat } : null)}
                    >
                      <Text style={[
                        styles.categoryOptionText,
                        { color: editingEvent?.category === cat ? '#FFFFFF' : theme.text }
                      ]}>
                        {cat}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>
              
              {/* Impact Score */}
              <View style={styles.fieldGroup}>
                <Text style={[styles.fieldLabel, { color: theme.textSecondary }]}>
                  Impact Score: {editingEvent?.impact_score || 5}
                </Text>
                <View style={styles.impactScoreRow}>
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((score) => (
                    <TouchableOpacity
                      key={score}
                      style={[
                        styles.impactDot,
                        { backgroundColor: theme.border },
                        (editingEvent?.impact_score || 5) >= score && { backgroundColor: theme.accent }
                      ]}
                      onPress={() => setEditingEvent(e => e ? { ...e, impact_score: score } : null)}
                    />
                  ))}
                </View>
                <View style={styles.impactLabels}>
                  <Text style={[styles.impactLabel, { color: theme.textTertiary }]}>Minor</Text>
                  <Text style={[styles.impactLabel, { color: theme.textTertiary }]}>Major</Text>
                </View>
              </View>
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  cancelButton: {
    paddingVertical: 8,
    paddingRight: 16,
  },
  cancelButtonText: {
    fontSize: 16,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  selectedCount: {
    fontSize: 14,
    fontWeight: '600',
  },
  headerRight: {
    width: 60,
  },
  homeButton: {
    paddingVertical: 8,
    paddingLeft: 12,
    paddingRight: 4,
    minWidth: 44,
    alignItems: 'flex-end',
  },
  titleSection: {
    paddingHorizontal: 20,
    paddingBottom: 12,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
  },
  
  // Source file indicator (Task 44 Part 3)
  sourceCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginHorizontal: 20,
    marginBottom: 12,
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
  },
  sourceInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 10,
  },
  sourceTextContainer: {
    flex: 1,
  },
  sourceLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  sourceFilename: {
    fontSize: 13,
    fontWeight: '500',
  },
  extractedBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  extractedBadgeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  
  selectionControls: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 20,
    marginBottom: 12,
    borderWidth: 1,
    borderRadius: 8,
  },
  selectionButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
  },
  selectionButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  selectionDivider: {
    width: 1,
    height: 20,
  },
  eventList: {
    flex: 1,
  },
  eventListContent: {
    paddingHorizontal: 20,
  },
  eventCard: {
    flexDirection: 'row',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  checkboxContainer: {
    paddingRight: 12,
    paddingTop: 2,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkmark: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
  eventContent: {
    flex: 1,
  },
  eventHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
    gap: 8,
  },
  eventYear: {
    fontSize: 14,
    fontWeight: '700',
  },
  categoryBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  categoryText: {
    fontSize: 11,
    fontWeight: '500',
  },
  eventTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  eventDescription: {
    fontSize: 14,
    lineHeight: 20,
  },
  confidenceWarning: {
    fontSize: 12,
    marginTop: 6,
  },
  eventActions: {
    flexDirection: 'column',
    gap: 8,
    marginLeft: 8,
  },
  actionButton: {
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  actionButtonText: {
    fontSize: 13,
    fontWeight: '500',
  },
  bottomActions: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 20,
    paddingVertical: 16,
    paddingBottom: 32,
    borderTopWidth: 1,
  },
  primaryButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 10,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '600',
  },
  disabledButton: {
    opacity: 0.5,
  },
  secondaryButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  secondaryButtonText: {
    fontSize: 15,
  },
  
  // Empty state (Task 44 Part 5)
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyIconCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 12,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
    marginBottom: 32,
  },
  emptyActions: {
    width: '100%',
    gap: 12,
  },
  emptyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    paddingVertical: 16,
    borderRadius: 12,
  },
  emptyButtonText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '600',
  },
  emptyButtonSecondary: {
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
  },
  emptyButtonSecondaryText: {
    fontSize: 16,
    fontWeight: '500',
  },
  backLink: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  backLinkText: {
    fontSize: 15,
  },
  
  // Modal styles
  modalContainer: {
    flex: 1,
  },
  modalContent: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
  },
  modalCancel: {
    fontSize: 16,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  modalSave: {
    fontSize: 16,
    fontWeight: '600',
  },
  modalBody: {
    flex: 1,
    padding: 20,
  },
  fieldGroup: {
    marginBottom: 24,
  },
  fieldLabel: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  textInput: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
  },
  textInputMulti: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    minHeight: 100,
  },
  categoryScroll: {
    flexDirection: 'row',
  },
  categoryOption: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    marginRight: 8,
  },
  categoryOptionText: {
    fontSize: 14,
    fontWeight: '500',
  },
  impactScoreRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  impactDot: {
    width: 28,
    height: 28,
    borderRadius: 14,
  },
  impactLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  impactLabel: {
    fontSize: 12,
  },
});
