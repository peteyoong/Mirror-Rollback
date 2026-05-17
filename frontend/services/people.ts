/**
 * Saved People — API client
 * =========================
 *
 * Wraps the backend /api/people/* endpoints. Mirrors the strict
 * accuracy contract enforced server-side: a null birth_time or
 * birth_location is only valid when its accuracy flag is "unknown".
 *
 * Source of truth for relationship_types + UX copy is the backend
 * /api/people/meta endpoint — call `getPeopleMeta()` on screen mount.
 */

import axios, { AxiosError } from 'axios';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// ---------------------------------------------------------------------------
// Base URL resolution
// ---------------------------------------------------------------------------
// IMPORTANT (P0 hotfix — May 2026):
//   The previous version of this resolver returned the *absolute*
//   EXPO_PUBLIC_BACKEND_URL value baked in at build time. On the
//   PREVIEW domain that happened to work, but the moment we
//   PUBLISHED, the bundle was hosted on a different host (the
//   Emergent production domain) while still trying to POST to the
//   preview backend — producing a stale-host 404 on Save.
//
//   New behaviour (mirrors services/api.ts):
//     • On any Emergent web host → return '' (relative). The Kubernetes
//       ingress proxy routes /api/* to backend:8001 regardless of which
//       Emergent domain serves the bundle.
//     • On localhost dev web → http://localhost:8001
//     • On native (iOS / Android) → fall back to the build-time
//       EXPO_PUBLIC_BACKEND_URL (mobile binaries have no concept of
//       "current origin").
const getApiBaseUrl = (): string => {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (
      hostname.includes('preview.emergentagent.com') ||
      hostname.includes('.emergent.host') ||
      hostname.includes('.emergentagent.com')
    ) {
      return '';
    }
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8001';
    }
  }
  const extraUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL;
  if (typeof extraUrl === 'string' && extraUrl.length > 0) {
    return extraUrl;
  }
  const envUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  if (typeof envUrl === 'string' && envUrl.length > 0) {
    return envUrl;
  }
  return '';
};

