import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';

// ============================================
// Tone Detection Keywords
// ============================================
const TONE_KEYWORDS = {
  stuck: ['stuck', 'trapped', 'blocked', 'can\'t move', 'stagnant', 'frozen', 'paralyzed'],
  uncertain: ['uncertain', 'unsure', 'don\'t know', 'confused', 'lost', 'unclear', 'doubt'],
  overwhelmed: ['overwhelmed', 'too much', 'exhausted', 'drained', 'burned out', 'overload'],
  excited: ['excited', 'thrilled', 'happy', 'joyful', 'energized', 'hopeful', 'inspired'],
  anxious: ['anxious', 'worried', 'nervous', 'stressed', 'tense', 'on edge', 'fearful'],
  sad: ['sad', 'down', 'low', 'disappointed', 'hurt', 'lonely', 'empty'],
  frustrated: ['frustrated', 'angry', 'annoyed', 'irritated', 'fed up', 'resentful'],
  calm: ['calm', 'peaceful', 'content', 'relaxed', 'centered', 'grounded', 'at ease'],
};

// ============================================
// "What stands out" Templates (based on detected tone)
// ============================================
const STANDOUT_TEMPLATES: { [tone: string]: string } = {
  stuck: "There seems to be a sense of being held in place. Sometimes what feels like stuckness is actually a moment of gathering before movement.",
  uncertain: "Uncertainty appears to be present in this reflection. Not knowing can feel uncomfortable, but it often precedes new understanding.",
  overwhelmed: "A lot seems to be happening at once. When everything feels like too much, it might be worth noticing which things are actually asking for attention right now.",
  excited: "There's an energy of possibility here. Excitement often signals alignment with something meaningful.",
  anxious: "Some tension seems to be present. Noticing where the body holds this anxiety might reveal what's asking for attention.",
  sad: "There's a heaviness in this reflection. Sadness, when allowed, often carries important information about what matters.",
  frustrated: "Friction seems present in what you've written. Frustration sometimes points to boundaries or values that feel crossed.",
  calm: "There's a quality of steadiness in this reflection. Moments of calm can be worth acknowledging, especially when they're not the norm.",
  neutral: "This reflection captures a moment of your experience. Simply naming what's present can sometimes shift how it lands.",
};

// ============================================
// Reframe Templates (based on Sun sign or Authority)
// ============================================
const SUN_REFRAMES: { [sign: string]: string } = {
  'Aries': "When urgency arises, it might be worth asking what would happen if action waited for clarity rather than the other way around.",
  'Taurus': "What feels heavy might become lighter when given time to settle. Stability doesn't always require immediate resolution.",
  'Gemini': "Multiple perspectives don't need to resolve into one. Perhaps what seems like scattered thinking is actually comprehensive seeing.",
  'Cancer': "Protecting what matters and opening to new possibilities don't have to be opposites. Safety can be a foundation for exploration.",
  'Leo': "The desire to be seen might be pointing toward something genuine that wants expression, not just recognition.",
  'Virgo': "What appears as imperfection might actually be exactly where growth is happening. Completion doesn't require perfection.",
  'Libra': "Balance might not mean equal weight on all sides. Sometimes harmony comes from knowing which side needs attention now.",
  'Scorpio': "What's hidden doesn't always need to be uncovered immediately. Depth reveals itself on its own timeline.",
  'Sagittarius': "The pull toward elsewhere might be worth examining — is it expansion or escape? Both can look similar.",
  'Capricorn': "Achievement and rest aren't opposites. Sometimes the most productive thing is to pause.",
  'Aquarius': "Being different doesn't require distance. Connection and individuality can coexist.",
  'Pisces': "Boundaries don't block feeling — they can actually create space for deeper presence.",
};

const AUTHORITY_REFRAMES: { [authority: string]: string } = {
  // Canonical labels from backend (frozen): Lunar | Emotional | Sacral | Splenic | Ego | Self | None
  'Sacral': "If energy isn't arising for something, that might be information worth honoring rather than overriding.",
  'Emotional': "What feels urgent right now might look different after the emotional wave passes. Time can be a clarifier.",
  'Splenic': "That quiet knowing — even when it can't be explained — might deserve more trust than the mind's analysis.",
  'Ego': "Commitment works best when it comes from genuine desire rather than obligation. What do you actually want here?",
  'Self': "Speaking this out loud to someone trusted might reveal what you already know but haven't yet heard yourself say.",
  'Lunar': "Major decisions might benefit from the full cycle of time. What's the rush?",
  'None': "Allowing the process to unfold without forcing a conclusion might reveal what's actually needed.",
};

