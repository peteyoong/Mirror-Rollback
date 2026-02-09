import React, { useEffect, useState } from 'react';
import { Platform } from 'react-native';

/**
 * Debug Viewport Overlay Component
 * Shows viewport dimensions and overflow status on web
 * Only renders when DEBUG_MIRROR is enabled
 */

interface ViewportInfo {
  innerWidth: number;
  innerHeight: number;
  rootWidth: number;
  scrollWidth: number;
  hasOverflow: boolean;
  devicePixelRatio: number;
}

const DEBUG_MIRROR = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

export function DebugViewportOverlay() {
  const [viewportInfo, setViewportInfo] = useState<ViewportInfo | null>(null);
  
  useEffect(() => {
    // Only run on web with DEBUG_MIRROR enabled
    if (Platform.OS !== 'web' || !DEBUG_MIRROR) return;
    
    const updateViewportInfo = () => {
      if (typeof window === 'undefined') return;
      
      const rootElement = document.getElementById('root');
      const rootWidth = rootElement?.clientWidth || 0;
      const scrollWidth = document.body.scrollWidth;
      
      setViewportInfo({
        innerWidth: window.innerWidth,
        innerHeight: window.innerHeight,
        rootWidth,
        scrollWidth,
        hasOverflow: scrollWidth > window.innerWidth,
        devicePixelRatio: window.devicePixelRatio || 1,
      });
    };
    
    // Initial update
    updateViewportInfo();
    
    // Update on resize
    window.addEventListener('resize', updateViewportInfo);
    
    // Also update periodically to catch dynamic content changes
    const interval = setInterval(updateViewportInfo, 2000);
    
    return () => {
      window.removeEventListener('resize', updateViewportInfo);
      clearInterval(interval);
    };
  }, []);
  
  // Don't render on native or without debug mode
  if (Platform.OS !== 'web' || !DEBUG_MIRROR || !viewportInfo) {
    return null;
  }
  
  const { innerWidth, innerHeight, rootWidth, scrollWidth, hasOverflow, devicePixelRatio } = viewportInfo;
  
  return (
    <div 
      className={`debug-viewport-overlay ${hasOverflow ? 'has-overflow' : ''}`}
      style={{
        position: 'fixed',
        bottom: 70,
        left: 8,
        background: hasOverflow ? 'rgba(255, 0, 0, 0.9)' : 'rgba(0, 0, 0, 0.9)',
        color: hasOverflow ? '#ffffff' : '#00ff00',
        fontFamily: 'monospace',
        fontSize: 10,
        padding: '8px 10px',
        borderRadius: 6,
        zIndex: 99999,
        maxWidth: 180,
        pointerEvents: 'none',
        lineHeight: 1.4,
      }}
    >
      <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
        🖥️ Viewport Debug
      </div>
      <div>innerW: {innerWidth}px</div>
      <div>innerH: {innerHeight}px</div>
      <div>rootW: {rootWidth}px</div>
      <div>scrollW: {scrollWidth}px</div>
      <div>DPR: {devicePixelRatio.toFixed(2)}</div>
      <div style={{ 
        marginTop: 4, 
        fontWeight: 'bold',
        color: hasOverflow ? '#ffff00' : '#00ff00' 
      }}>
        {hasOverflow ? '⚠️ OVERFLOW!' : '✅ No overflow'}
      </div>
    </div>
  );
}

export default DebugViewportOverlay;
