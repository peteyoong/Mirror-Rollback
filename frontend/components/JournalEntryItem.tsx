import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  TextInput,
  Modal,
  ActivityIndicator,
  Alert,
  Platform,
  Animated,
} from 'react-native';
import { Colors } from '../constants/colors';
import { format } from 'date-fns';
import { useTheme } from '../contexts/ThemeContext';

// Highlight animation constants
const HIGHLIGHT_DURATION = 2000; // 2 seconds
const HIGHLIGHT_FADE_DURATION = 400;

// Phase pill helpers
const getPhaseIcon = (phaseId: string): string => {
  const icons: { [key: string]: string } = {
    q1: '🌱',  // Recognition
    q2: '⚡',  // Confrontation
    q3: '🔀',  // The Crossroads
    q4: '🌊',  // Integration
  };
  return icons[phaseId] || '⭐';
};

const getPhaseColor = (phaseId: string, isDark: boolean): string => {
  const colors: { [key: string]: string } = {
    q1: isDark ? 'rgba(76, 175, 80, 0.2)' : 'rgba(76, 175, 80, 0.15)',
    q2: isDark ? 'rgba(255, 152, 0, 0.2)' : 'rgba(255, 152, 0, 0.15)',
    q3: isDark ? 'rgba(139, 92, 246, 0.2)' : 'rgba(139, 92, 246, 0.15)',
    q4: isDark ? 'rgba(33, 150, 243, 0.2)' : 'rgba(33, 150, 243, 0.15)',
  };
  return colors[phaseId] || (isDark ? 'rgba(139, 92, 246, 0.15)' : 'rgba(139, 92, 246, 0.1)');
};

interface JournalEntryItemProps {
  id: string;
  content: string;
  created_at: string;
  themes?: string[];
  phase_id?: string;  // Timeline phase ID
  phase_name?: string;  // Timeline phase name
  onReflect?: (content: string) => void;
  onEdit?: (id: string, newContent: string) => Promise<void>;
  onDelete?: (id: string) => Promise<void>;
  isReflectDisabled?: boolean;
  isHighlighted?: boolean; // NEW: highlight state for newly saved entries
}

