import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

export const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // 15 second timeout
});

// Add auth token to requests
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await AsyncStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (e) {
      console.log('Error getting token from storage:', e);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Handle auth errors
    if (error.response?.status === 401) {
      try {
        await AsyncStorage.removeItem('token');
      } catch (e) {
        console.log('Error removing token:', e);
      }
    }
    
    // Log network errors for debugging
    if (!error.response) {
      console.log('Network error - unable to reach server');
    }
    
    return Promise.reject(error);
  }
);
