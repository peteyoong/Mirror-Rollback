/**
 * Analytics Utility - Shared Event Emission
 * ==========================================
 * 
 * Centralized analytics helper for tracking events across the app.
 * Events are logged to console in dev and can be wired to analytics service.
 * 
 * Usage:
 *   import { emitAnalytics } from '../utils/analytics';
 *   emitAnalytics('event_name', { prop1: 'value1' });
 */

// Check if we're in development mode
const isDev = typeof __DEV__ !== 'undefined' ? __DEV__ : process.env.NODE_ENV === 'development';

/**
 * Emit an analytics event with optional payload.
 * 
 * @param event - The event name (e.g., 'enneagram_gate_cta_shown')
 * @param payload - Optional properties to include with the event
 */
export function emitAnalytics(event: string, payload?: Record<string, any>): void {
  const timestamp = new Date().toISOString();
  const eventData = { event, timestamp, ...payload };
  
  // Log to console in development
  if (isDev) {
    console.log('[P2Analytics]', event, payload);
  }
  
  // TODO: Wire to analytics service (e.g., Mixpanel, Amplitude, Segment)
  // analyticsService.track(event, eventData);
}

// =============================================================================
// ENNEAGRAM GATE ANALYTICS
// =============================================================================

export type EnneagramGateCTAVariant = 'retake_low_confidence' | 'upgrade_short' | 'refresh_stale';
export type EnneagramGateSurface = 'summary' | 'deep_dive' | 'results';

export interface EnneagramGateCTAShownPayload {
  variant: EnneagramGateCTAVariant;
  surface: EnneagramGateSurface;
  assessment_depth: string | null;
  confidence_tier: string | null;
  result_age_days: number | null;
  has_saved_session?: boolean | null;
}

export interface EnneagramGateCTAClickedPayload extends EnneagramGateCTAShownPayload {
  action: 'start_assessment';
  has_saved_session: boolean;
}

/**
 * Emit enneagram_gate_cta_shown event
 */
export function emitEnneagramGateCTAShown(payload: EnneagramGateCTAShownPayload): void {
  emitAnalytics('enneagram_gate_cta_shown', payload);
}

/**
 * Emit enneagram_gate_cta_clicked event
 */
export function emitEnneagramGateCTAClicked(payload: EnneagramGateCTAClickedPayload): void {
  emitAnalytics('enneagram_gate_cta_clicked', payload);
}
