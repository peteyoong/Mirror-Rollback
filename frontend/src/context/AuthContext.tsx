import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../services/api';

interface AstrologyPosition {
  name: string;
  sign: string;
  degree: number;
  minutes: number;
  formatted: string;
}

interface ComputedAstrologyProfile {
  ayanamsa: string;
  positions: {
    sun: AstrologyPosition;
    moon: AstrologyPosition;
    ascendant: AstrologyPosition;
  };
  birth_datetime_local: string;
  latitude: number;
  longitude: number;
  computed_at: string;
}

interface ComputedProfile {
  astrology?: ComputedAstrologyProfile;
  human_design?: any;
  numerology?: any;
}

interface BirthData {
  birth_datetime_local: string;
  tz_offset_minutes: number;
  latitude: number;
  longitude: number;
  updated_at?: string;
}

interface User {
  id: string;
  email: string;
  name: string;
  onboarding_completed: boolean;
  onboarding_answers?: {
    relationship_with_self: string;
    reflection_style: string;
    desired_depth: string;
    uncertainty_relationship: string;
    intention: string;
  };
  computed_profile?: ComputedProfile;
  birth_data?: BirthData;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      if (token) {
        try {
          const response = await api.get('/auth/me');
          setUser(response.data);
        } catch (error: any) {
          // Only remove token on auth errors, not network errors
          if (error.response?.status === 401 || error.response?.status === 403) {
            await AsyncStorage.removeItem('token');
          }
          console.log('Auth check failed:', error.message);
        }
      }
    } catch (error) {
      console.log('Error accessing storage:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    await AsyncStorage.setItem('token', response.data.token);
    setUser(response.data.user);
  };

  const register = async (email: string, password: string, name: string) => {
    const response = await api.post('/auth/register', { email, password, name });
    await AsyncStorage.setItem('token', response.data.token);
    setUser(response.data.user);
  };

  const logout = async () => {
    await AsyncStorage.removeItem('token');
    setUser(null);
  };

  const updateUser = (updatedUser: User) => {
    setUser(updatedUser);
  };

  const refreshUser = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      if (token) {
        const response = await api.get('/auth/me');
        setUser(response.data);
        console.log('User refreshed from /api/auth/me:', response.data.birth_data ? 'HAS birth_data' : 'NO birth_data');
      }
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        updateUser,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
