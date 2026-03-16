/**
 * Lifeline Upload Screen (Task 44)
 * 
 * The entry point for importing a Lifeline from a file.
 * Provides a clear upload step before the review screen.
 * 
 * Flow: Lifeline Intro → Upload Screen → Review Screen
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import { useTheme } from '../contexts/ThemeContext';
import { useAppStore } from '../store';
import api from '../services/api';

// =============================================================================
// CONSTANTS
// =============================================================================

// Supported file types for display
const SUPPORTED_FORMATS = [
  { ext: '.pptx', label: 'PowerPoint', icon: '📊' },
  { ext: '.xlsx', label: 'Excel', icon: '📈' },
  { ext: '.csv', label: 'CSV', icon: '📋' },
  { ext: '.pdf', label: 'PDF', icon: '📄' },
  { ext: '.jpg/.png', label: 'Images', icon: '🖼️' },
];

// Document picker MIME types
const MIME_TYPES = [
  'application/vnd.openxmlformats-officedocument.presentationml.presentation', // .pptx
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
  'application/vnd.ms-excel', // .xls
  'text/csv', // .csv
  'application/pdf', // .pdf
  'image/jpeg', // .jpg
  'image/png', // .png
];

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function LifelineUploadScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const { user } = useAppStore();
  
  // State
  const [selectedFile, setSelectedFile] = useState<{
    name: string;
    uri: string;
    size: number;
  } | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Debug logging helper
  const debugLog = (message: string, data?: any) => {
    console.log(`[LifelineUpload] ${message}`, data || '');
  };
  
  // Handle file selection
  const handleChooseFile = async () => {
    debugLog('Opening file picker...');
    setError(null);
    
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: MIME_TYPES,
        copyToCacheDirectory: true,
      });
      
      debugLog('File picker result:', result);
      
      if (result.canceled) {
        debugLog('File selection cancelled');
        return;
      }
      
      // DocumentPicker returns assets array
      const file = result.assets?.[0];
      
      if (!file) {
        debugLog('No file in result');
        setError('No file selected. Please try again.');
        return;
      }
      
      debugLog('Selected file:', { name: file.name, size: file.size, uri: file.uri });
      
      // Validate file extension
      const ext = file.name.toLowerCase().split('.').pop();
      const validExtensions = ['pptx', 'xlsx', 'xls', 'csv', 'pdf', 'jpg', 'jpeg', 'png'];
      
      if (!ext || !validExtensions.includes(ext)) {
        setError(`Unsupported file format (.${ext}). Please use PowerPoint, Excel, CSV, PDF, or images.`);
        return;
      }
      
      // Validate file size (10MB max)
      if (file.size && file.size > 10 * 1024 * 1024) {
        setError('File too large. Maximum size is 10MB.');
        return;
      }
      
      setSelectedFile({
        name: file.name,
        uri: file.uri,
        size: file.size || 0,
      });
      
    } catch (err: any) {
      debugLog('File picker error:', err);
      setError('Failed to open file picker. Please try again.');
    }
  };
  
  // Handle upload and extraction
  const handleUpload = async () => {
    if (!selectedFile || !user?.id) {
      setError('Please select a file first.');
      return;
    }
    
    debugLog('Starting upload...', { filename: selectedFile.name, userId: user.id });
    setIsUploading(true);
    setError(null);
    
    try {
      // Create form data for upload
      const formData = new FormData();
      
      // Handle file for both web and native
      if (Platform.OS === 'web') {
        // For web, fetch the blob from the uri
        const response = await fetch(selectedFile.uri);
        const blob = await response.blob();
        formData.append('file', blob, selectedFile.name);
      } else {
        // For native, use the uri directly
        formData.append('file', {
          uri: selectedFile.uri,
          name: selectedFile.name,
          type: getMimeType(selectedFile.name),
        } as any);
      }
      
      formData.append('user_id', user.id);
      
      debugLog('Uploading to API...');
      
      // Upload to backend
      const response = await api.post('/lifeline/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 60 second timeout for larger files
      });
      
      debugLog('Upload response:', response.data);
      
      if (!response.data.success) {
        setError(response.data.message || 'Failed to extract events from file.');
        setIsUploading(false);
        return;
      }
      
      const events = response.data.events || [];
      const extractedCount = events.length;
      
      debugLog(`Extraction complete: ${extractedCount} events found`);
      
      // Navigate to review screen with extracted data
      router.push({
        pathname: '/lifeline-import-review',
        params: {
          extractedEvents: JSON.stringify(events),
          sourceFilename: selectedFile.name,
          extractedCount: String(extractedCount),
          isRealImport: 'true', // Flag to indicate this is from real upload
        },
      });
      
    } catch (err: any) {
      debugLog('Upload error:', err);
      
      if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else if (err.message?.includes('timeout')) {
        setError('Upload timed out. Please try a smaller file.');
      } else {
        setError('Failed to upload file. Please check your connection and try again.');
      }
    } finally {
      setIsUploading(false);
    }
  };
  
  // Get MIME type from filename
  const getMimeType = (filename: string): string => {
    const ext = filename.toLowerCase().split('.').pop();
    const mimeMap: Record<string, string> = {
      'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'xls': 'application/vnd.ms-excel',
      'csv': 'text/csv',
      'pdf': 'application/pdf',
      'jpg': 'image/jpeg',
      'jpeg': 'image/jpeg',
      'png': 'image/png',
    };
    return mimeMap[ext || ''] || 'application/octet-stream';
  };
  
  // Handle cancel/back
  const handleCancel = () => {
    debugLog('Cancelled, navigating back');
    router.back();
  };
  
  // Format file size for display
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };
  
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={handleCancel}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Ionicons name="chevron-back" size={24} color={theme.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Import your lifeline</Text>
        <View style={styles.headerSpacer} />
      </View>
      
      {/* Main Content */}
      <View style={styles.content}>
        {/* Intro Text */}
        <Text style={[styles.introText, { color: theme.textSecondary }]}>
          Upload a PowerPoint, spreadsheet, PDF, CSV, or image.{'\n'}
          Mirror will extract possible turning points for you to review.
        </Text>
        
        {/* Supported Formats */}
        <View style={[styles.formatsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.formatsTitle, { color: theme.textTertiary }]}>SUPPORTED FORMATS</Text>
          <View style={styles.formatsList}>
            {SUPPORTED_FORMATS.map((format) => (
              <View key={format.ext} style={styles.formatItem}>
                <Text style={styles.formatIcon}>{format.icon}</Text>
                <Text style={[styles.formatLabel, { color: theme.textSecondary }]}>{format.ext}</Text>
              </View>
            ))}
          </View>
        </View>
        
        {/* Selected File Display */}
        {selectedFile && (
          <View style={[styles.selectedFileCard, { backgroundColor: `${theme.accent}10`, borderColor: theme.accent }]}>
            <View style={styles.selectedFileInfo}>
              <Ionicons name="document-text" size={24} color={theme.accent} />
              <View style={styles.selectedFileText}>
                <Text style={[styles.selectedFileName, { color: theme.text }]} numberOfLines={1}>
                  {selectedFile.name}
                </Text>
                <Text style={[styles.selectedFileSize, { color: theme.textSecondary }]}>
                  {formatFileSize(selectedFile.size)}
                </Text>
              </View>
            </View>
            <TouchableOpacity 
              style={styles.changeFileButton}
              onPress={handleChooseFile}
              disabled={isUploading}
            >
              <Text style={[styles.changeFileText, { color: theme.accent }]}>Change</Text>
            </TouchableOpacity>
          </View>
        )}
        
        {/* Error Display */}
        {error && (
          <View style={[styles.errorCard, { backgroundColor: '#E5373710', borderColor: '#E53737' }]}>
            <Ionicons name="alert-circle" size={20} color="#E53737" />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}
      </View>
      
      {/* Actions */}
      <View style={styles.actionsContainer}>
        {/* Primary CTA */}
        {!selectedFile ? (
          <TouchableOpacity
            style={[styles.primaryButton, { backgroundColor: theme.accent }]}
            onPress={handleChooseFile}
            activeOpacity={0.8}
          >
            <Ionicons name="folder-open-outline" size={20} color="#FFFFFF" />
            <Text style={styles.primaryButtonText}>Choose a file</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[
              styles.primaryButton, 
              { backgroundColor: theme.accent },
              isUploading && styles.buttonDisabled
            ]}
            onPress={handleUpload}
            disabled={isUploading}
            activeOpacity={0.8}
          >
            {isUploading ? (
              <>
                <ActivityIndicator size="small" color="#FFFFFF" />
                <Text style={styles.primaryButtonText}>Extracting moments...</Text>
              </>
            ) : (
              <>
                <Ionicons name="cloud-upload-outline" size={20} color="#FFFFFF" />
                <Text style={styles.primaryButtonText}>Upload and Extract</Text>
              </>
            )}
          </TouchableOpacity>
        )}
        
        {/* Cancel Button */}
        <TouchableOpacity
          style={styles.cancelButton}
          onPress={handleCancel}
          disabled={isUploading}
        >
          <Text style={[styles.cancelButtonText, { color: theme.textSecondary }]}>Cancel</Text>
        </TouchableOpacity>
        
        {/* Manual Entry Link */}
        <TouchableOpacity
          style={styles.manualLink}
          onPress={() => router.replace('/(tabs)/life')}
          disabled={isUploading}
        >
          <Text style={[styles.manualLinkText, { color: theme.textTertiary }]}>
            Or add moments manually
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  headerSpacer: {
    width: 32,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 16,
  },
  introText: {
    fontSize: 16,
    lineHeight: 24,
    textAlign: 'center',
    marginBottom: 32,
  },
  formatsCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 24,
  },
  formatsTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
    textAlign: 'center',
    marginBottom: 16,
  },
  formatsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 16,
  },
  formatItem: {
    alignItems: 'center',
    minWidth: 60,
  },
  formatIcon: {
    fontSize: 24,
    marginBottom: 4,
  },
  formatLabel: {
    fontSize: 12,
    fontWeight: '500',
  },
  selectedFileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 16,
  },
  selectedFileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 12,
  },
  selectedFileText: {
    flex: 1,
  },
  selectedFileName: {
    fontSize: 15,
    fontWeight: '500',
    marginBottom: 2,
  },
  selectedFileSize: {
    fontSize: 13,
  },
  changeFileButton: {
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  changeFileText: {
    fontSize: 14,
    fontWeight: '500',
  },
  errorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    marginBottom: 16,
  },
  errorText: {
    flex: 1,
    fontSize: 14,
    color: '#E53737',
    lineHeight: 20,
  },
  actionsContainer: {
    paddingHorizontal: 24,
    paddingBottom: 32,
    gap: 12,
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    paddingVertical: 16,
    borderRadius: 12,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  cancelButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
  },
  manualLink: {
    paddingVertical: 8,
    alignItems: 'center',
  },
  manualLinkText: {
    fontSize: 14,
  },
});
