import axios from 'axios';
import Constants from 'expo-constants';

const API_BASE_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// User APIs
export const createUser = async (data: {
  name?: string;
  birth_date: string;
  birth_time?: string;
  city: string;
  country: string;
  timezone: string;
}) => {
  const response = await api.post('/users', data);
  return response.data;
};

export const updateUserEmail = async (userId: string, email: string) => {
  const response = await api.put(`/users/${userId}/email`, { email });
  return response.data;
};

export const getUser = async (userId: string) => {
  const response = await api.get(`/users/${userId}`);
  return response.data;
};

// Location APIs
export const searchLocations = async (query: string) => {
  const response = await api.post('/locations/search', { query });
  return response.data.results;
};

// Chart APIs
export const calculateChart = async (userId: string) => {
  const response = await api.post('/charts/calculate', { user_id: userId });
  return response.data;
};

export const getChart = async (userId: string) => {
  const response = await api.get(`/charts/${userId}`);
  return response.data;
};

// Journal APIs
export const createJournalEntry = async (userId: string, content: string) => {
  const response = await api.post('/journal', {
    user_id: userId,
    content,
  });
  return response.data;
};

export const getJournalEntries = async (userId: string) => {
  const response = await api.get(`/journal/${userId}`);
  return response.data;
};

export const integrateJournalEntry = async (
  userId: string, 
  entryId: string, 
  question?: string
) => {
  const response = await api.post('/journal/integrate', {
    user_id: userId,
    entry_id: entryId,
    question
  });
  return response.data;
};

// Reflection APIs
export const getDailyReflection = async (userId: string) => {
  const response = await api.post('/reflections/daily', { user_id: userId });
  return response.data;
};

// Chat APIs
export const sendChatMessage = async (userId: string, message: string) => {
  const response = await api.post('/chat', {
    user_id: userId,
    message,
  });
  return response.data;
};

// Lenses APIs
export const getLenses = async () => {
  const response = await api.get('/lenses');
  return response.data;
};

// Chart Details API (for Lenses personalization)
export interface PlanetPosition {
  name: string;
  sign: string | null;
  degree: number | null;
  longitude: number | null;
  longitude_in_sign: number | null;
  house: number | null;
  formatted: string | null;
}

export interface HouseCusp {
  house: number;
  cusp: number;
  sign: string;
  degree: number;
  formatted: string;
}

export interface ChartDetails {
  computation_version: string;
  human_design: {
    type: string | null;
    authority: string | null;
    profile: string | null;
    incarnation_cross: string | null;
    strategy: string | null;
    personality_sun: any | null;
    design_sun: any | null;
    defined_centers: string[];
    defined_channels: string[];
    definition: string | null;
    design_datetime_utc_iso: string | null;
  };
  astrology: {
    sun: any | null;
    moon: any | null;
    // Ascendant can be stored as any of these field names
    rising?: any | null;
    ascendant?: any | null;
    asc?: any | null;
    mc: any | null;
    chart_type: string | null;
    sidereal_settings: any | null;
    planets: PlanetPosition[];
    houses: HouseCusp[];
  };
  numerology: {
    life_path: any | null;
    expression: any | null;
  };
}

export const getChartDetails = async (userId: string): Promise<ChartDetails> => {
  const response = await api.get(`/charts/${userId}/details`);
  return response.data;
};

export default api;