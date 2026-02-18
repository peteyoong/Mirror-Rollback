/**
 * API Origin Safety Check
 * =======================
 * 
 * Prevents STAGING frontend from connecting to wrong backends.
 * Shows a full-screen error if API origin doesn't match expected staging URL.
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { Colors } from '../constants/colors';

// Environment variables
const APP_ENV = process.env.EXPO_PUBLIC_ENV || 'unknown';
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || '';

// Known staging URLs - add more as needed
const VALID_STAGING_ORIGINS = [
  'cachebuster-2.preview.emergentagent.com',
  'localhost',
  '127.0.0.1',
];

// Known PROD URLs that should NEVER be used in staging
const BLOCKED_ORIGINS = [
  'mirror-live.preview.emergentagent.com',
  'mirror-lens-fixes.emergent.host',
  'mirror-prod',
];

interface ApiOriginSafetyCheckProps {
  children: React.ReactNode;
}

export const ApiOriginSafetyCheck: React.FC<ApiOriginSafetyCheckProps> = ({ children }) => {
  const [isSafe, setIsSafe] = useState(true);
  const [errorDetails, setErrorDetails] = useState<{
    windowOrigin: string;
    apiBaseUrl: string;
    reason: string;
  } | null>(null);

  useEffect(() => {
    // Only check in staging environment
    if (APP_ENV !== 'staging') {
      setIsSafe(true);
      return;
    }

    // Check if API_BASE_URL contains any blocked origins
    const apiUrlLower = API_BASE_URL.toLowerCase();
    
    for (const blocked of BLOCKED_ORIGINS) {
      if (apiUrlLower.includes(blocked.toLowerCase())) {
        setIsSafe(false);
        setErrorDetails({
          windowOrigin: Platform.OS === 'web' && typeof window !== 'undefined' 
            ? window.location?.origin || 'unknown' 
            : 'N/A (native)',
          apiBaseUrl: API_BASE_URL,
          reason: `API URL contains blocked origin: ${blocked}`,
        });
        return;
      }
    }

    // Check if API_BASE_URL is a valid staging URL
    let isValidStaging = false;
    for (const valid of VALID_STAGING_ORIGINS) {
      if (apiUrlLower.includes(valid.toLowerCase())) {
        isValidStaging = true;
        break;
      }
    }

    if (!isValidStaging && API_BASE_URL.length > 0) {
      // Not a known staging URL - might be misconfigured
      console.warn('[ApiOriginSafetyCheck] Unknown API origin:', API_BASE_URL);
      // Don't block, just warn - user might have a valid custom setup
    }

    setIsSafe(true);
  }, []);

  const handleReload = () => {
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      window.location.reload();
    }
  };

  if (!isSafe && errorDetails) {
    return (
      <View style={styles.container}>
        <View style={styles.errorCard}>
          <Text style={styles.errorIcon}>⚠️</Text>
          <Text style={styles.errorTitle}>Configuration Error</Text>
          <Text style={styles.errorSubtitle}>STAGING environment is pointing to wrong backend</Text>
          
          <View style={styles.detailsContainer}>
            <Text style={styles.detailLabel}>Window Origin:</Text>
            <Text style={styles.detailValue}>{errorDetails.windowOrigin}</Text>
            
            <Text style={styles.detailLabel}>API Base URL:</Text>
            <Text style={styles.detailValue}>{errorDetails.apiBaseUrl}</Text>
            
            <Text style={styles.detailLabel}>Reason:</Text>
            <Text style={styles.detailValueError}>{errorDetails.reason}</Text>
          </View>

          <Text style={styles.instructions}>
            This staging build is configured to call a production or incorrect backend.
            Please update EXPO_PUBLIC_API_BASE_URL in .env and rebuild.
          </Text>

          <TouchableOpacity style={styles.reloadButton} onPress={handleReload}>
            <Text style={styles.reloadButtonText}>Reload Page</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return <>{children}</>;
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  errorCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    maxWidth: 400,
    width: '100%',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#FF6B6B',
  },
  errorIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  errorTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#FF6B6B',
    marginBottom: 8,
    textAlign: 'center',
  },
  errorSubtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: 20,
    textAlign: 'center',
  },
  detailsContainer: {
    width: '100%',
    backgroundColor: Colors.background,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  detailLabel: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginBottom: 2,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  detailValue: {
    fontSize: 13,
    color: Colors.text,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 12,
  },
  detailValueError: {
    fontSize: 13,
    color: '#FF6B6B',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  instructions: {
    fontSize: 13,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 20,
  },
  reloadButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 12,
    paddingHorizontal: 32,
    borderRadius: 8,
  },
  reloadButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default ApiOriginSafetyCheck;
