import { ScrollViewStyleReset } from 'expo-router/html';
import type { PropsWithChildren } from 'react';

// BUILD_ID from environment variable - updated automatically on deploy
const BUILD_ID = process.env.EXPO_PUBLIC_BUILD_ID || 'dev';
const BUILD_VERSION = process.env.EXPO_PUBLIC_BUILD_VERSION || 'dev';

// Generate a cache-bust suffix for asset URLs
const CACHE_BUST = `?v=${BUILD_ID.replace(/[^a-zA-Z0-9]/g, '')}`;
const TIMESTAMP = Date.now();

/**
 * Custom HTML document for web builds
 * Implements iOS PWA standalone support and web layout hardening
 */
export default function Root({ children }: PropsWithChildren) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        
        {/* BUILD marker in page title - Default title for PWA */}
        <title>Project Mirror</title>
        
        {/* ============================================
            AGGRESSIVE CACHE CONTROL - CRITICAL FOR REDEPLOYS
            ============================================ */}
        <meta httpEquiv="Cache-Control" content="no-store, no-cache, must-revalidate, max-age=0, s-maxage=0, proxy-revalidate" />
        <meta httpEquiv="Pragma" content="no-cache" />
        <meta httpEquiv="Expires" content="-1" />
        <meta httpEquiv="Surrogate-Control" content="no-store" />
        
        {/* BUILD_ID in meta tag for verification */}
        <meta name="build-id" content={BUILD_ID} />
        <meta name="build-version" content={BUILD_VERSION} />
        <meta name="build-timestamp" content={String(TIMESTAMP)} />
        
        {/* ============================================
            IMMEDIATE CACHE VALIDATION SCRIPT
            Runs FIRST before any other scripts
            ============================================ */}
        <script dangerouslySetInnerHTML={{ __html: `
(function() {
  var BUILD_ID = "${BUILD_ID}";
  var BUILD_VERSION = "${BUILD_VERSION}";
  var STORAGE_KEY = "mirror_build_v3";
  var FORCE_REFRESH_KEY = "mirror_force_refresh";
  
  console.log("%c[CACHE-BUST] BUILD " + BUILD_VERSION + " | " + BUILD_ID, "background: #4ade80; color: black; padding: 4px 8px; font-weight: bold;");
  
  try {
    var cached = localStorage.getItem(STORAGE_KEY);
    var forceRefresh = sessionStorage.getItem(FORCE_REFRESH_KEY);
    var urlParams = new URLSearchParams(location.search);
    var urlBuild = urlParams.get("b");
    
    console.log("[CACHE-BUST] stored=" + (cached || "none") + " url=" + (urlBuild || "none") + " expected=" + BUILD_ID);
    
    // Clear force refresh flag if present
    if (forceRefresh) {
      sessionStorage.removeItem(FORCE_REFRESH_KEY);
      console.log("[CACHE-BUST] Force refresh completed");
    }
    
    // Check for build mismatch
    var buildMismatch = cached && cached !== BUILD_ID;
    var urlMismatch = urlBuild && urlBuild !== BUILD_ID;
    var needsRefresh = buildMismatch || urlMismatch;
    
    if (needsRefresh && !forceRefresh) {
      console.log("[CACHE-BUST] BUILD MISMATCH - Clearing ALL caches...");
      
      // Set force refresh flag to prevent infinite loop
      sessionStorage.setItem(FORCE_REFRESH_KEY, "1");
      
      // Clear localStorage build marker
      localStorage.setItem(STORAGE_KEY, BUILD_ID);
      
      // Unregister ALL service workers
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(function(regs) {
          console.log("[CACHE-BUST] Unregistering " + regs.length + " service workers");
          regs.forEach(function(r) { r.unregister(); });
        }).catch(function(e) {});
      }
      
      // Clear ALL Cache Storage
      if (window.caches && caches.keys) {
        caches.keys().then(function(names) {
          console.log("[CACHE-BUST] Deleting " + names.length + " caches");
          names.forEach(function(n) { caches.delete(n); });
        }).catch(function(e) {});
      }
      
      // Force hard reload with new build param
      var newUrl = location.pathname + "?b=" + BUILD_ID + "&t=" + Date.now() + location.hash;
      console.log("[CACHE-BUST] Redirecting to: " + newUrl);
      setTimeout(function() { location.replace(newUrl); }, 150);
      return;
    }
    
    // Store current build ID
    localStorage.setItem(STORAGE_KEY, BUILD_ID);
    
    // Ensure URL has correct build param
    if (!urlBuild || urlBuild !== BUILD_ID) {
      var newParams = new URLSearchParams(location.search);
      newParams.set("b", BUILD_ID);
      var newUrl = location.pathname + "?" + newParams.toString() + location.hash;
      history.replaceState(null, "", newUrl);
      console.log("[CACHE-BUST] Updated URL build param");
    }
    
    console.log("[CACHE-BUST] ✓ Build verified: " + BUILD_VERSION);
    
  } catch(e) {
    console.log("[CACHE-BUST] Error:", e);
  }
})();
        `}} />
        
        {/* ============================================
            VIEWPORT - Critical for iOS PWA
            ============================================ */}
        <meta 
          name="viewport" 
          content="width=device-width, initial-scale=1, viewport-fit=cover" 
        />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        
        {/* ============================================
            iOS PWA STANDALONE SUPPORT
            ============================================ */}
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Project Mirror" />
        <meta name="mobile-web-app-capable" content="yes" />
        
        {/* Theme color for browser chrome - matches app dark theme */}
        <meta name="theme-color" content="#111214" />
        
        {/* Prevent phone number detection on iOS */}
        <meta name="format-detection" content="telephone=no" />
        
        {/* ============================================
            PWA MANIFEST
            ============================================ */}
        <link rel="manifest" href="/manifest.webmanifest" />
        
        {/* ============================================
            APPLE TOUCH ICONS
            ============================================ */}
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon-180x180.png" />
        <link rel="apple-touch-icon" sizes="152x152" href="/apple-touch-icon-152x152.png" />
        <link rel="apple-touch-icon" sizes="120x120" href="/apple-touch-icon-120x120.png" />
        
        {/* iOS Splash Screens */}
        <link 
          rel="apple-touch-startup-image" 
          href="/splash-1170x2532.png"
          media="(device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3)"
        />
        <link 
          rel="apple-touch-startup-image" 
          href="/splash-1125x2436.png"
          media="(device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3)"
        />
        <link 
          rel="apple-touch-startup-image" 
          href="/splash-1242x2688.png"
          media="(device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 3)"
        />
        
        {/* 
          Critical inline CSS for web layout hardening
          Applied before any React rendering to prevent FOUC
        */}
        <style dangerouslySetInnerHTML={{ __html: `
          /* ============================================
             ROOT CONTAINER SIZING - FULL SCREEN
             ============================================ */
          html {
            height: 100%;
            width: 100%;
            margin: 0;
            padding: 0;
          }
          
          body {
            height: 100%;
            width: 100%;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
            overflow-y: auto;
            overscroll-behavior: none;
            -webkit-overflow-scrolling: touch;
            /* Use dvh for dynamic viewport on mobile */
            min-height: 100vh;
            min-height: 100dvh;
          }
          
          #root {
            min-height: 100%;
            min-height: 100vh;
            min-height: 100dvh;
            width: 100%;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
            /* Safe area padding for notch/home indicator */
            padding-top: env(safe-area-inset-top, 0px);
            padding-bottom: env(safe-area-inset-bottom, 0px);
            padding-left: env(safe-area-inset-left, 0px);
            padding-right: env(safe-area-inset-right, 0px);
          }
          
          /* Ensure React Native Web containers fill height */
          #root > div,
          #root > div > div {
            display: flex;
            flex-direction: column;
            flex: 1;
            min-height: 0;
            width: 100%;
          }
          
          /* ============================================
             PREVENT 100vw OVERFLOW TRAP
             ============================================ */
          * {
            box-sizing: border-box;
          }
          
          body > * {
            max-width: 100%;
          }
          
          /* ============================================
             MOBILE-FIRST LAYOUT
             ============================================ */
          @media screen and (max-width: 768px) {
            #root > div,
            #root > div > div,
            #root > div > div > div {
              max-width: none !important;
              width: 100% !important;
            }
          }
          
          /* ============================================
             TOUCH IMPROVEMENTS
             ============================================ */
          button, a, [role="button"] {
            -webkit-tap-highlight-color: transparent;
            touch-action: manipulation;
          }
          
          /* Hide scrollbars on mobile but keep functionality */
          body::-webkit-scrollbar,
          #root::-webkit-scrollbar {
            width: 0;
            height: 0;
            display: none;
          }
          
          /* ============================================
             DEBUG VIEWPORT OVERLAY (DEBUG_MIRROR only)
             ============================================ */
          .debug-viewport-overlay {
            position: fixed;
            bottom: 70px;
            left: 8px;
            background: rgba(0, 0, 0, 0.9);
            color: #00ff00;
            font-family: monospace;
            font-size: 10px;
            padding: 8px 10px;
            border-radius: 6px;
            z-index: 99999;
            max-width: 180px;
            pointer-events: none;
            line-height: 1.4;
          }
          
          .debug-viewport-overlay.has-overflow {
            border: 2px solid #ff0000;
            color: #ff6666;
          }
        `}} />
        
        {/* Expo's default scroll view style reset */}
        <ScrollViewStyleReset />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
