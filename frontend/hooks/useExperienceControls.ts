/**
 * useExperienceControls Hook
 * 
 * Provides access to the user's MirrorProfile and ExperienceControls
 * throughout the app. Handles loading, caching, and updates.
 * 
 * KEY: Now includes MirrorMode for structural experience differentiation
 */

import { useState, useEffect, useCallback } from 'react';
import { useAppStore } from '../store';
import {
  MirrorProfile,
  ExperienceControls,
  MirrorMode,
  ModeConfig,
  MODE_CONFIGS,
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

// Helper to get user-specific storage key
const getUserProfileKey = (userId?: string) => {
  return userId ? `mirror_profile_${userId}` : MIRROR_PROFILE_KEY;
};

const getUserControlsKey = (userId?: string) => {
  return userId ? `experience_controls_${userId}` : EXPERIENCE_CONTROLS_KEY;
};

interface UseExperienceControlsReturn {
  profile: MirrorProfile;
  controls: ExperienceControls;
  mode: MirrorMode;
  modeConfig: ModeConfig;
  summary: ExperienceSummary;
  toneTemplates: ToneTemplates;
  promptTemplate: string;
  isLoading: boolean;
  updateProfile: (profile: Partial<MirrorProfile>) => Promise<void>;
  refreshFromAnswers: () => Promise<void>;
}

export function useExperienceControls(): UseExperienceControlsReturn {
  const { questionnaireAnswers, user } = useAppStore();
  const userId = user?.id;
  
  const [profile, setProfile] = useState<MirrorProfile>(DEFAULT_MIRROR_PROFILE);
  const [controls, setControls] = useState<ExperienceControls>(DEFAULT_EXPERIENCE_CONTROLS);
  const [isLoading, setIsLoading] = useState(true);

  // Load persisted profile on mount - USER-SPECIFIC
  useEffect(() => {
    const loadProfile = async () => {
      try {
        // Try user-specific key first, then fall back to global key
        const userKey = getUserProfileKey(userId);
        const globalKey = MIRROR_PROFILE_KEY;
        
        let storedProfile = await storage.getItem(userKey);
        
        // If no user-specific profile, try global (for migration)
        if (!storedProfile && userId) {
          storedProfile = await storage.getItem(globalKey);
          // If found global, migrate to user-specific
          if (storedProfile) {
            console.log('[useExperienceControls] Migrating global profile to user-specific');
            await storage.setItem(userKey, storedProfile);
          }
        }
        
        if (storedProfile) {
          const parsed = JSON.parse(storedProfile) as MirrorProfile;
          setProfile(parsed);
          const derivedControls = deriveExperienceControls(parsed);
          setControls(derivedControls);
          
          // DEBUG: Log profile details
          console.log('[useExperienceControls] LOADED PROFILE for user:', userId);
          console.log('  primary_goal:', parsed.primary_goal);
          console.log('  uncertainty_style:', parsed.uncertainty_style);
          console.log('  desired_depth:', parsed.desired_depth);
          console.log('  support_style:', parsed.support_style);
          console.log('  current_self_state:', parsed.current_self_state);
          console.log('  DERIVED MODE:', derivedControls.mode);
          console.log('  verbosity:', derivedControls.verbosity);
          console.log('  tone:', derivedControls.tone);
          console.log('  prompt_style:', derivedControls.prompt_style);
          console.log('  signal_visibility:', derivedControls.signal_visibility);
          
        } else if (questionnaireAnswers.length >= 5) {
          // No stored profile but we have answers - create from answers
          const newProfile = createMirrorProfileFromAnswers(questionnaireAnswers);
          setProfile(newProfile);
          const derivedControls = deriveExperienceControls(newProfile);
          setControls(derivedControls);
          await persistProfile(newProfile, userId);
          
          console.log('[useExperienceControls] CREATED NEW PROFILE from answers for user:', userId);
          console.log('  DERIVED MODE:', derivedControls.mode);
          
        } else {
          // No profile, no answers - using DEFAULT
          console.log('[useExperienceControls] NO PROFILE FOUND - using DEFAULT for user:', userId);
          console.log('  DEFAULT MODE:', DEFAULT_EXPERIENCE_CONTROLS.mode);
          console.log('  DEFAULT desired_depth:', DEFAULT_MIRROR_PROFILE.desired_depth);
        }
      } catch (error) {
        console.error('[useExperienceControls] Failed to load profile:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadProfile();
  }, [userId]);

  // Persist profile to storage - USER-SPECIFIC
  const persistProfile = async (newProfile: MirrorProfile, forUserId?: string) => {
    const newControls = deriveExperienceControls(newProfile);
    const key = getUserProfileKey(forUserId || userId);
    await storage.setItem(key, JSON.stringify(newProfile));
    await storage.setItem(getUserControlsKey(forUserId || userId), JSON.stringify(newControls));
    console.log('[useExperienceControls] Persisted profile for user:', forUserId || userId);
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
    await persistProfile(newProfile, userId);
    console.log('[useExperienceControls] Profile updated for user:', userId, updates);
  }, [profile, userId]);

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
  const mode = controls.mode;
  const modeConfig = MODE_CONFIGS[mode];
  const summary = getExperienceSummary(profile, controls);
  const toneTemplates = getToneTemplates(controls);
  const promptTemplate = getPromptStyleTemplate(controls.prompt_style);

  return {
    profile,
    controls,
    mode,
    modeConfig,
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
 * Get the current MirrorMode - PRIMARY hook for structural differences
 */
export function useMirrorMode(): { mode: MirrorMode; config: ModeConfig } {
  const { mode, modeConfig } = useExperienceControls();
  return { mode, config: modeConfig };
}

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