// ============================================
// Question Templates (based on Rising sign or Profile)
// ============================================
const RISING_QUESTIONS: { [sign: string]: string } = {
  'Aries': "What if the first impulse wasn't the one to follow this time?",
  'Taurus': "Where might flexibility serve better than holding firm?",
  'Gemini': "What would choosing depth over breadth reveal here?",
  'Cancer': "Is there something being protected that no longer needs defending?",
  'Leo': "What wants to be expressed regardless of how it's received?",
  'Virgo': "What becomes possible when 'good enough' is allowed?",
  'Libra': "Setting aside others' preferences for a moment — what do you actually want?",
  'Scorpio': "Where might trust be possible, even without certainty?",
  'Sagittarius': "What might be asking for attention right here, not somewhere else?",
  'Capricorn': "What would rest look like if it didn't have to be earned?",
  'Aquarius': "Where might connection be available if you moved closer instead of observing?",
  'Pisces': "What boundaries might help you stay present without absorbing everything?",
};

const PROFILE_QUESTIONS: { [profile: string]: string } = {
  '1/3': "What might you discover if investigation and trial were both welcome here?",
  '1/4': "How might this situation look if shared with someone who knows you well?",
  '2/4': "What natural response is waiting to be called out by the right invitation?",
  '2/5': "What gift might be hiding behind the expectation to solve something?",
  '3/5': "What would this look like if the experiment couldn't fail, only inform?",
  '3/6': "How might your experience here be building toward a wisdom you can't yet see?",
  '4/1': "What would your closest people say about this if you asked them?",
  '4/6': "What perspective might emerge if you gave yourself permission to simply observe?",
  '5/1': "Setting aside what others expect — what do you actually understand here?",
  '5/2': "What if the solution isn't meant to come from effort this time?",
  '6/2': "What might become clear if you watched this situation from a distance before engaging?",
  '6/3': "How are your various experiences coming together to inform this moment?",
};

// ============================================
// Neutral Fallbacks
// ============================================
const NEUTRAL_STANDOUT = "This reflection captures a moment of your experience. Simply naming what's present can sometimes shift how it lands.";
const NEUTRAL_REFRAME = "What seems one way might look different from another angle. Perhaps there's more than one way to understand this.";
const NEUTRAL_QUESTION = "What might become clearer if you simply sat with this a little longer without needing to resolve it?";

// ============================================
// Helper Functions
// ============================================
function detectTone(text: string): string {
  const lowerText = text.toLowerCase();
  
  for (const [tone, keywords] of Object.entries(TONE_KEYWORDS)) {
    for (const keyword of keywords) {
      if (lowerText.includes(keyword)) {
        return tone;
      }
    }
  }
  
  return 'neutral';
}

interface ChartData {
  astrology?: {
    planets?: {
      Sun?: { sign?: string };
      Moon?: { sign?: string };
    };
    houses?: {
      formatted_cusps?: Array<{ sign?: string }>;
    };
  };
  human_design?: {
    type?: string;
    authority?: string;
    profile?: string;
  };
}

function generateReflection(journalText: string, chart: ChartData | null) {
  // Extract chart data
  const sunSign = chart?.astrology?.planets?.Sun?.sign;
  const moonSign = chart?.astrology?.planets?.Moon?.sign;
  const risingSign = chart?.astrology?.houses?.formatted_cusps?.[0]?.sign;
  const hdType = chart?.human_design?.type;
  const authority = chart?.human_design?.authority;
  const profile = chart?.human_design?.profile;
  
  // 1. What stands out (based on journal text tone)
  const detectedTone = detectTone(journalText);
  const standout = STANDOUT_TEMPLATES[detectedTone] || NEUTRAL_STANDOUT;
  
  // 2. Reframe (prefer Authority, fallback to Sun sign, then neutral)
  let reframe = NEUTRAL_REFRAME;
  let reframeSource = null;
  if (authority && AUTHORITY_REFRAMES[authority]) {
    reframe = AUTHORITY_REFRAMES[authority];
    reframeSource = `${authority} process`;
  } else if (sunSign && SUN_REFRAMES[sunSign]) {
    reframe = SUN_REFRAMES[sunSign];
    reframeSource = `Sun in ${sunSign}`;
  }
  
  // 3. Question (prefer Profile, fallback to Rising, then neutral)
  let question = NEUTRAL_QUESTION;
  let questionSource = null;
  if (profile && PROFILE_QUESTIONS[profile]) {
    question = PROFILE_QUESTIONS[profile];
    questionSource = `${profile} profile`;
  } else if (risingSign && RISING_QUESTIONS[risingSign]) {
    question = RISING_QUESTIONS[risingSign];
    questionSource = `Rising in ${risingSign}`;
  }
  
  return {
    standout,
    standoutTone: detectedTone,
    reframe,
    reframeSource,
    question,
    questionSource,
    hasChartData: !!(sunSign || authority || profile),
  };
}

