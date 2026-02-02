import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Modal,
  Pressable,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, clearUser } = useAppStore();
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);

  const performLogout = async () => {
    console.log('[Profile] Starting logout...');
    setIsLoggingOut(true);
    setShowLogoutModal(false);
    setShowResetModal(false);
    try {
      console.log('[Profile] Calling clearUser...');
      await clearUser();
      console.log('[Profile] clearUser complete, navigating to /onboarding...');
      router.replace('/onboarding');
      console.log('[Profile] Navigation called');
    } catch (error) {
      console.error('[Profile] Logout error:', error);
    } finally {
      setIsLoggingOut(false);
    }
  };

  const handleLogout = () => {
    // Directly perform logout without confirmation modal
    performLogout();
  };

  const handleResetSession = () => {
    // Directly perform reset without confirmation modal  
    performLogout();
  };

  // Confirmation Modal Component - works on both web and native
  const ConfirmModal = ({ 
    visible, 
    title, 
    message, 
    confirmText, 
    onConfirm, 
    onCancel 
  }: {
    visible: boolean;
    title: string;
    message: string;
    confirmText: string;
    onConfirm: () => void;
    onCancel: () => void;
  }) => {
    if (!visible) return null;
    
    return (
      <View style={styles.modalOverlay}>
        <Pressable style={styles.modalBackdrop} onPress={onCancel} />
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>{title}</Text>
          <Text style={styles.modalMessage}>{message}</Text>
          <View style={styles.modalButtons}>
            <TouchableOpacity style={styles.cancelButton} onPress={onCancel}>
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.confirmButton} onPress={onConfirm}>
              <Text style={styles.confirmButtonText}>{confirmText}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  };

  return (
    <>
      <View style={styles.wrapper}>
        <SafeAreaView style={styles.container} edges={['top']}>
          <ScrollView 
            style={styles.scrollView}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
        {/* Header */}
        <View style={styles.header}>
          <Ionicons name="person-circle-outline" size={64} color={Colors.textSecondary} />
          <Text style={styles.userName}>{user?.name || 'User'}</Text>
          {user?.id && (
            <Text style={styles.userId}>ID: {user.id.slice(-8)}</Text>
          )}
        </View>

        {/* User Info Card */}
        {user && (
          <View style={styles.infoCard}>
            <Text style={styles.cardTitle}>Your Profile</Text>
            
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Birth Date</Text>
              <Text style={styles.infoValue}>{user.birth_date || '—'}</Text>
            </View>
            
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Birth Time</Text>
              <Text style={styles.infoValue}>{user.birth_time || '—'}</Text>
            </View>
            
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Location</Text>
              <Text style={styles.infoValue}>
                {user.birth_location?.city 
                  ? `${user.birth_location.city}, ${user.birth_location.country}`
                  : '—'}
              </Text>
            </View>
          </View>
        )}

        {/* Actions */}
        <View style={styles.actionsCard}>
          <Text style={styles.cardTitle}>Session</Text>
          
          <Pressable 
            style={styles.actionButton}
            onPress={() => {
              console.log('[Profile] Log Out pressed');
              handleLogout();
            }}
            disabled={isLoggingOut}
            testID="logout-button"
          >
            <Ionicons name="log-out-outline" size={22} color={Colors.text} />
            <View style={styles.actionTextContainer} pointerEvents="none">
              <Text style={styles.actionTitle}>Log Out</Text>
              <Text style={styles.actionDescription}>
                Return to welcome screen
              </Text>
            </View>
            {isLoggingOut ? (
              <ActivityIndicator size="small" color={Colors.textTertiary} />
            ) : (
              <Ionicons name="chevron-forward" size={20} color={Colors.textTertiary} />
            )}
          </Pressable>

          <View style={styles.separator} />

          <Pressable 
            style={styles.actionButton}
            onPress={() => {
              console.log('[Profile] Reset Session pressed');
              handleResetSession();
            }}
            disabled={isLoggingOut}
            testID="reset-session-button"
          >
            <Ionicons name="refresh-outline" size={22} color={Colors.warning} />
            <View style={styles.actionTextContainer} pointerEvents="none">
              <Text style={[styles.actionTitle, { color: Colors.warning }]}>
                Reset Session
              </Text>
              <Text style={styles.actionDescription}>
                Start fresh as a new user
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={Colors.textTertiary} />
          </Pressable>
        </View>

        {/* Dev Info */}
        <View style={styles.devInfo}>
          <Text style={styles.devInfoText}>
            Project Mirror • Preview Build
          </Text>
        </View>
      </ScrollView>

      {/* Logout Confirmation Modal */}
      <ConfirmModal
        visible={showLogoutModal}
        title="Log Out"
        message="This will clear your session and return you to the welcome screen. Your data on the server will be preserved."
        confirmText="Log Out"
        onConfirm={performLogout}
        onCancel={() => setShowLogoutModal(false)}
      />

      {/* Reset Session Confirmation Modal */}
      <ConfirmModal
        visible={showResetModal}
        title="Reset Session"
        message="This will completely clear your local session, allowing you to register as a new user or log in with different details. Your existing data on the server will NOT be deleted."
        confirmText="Reset & Start Fresh"
        onConfirm={performLogout}
        onCancel={() => setShowResetModal(false)}
      />
        </SafeAreaView>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
    paddingVertical: 20,
  },
  userName: {
    fontSize: 22,
    fontWeight: '600',
    color: Colors.text,
    marginTop: 12,
  },
  userId: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginTop: 4,
    fontFamily: 'monospace',
  },
  infoCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 0.5,
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.border,
  },
  infoLabel: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  infoValue: {
    fontSize: 14,
    color: Colors.text,
    fontWeight: '500',
  },
  actionsCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
  actionTextContainer: {
    flex: 1,
    marginLeft: 12,
  },
  actionTitle: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.text,
  },
  actionDescription: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginTop: 2,
  },
  separator: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: Colors.border,
    marginVertical: 4,
  },
  devInfo: {
    alignItems: 'center',
    marginTop: 32,
  },
  devInfoText: {
    fontSize: 12,
    color: Colors.textTertiary,
  },
  // Modal styles
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    zIndex: 1000,
  },
  modalBackdrop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  modalContent: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 340,
    zIndex: 1001,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 12,
    textAlign: 'center',
  },
  modalMessage: {
    fontSize: 14,
    color: Colors.textSecondary,
    lineHeight: 20,
    marginBottom: 24,
    textAlign: 'center',
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: Colors.surfaceLight,
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.text,
  },
  confirmButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: Colors.error,
    alignItems: 'center',
  },
  confirmButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
