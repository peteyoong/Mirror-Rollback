/**
 * Forum Patterns Page
 * 
 * This is a thin wrapper around the main Patterns page that:
 * 1. Sets the ForumContext so the Patterns page knows we're in forum mode
 * 2. Renders the exact same Patterns experience as personal Mirror
 * 3. The InlineReflectButton in Patterns will automatically detect forum context
 */

import React, { useEffect } from 'react';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useForumContext } from '../../contexts/ForumContext';
import PatternsScreen from '../(tabs)/patterns';

export default function ForumPatternsScreen() {
  const { forumId, forumName } = useLocalSearchParams<{ forumId: string; forumName?: string }>();
  const { setForumContext, clearForumContext } = useForumContext();
  const router = useRouter();

  // Set forum context when this screen mounts
  useEffect(() => {
    if (forumId) {
      setForumContext({
        forumId: forumId,
        forumName: forumName || 'Forum',
        isInForumContext: true,
      });
    }

    // Clear forum context when leaving
    return () => {
      clearForumContext();
    };
  }, [forumId, forumName]);

  // Render the exact same Patterns page
  return <PatternsScreen />;
}
