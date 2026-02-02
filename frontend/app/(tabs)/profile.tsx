import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ScrollView,
  ActivityIndicator,
  Modal,
  Platform,
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
    setIsLoggingOut(true);
    setShowLogoutModal(false);
    setShowResetModal(false);
    try {
      await clearUser();
      router.replace('/onboarding');
    } catch (error) {
      console.error('Logout error:', error);
      if (Platform.OS === 'web') {
        window.alert('Failed to log out. Please try again.');
      } else {
        Alert.alert('Error', 'Failed to log out. Please try again.');
      }
    } finally {
      setIsLoggingOut(false);
    }
  };

  const handleLogout = () => {
    if (Platform.OS === 'web') {
      setShowLogoutModal(true);
    } else {
      Alert.alert(
        'Log Out',
        'This will clear your session and return you to the welcome screen. Your data on the server will be preserved.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Log Out', style: 'destructive', onPress: performLogout },
        ]
      );
    }
  };

  const handleResetSession = () => {
    if (Platform.OS === 'web') {
      setShowResetModal(true);
    } else {
      Alert.alert(
        'Reset Session',
        'This will completely clear your local session, allowing you to register as a new user or log in with different details.\n\nYour existing data on the server will NOT be deleted.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Reset & Start Fresh', style: 'destructive', onPress: performLogout },
        ]
      );
    }
  };

  // Confirmation Modal for Web
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
  }) => (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onCancel}
    >
      <View style={styles.modalOverlay}>
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
    </Modal>
  );

  return (
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
          
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={handleLogout}
            disabled={isLoggingOut}
          >
            <Ionicons name="log-out-outline" size={22} color={Colors.text} />
            <View style={styles.actionTextContainer}>
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
          </TouchableOpacity>

          <View style={styles.separator} />

          <TouchableOpacity 
            style={styles.actionButton}
            onPress={handleResetSession}
            disabled={isLoggingOut}
          >
            <Ionicons name="refresh-outline" size={22} color={Colors.warning} />
            <View style={styles.actionTextContainer}>
              <Text style={[styles.actionTitle, { color: Colors.warning }]}>
                Reset Session
              </Text>
              <Text style={styles.actionDescription}>
                Start fresh as a new user
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={Colors.textTertiary} />
          </TouchableOpacity>
        </View>

        {/* Dev Info */}
        <View style={styles.devInfo}>
          <Text style={styles.devInfoText}>
            Project Mirror • Preview Build
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
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
});
