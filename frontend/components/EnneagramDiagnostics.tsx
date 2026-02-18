/**
 * Enneagram Diagnostics Panel
 * ============================
 * 
 * Compact, non-blocking diagnostics panel for STAGING debugging.
 * Only renders when:
 * 1. DEBUG_MIRROR_ENV === true (EXPO_PUBLIC_DEBUG_MIRROR=true)
 * 2. AND URL contains ?debug=1
 * 
 * Features:
 * - Compact floating button that expands to panel
 * - Shows API config, result data, wing scores
 * - Scrollable content, never blocks CTA buttons
 * - Close button always visible
 * - pointerEvents only inside panel
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Modal,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../constants/colors';
import { 
  shouldShowDebugUI, 
  copyToClipboard, 
  formatDebugData,
  API_BASE_URL,
  APP_ENV,
  BUILD_VERSION,
  BUILD_ID,
} from '../utils/debugUtils';

interface EnneagramDiagnosticsProps {
  // Optional gesture activated flag for mobile
  gestureActivated?: boolean;
  // Result data
  resultId?: string;
  coreType?: number;
  wing?: number | string | null;
  confidenceTier?: string;
  wingLeftScore?: number | null;
  wingRightScore?: number | null;
  assessmentDepth?: string;
  // Custom endpoint used
  endpoint?: string;
}

export const EnneagramDiagnostics: React.FC<EnneagramDiagnosticsProps> = ({
  gestureActivated = false,
  resultId,
  coreType,
  wing,
  confidenceTier,
  wingLeftScore,
  wingRightScore,
  assessmentDepth,
  endpoint,
}) => {
  const insets = useSafeAreaInsets();
  const [isOpen, setIsOpen] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  // Check if debug UI should show
  const showDebug = shouldShowDebugUI(gestureActivated);

  // Don't render at all if debug is not enabled
  if (!showDebug) {
    return null;
  }

  const diagnosticData = {
    // API Config
    api_base_url: API_BASE_URL,
    app_env: APP_ENV,
    build_version: BUILD_VERSION,
    build_id: BUILD_ID,
    endpoint_used: endpoint || 'N/A',
    // Result Data
    result_id: resultId || 'N/A',
    core_type: coreType ?? 'N/A',
    wing: wing ?? 'N/A',
    confidence_tier: confidenceTier || 'N/A',
    wing_left_score: wingLeftScore ?? 'N/A',
    wing_right_score: wingRightScore ?? 'N/A',
    assessment_depth: assessmentDepth || 'N/A',
  };

  const handleCopy = async () => {
    const success = await copyToClipboard(formatDebugData(diagnosticData));
    if (success) {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  return (
    <>
      {/* Floating trigger - positioned to NOT block bottom CTAs */}
      <View 
        style={[styles.triggerContainer, { bottom: Math.max(insets.bottom + 120, 140) }]}
        pointerEvents="box-none"
      >
        <TouchableOpacity
          style={styles.trigger}
          onPress={() => setIsOpen(true)}
          activeOpacity={0.8}
        >
          <Ionicons name="bug-outline" size={14} color="#fff" />
          <Text style={styles.triggerText}>Diag</Text>
        </TouchableOpacity>
      </View>

      {/* Diagnostics Modal */}
      <Modal
        visible={isOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setIsOpen(false)}
      >
        <View style={styles.modalOverlay} pointerEvents="box-none">
          <View 
            style={[
              styles.panelContainer, 
              { 
                bottom: Math.max(insets.bottom + 100, 120),
                maxHeight: '50%',
              }
            ]}
            pointerEvents="auto"
          >
            {/* Header */}
            <View style={styles.panelHeader}>
              <Text style={styles.panelTitle}>Enneagram Diagnostics</Text>
              <View style={styles.headerActions}>
                <TouchableOpacity 
                  style={[styles.copyBtn, copySuccess && styles.copyBtnSuccess]}
                  onPress={handleCopy}
                >
                  <Ionicons 
                    name={copySuccess ? "checkmark" : "copy-outline"} 
                    size={14} 
                    color={copySuccess ? "#4CAF50" : Colors.accent} 
                  />
                </TouchableOpacity>
                <TouchableOpacity 
                  style={styles.closeBtn}
                  onPress={() => setIsOpen(false)}
                >
                  <Ionicons name="close" size={20} color={Colors.text} />
                </TouchableOpacity>
              </View>
            </View>

            {/* Content - Scrollable */}
            <ScrollView 
              style={styles.panelContent}
              showsVerticalScrollIndicator
            >
              {/* API Config Section */}
              <Text style={styles.sectionTitle}>API Config</Text>
              <View style={styles.row}>
                <Text style={styles.label}>API_BASE_URL:</Text>
                <Text style={styles.value} numberOfLines={1}>{diagnosticData.api_base_url}</Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>ENV:</Text>
                <Text style={styles.value}>{diagnosticData.app_env}</Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>Endpoint:</Text>
                <Text style={styles.value} numberOfLines={1}>{diagnosticData.endpoint_used}</Text>
              </View>

              {/* Result Data Section */}
              <Text style={[styles.sectionTitle, { marginTop: 12 }]}>Result Data</Text>
              <View style={styles.row}>
                <Text style={styles.label}>result_id:</Text>
                <Text style={styles.value}>{diagnosticData.result_id}</Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>core_type:</Text>
                <Text style={styles.value}>{diagnosticData.core_type}</Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>wing:</Text>
                <Text style={[styles.value, wing === null && styles.valueNull]}>
                  {wing === null ? 'null (not determined)' : String(wing)}
                </Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>confidence:</Text>
                <Text style={styles.value}>{diagnosticData.confidence_tier}</Text>
              </View>

              {/* Wing Scores Section */}
              <Text style={[styles.sectionTitle, { marginTop: 12 }]}>Wing Scores</Text>
              <View style={styles.row}>
                <Text style={styles.label}>wing_left_score:</Text>
                <Text style={[styles.value, wingLeftScore === null && styles.valueNull]}>
                  {wingLeftScore === null || wingLeftScore === undefined ? 'N/A' : wingLeftScore}
                </Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>wing_right_score:</Text>
                <Text style={[styles.value, wingRightScore === null && styles.valueNull]}>
                  {wingRightScore === null || wingRightScore === undefined ? 'N/A' : wingRightScore}
                </Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>assessment_depth:</Text>
                <Text style={styles.value}>{diagnosticData.assessment_depth}</Text>
              </View>
            </ScrollView>
          </View>
        </View>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  triggerContainer: {
    position: 'absolute',
    right: 12,
    zIndex: 999,
  },
  trigger: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: 'rgba(76, 175, 80, 0.85)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
    elevation: 4,
  },
  triggerText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    justifyContent: 'flex-end',
  },
  panelContainer: {
    position: 'absolute',
    right: 12,
    left: 12,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 8,
    overflow: 'hidden',
  },
  panelHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  panelTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  copyBtn: {
    padding: 6,
    borderRadius: 6,
    backgroundColor: 'rgba(147, 130, 255, 0.1)',
  },
  copyBtnSuccess: {
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  closeBtn: {
    padding: 4,
  },
  panelContent: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    maxHeight: 300,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.accent,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  row: {
    flexDirection: 'row',
    marginBottom: 4,
  },
  label: {
    fontSize: 11,
    color: Colors.textSecondary,
    width: 110,
  },
  value: {
    flex: 1,
    fontSize: 11,
    color: Colors.text,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  valueNull: {
    color: '#FF6B6B',
    fontStyle: 'italic',
  },
});

export default EnneagramDiagnostics;