export default function JournalEntryItem({
  id,
  content,
  created_at,
  themes = [],
  phase_id,
  phase_name,
  onReflect,
  onEdit,
  onDelete,
  isReflectDisabled = false,
  isHighlighted = false,
}: JournalEntryItemProps) {
  const { theme, isDark } = useTheme();
  const [showMenu, setShowMenu] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(content);
  const [isSaving, setIsSaving] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Highlight animation
  const highlightAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  
  // Run highlight animation when isHighlighted becomes true
  useEffect(() => {
    if (isHighlighted) {
      // Start highlight animation
      highlightAnim.setValue(1);
      scaleAnim.setValue(1.015); // Subtle scale bump
      
      // After HIGHLIGHT_DURATION, fade out
      const fadeTimer = setTimeout(() => {
        Animated.parallel([
          Animated.timing(highlightAnim, {
            toValue: 0,
            duration: HIGHLIGHT_FADE_DURATION,
            useNativeDriver: false, // backgroundColor can't use native driver
          }),
          Animated.timing(scaleAnim, {
            toValue: 1,
            duration: HIGHLIGHT_FADE_DURATION,
            useNativeDriver: true,
          }),
        ]).start();
      }, HIGHLIGHT_DURATION);
      
      return () => clearTimeout(fadeTimer);
    }
  }, [isHighlighted, highlightAnim, scaleAnim]);
  
  const formattedDate = format(new Date(created_at), 'MMM d, yyyy');

  // Interpolate highlight color
  const highlightBackgroundColor = highlightAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [
      theme.surface, 
      isDark ? 'rgba(139, 92, 246, 0.12)' : 'rgba(139, 92, 246, 0.08)'
    ],
  });
  
  const highlightBorderColor = highlightAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [
      'transparent',
      isDark ? 'rgba(139, 92, 246, 0.4)' : 'rgba(139, 92, 246, 0.3)'
    ],
  });

  const handleEdit = () => {
    setShowMenu(false);
    setEditContent(content);
    setIsEditing(true);
  };

  const handleSaveEdit = async () => {
    if (!onEdit || !editContent.trim()) return;
    
    setIsSaving(true);
    try {
      await onEdit(id, editContent.trim());
      setIsEditing(false);
    } catch (error) {
      console.error('[JournalEntry] Edit error:', error);
      // Show error feedback
      if (Platform.OS === 'web') {
        alert('Failed to save changes. Please try again.');
      } else {
        Alert.alert('Error', 'Failed to save changes. Please try again.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setEditContent(content);
    setIsEditing(false);
  };

  const handleDeletePress = () => {
    setShowMenu(false);
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    if (!onDelete) return;
    
    setIsDeleting(true);
    try {
      await onDelete(id);
      setShowDeleteConfirm(false);
    } catch (error) {
      console.error('[JournalEntry] Delete error:', error);
      if (Platform.OS === 'web') {
        alert('Failed to delete entry. Please try again.');
      } else {
        Alert.alert('Error', 'Failed to delete entry. Please try again.');
      }
      setIsDeleting(false);
    }
  };

  // Edit mode UI
  if (isEditing) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface }]}>
        <View style={styles.header}>
          <Text style={[styles.date, { color: theme.textTertiary }]}>{formattedDate}</Text>
          <Text style={[styles.editingLabel, { color: theme.accent }]}>Editing</Text>
        </View>
        <TextInput
          style={[styles.editInput, { 
            backgroundColor: theme.background, 
            color: theme.text,
            borderColor: theme.border,
          }]}
          value={editContent}
          onChangeText={setEditContent}
          multiline
          autoFocus
          placeholder="Write your reflection..."
          placeholderTextColor={theme.textTertiary}
        />
        <View style={styles.editActions}>
          <TouchableOpacity
            style={[styles.editCancelButton, { borderColor: theme.border }]}
            onPress={handleCancelEdit}
            disabled={isSaving}
          >
            <Text style={[styles.editCancelText, { color: theme.textSecondary }]}>Cancel</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.editSaveButton, 
              { backgroundColor: theme.accent },
              (!editContent.trim() || isSaving) && styles.editSaveButtonDisabled,
            ]}
            onPress={handleSaveEdit}
            disabled={!editContent.trim() || isSaving}
          >
            {isSaving ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.editSaveText}>Save</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <Animated.View 
      style={[
        styles.container, 
        { 
          backgroundColor: isHighlighted ? highlightBackgroundColor : theme.surface,
          borderWidth: isHighlighted ? 1.5 : 0,
          borderColor: isHighlighted ? highlightBorderColor : 'transparent',
          transform: [{ scale: scaleAnim }],
        }
      ]}
    >
      {/* Header with date and actions */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={[styles.date, { color: theme.textTertiary }]}>{formattedDate}</Text>
          {/* Phase Pill Tag - Timeline connection */}
          {phase_id && phase_name && (
            <View style={[styles.phasePill, { backgroundColor: getPhaseColor(phase_id, isDark) }]}>
              <Text style={styles.phaseIcon}>{getPhaseIcon(phase_id)}</Text>
              <Text style={[styles.phasePillText, { color: theme.text }]}>{phase_name}</Text>
            </View>
          )}
          {isHighlighted && (
            <Text style={[styles.savedLabel, { color: Colors.accent }]}>✓ Saved</Text>
          )}
        </View>
        <View style={styles.headerActions}>
          {/* Reflect with Mirror button - primary visible action */}
          {onReflect && (
            <TouchableOpacity 
              style={[
                styles.reflectButton,
                { backgroundColor: theme.accent + '15' },
                isReflectDisabled && styles.reflectButtonDisabled
              ]}
              onPress={() => onReflect(content)}
              disabled={isReflectDisabled}
            >
              <Text style={{ fontSize: 12, color: isReflectDisabled ? theme.textTertiary : theme.accent }}>✦</Text>
              <Text style={[
                styles.reflectButtonText,
                { color: isReflectDisabled ? theme.textTertiary : theme.accent }
              ]}>Reflect</Text>
            </TouchableOpacity>
          )}
          
          {/* Overflow menu trigger */}
          {(onEdit || onDelete) && (
            <TouchableOpacity
              style={styles.menuButton}
              onPress={() => setShowMenu(!showMenu)}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
              <Text style={[styles.menuDots, { color: theme.textTertiary }]}>•••</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Overflow menu dropdown */}
      {showMenu && (
        <View style={[styles.menuDropdown, { backgroundColor: theme.background, borderColor: theme.border }]}>
          {onEdit && (
            <TouchableOpacity style={styles.menuItem} onPress={handleEdit}>
              <Text style={[styles.menuItemText, { color: theme.text }]}>Edit</Text>
            </TouchableOpacity>
          )}
          {onDelete && (
            <TouchableOpacity style={styles.menuItem} onPress={handleDeletePress}>
              <Text style={[styles.menuItemText, styles.menuItemDelete, { color: theme.error }]}>Delete</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity style={styles.menuItem} onPress={() => setShowMenu(false)}>
            <Text style={[styles.menuItemText, { color: theme.textTertiary }]}>Cancel</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Content */}
      <TouchableOpacity 
        activeOpacity={0.8}
        onPress={() => showMenu && setShowMenu(false)}
      >
        <Text style={[styles.content, { color: theme.textSecondary }]} numberOfLines={5}>
          {content}
        </Text>
      </TouchableOpacity>

      {/* Themes/Tags */}
      {themes.length > 0 && (
        <View style={styles.themesContainer}>
          {themes.map((themeItem, index) => (
            <View key={index} style={[styles.themeTag, { backgroundColor: theme.background }]}>
              <Text style={[styles.themeText, { color: theme.textTertiary }]}>{themeItem}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        visible={showDeleteConfirm}
        transparent
        animationType="fade"
        onRequestClose={() => setShowDeleteConfirm(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => !isDeleting && setShowDeleteConfirm(false)}
        >
          <View style={[styles.deleteModal, { backgroundColor: theme.surface }]}>
            <Text style={[styles.deleteModalTitle, { color: theme.text }]}>
              Delete this entry?
            </Text>
            <Text style={[styles.deleteModalSubtitle, { color: theme.textSecondary }]}>
              This can't be undone.
            </Text>
            
            <View style={styles.deleteModalActions}>
              <TouchableOpacity
                style={[styles.deleteModalCancelButton, { borderColor: theme.border }]}
                onPress={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
              >
                <Text style={[styles.deleteModalCancelText, { color: theme.textSecondary }]}>
                  Keep it
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.deleteModalConfirmButton, { backgroundColor: theme.error }]}
                onPress={handleConfirmDelete}
                disabled={isDeleting}
              >
                {isDeleting ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <Text style={styles.deleteModalConfirmText}>Delete</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </TouchableOpacity>
      </Modal>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  savedLabel: {
    fontSize: 11,
    fontWeight: '600',
  },
  date: {
    fontSize: 12,
    color: Colors.textTertiary,
  },
  // Phase pill tag styles
  phasePill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    gap: 3,
  },
  phaseIcon: {
    fontSize: 10,
  },
  phasePillText: {
    fontSize: 10,
    fontWeight: '600',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  reflectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.accent + '15',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  reflectButtonDisabled: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  reflectButtonText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.accent,
  },
  menuButton: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  menuDots: {
    fontSize: 14,
    letterSpacing: 1,
    fontWeight: '700',
  },
  menuDropdown: {
    position: 'absolute',
    top: 40,
    right: 10,
    zIndex: 100,
    borderRadius: 10,
    borderWidth: 1,
    minWidth: 100,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 5,
  },
  menuItem: {
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  menuItemText: {
    fontSize: 14,
    fontWeight: '500',
  },
  menuItemDelete: {
    // Color set dynamically
  },
  content: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
  },
  themesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 10,
  },
  themeTag: {
    backgroundColor: Colors.background,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginRight: 8,
    marginBottom: 6,
  },
  themeText: {
    fontSize: 11,
    color: Colors.textTertiary,
  },
  
  // Edit mode styles
  editingLabel: {
    fontSize: 11,
    fontWeight: '600',
  },
  editInput: {
    borderRadius: 10,
    borderWidth: 1,
    padding: 12,
    fontSize: 15,
    lineHeight: 22,
    minHeight: 100,
    maxHeight: 200,
    textAlignVertical: 'top',
  },
  editActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 10,
    marginTop: 12,
  },
  editCancelButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
  },
  editCancelText: {
    fontSize: 14,
    fontWeight: '500',
  },
  editSaveButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    minWidth: 70,
    alignItems: 'center',
  },
  editSaveButtonDisabled: {
    opacity: 0.5,
  },
  editSaveText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
  
  // Delete confirmation modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  deleteModal: {
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 300,
    alignItems: 'center',
  },
  deleteModalTitle: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  deleteModalSubtitle: {
    fontSize: 14,
    marginBottom: 24,
    textAlign: 'center',
  },
  deleteModalActions: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  deleteModalCancelButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: 'center',
  },
  deleteModalCancelText: {
    fontSize: 15,
    fontWeight: '500',
  },
  deleteModalConfirmButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  deleteModalConfirmText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
  },
});
