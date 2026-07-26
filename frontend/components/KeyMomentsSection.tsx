/**
 * KeyMomentsSection Component
 * 
 * Surfaces emotionally or psychologically meaningful journal moments
 * that feel recurring, charged, or pattern-relevant.
 * 
 * Location: Between Journal composer + Micro-Mirror and Journal history list
 * 
 * v1 Implementation: Frontend-only scoring using:
 * - Repeated themes/keywords
 * - Entry length (longer = more significant)
 * - Recency weighted
 * - Matches with common tension patterns
 */

import React, { useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { Colors } from '../constants/colors';

// ============================================
// TYPES
// ============================================

interface JournalEntry {
  id: string;
  content: string;
  created_at: string;
  themes?: string[];
}

interface KeyMoment {
  id: string;
  extractedLine: string;
  date: string;
  patternLabel?: string;
  signalScore: number;
  originalEntry: JournalEntry;
}

interface KeyMomentsSectionProps {
  journalEntries: JournalEntry[];
  onMomentPress?: (entry: JournalEntry) => void;
  onReflectWithMirror?: (entry: JournalEntry) => void;
  maxMoments?: number;
}

// ============================================
// PATTERN DETECTION KEYWORDS
// ============================================

const TENSION_PATTERNS: { label: string; keywords: string[] }[] = [
  { label: 'Freedom vs Obligation', keywords: ['freedom', 'obligation', 'duty', 'trapped', 'escape', 'responsibility', 'should', 'have to'] },
  { label: 'Control vs Surrender', keywords: ['control', 'surrender', 'let go', 'grip', 'manage', 'trust', 'release'] },
  { label: 'Connection vs Independence', keywords: ['alone', 'together', 'lonely', 'space', 'need them', 'need me', 'dependent', 'independent'] },
  { label: 'Silence vs Expression', keywords: ['silence', 'speak', 'voice', 'quiet', 'say', 'told', 'words', 'unspoken'] },
  { label: 'Safety vs Risk', keywords: ['safe', 'risk', 'afraid', 'brave', 'comfort', 'edge', 'familiar', 'unknown'] },
  { label: 'Past vs Future', keywords: ['past', 'future', 'before', 'again', 'forward', 'backward', 'remember', 'imagine'] },
  { label: 'Self vs Others', keywords: ['myself', 'them', 'selfish', 'boundaries', 'give', 'take', 'please', 'need'] },
];

const EMOTIONALLY_CHARGED_KEYWORDS = [
  'always', 'never', 'hate', 'love', 'afraid', 'angry', 'sad', 'hurt',
  'betrayed', 'abandoned', 'alone', 'lost', 'confused', 'overwhelmed',
  'exhausted', 'drained', 'anxious', 'worried', 'scared', 'hopeless',
  'stuck', 'trapped', 'free', 'relief', 'peace', 'joy', 'grateful'
];

// ============================================
// SCORING LOGIC (v1 - Frontend only)
// ============================================

function detectPatternLabel(content: string): string | undefined {
  const lowerContent = content.toLowerCase();
  
  for (const pattern of TENSION_PATTERNS) {
    const matchCount = pattern.keywords.filter(kw => lowerContent.includes(kw)).length;
    if (matchCount >= 2) {
      return pattern.label;
    }
  }
  
  return undefined;
}

function countEmotionalCharge(content: string): number {
  const lowerContent = content.toLowerCase();
  return EMOTIONALLY_CHARGED_KEYWORDS.filter(kw => lowerContent.includes(kw)).length;
}

function extractKeyLine(content: string): string {
  // Extract the most meaningful sentence (heuristic: first sentence with emotional charge, or first sentence)
  const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 10);
  
  // Score each sentence by emotional charge
  let bestSentence = sentences[0] || content;
  let bestScore = 0;
  
  for (const sentence of sentences.slice(0, 3)) { // Check first 3 sentences
    const score = countEmotionalCharge(sentence);
    if (score > bestScore) {
      bestScore = score;
      bestSentence = sentence;
    }
  }
  
  // Truncate if too long
  const trimmed = bestSentence.trim();
  if (trimmed.length > 100) {
    return trimmed.substring(0, 97) + '...';
  }
  
  return trimmed;
}

function scoreEntry(entry: JournalEntry, allEntries: JournalEntry[]): number {
  let score = 0;
  const content = entry.content.toLowerCase();
  
  // 1. Emotional charge (0-10 points)
  score += Math.min(countEmotionalCharge(entry.content), 10);
  
  // 2. Length bonus (longer entries = more processing, up to 5 points)
  score += Math.min(entry.content.length / 200, 5);
  
  // 3. Pattern match bonus (5 points if matches a tension pattern)
  if (detectPatternLabel(entry.content)) {
    score += 5;
  }
  
  // 4. Recency bonus (0-3 points, decays over 7 days)
  const daysSince = (Date.now() - new Date(entry.created_at).getTime()) / (1000 * 60 * 60 * 24);
  score += Math.max(0, 3 - (daysSince / 3));
  
  // 5. Theme repetition bonus (if this entry's themes appear in other entries)
  if (entry.themes && entry.themes.length > 0) {
    const otherEntries = allEntries.filter(e => e.id !== entry.id);
    const otherThemes = otherEntries.flatMap(e => e.themes || []);
    const sharedThemes = entry.themes.filter(t => otherThemes.includes(t));
    score += sharedThemes.length * 2;
  }
  
  return score;
}

