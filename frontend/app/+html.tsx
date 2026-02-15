import { ScrollViewStyleReset } from 'expo-router/html';
import type { PropsWithChildren } from 'react';

// BUILD_ID must be updated on every deploy for cache verification
// MUST MATCH /app/frontend/utils/buildInfo.ts
const BUILD_ID = '2026-02-15T14:50:00Z';
const BUILD_VERSION = 'v24-unified-backend-url';

// Generate a cache-bust suffix for asset URLs
const CACHE_BUST = `?v=${BUILD_ID.replace(/[^a-zA-Z0-9]/g, '')}`;

/**
 * Custom HTML document for web builds
 * Implements iOS PWA standalone support and web layout hardening
 */
export default function Root({ children }: PropsWithChildren) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        
        {/* BUILD marker in page title */}
        <title>{`Mirror • BUILD ${BUILD_ID}`}</title>
        
        {/* ============================================
            CACHE CONTROL - CRITICAL FOR REDEPLOYS
            ============================================ */}
        <meta httpEquiv="Cache-Control" content="no-store, no-cache, must-revalidate, max-age=0" />
        <meta httpEquiv="Pragma" content="no-cache" />
        <meta httpEquiv="Expires" content="0" />
        
        {/* BUILD_ID in meta tag for verification */}
        <meta name="build-id" content={BUILD_ID} />
        <meta name="build-version" content={BUILD_VERSION} />
        
        {/* ============================================
            QUERY-BASED BUILD NAMESPACE
            Forces URL to include build-specific query param
            This prevents stale HTML from "winning" because each build's
            URL is unique and won't match old cached responses
            ============================================ */}
        <script dangerouslySetInnerHTML={{ __html: `
(function() {
  try {
    var BUILD_ID = "${BUILD_ID}";
    var BUILD_KEY = "b";
    var params = new URLSearchParams(location.search);
    var urlBuild = params.get(BUILD_KEY);
    
    console.log("[BUILD-NS] Current URL build:", urlBuild || "none");
    console.log("[BUILD-NS] Expected build:", BUILD_ID);
    
    // If URL doesn't have the correct build param, redirect
    if (urlBuild !== BUILD_ID) {
      // Set or update the build param
      params.set(BUILD_KEY, BUILD_ID);
      var newUrl = location.pathname + "?" + params.toString() + location.hash;
      console.log("[BUILD-NS] Redirecting to:", newUrl);
      location.replace(newUrl);
      return; // Stop execution
    }
    
    console.log("[BUILD-NS] URL has correct build namespace");
  } catch(e) { console.log("[BUILD-NS] Error:", e); }
})();
        `}} />
        
        {/* ============================================
            PRE-REACT BUILD WATERMARK
            Visible immediately on page load, before React mounts
            ============================================ */}
        <script dangerouslySetInnerHTML={{ __html: `
(function() {
  try {
    var BUILD_ID = "${BUILD_ID}";
    var BUILD_VERSION = "${BUILD_VERSION}";
    
    // Create watermark element
    var watermark = document.createElement('div');
    watermark.id = 'build-watermark';
    watermark.textContent = 'BUILD ' + BUILD_ID + ' • ' + BUILD_VERSION;
    watermark.style.cssText = [
      'position: fixed',
      'top: calc(env(safe-area-inset-top, 0px) + 8px)',
      'left: 8px',
      'z-index: 2147483647',
      'background: rgba(0, 0, 0, 0.7)',
      'color: #fff',
      'padding: 6px 10px',
      'border-radius: 10px',
      'font-size: 10px',
      'font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
      'font-weight: 500',
      'letter-spacing: 0.3px',
      'pointer-events: none',
      'box-shadow: 0 2px 8px rgba(0,0,0,0.3)',
      'white-space: nowrap'
    ].join(';');
    
    // Add to DOM as soon as body exists
    function addWatermark() {
      if (document.body) {
        document.body.appendChild(watermark);
        console.log('[WATERMARK] Added: BUILD ' + BUILD_ID + ' • ' + BUILD_VERSION);
      } else {
        // Body not ready, try again
        setTimeout(addWatermark, 10);
      }
    }
    
    // Start trying to add watermark
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', addWatermark);
    } else {
      addWatermark();
    }
    
  } catch(e) { console.log('[WATERMARK] Error:', e); }
})();
        `}} />
        
        {/* ============================================
            HARD CACHE BUSTER - Service Worker unregister + Cache clear + Force reload
            This runs BEFORE React loads
            ============================================ */}
        <script dangerouslySetInnerHTML={{ __html: `
(function () {
  try {
    var BUILD_ID = "${BUILD_ID}";
    var STORAGE_KEY = "mirror_build_id";
    var cached = null;
    
    try { cached = localStorage.getItem(STORAGE_KEY); } catch(e) {}
    
    console.log("[BUILD] expected=" + BUILD_ID + " current=" + (cached || "none"));
    
    // Detect emergent hosts
    var host = location.hostname || "";
    var isEmergent = host.includes("emergent.host") || host.includes("emergentagent") || host.includes("preview.");
    var isFirstVisit = !cached;
    var buildMismatch = cached && cached !== BUILD_ID;
    var alreadyRefreshed = location.search.includes("refreshed=1");
    
    // Force refresh if: build mismatch OR (first visit on emergent AND not already refreshed)
    if ((buildMismatch || (isFirstVisit && isEmergent)) && !alreadyRefreshed) {
      console.log("[BUILD] Clearing caches and service workers...");
      
      // Unregister ALL service workers
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations()
          .then(function(regs) { 
            console.log("[BUILD] Unregistering " + regs.length + " service workers");
            return Promise.all(regs.map(function(r) { return r.unregister(); })); 
          })
          .catch(function(e) { console.log("[BUILD] SW error:", e); });
      }
      
      // Clear ALL caches
      if (window.caches && caches.keys) {
        caches.keys()
          .then(function(names) { 
            console.log("[BUILD] Deleting " + names.length + " caches");
            return Promise.all(names.map(function(n) { return caches.delete(n); })); 
          })
          .catch(function(e) { console.log("[BUILD] Cache error:", e); });
      }
      
      // Store new build ID
      try { localStorage.setItem(STORAGE_KEY, BUILD_ID); } catch(e) {}
      
      // Reload with cache-buster
      var newUrl = location.pathname + "?refreshed=1&b=" + BUILD_ID + "&t=" + Date.now();
      console.log("[BUILD] Redirecting to:", newUrl);
      setTimeout(function() { location.replace(newUrl); }, 100);
    } else {
      // Store build ID for next time
      try { localStorage.setItem(STORAGE_KEY, BUILD_ID); } catch(e) {}
      console.log("[BUILD] OK - " + BUILD_ID);
    }
  } catch (e) { console.log("[BUILD] Error:", e); }
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
        
        {/* Theme color for browser chrome */}
        <meta name="theme-color" content="#FAF9F7" />
        
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
