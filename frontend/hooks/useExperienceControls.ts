/**
 * useExperienceControls Hook
 * 
 * Provides access to the user's MirrorProfile and ExperienceControls
 * throughout the app. Handles loading, caching, and updates.
 * 
 * PERSISTENCE PRIORITY:
 * 1. Backend (canonical source of truth)
 * 2. User-specific AsyncStorage (local cache/fallback)
 * 3. DEFAULT_MIRROR_PROFILE (last resort)
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
import { getMirrorProfile, saveMirrorProfile, MirrorProfileData } from '../services/api';

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
  profileSource: 'backend' | 'local' | 'default';
  hasProfile: boolean;
  updateProfile: (profile: Partial<MirrorProfile>) => Promise<void>;
  refreshFromAnswers: () => Promise<void>;
  saveToBackend: (answers?: string[]) => Promise<void>;
}

export function useExperienceControls(): UseExperienceControlsReturn {
  const { questionnaireAnswers, user } = useAppStore();
  const userId = user?.id;
  
  const [profile, setProfile] = useState<MirrorProfile>(DEFAULT_MIRROR_PROFILE);
  const [controls, setControls] = useState<ExperienceControls>(DEFAULT_EXPERIENCE_CONTROLS);
  const [isLoading, setIsLoading] = useState(true);
  const [profileSource, setProfileSource] = useState<'backend' | 'local' | 'default'>('default');
  const [hasProfile, setHasProfile] = useState(false);

  // Load profile with priority: backend > local > default
  useEffect(() => {
    const loadProfile = async () => {
      if (!userId) {
        console.log('[useExperienceControls] No userId - using DEFAULT');
        setIsLoading(false);
        return;
      }
      
      try {
        console.log('[useExperienceControls] ===== LOADING PROFILE for user:', userId, '=====');
        
        // STEP 1: Try backend first (canonical source)
        try {
          const backendResponse = await getMirrorProfile(userId);
          
          if (backendResponse.has_profile && backendResponse.mirror_profile) {
            const backendProfile = backendResponse.mirror_profile as MirrorProfile;
            const derivedControls = deriveExperienceControls(backendProfile);
            
            setProfile(backendProfile);
            setControls(derivedControls);
            setProfileSource('backend');
            setHasProfile(true);
            
            // Also update local cache
            const userKey = getUserProfileKey(userId);
            await storage.setItem(userKey, JSON.stringify(backendProfile));
            
            console.log('[useExperienceControls] LOADED FROM BACKEND:');
            console.log('  primary_goal:', backendProfile.primary_goal);
            console.log('  desired_depth:', backendProfile.desired_depth);
            console.log('  support_style:', backendProfile.support_style);
            console.log('  current_self_state:', backendProfile.current_self_state);
            console.log('  DERIVED MODE:', derivedControls.mode);
            console.log('  verbosity:', derivedControls.verbosity);
            console.log('  tone:', derivedControls.tone);
            setIsLoading(false);
            return;
          }
          
          console.log('[useExperienceControls] Backend has no profile for this user');
        } catch (backendError) {
          console.log('[useExperienceControls] Backend fetch failed:', backendError);
        }
        
        // STEP 2: Try user-specific local storage
        const userKey = getUserProfileKey(userId);
        let storedProfile = await storage.getItem(userKey);
        
        // STEP 2b: Try migrating from global key if no user-specific exists
        if (!storedProfile) {
          const globalProfile = await storage.getItem(MIRROR_PROFILE_KEY);
          if (globalProfile) {
            console.log('[useExperienceControls] Migrating from global to user-specific key');
            storedProfile = globalProfile;
            await storage.setItem(userKey, globalProfile);
          }
        }
        
        if (storedProfile) {
          const localProfile = JSON.parse(storedProfile) as MirrorProfile;
          const derivedControls = deriveExperienceControls(localProfile);
          
          setProfile(localProfile);
          setControls(derivedControls);
          setProfileSource('local');
          setHasProfile(true);
          
          console.log('[useExperienceControls] LOADED FROM LOCAL STORAGE:');
          console.log('  primary_goal:', localProfile.primary_goal);
          console.log('  desired_depth:', localProfile.desired_depth);
          console.log('  DERIVED MODE:', derivedControls.mode);
          
          // STEP 2c: Migrate local to backend
          console.log('[useExperienceControls] Migrating local profile to backend...');
          try {
            await saveMirrorProfile({
              user_id: userId,
              mirror_profile: localProfile as MirrorProfileData,
            });
            console.log('[useExperienceControls] Migration to backend successful');
            setProfileSource('backend');
          } catch (migrationError) {
            console.log('[useExperienceControls] Migration to backend failed:', migrationError);
          }
          
          setIsLoading(false);
          return;
        }
        
        // STEP 3: Create from questionnaire answers if available
        if (questionnaireAnswers.length >= 5) {
          console.log('[useExperienceControls] Creating profile from questionnaire answers');
          const newProfile = createMirrorProfileFromAnswers(questionnaireAnswers);
          const derivedControls = deriveExperienceControls(newProfile);
          
          setProfile(newProfile);
          setControls(derivedControls);
          setHasProfile(true);
          
          // Save to backend
          try {
            await saveMirrorProfile({
              user_id: userId,
              mirror_profile: newProfile as MirrorProfileData,
              questionnaire_answers: questionnaireAnswers,
            });
            setProfileSource('backend');
            console.log('[useExperienceControls] New profile saved to backend');
          } catch (saveError) {
            // Save to local as fallback
            await storage.setItem(userKey, JSON.stringify(newProfile));
            setProfileSource('local');
            console.log('[useExperienceControls] Saved to local (backend save failed)');
          }
          
          setIsLoading(false);
          return;
        }
        
        // STEP 4: Use DEFAULT
        console.log('[useExperienceControls] NO PROFILE FOUND - using DEFAULT');
        console.log('  DEFAULT MODE:', DEFAULT_EXPERIENCE_CONTROLS.mode);
        console.log('  User needs to complete questionnaire or set preferences');
        setProfileSource('default');
        setHasProfile(false);
        
      } catch (error) {
        console.error('[useExperienceControls] Error loading profile:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadProfile();
  }, [userId]);

  // Save profile to backend and local storage
  const saveToBackend = useCallback(async (answers?: string[]) => {
    if (!userId) {
      console.log('[useExperienceControls] Cannot save - no userId');
      return;
    }
    
    try {
      await saveMirrorProfile({
        user_id: userId,
        mirror_profile: profile as MirrorProfileData,
        questionnaire_answers: answers,
      });
      
      // Also update local cache
      await storage.setItem(getUserProfileKey(userId), JSON.stringify(profile));
      
      setProfileSource('backend');
      setHasProfile(true);
      console.log('[useExperienceControls] Profile saved to backend and local cache');
    } catch (error) {
      console.error('[useExperienceControls] Failed to save to backend:', error);
      throw error;
    }
  }, [userId, profile]);

  // Persist profile to storage - USER-SPECIFIC
  const persistProfile = async (newProfile: MirrorProfile, forUserId?: string) => {
    const newControls = deriveExperienceControls(newProfile);
    const key = getUserProfileKey(forUserId || userId);
    await storage.setItem(key, JSON.stringify(newProfile));
    await storage.setItem(getUserControlsKey(forUserId || userId), JSON.stringify(newControls));
    console.log('[useExperienceControls] Persisted profile locally for user:', forUserId || userId);
  };

  // Update profile (for settings edits) - saves to both backend and local
  const updateProfile = useCallback(async (updates: Partial<MirrorProfile>) => {
    const newProfile: MirrorProfile = {
      ...profile,
      ...updates,
      updated_at: new Date().toISOString(),
    };
    setProfile(newProfile);
    const newControls = deriveExperienceControls(newProfile);
    setControls(newControls);
    
    // Save to backend first, then local
    if (userId) {
      try {
        await saveMirrorProfile({
          user_id: userId,
          mirror_profile: newProfile as MirrorProfileData,
        });
        setProfileSource('backend');
        console.log('[useExperienceControls] Profile updated and saved to backend');
      } catch (error) {
        console.log('[useExperienceControls] Backend save failed, using local only');
      }
    }
    
    await persistProfile(newProfile, userId);
    setHasProfile(true);
    console.log('[useExperienceControls] Profile updated:', updates);
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
    profileSource,
    hasProfile,
    updateProfile,
    refreshFromAnswers,
    saveToBackend,
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
