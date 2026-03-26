/**
 * useExperienceControls Hook
 * 
 * Provides access to the user's MirrorProfile and ExperienceControls
 * throughout the app. Handles loading, caching, and updates.
 */

import { useState, useEffect, useCallback } from 'react';
import { useAppStore } from '../store';
import {
  MirrorProfile,
  ExperienceControls,
  deriveExperienceControls,
  createMirrorProfileFromAnswers,
  getExperienceSummary,
  getToneTemplates,
  getPromptStyleTemplate,
  DEFAULT_MIRROR_PROFILE,
  DEFAULT_EXPERIENCE_CONTROLS,
  ExperienceSummary,
  ToneTemplates,
} from '../types/mirror-profile';
import { storage } from '../store';

const MIRROR_PROFILE_KEY = 'mirror_profile';
const EXPERIENCE_CONTROLS_KEY = 'experience_controls';

interface UseExperienceControlsReturn {
  profile: MirrorProfile;
  controls: ExperienceControls;
  summary: ExperienceSummary;
  toneTemplates: ToneTemplates;
  promptTemplate: string;
  isLoading: boolean;
  updateProfile: (profile: Partial<MirrorProfile>) => Promise<void>;
  refreshFromAnswers: () => Promise<void>;
}

export function useExperienceControls(): UseExperienceControlsReturn {
  const { questionnaireAnswers } = useAppStore();
  
  const [profile, setProfile] = useState<MirrorProfile>(DEFAULT_MIRROR_PROFILE);
  const [controls, setControls] = useState<ExperienceControls>(DEFAULT_EXPERIENCE_CONTROLS);
  const [isLoading, setIsLoading] = useState(true);

  // Load persisted profile on mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const storedProfile = await storage.getItem(MIRROR_PROFILE_KEY);
        if (storedProfile) {
          const parsed = JSON.parse(storedProfile) as MirrorProfile;
          setProfile(parsed);
          setControls(deriveExperienceControls(parsed));
        } else if (questionnaireAnswers.length >= 5) {
          // No stored profile but we have answers - create from answers
          const newProfile = createMirrorProfileFromAnswers(questionnaireAnswers);
          setProfile(newProfile);
          setControls(deriveExperienceControls(newProfile));
          await persistProfile(newProfile);
        }
      } catch (error) {
        console.error('[useExperienceControls] Failed to load profile:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadProfile();
  }, []);

  // Persist profile to storage
  const persistProfile = async (newProfile: MirrorProfile) => {
    const newControls = deriveExperienceControls(newProfile);
    await storage.setItem(MIRROR_PROFILE_KEY, JSON.stringify(newProfile));
    await storage.setItem(EXPERIENCE_CONTROLS_KEY, JSON.stringify(newControls));
  };

  // Update profile (for settings edits)
  const updateProfile = useCallback(async (updates: Partial<MirrorProfile>) => {
    const newProfile: MirrorProfile = {
      ...profile,
      ...updates,
      updated_at: new Date().toISOString(),
    };
    setProfile(newProfile);
    const newControls = deriveExperienceControls(newProfile);
    setControls(newControls);
    await persistProfile(newProfile);
    console.log('[useExperienceControls] Profile updated:', updates);
  }, [profile]);

  // Refresh from questionnaire answers (after re-taking questionnaire)
  const refreshFromAnswers = useCallback(async () => {
    if (questionnaireAnswers.length >= 5) {
      const newProfile = createMirrorProfileFromAnswers(questionnaireAnswers);
      setProfile(newProfile);
      const newControls = deriveExperienceControls(newProfile);
      setControls(newControls);
      await persistProfile(newProfile);
      console.log('[useExperienceControls] Profile refreshed from answers');
    }
  }, [questionnaireAnswers]);

  // Derived values
  const summary = getExperienceSummary(profile, controls);
  const toneTemplates = getToneTemplates(controls);
  const promptTemplate = getPromptStyleTemplate(controls.prompt_style);

  return {
    profile,
    controls,
    summary,
    toneTemplates,
    promptTemplate,
    isLoading,
    updateProfile,
    refreshFromAnswers,
  };
}

// ============================================================
// HELPER HOOKS FOR SPECIFIC USE CASES
// ============================================================

/**
 * Get signal visibility level for the current user
 */
export function useSignalVisibility(): 'minimal' | 'standard' | 'expanded' {
  const { controls } = useExperienceControls();
  return controls.signal_visibility;
}

/**
 * Get home priority for card ordering
 */
export function useHomePriority(): string {
  const { controls } = useExperienceControls();
  return controls.home_priority;
}

/**
 * Get verbosity level for content length
 */
export function useVerbosity(): 'low' | 'medium' | 'high' {
  const { controls } = useExperienceControls();
  return controls.verbosity;
}

/**
 * Get tone for copy styling
 */
export function useTone(): string {
  const { controls } = useExperienceControls();
  return controls.tone;
}
