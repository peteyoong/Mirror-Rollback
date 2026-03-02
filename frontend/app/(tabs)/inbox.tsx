/**
 * Inbox Screen - Phase 12: Notifications Inbox
 * 
 * Displays user notifications (transit nudges) and preferences.
 * Consumes Phase 9 backend APIs.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Switch,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { Spacing } from '../../constants/spacing';
import { useAppStore } from '../../store';
import {
  getNotifications,
  markNotificationRead,
  getNotificationPrefs,
  updateNotificationPrefs,
  Notification,
  NotificationPrefs,
} from '../../services/api';
import { SafeIcon } from '../../components/SafeIcon';

// Format date for display
const formatDate = (isoString: string): string => {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  } catch {
    return '';
  }
};

// Max per week options
const MAX_PER_WEEK_OPTIONS = [1, 2, 3, 5, 7];

export default function InboxScreen() {
  const router = useRouter();
  const user = useAppStore((state) => state.user);
  
  // State
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [prefs, setPrefs] = useState<NotificationPrefs>({ enabled: false });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Modal state
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null);
  const [showPrefsModal, setShowPrefsModal] = useState(false);
  
  // Fetch data
  const fetchData = useCallback(async (showLoading = true) => {
    if (!user?.id) return;
    
    if (showLoading) setLoading(true);
    setError(null);
    
    try {
      const [notifs, userPrefs] = await Promise.all([
        getNotifications(user.id),
        getNotificationPrefs(user.id),
      ]);
      
      setNotifications(notifs || []);
      setPrefs(userPrefs || { enabled: false });
    } catch (err: any) {
      console.error('[Inbox] Fetch error:', err);
      setError('Unable to load notifications');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.id]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  // Handle refresh
  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    fetchData(false);
  }, [fetchData]);
  
  // Handle notification tap
  const handleNotificationTap = useCallback(async (notif: Notification) => {
    setSelectedNotification(notif);
    
    // Mark as read if unread
    if (!notif.read_at) {
      try {
        await markNotificationRead(notif.id);
        setNotifications(prev => 
          prev.map(n => n.id === notif.id ? { ...n, read_at: new Date().toISOString() } : n)
        );
      } catch (err) {
        console.error('[Inbox] Mark read error:', err);
      }
    }
  }, []);
  
  // Handle view timeline
  const handleViewTimeline = useCallback((notif: Notification) => {
    setSelectedNotification(null);
    
    // Navigate to astrology lens with window mode
    const params = new URLSearchParams();
    params.set('tab', 'astrology');
    params.set('mode', 'window');
    if (notif.data?.from_utc) params.set('from', notif.data.from_utc);
    if (notif.data?.to_utc) params.set('to', notif.data.to_utc);
    
    router.push(`/(tabs)/lenses?${params.toString()}`);
  }, [router]);
  
  // Handle toggle prefs
  const handleToggleEnabled = useCallback(async (enabled: boolean) => {
    if (!user?.id) return;
    
    try {
      const updated = await updateNotificationPrefs(user.id, { enabled });
      setPrefs(updated);
    } catch (err) {
      console.error('[Inbox] Update prefs error:', err);
    }
  }, [user?.id]);
  
  // Handle max per week change
  const handleMaxPerWeekChange = useCallback(async (maxPerWeek: number) => {
    if (!user?.id) return;
    
    try {
      const updated = await updateNotificationPrefs(user.id, { max_per_week: maxPerWeek });
      setPrefs(updated);
    } catch (err) {
      console.error('[Inbox] Update prefs error:', err);
    }
  }, [user?.id]);
  
  // Count unread
  const unreadCount = notifications.filter(n => !n.read_at).length;
  
  // Render empty state
  const renderEmptyState = () => (
    <View style={styles.emptyContainer}>
      <SafeIcon name="notifications-outline" size={48} color={Colors.textTertiary} />
      <Text style={styles.emptyTitle}>No notes yet.</Text>
      <Text style={styles.emptySubtitle}>
        If you'd like, you can turn on gentle heads-ups.
      </Text>
      <TouchableOpacity
        style={styles.enableButton}
        onPress={() => handleToggleEnabled(true)}
        activeOpacity={0.7}
      >
        <Text style={styles.enableButtonText}>Enable notifications</Text>
      </TouchableOpacity>
    </View>
  );
  
  // Render notification item
  const renderNotificationItem = (notif: Notification) => {
    const isUnread = !notif.read_at;
    
    return (
      <TouchableOpacity
        key={notif.id}
        style={[styles.notificationItem, isUnread && styles.notificationItemUnread]}
        onPress={() => handleNotificationTap(notif)}
        activeOpacity={0.7}
      >
        {isUnread && <View style={styles.unreadDot} />}
        <View style={styles.notificationContent}>
          <Text style={[styles.notificationTitle, isUnread && styles.notificationTitleUnread]} numberOfLines={1}>
            {notif.title}
          </Text>
          <Text style={styles.notificationBody} numberOfLines={2}>
            {notif.body}
          </Text>
          <Text style={styles.notificationDate}>{formatDate(notif.created_at)}</Text>
        </View>
        <SafeIcon name="chevron-forward" size={16} color={Colors.textTertiary} />
      </TouchableOpacity>
    );
  };
  
  // Render detail modal
  const renderDetailModal = () => {
    if (!selectedNotification) return null;
    
    return (
      <Modal
        visible={!!selectedNotification}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setSelectedNotification(null)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setSelectedNotification(null)}>
              <SafeIcon name="close" size={24} color={Colors.text} />
            </TouchableOpacity>
            <Text style={styles.modalHeaderTitle}>Notification</Text>
            <View style={{ width: 24 }} />
          </View>
          
          <ScrollView style={styles.modalContent} showsVerticalScrollIndicator={false}>
            <Text style={styles.modalTitle}>{selectedNotification.title}</Text>
            <Text style={styles.modalBody}>{selectedNotification.body}</Text>
            
            {/* Based on chips */}
            {selectedNotification.data?.based_on && selectedNotification.data.based_on.length > 0 && (
              <View style={styles.basedOnContainer}>
                <Text style={styles.basedOnLabel}>Based on:</Text>
                <View style={styles.basedOnChips}>
                  {selectedNotification.data.based_on.map((item, index) => (
                    <View key={index} style={styles.basedOnChip}>
                      <Text style={styles.basedOnChipText}>{item}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
            
            <Text style={styles.modalDate}>{formatDate(selectedNotification.created_at)}</Text>
            
            {/* View timeline button */}
            <TouchableOpacity
              style={styles.timelineButton}
              onPress={() => handleViewTimeline(selectedNotification)}
              activeOpacity={0.7}
            >
              <Text style={styles.timelineButtonText}>View timeline →</Text>
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      </Modal>
    );
  };
  
  // Render preferences section
  const renderPreferences = () => (
    <View style={styles.prefsContainer}>
      <Text style={styles.prefsTitle}>Settings</Text>
      
      <View style={styles.prefRow}>
        <View style={styles.prefLabelContainer}>
          <Text style={styles.prefLabel}>Gentle heads-ups</Text>
          <Text style={styles.prefSubtitle}>Receive transit-based notes</Text>
        </View>
        <Switch
          value={prefs.enabled}
          onValueChange={handleToggleEnabled}
          trackColor={{ false: Colors.border, true: Colors.accent }}
          thumbColor={Colors.text}
        />
      </View>
      
      {prefs.enabled && (
        <>
          <View style={styles.prefRow}>
            <Text style={styles.prefLabel}>Quiet hours</Text>
            <Text style={styles.prefValue}>10 PM – 7 AM</Text>
          </View>
          
          <View style={styles.prefRow}>
            <Text style={styles.prefLabel}>Max per week</Text>
            <View style={styles.maxPerWeekOptions}>
              {MAX_PER_WEEK_OPTIONS.map((num) => (
                <TouchableOpacity
                  key={num}
                  style={[
                    styles.maxPerWeekOption,
                    prefs.max_per_week === num && styles.maxPerWeekOptionSelected,
                  ]}
                  onPress={() => handleMaxPerWeekChange(num)}
                >
                  <Text style={[
                    styles.maxPerWeekOptionText,
                    prefs.max_per_week === num && styles.maxPerWeekOptionTextSelected,
                  ]}>
                    {num}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </>
      )}
    </View>
  );
  
  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <StatusBar style="light" />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={Colors.textTertiary} />
          <Text style={styles.loadingText}>Loading inbox...</Text>
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar style="light" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Inbox</Text>
        {unreadCount > 0 && (
          <View style={styles.unreadBadge}>
            <Text style={styles.unreadBadgeText}>{unreadCount}</Text>
          </View>
        )}
      </View>
      
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.textTertiary}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Error state */}
        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity onPress={() => fetchData()} style={styles.retryButton}>
              <Text style={styles.retryButtonText}>Retry</Text>
            </TouchableOpacity>
          </View>
        )}
        
        {/* Empty state or notification list */}
        {notifications.length === 0 && !prefs.enabled ? (
          renderEmptyState()
        ) : notifications.length === 0 ? (
          <View style={styles.emptyContainer}>
            <SafeIcon name="checkmark-circle-outline" size={48} color={Colors.textTertiary} />
            <Text style={styles.emptyTitle}>All caught up.</Text>
            <Text style={styles.emptySubtitle}>
              You'll receive notes here when there's something to share.
            </Text>
          </View>
        ) : (
          <View style={styles.notificationsList}>
            {notifications.map(renderNotificationItem)}
          </View>
        )}
        
        {/* Preferences */}
        {renderPreferences()}
      </ScrollView>
      
      {/* Detail Modal */}
      {renderDetailModal()}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  loadingText: {
    fontSize: 13,
    color: Colors.textTertiary,
    opacity: 0.6,
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    gap: Spacing.sm,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '300',
    color: Colors.text,
  },
  unreadBadge: {
    backgroundColor: Colors.accent,
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  unreadBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.background,
  },
  
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: Spacing.lg,
    paddingBottom: Spacing.xxl,
  },
  
  // Empty state
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: Spacing.xxxl,
    gap: Spacing.md,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '400',
    color: Colors.text,
    marginTop: Spacing.md,
  },
  emptySubtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
    maxWidth: 260,
    lineHeight: 22,
  },
  enableButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 12,
    paddingHorizontal: Spacing.lg,
    borderRadius: 8,
    marginTop: Spacing.md,
  },
  enableButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.background,
  },
  
  // Error state
  errorContainer: {
    alignItems: 'center',
    paddingVertical: Spacing.xl,
    gap: Spacing.sm,
  },
  errorText: {
    fontSize: 14,
    color: Colors.error || '#FF6B6B',
  },
  retryButton: {
    paddingVertical: 8,
    paddingHorizontal: Spacing.md,
  },
  retryButtonText: {
    fontSize: 14,
    color: Colors.accent,
    fontWeight: '500',
  },
  
  // Notifications list
  notificationsList: {
    gap: 1,
    marginBottom: Spacing.xl,
  },
  notificationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.02)',
    borderRadius: 8,
    padding: Spacing.md,
    marginBottom: 8,
  },
  notificationItemUnread: {
    backgroundColor: 'rgba(255,255,255,0.05)',
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.accent,
    marginRight: Spacing.sm,
  },
  notificationContent: {
    flex: 1,
  },
  notificationTitle: {
    fontSize: 15,
    fontWeight: '400',
    color: Colors.text,
    opacity: 0.8,
    marginBottom: 4,
  },
  notificationTitleUnread: {
    opacity: 1,
    fontWeight: '500',
  },
  notificationBody: {
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 19,
    marginBottom: 6,
  },
  notificationDate: {
    fontSize: 11,
    color: Colors.textTertiary,
    opacity: 0.6,
  },
  
  // Preferences
  prefsContainer: {
    marginTop: Spacing.xl,
    paddingTop: Spacing.lg,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.05)',
  },
  prefsTitle: {
    fontSize: 11,
    fontWeight: '500',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: Spacing.md,
  },
  prefRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: Spacing.sm,
  },
  prefLabelContainer: {
    flex: 1,
  },
  prefLabel: {
    fontSize: 15,
    color: Colors.text,
  },
  prefSubtitle: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginTop: 2,
  },
  prefValue: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  maxPerWeekOptions: {
    flexDirection: 'row',
    gap: 8,
  },
  maxPerWeekOption: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    backgroundColor: 'rgba(255,255,255,0.05)',
  },
  maxPerWeekOptionSelected: {
    backgroundColor: Colors.accent,
  },
  maxPerWeekOptionText: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
  maxPerWeekOptionTextSelected: {
    color: Colors.background,
    fontWeight: '500',
  },
  
  // Modal
  modalContainer: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.05)',
  },
  modalHeaderTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.text,
  },
  modalContent: {
    flex: 1,
    padding: Spacing.lg,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '400',
    color: Colors.text,
    marginBottom: Spacing.md,
    lineHeight: 28,
  },
  modalBody: {
    fontSize: 15,
    color: Colors.textSecondary,
    lineHeight: 24,
    marginBottom: Spacing.lg,
  },
  modalDate: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginBottom: Spacing.xl,
  },
  basedOnContainer: {
    marginBottom: Spacing.lg,
  },
  basedOnLabel: {
    fontSize: 11,
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: Spacing.sm,
  },
  basedOnChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  basedOnChip: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 4,
    paddingVertical: 4,
    paddingHorizontal: 10,
  },
  basedOnChipText: {
    fontSize: 12,
    color: Colors.textSecondary,
  },
  timelineButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 14,
    paddingHorizontal: Spacing.lg,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: Spacing.md,
  },
  timelineButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.background,
  },
});
