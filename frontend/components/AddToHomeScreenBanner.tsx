import React, { useEffect, useState } from 'react';
import { Platform, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../constants/colors';

const BANNER_DISMISSED_KEY = 'pwa_banner_dismissed';

/**
 * Check if running in standalone mode (PWA installed)
 */
export function useIsStandalone(): boolean {
  const [isStandalone, setIsStandalone] = useState(false);
  
  useEffect(() => {
    if (Platform.OS !== 'web' || typeof window === 'undefined') {
      setIsStandalone(false);
      return;
    }
    
    // Check for iOS standalone mode
    const isIOSStandalone = (window.navigator as any).standalone === true;
    
    // Check for PWA display-mode: standalone
    const isDisplayStandalone = window.matchMedia('(display-mode: standalone)').matches;
    
    // Check for fullscreen mode
    const isFullscreen = window.matchMedia('(display-mode: fullscreen)').matches;
    
    setIsStandalone(isIOSStandalone || isDisplayStandalone || isFullscreen);
  }, []);
  
  return isStandalone;
}

/**
 * Check if running on mobile browser (iOS or Android)
 */
function useIsMobileBrowser(): boolean {
  const [isMobile, setIsMobile] = useState(false);
  const isStandalone = useIsStandalone();
  
  useEffect(() => {
    if (Platform.OS !== 'web' || typeof window === 'undefined') {
      setIsMobile(false);
      return;
    }
    
    const ua = window.navigator.userAgent;
    const isIOS = /iPad|iPhone|iPod/.test(ua);
    const isAndroid = /Android/.test(ua);
    const isMobileDevice = isIOS || isAndroid || window.innerWidth < 768;
    
    setIsMobile(isMobileDevice && !isStandalone);
  }, [isStandalone]);
  
  return isMobile;
}

/**
 * iOS Add to Home Screen Banner
 * Shows on mobile browsers when not installed as PWA
 */
export function AddToHomeScreenBanner() {
  const [visible, setVisible] = useState(false);
  const [showAlways, setShowAlways] = useState(true); // For debugging - always show initially
  const isMobileBrowser = useIsMobileBrowser();
  const isStandalone = useIsStandalone();
  
  useEffect(() => {
    // Only check visibility on web
    if (Platform.OS !== 'web') {
      setVisible(false);
      return;
    }
    
    // Check if banner was dismissed
    AsyncStorage.getItem(BANNER_DISMISSED_KEY).then((dismissed) => {
      // Show if not dismissed AND on mobile browser AND not standalone
      if (dismissed !== 'true' && isMobileBrowser && !isStandalone) {
        setVisible(true);
      }
    });
  }, [isMobileBrowser, isStandalone]);
  
  const handleDismiss = async () => {
    setVisible(false);
    await AsyncStorage.setItem(BANNER_DISMISSED_KEY, 'true');
  };
  
  // Don't render on native or if already standalone
  if (Platform.OS !== 'web' || !visible || isStandalone) {
    return null;
  }
  
  // Detect iOS for specific instructions
  const isIOS = typeof window !== 'undefined' && /iPad|iPhone|iPod/.test(window.navigator.userAgent);
  
  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Ionicons name="phone-portrait-outline" size={24} color={Colors.text} />
        <View style={styles.textContainer}>
          <Text style={styles.title}>📱 Get full-screen mode!</Text>
          <Text style={styles.subtitle}>
            {isIOS 
              ? 'Tap Share ⬆️ → "Add to Home Screen"'
              : 'Tap Menu ⋮ → "Add to Home Screen"'
            }
          </Text>
        </View>
        <TouchableOpacity onPress={handleDismiss} style={styles.closeButton}>
          <Ionicons name="close" size={24} color={Colors.textTertiary} />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 70, // Position above the tab bar (tab bar height is ~60)
    left: 0,
    right: 0,
    backgroundColor: Colors.surface,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.border,
    zIndex: 999,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    paddingHorizontal: 16,
    gap: 12,
  },
  textContainer: {
    flex: 1,
  },
  title: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 2,
  },
  subtitle: {
    fontSize: 12,
    color: Colors.textSecondary,
  },
  closeButton: {
    padding: 4,
  },
});

export default AddToHomeScreenBanner;
