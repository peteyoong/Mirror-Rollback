import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { getForumStory, ForumStoryResponse } from '../../services/api';

// Helper to parse the story into sections
interface ParsedStory {
  sections: { title: string; content: string }[];
  question: string | null;
}

function parseStory(storyText: string): ParsedStory {
  const result: ParsedStory = { sections: [], question: null };
  
  // Extract question
  const questionMatch = storyText.match(/\[QUESTION\]\s*([\s\S]*?)$/);
  if (questionMatch) {
    result.question = questionMatch[1].trim();
    storyText = storyText.replace(/\[QUESTION\][\s\S]*$/, '');
  }
  
  // Extract sections
  const sectionRegex = /\[SECTION:([^\]]+)\]\s*([\s\S]*?)(?=\[SECTION:|$)/g;
  let match;
  while ((match = sectionRegex.exec(storyText)) !== null) {
    result.sections.push({
      title: match[1].trim(),
      content: match[2].trim()
    });
  }
  
  // Fallback: if no sections found, treat entire text as one section
  if (result.sections.length === 0 && storyText.trim()) {
    // Try to split by common headers or just use the whole text
    result.sections.push({
      title: '',
      content: storyText.trim()
    });
  }
  
  return result;
}

export default function ForumStoryScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const { forumId } = useLocalSearchParams();

  const [story, setStory] = useState<ForumStoryResponse | null>(null);
  const [parsedStory, setParsedStory] = useState<ParsedStory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.id && forumId) {
      fetchStory();
    }
  }, [user?.id, forumId]);

  const fetchStory = async (forceRefresh: boolean = false) => {
    if (!user?.id || !forumId) return;

    setLoading(true);
    setError(null);

    try {
      // If force refresh, we need to clear cache first - for now just fetch
      const response = await getForumStory(forumId as string, user.id);
      setStory(response);
      setParsedStory(parseStory(response.story));
    } catch (err: any) {
      console.error('[ForumStory] Error:', err);
      setError('Unable to generate the forum story. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    router.back();
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: theme.border }]}>
        <TouchableOpacity onPress={handleBack} style={styles.backButton}>
          <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.content} 
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Title */}
        <View style={styles.titleSection}>
          <Text style={[styles.title, { color: theme.text }]}>The Story of This Circle</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            A reflective view of what this group composition may bring
          </Text>
        </View>

        {/* Content */}
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.accent} />
            <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
              Reflecting on this circle...
            </Text>
            <Text style={[styles.loadingSubtext, { color: theme.textTertiary }]}>
              This may take a moment
            </Text>
          </View>
        ) : error ? (
          <View style={styles.errorContainer}>
            <Text style={[styles.errorText, { color: theme.error }]}>{error}</Text>
            <TouchableOpacity
              style={[styles.retryButton, { backgroundColor: theme.accent + '20' }]}
              onPress={() => fetchStory()}
            >
              <Text style={[styles.retryButtonText, { color: theme.accent }]}>Try Again</Text>
            </TouchableOpacity>
          </View>
        ) : parsedStory ? (
          <View style={styles.storyContainer}>
            {/* Story Sections */}
            {parsedStory.sections.map((section, index) => (
              <View 
                key={index} 
                style={[
                  styles.storySection, 
                  { backgroundColor: theme.surface },
                  index > 0 && { marginTop: 16 }
                ]}
              >
                {section.title && (
                  <Text style={[styles.sectionTitle, { color: theme.text }]}>
                    {section.title}
                  </Text>
                )}
                <Text style={[styles.sectionContent, { color: theme.text }]}>
                  {section.content}
                </Text>
              </View>
            ))}

            {/* Reflective Question */}
            {parsedStory.question && (
              <View style={[styles.questionSection, { backgroundColor: theme.accent + '10', borderColor: theme.accent + '30' }]}>
                <Text style={[styles.questionLabel, { color: theme.accent }]}>
                  A question to explore together
                </Text>
                <Text style={[styles.questionText, { color: theme.text }]}>
                  {parsedStory.question}
                </Text>
              </View>
            )}

            {/* Meta info */}
            <View style={styles.metaContainer}>
              {story?.from_cache && (
                <Text style={[styles.metaText, { color: theme.textTertiary }]}>
                  This reflection was generated earlier today
                </Text>
              )}
              <TouchableOpacity
                style={[styles.refreshButton, { borderColor: theme.border }]}
                onPress={() => fetchStory(true)}
              >
                <Text style={[styles.refreshButtonText, { color: theme.textSecondary }]}>
                  Generate New Reflection
                </Text>
              </TouchableOpacity>
            </View>

            {/* Footer note */}
            <View style={styles.footerNote}>
              <Text style={[styles.footerNoteText, { color: theme.textTertiary }]}>
                This reflection uses non-deterministic language and is meant as a starting point for discussion, not a definitive analysis.
              </Text>
            </View>
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backButton: {
    paddingVertical: 4,
  },
  backText: {
    fontSize: 16,
    fontWeight: '500',
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  titleSection: {
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
  },
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    fontSize: 16,
    marginTop: 16,
  },
  loadingSubtext: {
    fontSize: 13,
    marginTop: 6,
    fontStyle: 'italic',
  },
  errorContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  errorText: {
    fontSize: 15,
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    fontSize: 15,
    fontWeight: '600',
  },
  storyContainer: {
    gap: 0,
  },
  storySection: {
    padding: 20,
    borderRadius: 16,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    letterSpacing: 0.3,
    marginBottom: 12,
  },
  sectionContent: {
    fontSize: 15,
    lineHeight: 24,
    letterSpacing: 0.2,
  },
  questionSection: {
    marginTop: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
  },
  questionLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 10,
  },
  questionText: {
    fontSize: 16,
    lineHeight: 24,
    fontStyle: 'italic',
  },
  metaContainer: {
    alignItems: 'center',
    gap: 12,
    marginTop: 24,
  },
  metaText: {
    fontSize: 12,
    fontStyle: 'italic',
  },
  refreshButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
  },
  refreshButtonText: {
    fontSize: 13,
    fontWeight: '500',
  },
  footerNote: {
    marginTop: 20,
    paddingHorizontal: 8,
  },
  footerNoteText: {
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
    fontStyle: 'italic',
  },
});
