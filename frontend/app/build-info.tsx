/**
 * Build Info Screen
 * 
 * Displays full provenance information for debugging environment mismatches.
 * Shows frontend build version, backend health, and environment configuration.
 * 
 * Access: Settings → tap "Mirror" title 5 times OR navigate to /build-info
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../constants/colors';
import { API_BASE_URL } from '../services/api';
import { BUILD_ID, BUILD_VERSION } from '../utils/buildInfo';

// Environment variables
const ENV = process.env.EXPO_PUBLIC_ENV || 'unknown';
const DEBUG_MIRROR = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

interface BackendHealth {
  env: string;
  status: string;
  build_version: string;
  build_label: string;
  git_sha: string;
  db_name: string;
  db_type: string;
  timestamp_utc: string;
  expected_frontend_env: string;
  api_origin?: string;
}

// Get window origin for web platform
const getWindowOrigin = (): string => {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    return window.location.origin;
  }
  return 'native-app';
};

export default function BuildInfoScreen() {
  const router = useRouter();
  const [backendHealth, setBackendHealth] = useState<BackendHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshCount, setRefreshCount] = useState(0);
  const windowOrigin = getWindowOrigin();

  const fetchBackendHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setBackendHealth(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch backend health');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBackendHealth();
  }, [refreshCount]);

  // Check for environment mismatch (RED warning)
  const hasEnvMismatch = backendHealth && backendHealth.expected_frontend_env !== ENV;
  
  // Check for origin mismatch (YELLOW warning) - only on web
  const hasOriginMismatch = Platform.OS === 'web' && 
    backendHealth?.api_origin && 
    windowOrigin !== 'native-app' &&
    !backendHealth.api_origin.includes(windowOrigin) &&
    !windowOrigin.includes('localhost');

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Build Info</Text>
        <TouchableOpacity
          style={styles.refreshButton}
          onPress={() => setRefreshCount(c => c + 1)}
        >
          <Ionicons name="refresh" size={20} color={Colors.text} />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>
        {/* Environment Mismatch Warning - RED */}
        {hasEnvMismatch && (
          <View style={styles.warningCard}>
            <Ionicons name="warning" size={24} color="#FF6B6B" />
            <Text style={styles.warningText}>
              Environment Mismatch Detected!{'\n'}
              Frontend: {ENV} | Backend: {backendHealth?.expected_frontend_env}
            </Text>
          </View>
        )}

        {/* Origin Mismatch Warning - YELLOW */}
        {hasOriginMismatch && (
          <View style={styles.originWarningCard}>
            <Ionicons name="alert-circle" size={24} color="#F5A623" />
            <View style={styles.originWarningContent}>
              <Text style={styles.originWarningTitle}>Origin Mismatch</Text>
              <Text style={styles.originWarningText}>
                window.location: {windowOrigin}{'\n'}
                api_origin: {backendHealth?.api_origin}
              </Text>
            </View>
          </View>
        )}

        {/* Frontend Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📱 Frontend</Text>
          <View style={styles.infoCard}>
            <InfoRow label="ENV" value={ENV} highlight={hasEnvMismatch} />
            <InfoRow label="BUILD_VERSION" value={BUILD_VERSION} />
            <InfoRow label="BUILD_ID" value={BUILD_ID} />
            <InfoRow label="API_BASE_URL" value={API_BASE_URL} />
            {Platform.OS === 'web' && <InfoRow label="window.origin" value={windowOrigin} />}
            <InfoRow label="DEBUG_MIRROR" value={DEBUG_MIRROR ? 'true' : 'false'} />
            <InfoRow label="Platform" value={Platform.OS} />
          </View>
        </View>

        {/* Backend Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🖥️ Backend</Text>
          {loading ? (
            <View style={styles.loadingCard}>
              <ActivityIndicator color={Colors.accent} />
              <Text style={styles.loadingText}>Fetching backend health...</Text>
            </View>
          ) : error ? (
            <View style={styles.errorCard}>
              <Ionicons name="alert-circle" size={24} color="#FF6B6B" />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : backendHealth ? (
            <View style={styles.infoCard}>
              <InfoRow label="env" value={backendHealth.env} highlight={hasEnvMismatch} />
              <InfoRow label="status" value={backendHealth.status} />
              <InfoRow label="build_version" value={backendHealth.build_version} />
              <InfoRow label="build_label" value={backendHealth.build_label} />
              <InfoRow label="git_sha" value={backendHealth.git_sha} />
              <InfoRow label="db_name" value={backendHealth.db_name} />
              <InfoRow label="db_type" value={backendHealth.db_type} />
              <InfoRow label="api_origin" value={backendHealth.api_origin || 'N/A'} />
              <InfoRow label="timestamp" value={backendHealth.timestamp_utc} />
            </View>
          ) : null}
        </View>

        {/* Verification Checklist */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>✅ Verification Checklist</Text>
          <View style={styles.checklistCard}>
            <ChecklistItem 
              label="Frontend ENV matches Backend" 
              passed={!hasEnvMismatch}
            />
            <ChecklistItem 
              label="Backend is healthy" 
              passed={backendHealth?.status === 'healthy'}
            />
            <ChecklistItem 
              label="API_BASE_URL is reachable" 
              passed={!!backendHealth && !error}
            />
            <ChecklistItem 
              label="Database connected" 
              passed={!!backendHealth?.db_name && backendHealth?.db_name !== 'unknown'}
            />
          </View>
        </View>

        {/* Raw JSON (Debug only) */}
        {DEBUG_MIRROR && backendHealth && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>🔧 Raw Backend Response</Text>
            <View style={styles.jsonCard}>
              <Text style={styles.jsonText}>
                {JSON.stringify(backendHealth, null, 2)}
              </Text>
            </View>
          </View>
        )}

        <View style={styles.bottomSpacer} />
      </ScrollView>
    </SafeAreaView>
  );
}