const peopleApi = axios.create({
  baseURL: `${getApiBaseUrl()}/api`,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AccuracyFlag = 'exact' | 'unknown';
export type PrecisionLevel = 'high' | 'medium' | 'low';

export interface SavedPersonLocation {
  city: string;
  country: string;
  latitude?: number | null;
  longitude?: number | null;
}

export interface SavedPerson {
  id: string;
  user_id: string;
  name: string;
  relationship_type: string;
  birth_date: string;                              // YYYY-MM-DD
  birth_time: string | null;                       // HH:MM (24h) or null
  birth_time_accuracy: AccuracyFlag;
  birth_location: SavedPersonLocation | null;
  birth_location_accuracy: AccuracyFlag;
  notes: string | null;
  timezone: string | null;
  created_at: string;
  updated_at: string;
  precision_level: PrecisionLevel;
}

export interface PeopleMeta {
  relationship_types: string[];
  accuracy_values: string[];
  ux_copy: { birth_details_hint: string };
}

export interface SavedPersonCreatePayload {
  name: string;
  relationship_type: string;
  birth_date: string;
  birth_time: string | null;
  birth_time_accuracy: AccuracyFlag;
  birth_location: SavedPersonLocation | null;
  birth_location_accuracy: AccuracyFlag;
  notes?: string | null;
  timezone?: string | null;
}

export type SavedPersonUpdatePayload = Partial<SavedPersonCreatePayload>;

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

export const getPeopleMeta = async (): Promise<PeopleMeta> => {
  const r = await peopleApi.get<PeopleMeta>('/people/meta');
  return r.data;
};

export const listSavedPeople = async (
  userId: string,
): Promise<{ people: SavedPerson[]; count: number }> => {
  const r = await peopleApi.get<{ people: SavedPerson[]; count: number }>(
    `/people/${userId}`,
  );
  return r.data;
};

export const getSavedPerson = async (
  userId: string,
  personId: string,
): Promise<SavedPerson> => {
  const r = await peopleApi.get<SavedPerson>(
    `/people/${userId}/${personId}`,
  );
  return r.data;
};

export const createSavedPerson = async (
  userId: string,
  payload: SavedPersonCreatePayload,
): Promise<SavedPerson> => {
  const r = await peopleApi.post<SavedPerson>(`/people/${userId}`, payload);
  return r.data;
};

export const updateSavedPerson = async (
  userId: string,
  personId: string,
  payload: SavedPersonUpdatePayload,
): Promise<SavedPerson> => {
  const r = await peopleApi.patch<SavedPerson>(
    `/people/${userId}/${personId}`,
    payload,
  );
  return r.data;
};

export const deleteSavedPerson = async (
  userId: string,
  personId: string,
): Promise<{ ok: boolean; deleted_id: string }> => {
  const r = await peopleApi.delete<{ ok: boolean; deleted_id: string }>(
    `/people/${userId}/${personId}`,
  );
  return r.data;
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Translate a backend Pydantic-style validation error response into a
 * single friendly sentence. Falls back to a generic friendly message
 * — NEVER returns raw axios strings like "Request failed with status
 * code 404" to the UI.
 */
export const friendlyPeopleError = (err: unknown): string => {
  if (axios.isAxiosError(err)) {
    const ax = err as AxiosError<any>;
    const data = ax.response?.data;
    if (data) {
      // FastAPI 422: { detail: [{ msg: "..." }] }
      if (Array.isArray(data.detail) && data.detail.length > 0) {
        const first = data.detail[0];
        if (first?.msg) return String(first.msg).replace(/^Value error,\s*/i, '');
      }
      // FastAPI 400: { detail: "..." }
      if (typeof data.detail === 'string') return data.detail;
    }
    // Map raw HTTP status codes to friendly copy. Critical: NEVER
    // surface ax.message verbatim — that's the "Request failed with
    // status code 404" leak the user reported.
    const status = ax.response?.status;
    if (status === 404) return "Couldn't save this person. Please try again.";
    if (status === 401 || status === 403) return 'You are not signed in. Please sign in again.';
    if (status && status >= 500) return 'The server hit a snag. Please try again in a moment.';
    if (status && status >= 400) return "Couldn't save this person. Please try again.";
    // Network / timeout — no response object at all.
    if (!ax.response) return "We couldn't reach the server. Check your connection and try again.";
  }
  return 'Something went wrong. Please try again.';
};

/**
 * UI label for a relationship_type value. Keeps display capitalisation
 * consistent without coupling to the backend's snake_case keys.
 */
export const formatRelationshipType = (raw: string): string => {
  switch (raw) {
    case 'partner':       return 'Partner';
    case 'spouse':        return 'Spouse';
    case 'ex_partner':    return 'Ex-partner';
    case 'parent':        return 'Parent';
    case 'child':         return 'Child';
    case 'sibling':       return 'Sibling';
    case 'family_other':  return 'Other family';
    case 'friend':        return 'Friend';
    case 'close_friend':  return 'Close friend';
    case 'colleague':     return 'Colleague';
    case 'boss':          return 'Boss';
    case 'report':        return 'Direct report';
    case 'client':        return 'Client';
    case 'mentor':        return 'Mentor';
    case 'mentee':        return 'Mentee';
    case 'other':         return 'Other';
    default:              return raw.replace(/_/g, ' ');
  }
};

/**
 * Precision badge label & semantic colour key. The colour itself is
 * resolved against the active theme by the consumer.
 */
export const precisionLabel = (level: PrecisionLevel): {
  label: string; tone: 'success' | 'warn' | 'muted';
} => {
  switch (level) {
    case 'high':   return { label: 'High precision',   tone: 'success' };
    case 'medium': return { label: 'Some details missing', tone: 'warn' };
    case 'low':    return { label: 'Low precision',    tone: 'muted' };
  }
};

if (__DEV__) {
  // Tiny dev-time sanity log so we can confirm the base URL once.
  // eslint-disable-next-line no-console
  console.log(
    '[PeopleAPI] base =',
    `${getApiBaseUrl()}/api`,
    'platform =', Platform.OS,
  );
}
