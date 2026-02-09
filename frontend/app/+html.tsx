import { ScrollViewStyleReset } from 'expo-router/html';
import type { PropsWithChildren } from 'react';

/**
 * Custom HTML document for web builds
 * Implements web layout hardening for mobile Safari compatibility
 */
export default function Root({ children }: PropsWithChildren) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        {/* 
          Viewport meta with viewport-fit=cover for iPhone safe areas
          This is critical for full-screen mobile Safari support
        */}
        <meta 
          name="viewport" 
          content="width=device-width, initial-scale=1, shrink-to-fit=no, viewport-fit=cover, user-scalable=no, maximum-scale=1" 
        />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        
        {/* PWA / Mobile App meta tags */}
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="theme-color" content="#FAF9F7" />
        
        {/* Prevent phone number detection on iOS */}
        <meta name="format-detection" content="telephone=no" />
        
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
