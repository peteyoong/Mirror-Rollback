import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

// Forum context for tracking forum state across the app
interface ForumContextData {
  forumId: string | null;
  forumName: string | null;
  exerciseId: string | null;
  exerciseTitle: string | null;
  isInForumContext: boolean;
}

interface ForumContextValue extends ForumContextData {
  setForumContext: (data: Partial<ForumContextData>) => void;
  clearForumContext: () => void;
  // For prefilled reflection source
  prefilledSource: PrefilledSource | null;
  setPrefilledSource: (source: PrefilledSource | null) => void;
}

// Source data for prefilled reflection
export interface PrefilledSource {
  sourceType: 'patterns' | 'mirror';
  lens?: 'human-design' | 'enneagram' | 'daily-insight';
  insightId: string;
  insightName: string;
  insightValue: string;
  // Guidance content
  theme: string;
  strength: string;
  challenge: string;
  guidance: string;
}

const defaultContext: ForumContextData = {
  forumId: null,
  forumName: null,
  exerciseId: null,
  exerciseTitle: null,
  isInForumContext: false,
};

const ForumContext = createContext<ForumContextValue | undefined>(undefined);

export function ForumContextProvider({ children }: { children: ReactNode }) {
  const [contextData, setContextData] = useState<ForumContextData>(defaultContext);
  const [prefilledSource, setPrefilledSource] = useState<PrefilledSource | null>(null);

  const setForumContext = useCallback((data: Partial<ForumContextData>) => {
    setContextData(prev => ({
      ...prev,
      ...data,
      isInForumContext: !!(data.forumId || prev.forumId),
    }));
  }, []);

  const clearForumContext = useCallback(() => {
    setContextData(defaultContext);
    setPrefilledSource(null);
  }, []);

  return (
    <ForumContext.Provider
      value={{
        ...contextData,
        setForumContext,
        clearForumContext,
        prefilledSource,
        setPrefilledSource,
      }}
    >
      {children}
    </ForumContext.Provider>
  );
}

export function useForumContext() {
  const context = useContext(ForumContext);
  if (!context) {
    throw new Error('useForumContext must be used within a ForumContextProvider');
  }
  return context;
}

// Hook to check if in forum context
export function useIsInForumContext() {
  const context = useContext(ForumContext);
  return context?.isInForumContext ?? false;
}