// ============================================
// Component
// ============================================
interface MirrorReflectionModalProps {
  visible: boolean;
  onClose: () => void;
  journalText: string;
  chart: ChartData | null;
}

export default function MirrorReflectionModal({
  visible,
  onClose,
  journalText,
  chart,
}: MirrorReflectionModalProps) {
  const reflection = generateReflection(journalText, chart);
  
  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.modalContainer}>
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.headerTitle}>
              <Ionicons name="sparkles" size={20} color={Colors.accent} />
              <Text style={styles.title}>Mirror Reflection</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color={Colors.textSecondary} />
            </TouchableOpacity>
          </View>
          
          {/* Micro-copy disclaimer */}
          <Text style={styles.microcopy}>
            This reflection is generated from patterns, not predictions.
          </Text>
          
          <ScrollView 
            style={styles.scrollView}
            showsVerticalScrollIndicator={false}
          >
            {/* Journal excerpt */}
            <View style={styles.excerptContainer}>
              <Text style={styles.excerptLabel}>From your journal:</Text>
              <Text style={styles.excerptText} numberOfLines={3}>
                "{journalText}"
              </Text>
            </View>
            
            {/* What stands out */}
            <View style={styles.section}>
              <Text style={styles.sectionLabel}>What stands out</Text>
              <Text style={styles.sectionText}>{reflection.standout}</Text>
              {reflection.standoutTone !== 'neutral' && (
                <Text style={styles.sourceText}>
                  Noticed tone: {reflection.standoutTone}
                </Text>
              )}
            </View>
            
            {/* A possible reframe */}
            <View style={styles.section}>
              <Text style={styles.sectionLabel}>A possible reframe</Text>
              <Text style={styles.sectionText}>{reflection.reframe}</Text>
              {reflection.reframeSource && (
                <Text style={styles.sourceText}>
                  Informed by {reflection.reframeSource}
                </Text>
              )}
            </View>
            
            {/* A question to sit with */}
            <View style={[styles.section, styles.sectionLast]}>
              <Text style={styles.sectionLabel}>A question to sit with</Text>
              <Text style={styles.questionText}>{reflection.question}</Text>
              {reflection.questionSource && (
                <Text style={styles.sourceText}>
                  Informed by {reflection.questionSource}
                </Text>
              )}
            </View>
            
            {/* Footer */}
            <Text style={styles.footer}>
              Take what resonates; leave what doesn't.
            </Text>
          </ScrollView>
          
          {/* Done button */}
          <TouchableOpacity style={styles.doneButton} onPress={onClose}>
            <Text style={styles.doneButtonText}>Done</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: Colors.background,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '90%',
    paddingBottom: 24,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerTitle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
  },
  closeButton: {
    padding: 4,
  },
  microcopy: {
    fontSize: 12,
    color: Colors.textTertiary,
    textAlign: 'center',
    paddingHorizontal: 20,
    paddingTop: 12,
    fontStyle: 'italic',
  },
  scrollView: {
    paddingHorizontal: 20,
  },
  excerptContainer: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
    marginBottom: 24,
  },
  excerptLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  excerptText: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  section: {
    marginBottom: 28,
    paddingBottom: 24,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  sectionLast: {
    borderBottomWidth: 0,
    marginBottom: 20,
    paddingBottom: 0,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.accent,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 12,
  },
  sectionText: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.text,
  },
  questionText: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.text,
    fontStyle: 'italic',
  },
  sourceText: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 12,
    fontStyle: 'italic',
  },
  footer: {
    fontSize: 12,
    lineHeight: 18,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginBottom: 20,
  },
  doneButton: {
    marginHorizontal: 20,
    backgroundColor: Colors.accent,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  doneButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.surface,
  },
});
