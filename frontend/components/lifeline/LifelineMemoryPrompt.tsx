/**
 * LifelineMemoryPrompt Component
 * 
 * A gentle, reflective prompt card that encourages users to expand their Lifeline
 * by surfacing memory prompts based on patterns or timeline gaps.
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';

// =============================================================================
// TYPES
// =============================================================================

export type PromptType = 
  | 'pressure' 
  | 'identity' 
  | 'relationship' 
  | 'career' 
  | 'doubt'
  | 'gap'
  | 'pattern';

export interface MemoryPrompt {
  id: string;
  type: PromptType;
  title: string;
  text: string;
  prefillData?: {
    description?: string;
    year?: number;
    category?: string;
  };
}

interface LifelineMemoryPromptProps {
  prompt: MemoryPrompt;
  onAddMoment: (prompt: MemoryPrompt) => void;
  onDismiss: (promptId: string) => void;
}

// =============================================================================
// PROMPT TEMPLATES
// =============================================================================

export const MEMORY_PROMPT_TEMPLATES: Record<PromptType, { title: string; prompts: string[] }> = {
  pressure: {
    title: 'Pressure moment',
    prompts: [
      'Was there a moment when pressure forced a decision?',
      'A time when external pressure led to an unexpected change?',
      'When did pressure create clarity you didn\'t expect?',
    ],
  },
  identity: {
    title: 'Identity shift',
    prompts: [
      'A moment that changed how you saw yourself?',
      'When did your sense of who you are shift significantly?',
      'A time when you became someone different than before?',
    ],
  },
  relationship: {
    title: 'Relationship turning point',
    prompts: [
      'A moment that changed an important relationship?',
      'When did a connection deepen or end unexpectedly?',
      'A time when someone\'s role in your life shifted?',
    ],
  },
  career: {
    title: 'Career pivot',
    prompts: [
      'A moment when your direction changed professionally?',
      'When did your work take an unexpected turn?',
      'A time when a career door opened or closed?',
    ],
  },
  doubt: {
    title: 'Questioning moment',
    prompts: [
      'A moment when you questioned your path?',
      'When did uncertainty become a turning point?',
      'A time when doubt led to something new?',
    ],
  },
  gap: {
    title: 'Quiet period',
    prompts: [], // Generated dynamically based on gap years
  },
  pattern: {
    title: 'Pattern echo',
    prompts: [], // Generated based on detected patterns
  },
};

// =============================================================================
// PROMPT GENERATORS
// =============================================================================

/**
 * Generate a gap-based prompt for a quiet period in the timeline
 */
export function generateGapPrompt(startYear: number, endYear: number): MemoryPrompt {
  const midYear = Math.floor((startYear + endYear) / 2);
  
  return {
    id: `gap-${startYear}-${endYear}`,
    type: 'gap',
    title: 'Quiet period',
    text: `Your timeline has a quiet period around ${startYear}–${endYear}. Was something important happening then?`,
    prefillData: {
      year: midYear,
      description: `Something from around ${midYear}...`,
    },
  };
}

/**
 * Generate a pattern-based prompt
 */
export function generatePatternPrompt(patternName: string, category: string): MemoryPrompt {
  return {
    id: `pattern-${patternName}-${Date.now()}`,
    type: 'pattern',
    title: 'Pattern echo',
    text: `You've shown a pattern of ${patternName.toLowerCase()}. Was there an earlier moment that fits this theme?`,
    prefillData: {
      category,
      description: `A moment related to ${patternName.toLowerCase()}...`,
    },
  };
}

/**
 * Generate a random prompt from a specific type
 */
export function generateTypePrompt(type: PromptType): MemoryPrompt | null {
  const template = MEMORY_PROMPT_TEMPLATES[type];
  if (!template || template.prompts.length === 0) return null;
  
  const randomIndex = Math.floor(Math.random() * template.prompts.length);
  const promptText = template.prompts[randomIndex];
  
  // Map type to category for prefill
  const categoryMap: Record<PromptType, string> = {
    pressure: 'Turning Point',
    identity: 'Identity',
    relationship: 'Relationships',
    career: 'Career',
    doubt: 'Turning Point',
    gap: 'Other',
    pattern: 'Other',
  };
  
  return {
    id: `${type}-${Date.now()}`,
    type,
    title: template.title,
    text: promptText,
    prefillData: {
      category: categoryMap[type],
      description: promptText,
    },
  };
}

