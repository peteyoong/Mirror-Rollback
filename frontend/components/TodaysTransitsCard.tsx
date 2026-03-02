/**
 * Today's Transits Card - Transit Engine Frontend Integration
 * 
 * Displays transit insights in the Daily Insights feed.
 * Uses grounded, non-fatalistic language (handled by backend).
 * 
 * Features:
 * - Loading skeleton while fetching
 * - Graceful error handling with inline message
 * - Respects Mirror guardrails
 * - Debug info in staging/preview
 * - Add to Journal functionality
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { Colors } from '../constants/colors';
import { BUILD_ENV } from '../utils/buildInfo';
import { useAppStore } from '../store';
import { storage } from '../store';
import { 
  getTransitInsightNow, 
  getTransitBuildId,
  TransitInterpretation,
  AttentionWindow,
} from '../services/transitService';
import { createJournalEntry, JournalEntryResponse } from '../services/api';
import { SafeIcon } from './SafeIcon';

// No props needed - we get userId from canonical store
interface TodaysTransitsCardProps {}

// Format timestamp for display
const formatTimestamp = (isoString: string): string => {
  try {
    const date = new Date(isoString);
    // Format as local time
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  } catch {
    return isoString; // Fallback to ISO if parsing fails
  }
};

// Format attention window time range
const formatWindowRange = (from: string, to: string): string => {
  try {
    const fromDate = new Date(from);
    const toDate = new Date(to);
    
    // If same day, just show the date
    if (fromDate.toDateString() === toDate.toDateString()) {
      return fromDate.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    }
    
    // Different days
    return `${fromDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${toDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
  } catch {
    return from;
  }
};

export default function TodaysTransitsCard({}: TodaysTransitsCardProps) {
  // Get canonical user from Zustand store (source of truth)
  const user = useAppStore(s => s.user);
  const canonicalUserId = user?.id || null;
  
  const [insight, setInsight] = useState<TransitInterpretation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [buildId, setBuildId] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [practiceExpanded, setPracticeExpanded] = useState(false);
  
  // Journal save state
  const [savingToJournal, setSavingToJournal] = useState(false);
  const [journalSaveSuccess, setJournalSaveSuccess] = useState(false);
  const [journalSaveError, setJournalSaveError] = useState<string | null>(null);
  const [savedEntryId, setSavedEntryId] = useState<string | null>(null);

  const isStaging = BUILD_ENV === 'staging' || BUILD_ENV === 'preview';

  // Diagnostic: Check for user_id mismatch (staging only)
  useEffect(() => {
    if (!isStaging) return;
    
    const checkUserIdMismatch = async () => {
      try {
        // Check localStorage for any stale user IDs
        const localStorageUserId = await storage.getItem('MIRROR_USER_ID');
        const legacyUserId = await storage.getItem('mirror_last_user_id');
        
        console.log('[TodaysTransitsCard] User ID Diagnostic:');
        console.log(`  Canonical (store): ${canonicalUserId || '(none)'}`);
        console.log(`  localStorage MIRROR_USER_ID: ${localStorageUserId || '(none)'}`);
        console.log(`  localStorage legacy: ${legacyUserId || '(none)'}`);
        
        // If canonical differs from localStorage, overwrite localStorage (staging only)
        if (canonicalUserId && localStorageUserId && canonicalUserId !== localStorageUserId) {
          console.warn('[TodaysTransitsCard] ⚠️ User ID mismatch detected! Overwriting localStorage with canonical.');
          await storage.setItem('MIRROR_USER_ID', canonicalUserId);
          await storage.setItem('mirror_last_user_id', canonicalUserId);
          console.log('[TodaysTransitsCard] ✓ localStorage updated with canonical user_id');
        }
      } catch (e) {
        console.error('[TodaysTransitsCard] Diagnostic error:', e);
      }
    };
    
    checkUserIdMismatch();
  }, [canonicalUserId, isStaging]);

  const fetchInsight = useCallback(async () => {
    // Use canonical user_id from store only
    if (!canonicalUserId) {
      console.log('[TodaysTransitsCard] No canonical userId available, skipping fetch');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log(`[TodaysTransitsCard] Fetching with canonical userId: ${canonicalUserId}`);
      const data = await getTransitInsightNow(canonicalUserId);
      setInsight(data);
      
      // Fetch build ID for debug (staging only)
      if (isStaging) {
        const id = await getTransitBuildId();
        setBuildId(id);
      }
    } catch (err: any) {
      console.error('[TodaysTransitsCard] Error fetching insight:', err);
      
      // Check for specific error types
      if (err?.response?.status === 404) {
        setError('Chart not found. Complete your profile to see transits.');
      } else if (err?.response?.status >= 500) {
        setError('Transit service temporarily unavailable.');
      } else {
        setError('Unable to load transits right now.');
      }
    } finally {
      setLoading(false);
    }
  }, [canonicalUserId, isStaging]);

  useEffect(() => {
    fetchInsight();
  }, [fetchInsight]);

  // Build journal content from transit insight
  const buildJournalContent = useCallback((): string => {
    if (!insight) return '';
    
    const lines: string[] = [];
    
    // Title
    lines.push("📍 Today's Transits");
    lines.push(`As of: ${formatTimestamp(insight.meta.timestamp_utc)}`);
    lines.push('');
    
    // Headline
    lines.push(insight.headline);
    lines.push('');
    
    // Key Points
    lines.push("What's Active:");
    insight.key_points.forEach(point => {
      lines.push(`• ${point}`);
    });
    lines.push('');
    
    // Reflect questions
    lines.push('Reflect:');
    insight.reflect.forEach(question => {
      lines.push(`• ${question}`);
    });
    lines.push('');
    
    // Two-minute practice
    lines.push(`⏱ ${insight.two_minute_practice.title}`);
    insight.two_minute_practice.steps.forEach((step, index) => {
      lines.push(`${index + 1}. ${step}`);
    });
    
    return lines.join('\n');
  }, [insight]);

  // Save transit insight to journal
  const handleSaveToJournal = useCallback(async () => {
    if (!canonicalUserId || !insight) return;
    
    setSavingToJournal(true);
    setJournalSaveError(null);
    setJournalSaveSuccess(false);
    
    try {
      const content = buildJournalContent();
      
      const response = await createJournalEntry({
        user_id: canonicalUserId,
        content,
        source: 'transits_card',
        source_label: "Today's Transits",
      });
      
      console.log('[TodaysTransitsCard] Journal entry saved:', response.id);
      console.log('[TodaysTransitsCard] Transit signature:', response.transit_signature);
      
      setSavedEntryId(response.id);
      setJournalSaveSuccess(true);
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setJournalSaveSuccess(false);
      }, 3000);
      
    } catch (err: any) {
      console.error('[TodaysTransitsCard] Failed to save to journal:', err);
      setJournalSaveError('Failed to save. Tap to retry.');
    } finally {
      setSavingToJournal(false);
    }
  }, [canonicalUserId, insight, buildJournalContent]);

  // Don't render if no user logged in
  if (!canonicalUserId) {
    return null;
  }

  // Loading state - skeleton
  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.card}>
          <View style={styles.header}>
            <Text style={styles.cardTitle}>TODAY'S TRANSITS</Text>
          </View>
          <View style={styles.loadingContent}>
            <ActivityIndicator size="small" color={Colors.textTertiary} />
            <Text style={styles.loadingText}>Loading cosmic currents...</Text>
          </View>
        </View>
      </View>
    );
  }

  // Error state - inline message
  if (error) {
    return (
      <View style={styles.container}>
        <View style={styles.card}>
          <View style={styles.header}>
            <Text style={styles.cardTitle}>TODAY'S TRANSITS</Text>
          </View>
          <View style={styles.errorContent}>
            <SafeIcon name="alert-circle-outline" size={20} color={Colors.textTertiary} />
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity onPress={fetchInsight} style={styles.retryButton}>
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          </View>
          {/* Debug info in staging */}
          {isStaging && (
            <Text style={styles.debugLine}>
              DEBUG: userId={canonicalUserId?.slice(0,8)}...
            </Text>
          )}
        </View>
      </View>
    );
  }

  // No insight available
  if (!insight) {
    return null;
  }

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        {/* Header with collapse toggle */}
        <TouchableOpacity 
          style={styles.header} 
          onPress={() => setCollapsed(!collapsed)}
          activeOpacity={0.7}
        >
          <Text style={styles.cardTitle}>TODAY'S TRANSITS</Text>
          <SafeIcon 
            name={collapsed ? 'chevron-down' : 'chevron-up'} 
            size={16} 
            color={Colors.textTertiary} 
          />
        </TouchableOpacity>

        {!collapsed && (
          <>
            {/* Timestamp - subtle */}
            <Text style={styles.timestamp}>
              As of: {formatTimestamp(insight.meta.timestamp_utc)}
            </Text>

            {/* Headline */}
            <Text style={styles.headline}>{insight.headline}</Text>

            {/* Key Points */}
            <View style={styles.section}>
              <Text style={styles.sectionLabel}>WHAT'S ACTIVE</Text>
              {insight.key_points.map((point, index) => (
                <View key={index} style={styles.bulletItem}>
                  <Text style={styles.bullet}>•</Text>
                  <Text style={styles.bulletText}>{point}</Text>
                </View>
              ))}
            </View>

            {/* Reflect Questions */}
            <View style={styles.section}>
              <Text style={styles.sectionLabel}>REFLECT</Text>
              {insight.reflect.map((question, index) => (
                <Text key={index} style={styles.reflectQuestion}>
                  {question}
                </Text>
              ))}
            </View>

            {/* Two Minute Practice - Collapsible */}
            <TouchableOpacity 
              style={styles.practiceHeader}
              onPress={() => setPracticeExpanded(!practiceExpanded)}
              activeOpacity={0.7}
            >
              <View style={styles.practiceHeaderLeft}>
                <SafeIcon name="time-outline" size={14} color={Colors.accent} />
                <Text style={styles.practiceTitle}>
                  {insight.two_minute_practice.title}
                </Text>
              </View>
              <Text style={styles.practiceToggle}>
                {practiceExpanded ? 'Hide' : '2 min'}
              </Text>
            </TouchableOpacity>
            
            {practiceExpanded && (
              <View style={styles.practiceSteps}>
                {insight.two_minute_practice.steps.map((step, index) => (
                  <View key={index} style={styles.stepItem}>
                    <Text style={styles.stepNumber}>{index + 1}</Text>
                    <Text style={styles.stepText}>{step}</Text>
                  </View>
                ))}
              </View>
            )}

            {/* Attention Windows - Only if non-empty */}
            {insight.attention_windows.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionLabel}>ATTENTION WINDOWS</Text>
                <View style={styles.windowsContainer}>
                  {insight.attention_windows.slice(0, 5).map((window, index) => (
                    <View key={index} style={styles.windowChip}>
                      <Text style={styles.windowLabel}>{window.label}</Text>
                      <Text style={styles.windowTime}>
                        {formatWindowRange(window.from_utc, window.to_utc)}
                      </Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* Add to Journal Button */}
            <View style={styles.journalSection}>
              {journalSaveSuccess ? (
                <View style={styles.successBanner}>
                  <SafeIcon name="checkmark-circle" size={16} color="#4CAF50" />
                  <Text style={styles.successText}>Saved to Journal</Text>
                </View>
              ) : journalSaveError ? (
                <TouchableOpacity 
                  style={styles.errorBanner}
                  onPress={handleSaveToJournal}
                  activeOpacity={0.7}
                >
                  <SafeIcon name="alert-circle" size={16} color="#FF6B6B" />
                  <Text style={styles.errorBannerText}>{journalSaveError}</Text>
                </TouchableOpacity>
              ) : (
                <TouchableOpacity 
                  style={styles.addToJournalButton}
                  onPress={handleSaveToJournal}
                  disabled={savingToJournal}
                  activeOpacity={0.7}
                >
                  {savingToJournal ? (
                    <ActivityIndicator size="small" color={Colors.accent} />
                  ) : (
                    <>
                      <SafeIcon name="bookmark-outline" size={16} color={Colors.accent} />
                      <Text style={styles.addToJournalText}>Add to Journal</Text>
                    </>
                  )}
                </TouchableOpacity>
              )}
            </View>

            {/* Debug info - staging only */}
            {isStaging && buildId && (
              <Text style={styles.debugLine}>
                TRANSITS BUILD: {buildId}
              </Text>
            )}
          </>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 16,
    marginBottom: 8,
  },
  card: {
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.06)',
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 10,
    fontWeight: '500',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    opacity: 0.6,
  },
  timestamp: {
    fontSize: 11,
    color: Colors.textTertiary,
    opacity: 0.5,
    marginBottom: 12,
  },
  headline: {
    fontSize: 16,
    color: Colors.text,
    lineHeight: 24,
    fontWeight: '400',
    marginBottom: 16,
  },
  section: {
    marginBottom: 16,
  },
  sectionLabel: {
    fontSize: 9,
    fontWeight: '600',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    opacity: 0.5,
    marginBottom: 8,
  },
  bulletItem: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  bullet: {
    fontSize: 14,
    color: Colors.textTertiary,
    marginRight: 8,
    marginTop: 2,
  },
  bulletText: {
    fontSize: 14,
    color: Colors.textSecondary,
    lineHeight: 21,
    flex: 1,
  },
  reflectQuestion: {
    fontSize: 14,
    color: Colors.textSecondary,
    lineHeight: 21,
    fontStyle: 'italic',
    marginBottom: 8,
  },
  practiceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: 'rgba(201, 169, 98, 0.08)',
    borderRadius: 8,
    marginBottom: 8,
  },
  practiceHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  practiceTitle: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.accent,
  },
  practiceToggle: {
    fontSize: 11,
    color: Colors.textTertiary,
    opacity: 0.7,
  },
  practiceSteps: {
    paddingLeft: 12,
    paddingBottom: 8,
  },
  stepItem: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  stepNumber: {
    fontSize: 12,
    color: Colors.accent,
    fontWeight: '600',
    width: 20,
    marginTop: 2,
  },
  stepText: {
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 20,
    flex: 1,
  },
  windowsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  windowChip: {
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderRadius: 6,
    paddingVertical: 6,
    paddingHorizontal: 10,
  },
  windowLabel: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginBottom: 2,
  },
  windowTime: {
    fontSize: 10,
    color: Colors.textTertiary,
    opacity: 0.7,
  },
  loadingContent: {
    alignItems: 'center',
    paddingVertical: 20,
    gap: 10,
  },
  loadingText: {
    fontSize: 13,
    color: Colors.textTertiary,
    opacity: 0.6,
  },
  errorContent: {
    alignItems: 'center',
    paddingVertical: 16,
    gap: 8,
  },
  errorText: {
    fontSize: 13,
    color: Colors.textTertiary,
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 6,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 6,
    marginTop: 4,
  },
  retryText: {
    fontSize: 12,
    color: Colors.textSecondary,
  },
  debugLine: {
    fontSize: 9,
    color: Colors.textTertiary,
    opacity: 0.3,
    textAlign: 'center',
    marginTop: 12,
    fontFamily: 'monospace',
  },
  // Journal button styles
  journalSection: {
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.06)',
  },
  addToJournalButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(201, 169, 98, 0.12)',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(201, 169, 98, 0.2)',
  },
  addToJournalText: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.accent,
  },
  successBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(76, 175, 80, 0.12)',
    borderRadius: 8,
  },
  successText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#4CAF50',
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(255, 107, 107, 0.12)',
    borderRadius: 8,
  },
  errorBannerText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#FF6B6B',
  },
});
