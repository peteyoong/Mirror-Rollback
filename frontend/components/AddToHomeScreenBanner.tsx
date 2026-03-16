import React, { useEffect, useState, createContext, useContext, useCallback } from 'react';
import { Platform, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../constants/colors';

const BANNER_DISMISSED_KEY = 'pwa_banner_dismissed';

// Banner height constant for consistent spacing
export const PWA_BANNER_HEIGHT = 70;

// ============================================================================
// BANNER CONTEXT - Allows screens to know if banner is visible
// ============================================================================

interface BannerContextType {
  isBannerVisible: boolean;
  bannerHeight: number;
  dismissBanner: () => void;
}

const BannerContext = createContext<BannerContextType>({
  isBannerVisible: false,
  bannerHeight: 0,
  dismissBanner: () => {},
});

/**
 * Hook to get banner visibility and safe bottom padding
 * Use this in scroll views to add proper bottom spacing
 */
export function useBannerSafeArea(): { bottomPadding: number; isBannerVisible: boolean } {
  const { isBannerVisible, bannerHeight } = useContext(BannerContext);
  return {
    bottomPadding: isBannerVisible ? bannerHeight : 0,
    isBannerVisible,
  };
}

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
 * Banner Provider - Wrap your app with this to enable banner-aware layouts
 */
export function BannerProvider({ children }: { children: React.ReactNode }) {
  const [isBannerVisible, setIsBannerVisible] = useState(false);
  const [bannerHeight, setBannerHeight] = useState(0);
  const isMobileBrowser = useIsMobileBrowser();
  const isStandalone = useIsStandalone();
  
  useEffect(() => {
    if (Platform.OS !== 'web') {
      setIsBannerVisible(false);
      setBannerHeight(0);
      return;
    }
    
    // Check if banner was dismissed
    AsyncStorage.getItem(BANNER_DISMISSED_KEY).then((dismissed) => {
      const shouldShow = dismissed !== 'true' && isMobileBrowser && !isStandalone;
      setIsBannerVisible(shouldShow);
      setBannerHeight(shouldShow ? PWA_BANNER_HEIGHT : 0);
    });
  }, [isMobileBrowser, isStandalone]);
  
  const dismissBanner = useCallback(async () => {
    setIsBannerVisible(false);
    setBannerHeight(0);
    await AsyncStorage.setItem(BANNER_DISMISSED_KEY, 'true');
  }, []);
  
  return (
    <BannerContext.Provider value={{ isBannerVisible, bannerHeight, dismissBanner }}>
      {children}
    </BannerContext.Provider>
  );
}

/**
 * iOS Add to Home Screen Banner
 * Shows on mobile browsers when not installed as PWA
 */
export function AddToHomeScreenBanner() {
  const { isBannerVisible, dismissBanner } = useContext(BannerContext);
  const isStandalone = useIsStandalone();
  
  // Don't render on native or if already standalone or if dismissed
  if (Platform.OS !== 'web' || !isBannerVisible || isStandalone) {
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
        <TouchableOpacity onPress={dismissBanner} style={styles.closeButton} accessibilityLabel="Dismiss banner">
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