// Info Row Component
function InfoRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={[styles.infoValue, highlight && styles.infoValueHighlight]} numberOfLines={1}>
        {value}
      </Text>
    </View>
  );
}

// Checklist Item Component
function ChecklistItem({ label, passed }: { label: string; passed: boolean }) {
  return (
    <View style={styles.checklistItem}>
      <Ionicons 
        name={passed ? "checkmark-circle" : "close-circle"} 
        size={18} 
        color={passed ? "#4ADE80" : "#FF6B6B"} 
      />
      <Text style={[styles.checklistText, !passed && styles.checklistTextFailed]}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.border,
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
  },
  refreshButton: {
    padding: 8,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  infoCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.border,
  },
  infoLabel: {
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: Colors.textTertiary,
  },
  infoValue: {
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: Colors.text,
    maxWidth: '60%',
    textAlign: 'right',
  },
  infoValueHighlight: {
    color: '#FF6B6B',
    fontWeight: 'bold',
  },
  warningCard: {
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderWidth: 1,
    borderColor: '#FF6B6B',
  },
  warningText: {
    flex: 1,
    fontSize: 13,
    color: '#FF6B6B',
    lineHeight: 20,
  },
  originWarningCard: {
    backgroundColor: 'rgba(245, 166, 35, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    borderWidth: 1,
    borderColor: '#F5A623',
  },
  originWarningContent: {
    flex: 1,
  },
  originWarningTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F5A623',
    marginBottom: 4,
  },
  originWarningText: {
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: '#B87D00',
    lineHeight: 18,
  },
  loadingCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
  errorCard: {
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    flex: 1,
    fontSize: 13,
    color: '#FF6B6B',
  },
  checklistCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  checklistItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 8,
  },
  checklistText: {
    fontSize: 13,
    color: Colors.text,
  },
  checklistTextFailed: {
    color: '#FF6B6B',
  },
  jsonCard: {
    backgroundColor: '#0a0a14',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#333',
  },
  jsonText: {
    fontSize: 10,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: '#00FF00',
  },
  bottomSpacer: {
    height: 40,
  },
});
