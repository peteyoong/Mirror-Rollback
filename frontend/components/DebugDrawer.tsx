/**
 * DebugDrawer Component
 * =====================
 * 
 * A collapsible, non-blocking debug panel for Enneagram screens.
 * 
 * Features:
 * - Hidden by default (even when DEBUG_MIRROR=true)
 * - Appears only after explicit activation (URL ?debug=1 or gesture)
 * - Collapsible bottom drawer that doesn't block navigation
 * - Copy to clipboard functionality
 * - SafeArea aware - doesn't overlap notch or bottom buttons
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Modal,
  Pressable,
  Alert,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../constants/colors';
import { copyToClipboard, formatDebugData, shouldShowDebugUI } from '../utils/debugUtils';

interface DebugDrawerProps {
  // Whether debug gesture has been activated (for mobile)
  gestureActivated: boolean;
  // Debug data to display
  data: Record<string, any>;
  // Optional title
  title?: string;
  // Optional: Position of the drawer trigger (default: bottom-right)
  position?: 'bottom-left' | 'bottom-right';
}

export const DebugDrawer: React.FC<DebugDrawerProps> = ({
  gestureActivated,
  data,
  title = 'Debug Info',
  position = 'bottom-right',
}) => {
  const insets = useSafeAreaInsets();
  const [isOpen, setIsOpen] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  
  // Check if debug UI should be shown
  const showDebug = shouldShowDebugUI(gestureActivated);
  
  // Don't render anything if debug is not enabled
  if (!showDebug) return null;
  
  const handleCopy = async () => {
    const success = await copyToClipboard(formatDebugData(data));
    if (success) {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
      if (Platform.OS !== 'web') {
        Alert.alert('Copied', 'Debug data copied to clipboard');
      }
    }
  };
  
  const renderDataRow = (key: string, value: any, indent: number = 0) => {
    const displayValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
    return (
      <Text key={key} style={[styles.dataText, { marginLeft: indent * 12 }]}>
        <Text style={styles.dataKey}>{key}:</Text> {displayValue}
      </Text>
    );
  };
  
  const renderData = (obj: Record<string, any>, indent: number = 0): React.ReactNode[] => {
    return Object.entries(obj).map(([key, value]) => {
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        return (
          <View key={key}>
            <Text style={[styles.dataKey, { marginLeft: indent * 12 }]}>{key}:</Text>
            {renderData(value, indent + 1)}
          </View>
        );
      }
      return renderDataRow(key, value, indent);
    });
  };

  return (
    <>
      {/* Floating Trigger Button */}
      <TouchableOpacity
        style={[
          styles.floatingButton,
          position === 'bottom-left' ? styles.floatingButtonLeft : styles.floatingButtonRight,
          { bottom: Math.max(insets.bottom + 80, 100) }, // Above any bottom CTAs
        ]}
        onPress={() => setIsOpen(true)}
        activeOpacity={0.8}
      >
        <Ionicons name="bug-outline" size={16} color="#fff" />
        <Text style={styles.floatingButtonText}>Debug</Text>
      </TouchableOpacity>

      {/* Debug Modal/Drawer */}
      <Modal
        visible={isOpen}
        transparent
        animationType="slide"
        onRequestClose={() => setIsOpen(false)}
      >
        <Pressable style={styles.modalOverlay} onPress={() => setIsOpen(false)}>
          <Pressable 
            style={[styles.drawerContainer, { paddingBottom: insets.bottom + 16 }]}
            onPress={e => e.stopPropagation()}
          >
            {/* Header */}
            <View style={styles.drawerHeader}>
              <View style={styles.drawerHandle} />
              <View style={styles.headerRow}>
                <Text style={styles.drawerTitle}>{title}</Text>
                <View style={styles.headerActions}>
                  <TouchableOpacity 
                    style={[styles.copyButton, copySuccess && styles.copyButtonSuccess]}
                    onPress={handleCopy}
                  >
                    <Ionicons 
                      name={copySuccess ? "checkmark" : "copy-outline"} 
                      size={16} 
                      color={copySuccess ? "#4CAF50" : Colors.accent} 
                    />
                    <Text style={[styles.copyButtonText, copySuccess && styles.copyButtonTextSuccess]}>
                      {copySuccess ? 'Copied!' : 'Copy'}
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={styles.closeButton}
                    onPress={() => setIsOpen(false)}
                  >
                    <Ionicons name="close" size={24} color={Colors.text} />
                  </TouchableOpacity>
                </View>
              </View>
            </View>
            
            {/* Content */}
            <ScrollView 
              style={styles.drawerContent}
              showsVerticalScrollIndicator={true}
            >
              <View style={styles.dataContainer}>
                {renderData(data)}
              </View>
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  // Floating trigger button
  floatingButton: {
    position: 'absolute',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(76, 175, 80, 0.9)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    zIndex: 1000,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  floatingButtonLeft: {
    left: 16,
  },
  floatingButtonRight: {
    right: 16,
  },
  floatingButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  
  // Modal overlay
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  
  // Drawer container
  drawerContainer: {
    backgroundColor: Colors.surface,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '60%',
    minHeight: 200,
  },
  
  // Header
  drawerHeader: {
    alignItems: 'center',
    paddingTop: 8,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    paddingBottom: 12,
  },
  drawerHandle: {
    width: 40,
    height: 4,
    backgroundColor: Colors.border,
    borderRadius: 2,
    marginBottom: 12,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
  },
  drawerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  
  // Copy button
  copyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: 'rgba(147, 130, 255, 0.1)',
  },
  copyButtonSuccess: {
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  copyButtonText: {
    fontSize: 13,
    color: Colors.accent,
    fontWeight: '500',
  },
  copyButtonTextSuccess: {
    color: '#4CAF50',
  },
  
  // Close button
  closeButton: {
    padding: 4,
  },
  
  // Content
  drawerContent: {
    flex: 1,
    paddingHorizontal: 16,
  },
  dataContainer: {
    paddingVertical: 12,
  },
  dataText: {
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 20,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  dataKey: {
    color: Colors.accent,
    fontWeight: '600',
  },
});

export default DebugDrawer;
