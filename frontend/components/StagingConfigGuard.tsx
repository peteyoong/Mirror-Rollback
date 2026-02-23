/**
 * Staging Configuration Guard
 * ===========================
 * 
 * Hard guardrails for staging deployments to prevent misconfiguration.
 * 
 * Checks:
 * 1. API_BASE_URL must be set and start with "https://"
 * 2. Warns if not using the staging always-on host
 * 
 * Only active in staging environment (EXPO_PUBLIC_ENV === 'staging')
 */

import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { API_BASE_URL, IS_API_CONFIGURED } from '../utils/apiBase';

// Environment check
const APP_ENV = process.env.EXPO_PUBLIC_ENV || 'unknown';
const IS_STAGING = APP_ENV === 'staging';
const BUILD_VERSION = process.env.EXPO_PUBLIC_BUILD_VERSION || 'unknown';
const BUILD_ID = process.env.EXPO_PUBLIC_BUILD_ID || 'unknown';

// Expected staging host
const STAGING_HOST = 'mirror-lens-fixes.emergent.host';

interface ConfigCheckResult {
  isValid: boolean;
  isFatal: boolean;
  error: string | null;
  warning: string | null;
}

/**
 * Check staging configuration
 */
function checkStagingConfig(): ConfigCheckResult {
  // Only check in staging
  if (!IS_STAGING) {
    return { isValid: true, isFatal: false, error: null, warning: null };
  }

  // Check if API_BASE_URL is configured
  if (!IS_API_CONFIGURED || !API_BASE_URL) {
    return {
      isValid: false,
      isFatal: true,
      error: `STAGING MISCONFIG: API base URL is missing or empty.\nEXPO_PUBLIC_API_BASE_URL must be set.`,
      warning: null,
    };
  }

  // Check if it starts with https://
  if (!API_BASE_URL.startsWith('https://')) {
    return {
      isValid: false,
      isFatal: true,
      error: `STAGING MISCONFIG: Invalid API base URL.\nMust start with "https://"\nCurrent: "${API_BASE_URL}"`,
      warning: null,
    };
  }

  // Check if using staging always-on host
  if (!API_BASE_URL.includes(STAGING_HOST)) {
    return {
      isValid: true,
      isFatal: false,
      error: null,
      warning: `WARNING: Not using staging always-on API.\nExpected: ${STAGING_HOST}\nCurrent: ${API_BASE_URL}`,
    };
  }

  return { isValid: true, isFatal: false, error: null, warning: null };
}

interface StagingConfigGuardProps {
  children: React.ReactNode;
}

/**
 * Wrapper component that checks staging configuration before rendering children.
 * Shows full-screen error if configuration is invalid.
 */
export function StagingConfigGuard({ children }: StagingConfigGuardProps) {
  // Only check in staging
  if (!IS_STAGING) {
    return <>{children}</>;
  }

  const configCheck = checkStagingConfig();

  // Fatal error - show full screen error
  if (configCheck.isFatal && configCheck.error) {
    return (
      <SafeAreaView style={styles.errorContainer}>
        <View style={styles.errorBox}>
          <Text style={styles.errorTitle}>⚠️ CONFIGURATION ERROR</Text>
          <Text style={styles.errorMessage}>{configCheck.error}</Text>
          <View style={styles.buildInfo}>
            <Text style={styles.buildText}>ENV: {APP_ENV}</Text>
            <Text style={styles.buildText}>BUILD: {BUILD_VERSION}</Text>
            <Text style={styles.buildText}>ID: {BUILD_ID}</Text>
            <Text style={styles.buildText}>API: {API_BASE_URL || '(not set)'}</Text>
          </View>
          <Text style={styles.helpText}>
            Check .env file and redeploy.
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  // Warning - log to console but don't block UI
  if (configCheck.warning) {
    // Log warning to console for debugging but don't show UI warning banner
    // This keeps the UX clean for external testers
    console.warn('[StagingConfigGuard]', configCheck.warning);
  }

  return <>{children}</>;
}

const styles = StyleSheet.create({
  errorContainer: {
    flex: 1,
    backgroundColor: '#1a0000',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorBox: {
    backgroundColor: 'rgba(255, 0, 0, 0.1)',
    borderWidth: 2,
    borderColor: '#ff0000',
    borderRadius: 12,
    padding: 24,
    maxWidth: 400,
    width: '100%',
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ff4444',
    textAlign: 'center',
    marginBottom: 16,
  },
  errorMessage: {
    fontSize: 14,
    color: '#ff8888',
    textAlign: 'center',
    marginBottom: 20,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    lineHeight: 22,
  },
  buildInfo: {
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  buildText: {
    fontSize: 11,
    color: '#ffaaaa',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 4,
  },
  helpText: {
    fontSize: 12,
    color: '#ff6666',
    textAlign: 'center',
    fontStyle: 'italic',
  },
});

export default StagingConfigGuard;
