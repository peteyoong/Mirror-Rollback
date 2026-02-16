import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Colors } from '../constants/colors';
import { Spacing } from '../constants/spacing';
import { API_URL_MISSING } from '../services/api';
import { SafeIcon } from './SafeIcon';

interface ApiOfflineBannerProps {
  onRetry?: () => void;
  message?: string;
}

/**
 * ApiOfflineBanner - Non-blocking notification when API is unavailable
 * 
 * Shows a subtle banner but does NOT block UI rendering.
 * Users can still see and interact with static content.
 */
export default function ApiOfflineBanner({ onRetry, message }: ApiOfflineBannerProps) {
  if (!API_URL_MISSING) return null;
  
  return (
    <View style={styles.banner}>
      <SafeIcon name="cloud-offline-outline" size={14} color={Colors.warning} />
      <Text style={styles.text}>
        {message || 'API not configured — some features disabled'}
      </Text>
      {onRetry && (
        <TouchableOpacity onPress={onRetry} style={styles.retryButton}>
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

/**
 * InlineRetry - Retry button for failed fetches
 */
export function InlineRetry({ onRetry, message }: { onRetry: () => void; message?: string }) {
  return (
    <TouchableOpacity style={styles.inlineRetry} onPress={onRetry} activeOpacity={0.7}>
      <SafeIcon name="refresh-outline" size={16} color={Colors.textSecondary} />
      <Text style={styles.inlineRetryText}>{message || 'Tap to retry'}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 179, 71, 0.1)',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    gap: Spacing.xs,
  },
  text: {
    flex: 1,
    fontSize: 11,
    color: Colors.warning,
  },
  retryButton: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xxs,
  },
  retryText: {
    fontSize: 11,
    color: Colors.warning,
    fontWeight: '500',
  },
  inlineRetry: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.lg,
    gap: Spacing.xs,
  },
  inlineRetryText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
});