/**
 * Detect gaps in timeline and return gap prompts
 */
export function detectTimelineGaps(events: Array<{ year?: number | null }>): MemoryPrompt[] {
  const years = events
    .map(e => e.year)
    .filter((y): y is number => y !== null && y !== undefined)
    .sort((a, b) => a - b);
  
  if (years.length < 2) return [];
  
  const gaps: MemoryPrompt[] = [];
  const currentYear = new Date().getFullYear();
  
  for (let i = 0; i < years.length - 1; i++) {
    const gap = years[i + 1] - years[i];
    if (gap > 3) {
      gaps.push(generateGapPrompt(years[i], years[i + 1]));
    }
  }
  
  // Also check gap from last event to now
  const lastYear = years[years.length - 1];
  if (currentYear - lastYear > 3) {
    gaps.push(generateGapPrompt(lastYear, currentYear));
  }
  
  return gaps;
}

/**
 * Generate a set of prompts based on user's lifeline data
 */
export function generatePromptQueue(
  events: Array<{ year?: number | null; category?: string }>,
  patterns?: { categories?: Array<[string, number]> }
): MemoryPrompt[] {
  const prompts: MemoryPrompt[] = [];
  
  // 1. Add gap prompts
  const gapPrompts = detectTimelineGaps(events);
  prompts.push(...gapPrompts);
  
  // 2. Add pattern-based prompts if patterns exist
  if (patterns?.categories && patterns.categories.length > 0) {
    const topCategory = patterns.categories[0][0];
    if (topCategory) {
      const patternPrompt = generatePatternPrompt(topCategory, topCategory);
      prompts.push(patternPrompt);
    }
  }
  
  // 3. Add type-based prompts (rotate through types)
  const types: PromptType[] = ['pressure', 'identity', 'relationship', 'career', 'doubt'];
  
  // Pick 2-3 random type prompts
  const shuffledTypes = types.sort(() => Math.random() - 0.5).slice(0, 3);
  for (const type of shuffledTypes) {
    const prompt = generateTypePrompt(type);
    if (prompt) prompts.push(prompt);
  }
  
  return prompts;
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function LifelineMemoryPrompt({
  prompt,
  onAddMoment,
  onDismiss,
}: LifelineMemoryPromptProps) {
  const { theme } = useTheme();
  
  // Icon based on prompt type
  const getIcon = () => {
    switch (prompt.type) {
      case 'pressure': return '💫';
      case 'identity': return '🪞';
      case 'relationship': return '🤝';
      case 'career': return '🚀';
      case 'doubt': return '🌊';
      case 'gap': return '📅';
      case 'pattern': return '🔄';
      default: return '✨';
    }
  };
  
  return (
    <View style={[styles.container, { backgroundColor: theme.cardBackground, borderColor: theme.border }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.icon}>{getIcon()}</Text>
        <Text style={[styles.title, { color: theme.textSecondary }]}>
          {prompt.title}
        </Text>
      </View>
      
      {/* Prompt Text */}
      <Text style={[styles.promptText, { color: theme.text }]}>
        {prompt.text}
      </Text>
      
      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={[styles.primaryButton, { backgroundColor: theme.accent }]}
          onPress={() => onAddMoment(prompt)}
          activeOpacity={0.8}
        >
          <Text style={styles.primaryButtonText}>Add this moment</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.secondaryButton}
          onPress={() => onDismiss(prompt.id)}
          activeOpacity={0.7}
        >
          <Text style={[styles.secondaryButtonText, { color: theme.textSecondary }]}>
            Not now
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  icon: {
    fontSize: 22,
    marginRight: 8,
  },
  title: {
    fontSize: 12,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  promptText: {
    fontSize: 16,
    lineHeight: 24,
    fontStyle: 'italic',
    marginBottom: 16,
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  primaryButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '500',
  },
  secondaryButton: {
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  secondaryButtonText: {
    fontSize: 14,
  },
});