function deriveKeyMoments(entries: JournalEntry[], maxMoments: number): KeyMoment[] {
  if (entries.length === 0) return [];
  
  // Score all entries
  const scored = entries.map(entry => ({
    entry,
    score: scoreEntry(entry, entries),
  }));
  
  // Sort by score descending
  scored.sort((a, b) => b.score - a.score);
  
  // Take top N
  const topEntries = scored.slice(0, maxMoments);
  
  // Convert to KeyMoment format
  return topEntries.map(({ entry, score }) => ({
    id: entry.id,
    extractedLine: extractKeyLine(entry.content),
    date: formatRelativeDate(entry.created_at),
    patternLabel: detectPatternLabel(entry.content),
    signalScore: score,
    originalEntry: entry,
  }));
}

function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// ============================================
// COMPONENT
// ============================================

export default function KeyMomentsSection({
  journalEntries,
  onMomentPress,
  onReflectWithMirror,
  maxMoments = 3,
}: KeyMomentsSectionProps) {
  const { theme, isDark } = useTheme();
  
  // Derive key moments from journal entries
  const keyMoments = useMemo(() => {
    return deriveKeyMoments(journalEntries, maxMoments);
  }, [journalEntries, maxMoments]);
  
  // Don't render if no key moments or too few entries
  if (keyMoments.length === 0 || journalEntries.length < 2) {
    return null;
  }
  
  return (
    <View style={[styles.container, { borderTopColor: theme.border }]}>
      {/* Section Header */}
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: theme.textTertiary }]}>
          MOMENTS MIRROR NOTICED
        </Text>
        <View style={[styles.headerLine, { backgroundColor: theme.border }]} />
      </View>
      
      {/* Key Moments List */}
      <View style={styles.momentsList}>
        {keyMoments.map((moment, index) => (
          <TouchableOpacity
            key={moment.id}
            style={[
              styles.momentCard,
              { 
                backgroundColor: isDark ? 'rgba(139, 92, 246, 0.06)' : 'rgba(139, 92, 246, 0.04)',
                borderColor: isDark ? 'rgba(139, 92, 246, 0.15)' : 'rgba(139, 92, 246, 0.12)',
              },
            ]}
            onPress={() => onMomentPress?.(moment.originalEntry)}
            activeOpacity={0.7}
          >
            {/* Pattern Label (if detected) */}
            {moment.patternLabel && (
              <View style={styles.patternLabelContainer}>
                <Text style={[styles.patternLabel, { color: Colors.accent }]}>
                  {moment.patternLabel}
                </Text>
              </View>
            )}
            
            {/* Extracted Line */}
            <Text 
              style={[styles.extractedLine, { color: theme.text }]}
              numberOfLines={2}
            >
              "{moment.extractedLine}"
            </Text>
            
            {/* Footer: Date + Action */}
            <View style={styles.momentFooter}>
              <Text style={[styles.momentDate, { color: theme.textTertiary }]}>
                {moment.date}
              </Text>
              
              {onReflectWithMirror && (
                <TouchableOpacity
                  style={styles.reflectButton}
                  onPress={(e) => {
                    e.stopPropagation();
                    onReflectWithMirror(moment.originalEntry);
                  }}
                  hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                >
                  <Text style={[styles.reflectButtonText, { color: Colors.accent }]}>
                    Reflect ›
                  </Text>
                </TouchableOpacity>
              )}
            </View>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

// ============================================
// STYLES - Lower visual priority for demoted section
// ============================================

const styles = StyleSheet.create({
  container: {
    marginTop: 24, // More top margin since it's at bottom of list
    marginBottom: 16,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10, // Reduced from 12
    gap: 8,
  },
  headerTitle: {
    fontSize: 9, // Reduced from 10 - smaller heading
    fontWeight: '500',
    letterSpacing: 0.8,
  },
  headerLine: {
    flex: 1,
    height: StyleSheet.hairlineWidth,
  },
  momentsList: {
    gap: 8, // Reduced from 10
  },
  momentCard: {
    padding: 10, // Reduced from 12
    borderRadius: 8, // Reduced from 10
    borderWidth: 1,
  },
  patternLabelContainer: {
    marginBottom: 4, // Reduced from 6
  },
  patternLabel: {
    fontSize: 9, // Reduced from 10
    fontWeight: '500',
    letterSpacing: 0.4,
  },
  extractedLine: {
    fontSize: 13, // Reduced from 14
    lineHeight: 18, // Reduced from 20
    fontStyle: 'italic',
  },
  momentFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8, // Reduced from 10
  },
  momentDate: {
    fontSize: 10, // Reduced from 11
  },
  reflectButton: {
    paddingVertical: 3,
    paddingHorizontal: 6,
  },
  reflectButtonText: {
    fontSize: 11, // Reduced from 12
    fontWeight: '500',
  },
});
