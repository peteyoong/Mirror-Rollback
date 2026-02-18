/**
 * Web Build Version Checker
 * =========================
 * 
 * Automatically refreshes the page when a new build is deployed.
 * Only runs on web platform.
 * 
 * How it works:
 * 1. On mount, fetches current build version from /api/build-version
 * 2. Compares with stored version in localStorage
 * 3. If mismatch detected, clears caches and reloads once
 * 4. Stores new version to prevent reload loops
 */

import { useEffect } from 'react';
import { Platform } from 'react-native';

const STORAGE_KEY = 'mirror_web_build_id';
const RELOAD_FLAG_KEY = 'mirror_web_just_reloaded';

// Current build ID baked into the bundle
const BUNDLE_BUILD_ID = process.env.EXPO_PUBLIC_BUILD_ID || 'unknown';

export const useWebBuildVersionCheck = () => {
  useEffect(() => {
    // Only run on web
    if (Platform.OS !== 'web' || typeof window === 'undefined') {
      return;
    }

    const checkBuildVersion = async () => {
      try {
        // Check if we just reloaded to prevent loops
        const justReloaded = sessionStorage.getItem(RELOAD_FLAG_KEY);
        if (justReloaded === 'true') {
          // Clear the flag and update stored version
          sessionStorage.removeItem(RELOAD_FLAG_KEY);
          localStorage.setItem(STORAGE_KEY, BUNDLE_BUILD_ID);
          console.log('[BuildCheck] Just reloaded, storing new build:', BUNDLE_BUILD_ID);
          return;
        }

        // Get stored build ID
        const storedBuildId = localStorage.getItem(STORAGE_KEY);
        
        // First visit - store current build
        if (!storedBuildId) {
          localStorage.setItem(STORAGE_KEY, BUNDLE_BUILD_ID);
          console.log('[BuildCheck] First visit, storing build:', BUNDLE_BUILD_ID);
          return;
        }

        // Compare with bundle build ID
        if (storedBuildId !== BUNDLE_BUILD_ID) {
          console.log('[BuildCheck] Build mismatch detected!');
          console.log('[BuildCheck] Stored:', storedBuildId);
          console.log('[BuildCheck] Current:', BUNDLE_BUILD_ID);
          
          // Set reload flag to prevent loops
          sessionStorage.setItem(RELOAD_FLAG_KEY, 'true');
          
          // Clear caches if available
          if ('caches' in window) {
            try {
              const cacheNames = await caches.keys();
              await Promise.all(cacheNames.map(name => caches.delete(name)));
              console.log('[BuildCheck] Cleared browser caches');
            } catch (e) {
              console.warn('[BuildCheck] Failed to clear caches:', e);
            }
          }
          
          // Force reload
          console.log('[BuildCheck] Reloading page...');
          window.location.reload();
          return;
        }

        console.log('[BuildCheck] Build version matches:', BUNDLE_BUILD_ID);
      } catch (error) {
        console.warn('[BuildCheck] Error checking build version:', error);
      }
    };

    // Run check after a short delay to let the app initialize
    const timeoutId = setTimeout(checkBuildVersion, 1000);
    
    return () => clearTimeout(timeoutId);
  }, []);
};

export default useWebBuildVersionCheck;
