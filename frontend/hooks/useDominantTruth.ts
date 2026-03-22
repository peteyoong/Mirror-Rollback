/**
 * useDominantTruth Hook
 * React hook for accessing the Dominant Truth across surfaces
 */

import { useState, useEffect, useCallback } from 'react';
import {
  DominantTruthContext,
  DailyDominantTruth,
  getDailyDominantTruth,
  getDominantTruthForHome,
  getDominantTruthForChat,
  getDominantTruthForJournal,
  getDominantTruthForLifeline,
  clearDominantTruthCache,
} from '../services/dominantTruthService';
import { Timeframe } from '../services/astrology/astrologyTypes';

// ============================================
// FULL HOOK
// ============================================

export function useDominantTruth(userId: string | undefined, timeframe: Timeframe = 'today') {
  const [context, setContext] = useState<DominantTruthContext | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTruth = useCallback(async () => {
    if (!userId) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await getDailyDominantTruth(userId, timeframe);
      setContext(result);
    } catch (err) {
      console.error('[useDominantTruth] Error:', err);
      setError('Failed to load pattern');
    } finally {
      setIsLoading(false);
    }
  }, [userId, timeframe]);

  useEffect(() => {
    loadTruth();
  }, [loadTruth]);

  const refresh = useCallback(() => {
    clearDominantTruthCache();
    loadTruth();
  }, [loadTruth]);

  return {
    context,
    full: context?.full || null,
    isLoading,
    error,
    hasPattern: !!context?.full,
    refresh,
  };
}

// ============================================
// SURFACE-SPECIFIC HOOKS
// ============================================

/**
 * Hook for Home screen - returns headline only
 */
export function useDominantTruthForHome(userId: string | undefined) {
  const [data, setData] = useState<{
    headline: string;
    supportingLine: string | null;
    hasPattern: boolean;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!userId) {
      setIsLoading(false);
      return;
    }

    getDominantTruthForHome(userId)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setIsLoading(false));
  }, [userId]);

  return { data, isLoading, hasPattern: !!data };
}

/**
 * Hook for Mirror Chat - returns system context
 */
export function useDominantTruthForChat(userId: string | undefined) {
  const [data, setData] = useState<{
    systemContext: string;
    topChip: string;
    hasPattern: boolean;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!userId) {
      setIsLoading(false);
      return;
    }

    getDominantTruthForChat(userId)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setIsLoading(false));
  }, [userId]);

  return { data, isLoading, hasPattern: !!data };
}

/**
 * Hook for Journal - returns prefill content
 */
export function useDominantTruthForJournal(userId: string | undefined) {
  const [data, setData] = useState<{
    title: string;
    prefill: string;
    question: string;
    hasPattern: boolean;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!userId) {
      setIsLoading(false);
      return;
    }

    getDominantTruthForJournal(userId)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setIsLoading(false));
  }, [userId]);

  return { data, isLoading, hasPattern: !!data };
}

/**
 * Hook for Lifeline - returns suggested tag
 */
export function useDominantTruthForLifeline(userId: string | undefined) {
  const [data, setData] = useState<{
    suggestedTag: string;
    headline: string;
    hasPattern: boolean;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!userId) {
      setIsLoading(false);
      return;
    }

    getDominantTruthForLifeline(userId)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setIsLoading(false));
  }, [userId]);

  return { data, isLoading, hasPattern: !!data };
}
