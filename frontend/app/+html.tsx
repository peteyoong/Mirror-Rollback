import { ScrollViewStyleReset } from 'expo-router/html';
import type { PropsWithChildren } from 'react';

// BUILD_ID must be updated on every deploy for cache verification
const BUILD_ID = '2026-02-11T07:35:00Z';
const BUILD_VERSION = 'v8-fresh';

/**
 * Custom HTML document for web builds
 * Implements iOS PWA standalone support and web layout hardening
 */
export default function Root({ children }: PropsWithChildren) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        
        {/* ============================================
            CACHE CONTROL - CRITICAL FOR REDEPLOYS
            ============================================ */}
        <meta httpEquiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
        <meta httpEquiv="Pragma" content="no-cache" />
        <meta httpEquiv="Expires" content="0" />
        
        {/* BUILD_ID in meta tag for verification */}
        <meta name="build-id" content={BUILD_ID} />
        <meta name="build-version" content={BUILD_VERSION} />
        
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
