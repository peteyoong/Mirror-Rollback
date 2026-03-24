import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  Dimensions,
  Pressable,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useForumContext, PrefilledSource } from '../contexts/ForumContext';
import { useRouter } from 'expo-router';
import api from '../services/api';
import DebugFooter, { SectionDebug, isDebugEnabled } from './DebugFooter';
import { 
  formatSequenceExplanation, 
  getArcDescription, 
  getGateTheme,
  generateSphereInterpretation,
  getSphereDescriptor,
  getSequenceRole,
  SEQUENCE_ROLES 
} from '../utils/humanDesignContext';
import {
  TYPE_PATTERNS,
  AUTHORITY_PATTERNS,
  synthesizeHDPattern,
  getHDTodayContent,
  getHDWeekContent,
  getHDMonthContent,
  getCenterPattern,
} from '../utils/humanDesignPatterns';
import {
  MirrorCard,
  getTypeMirrorCard,
  getAuthorityMirrorCard,
  getProfileMirrorCard,
  getCenterMirrorCard,
  getCrossMirrorCard,
  CrossLinkContext,
  getGateCrossLink,
  getCenterCrossLink,
  getTypeCrossLink,
  getAuthorityCrossLink,
} from '../utils/humanDesignMirrorCards';
import {
  generateHDSynthesis,
  HDSynthesisInput,
  HDSynthesis,
  generatePatternThread,
  PatternThread,
  generatePatternState,
  PatternState,
} from '../utils/humanDesignSynthesis';
import { CrossLensPatternBridge } from './CrossLensPatternBridge';
import { CollapsibleCard, NestedCollapsible, SectionHeader } from './CollapsibleCard';
import GeneKeysView from './GeneKeysView';
import CentersView, { CentersViewHandle } from './CentersView';
import DefinedGatesView from './DefinedGatesView';
import { ForumContextBanner } from './ForumContextBanner';
import { InlineReflectButton } from './UniversalReflectButton';
import { UniversalReflectionModal, ReflectionSource } from './UniversalReflectionModal';
import KeystoneReferenceLink from './KeystoneReferenceLink';

// Build info for debugging
const BUILD_VERSION = process.env.EXPO_PUBLIC_BUILD_VERSION || 'unknown';
const BUILD_ID = process.env.EXPO_PUBLIC_BUILD_ID || 'unknown';

// ============================================
// OVERVIEW DATA (Reflective Translations)
// ============================================

// Energy pattern descriptions by Type (reflective, not technical)
const TYPE_ENERGY_PATTERNS: { [key: string]: string } = {
  'Generator': 'Your energy is designed to respond. When something genuinely excites you, your body lights up with sustainable energy to pursue it. Without that inner response, energy becomes forced and depleting.',
  'Manifesting Generator': 'Your energy moves fast and multi-directionally. You\'re designed to respond to what excites you, then act quickly—sometimes skipping steps. Your vitality comes from engaging with multiple interests that truly call to you.',
  'Projector': 'Your energy is focused and penetrating, designed to guide and see into others. Rather than initiating or generating, you thrive when recognized and invited into the spaces where your insight is valued.',
  'Manifestor': 'Your energy is designed to initiate and impact. You carry a powerful force that starts things and sets change in motion. Your flow comes from acting on your own impulses while keeping others informed.',
  'Reflector': 'Your energy mirrors the world around you. You\'re designed to sample and reflect the health of your environment, taking in experiences over time before gaining clarity. Your wisdom comes from this unique openness.',
};

// Strategy translations (everyday language)
const STRATEGY_TRANSLATIONS: { [key: string]: string } = {
  'Wait to Respond': 'Wait for something in life to spark your inner "yes" before committing your energy. Your body knows before your mind—trust that gut response.',
  'Wait for the Invitation': 'Wait to be recognized and invited before sharing your gifts. Unsolicited guidance often misses the mark; invited guidance transforms.',
  'Inform Before Acting': 'Let others know what you\'re about to do before you do it. This isn\'t asking permission—it\'s reducing resistance and keeping peace.',
  'Wait a Lunar Cycle': 'Give yourself a full moon cycle before making major decisions. Your clarity unfolds over time as you experience different energetic environments.',
};

// Authority translations (decision-making in everyday terms)
const AUTHORITY_TRANSLATIONS: { [key: string]: { short: string; expanded: string } } = {
  'Emotional': {
    short: 'Clarity comes through emotional waves',
    expanded: 'Your decisions gain clarity over time as your emotions move through highs and lows. Never decide in the peak of excitement or the depth of frustration—wait for calm.'
  },
  'Sacral': {
    short: 'Clarity comes from gut responses',
    expanded: 'Your body responds with sounds or sensations: an "uh-huh" of yes or an "unh-uh" of no. Trust these visceral reactions—they know before your mind does.'
  },
  'Splenic': {
    short: 'Clarity comes in the moment',
    expanded: 'Your intuition speaks once, quietly, in the present moment. Learn to recognize that subtle knowing—if you hesitate, you may miss it.'
  },
  'Ego': {
    short: 'Clarity comes from what you truly want',
    expanded: 'Your decisions are clear when you ask: "Do I really want this? Is my heart in it?" If there\'s no genuine desire, the energy won\'t sustain.'
  },
  'Self-Projected': {
    short: 'Clarity comes through hearing yourself speak',
    expanded: 'Talk through your decisions with others. Not for their advice—but to hear your own voice and recognize what\'s true for you in the speaking.'
  },
  'Mental': {
    short: 'Clarity comes from environment and sounding boards',
    expanded: 'Discuss your decisions in different environments with trusted people. You\'re not looking for answers from them—you\'re finding clarity through the process.'
  },
  'Lunar': {
    short: 'Clarity comes over a full moon cycle',
    expanded: 'Major decisions need about 28 days. Experience your question through different energetic environments before settling into knowing.'
  },
  'None': {
    short: 'Clarity comes through environment',
    expanded: 'Your decisions are influenced by place and people around you. Take time in different settings and notice where you feel most clear.'
  },
};

// Where this helps - by Type
const TYPE_MANIFESTATIONS: { [key: string]: { decisions: string; work: string; relationships: string; energy: string } } = {
  'Generator': {
    decisions: 'Wait for options to appear, then notice your gut response',
    work: 'Most fulfilled when engaged in work that genuinely excites you',
    relationships: 'Thrive with partners who understand your need to respond rather than be pushed',
    energy: 'Sustainable when following satisfaction; draining when forcing through frustration',
  },
  'Manifesting Generator': {
    decisions: 'Respond to what excites, then trust your quick moves',
    work: 'Need variety and permission to change direction when mastery is reached',
    relationships: 'Valued for your energy and speed; need space to pivot',
    energy: 'High and multi-directional when engaged; scattered when bored',
  },
  'Projector': {
    decisions: 'Wait to be asked; your insights land better when invited',
    work: 'Excel in guiding, managing, and seeing others deeply',
    relationships: 'Need recognition and appreciation for your unique perspective',
    energy: 'Powerful in focused bursts; need rest and solitude to recharge',
  },
  'Manifestor': {
    decisions: 'Act on your impulses; inform others before moving',
    work: 'Best at initiating, starting projects, and catalyzing change',
    relationships: 'Need independence; partners who don\'t try to control you',
    energy: 'Comes in powerful surges; requires rest between initiations',
  },
  'Reflector': {
    decisions: 'Take a full lunar cycle; let clarity emerge over time',
    work: 'Natural evaluators of community and environment health',
    relationships: 'Deeply affected by who you\'re with; choose environments carefully',
    energy: 'Varies with the moon and surroundings; honor your fluctuations',
  },
};

// Reflection prompts by Type
const TYPE_REFLECTIONS: { [key: string]: string } = {
  'Generator': 'Where are you saying yes out of obligation rather than genuine excitement—and where might your true response be waiting?',
  'Manifesting Generator': 'Where are you forcing yourself to finish what no longer calls you—and where might a new response be pulling your energy?',
  'Projector': 'Where are you offering guidance that wasn\'t invited—and where might recognition be waiting if you simply wait?',
  'Manifestor': 'Where are you holding back your impulse to avoid conflict—and where might informing others create more peace than hiding?',
  'Reflector': 'Where are you rushing decisions that need more time—and where might the full cycle bring surprising clarity?',
};

// ============================================
// MECHANICS STORY CONTENT (for Explore modals)
// ============================================

interface MechanicStory {
  explanation: string[];
  patterns: string[];
  challenge: string;
  reflection: string;
}

// Type Stories - detailed content for each type
const TYPE_STORIES: { [key: string]: MechanicStory } = {
  'Generator': {
    explanation: [
      'Generators are the life force of humanity, designed to find work they love and build mastery over time. Your energy is sustainable and powerful when directed toward what genuinely excites you.',
      'The key to your design is response—waiting for life to bring you something to react to, rather than initiating from mental ideas. When you feel that inner "uh-huh" of yes, your energy lights up.',
      'This isn\'t passivity; it\'s attunement. Your body knows what\'s correct for you before your mind does.'
    ],
    patterns: [
      'Strong gut responses to opportunities—either excitement or resistance',
      'Deep satisfaction when engaged in meaningful work',
      'Frustration when pushing through without genuine interest',
      'Natural ability to build and sustain energy for projects you love',
      'Others drawn to your vitality and presence'
    ],
    challenge: 'The most common challenge for Generators is saying yes to things out of obligation, social pressure, or mental reasoning—ignoring that subtle gut feeling. Over time, this leads to frustration and exhaustion.',
    reflection: 'Where in your life are you saying yes without feeling that genuine inner response? What might shift if you waited for real excitement?'
  },
  'Manifesting Generator': {
    explanation: [
      'Manifesting Generators combine the sustainable energy of a Generator with the initiating capacity of a Manifestor. You\'re designed to respond AND move quickly once something excites you.',
      'Your path often appears non-linear—you may skip steps, pivot directions, or work on multiple projects simultaneously. This isn\'t inconsistency; it\'s efficiency.',
      'Trust your response, then trust your speed. You\'re designed to find shortcuts and master things quickly before moving to the next calling.'
    ],
    patterns: [
      'Quick bursts of energy when something genuinely excites you',
      'Natural tendency to multi-task and juggle projects',
      'Finding efficient shortcuts others might miss',
      'Frustration when forced to slow down or follow linear paths',
      'Rapid skill acquisition followed by desire to move on'
    ],
    challenge: 'The most common challenge is forcing yourself to finish what no longer excites you, or judging yourself for "not completing things." Your design includes pivoting—the key is responding to what\'s truly calling you.',
    reflection: 'Where are you forcing yourself to continue something that stopped exciting you? What new response might be waiting?'
  },
  'Projector': {
    explanation: [
      'Projectors are the guides and seers of humanity, designed to understand systems, people, and patterns more deeply than others. Your gift is penetrating insight.',
      'Your energy works differently—rather than sustained output, you work in focused bursts and need more rest. Recognition and invitation are essential for your gifts to land.',
      'When you\'re invited into a situation, your guidance transforms. When you offer unsolicited advice, it often falls flat—not because it\'s wrong, but because the receptivity isn\'t there.'
    ],
    patterns: [
      'Ability to see what others miss in people and systems',
      'Need for recognition and appreciation of your unique perspective',
      'Energy that works best in focused bursts rather than marathons',
      'Natural talent for guiding, managing, and advising',
      'Sensitivity to whether you\'ve been truly invited or not'
    ],
    challenge: 'The most common challenge is offering guidance that wasn\'t asked for, then feeling bitter when it\'s rejected or ignored. Learning to wait for genuine invitations—and rest properly—transforms your experience.',
    reflection: 'Where have you been giving advice that wasn\'t invited? What might open up if you simply waited to be asked?'
  },
  'Manifestor': {
    explanation: [
      'Manifestors are the initiators of humanity, designed to start things, catalyze change, and impact the world through action. You carry a powerful urge to act on your impulses.',
      'Your energy comes in surges rather than sustained waves. You\'re designed to initiate, not to be controlled or managed by others. Independence is core to your nature.',
      'The key practice for Manifestors is informing—not asking permission, but letting others know what you\'re about to do. This reduces resistance and creates peace in your wake.'
    ],
    patterns: [
      'Strong urges to initiate and start new things',
      'Resistance when others try to control or manage you',
      'Impact that ripples outward and affects others',
      'Energy that surges powerfully then needs rest',
      'Peace when acting freely; anger when constrained'
    ],
    challenge: 'The most common challenge is either suppressing your initiating impulse to avoid conflict, or acting without informing and creating unexpected resistance. Neither leads to peace.',
    reflection: 'Where are you holding back an impulse because you fear others\' reactions? What might happen if you simply informed them first?'
  },
  'Reflector': {
    explanation: [
      'Reflectors are the mirrors of humanity, designed to sample and reflect the health of their environment. With all centers undefined, you take in the world in a completely unique way.',
      'Your clarity doesn\'t come quickly—it unfolds over approximately 28 days, one full lunar cycle. Major decisions benefit from this patient process.',
      'You\'re deeply affected by your environment and the people around you. This isn\'t weakness; it\'s your gift of evaluation. Where you feel good indicates a healthy place.'
    ],
    patterns: [
      'Deep sensitivity to environment and people around you',
      'Wisdom that comes from sampling many different perspectives',
      'Surprise when you realize how different you feel in different places',
      'Natural ability to evaluate the health of communities and groups',
      'Disappointment when environments don\'t match their potential'
    ],
    challenge: 'The most common challenge is rushing major decisions without allowing the full lunar cycle. The pressure to "know quickly" doesn\'t serve your design.',
    reflection: 'What decision are you currently rushing? What might become clear if you gave yourself a full month to experience it?'
  }
};

// Authority Stories
const AUTHORITY_STORIES: { [key: string]: MechanicStory } = {
  'Emotional': {
    explanation: [
      'Your inner authority moves through emotional waves—highs and lows that carry you from excitement to doubt and back again. Clarity doesn\'t exist in any single moment for you.',
      'The practice is to ride the wave. A decision that feels amazing at an emotional high may feel wrong at a low—and vice versa. Only when you\'ve experienced both extremes does clarity emerge.',
      'This requires patience. Sleeping on important decisions, revisiting them over days, and asking "how do I feel about this now?" are your tools.'
    ],
    patterns: [
      'Strong emotional responses to decisions and opportunities',
      'Changing feelings about the same choice over time',
      'Clarity that emerges after riding emotional waves',
      'Regret when deciding at emotional peaks or valleys',
      'Wisdom that comes from waiting for calm'
    ],
    challenge: 'The biggest challenge is deciding in the heat of the moment—either in extreme excitement or deep frustration. Both lead to choices that don\'t hold up over time.',
    reflection: 'Think of a recent important decision. Did you allow yourself to feel through the whole emotional cycle, or did you decide at a peak or valley?'
  },
  'Sacral': {
    explanation: [
      'Your body speaks through gut responses—visceral sounds and sensations that indicate yes or no. An "uh-huh" of expansion, an "unh-uh" of contraction. This is your truth.',
      'The mind might argue, analyze, or second-guess, but the sacral response is immediate and reliable. It responds to yes/no questions in the moment.',
      'The practice is to pay attention to what your body does before your mind kicks in. That first response is usually correct.'
    ],
    patterns: [
      'Immediate gut responses to questions and opportunities',
      'Sounds or sensations that indicate yes or no',
      'Energy that sustains when the sacral says yes',
      'Depletion when overriding the gut response',
      'Confusion when trying to reason rather than respond'
    ],
    challenge: 'The biggest challenge is ignoring or overriding your gut response because of mental reasoning, social pressure, or should\'s. Your body knows—the question is whether you listen.',
    reflection: 'When was the last time you overrode a gut "no" because you thought you should say yes? What happened?'
  },
  'Splenic': {
    explanation: [
      'Your intuition speaks once, quietly, in the present moment. It\'s a survival intelligence—immediate knowing about what\'s healthy, safe, or correct right now.',
      'Unlike emotional authority, there\'s no wave to ride. The splenic hit comes and goes quickly. If you miss it or hesitate, the moment passes.',
      'The practice is developing sensitivity to that subtle inner voice. It often speaks as a quiet knowing, a physical sensation, or an immediate recognition.'
    ],
    patterns: [
      'Quick, quiet knowing in the moment',
      'Instincts about safety, health, and timing',
      'Clarity that comes instantly rather than over time',
      'Confusion when trying to analyze rather than sense',
      'Trust that builds through honoring subtle hits'
    ],
    challenge: 'The biggest challenge is second-guessing your immediate knowing with mental analysis. By the time you\'ve "thought it through," the true intuitive hit has passed.',
    reflection: 'Can you remember a time when you knew something instantly but talked yourself out of it? What happened when you ignored that first hit?'
  },
  'Ego': {
    explanation: [
      'Your decisions are clear when connected to what you truly want—what your heart desires and is willing to commit to. Willpower is your guide.',
      'The question isn\'t "should I?" but "do I really want this? Is my heart in it?" If there\'s no genuine desire, the energy to sustain it won\'t be there.',
      'This isn\'t selfishness; it\'s honoring the truth of your design. When you commit to what you genuinely want, you follow through. When you don\'t, it falls apart.'
    ],
    patterns: [
      'Clarity when desires are genuinely felt',
      'Strong willpower when heart is committed',
      'Difficulty sustaining what you don\'t truly want',
      'Decisions that hold when genuinely desired',
      'Natural capacity for promise and commitment'
    ],
    challenge: 'The biggest challenge is saying yes to things you should want rather than things you actually want. Without genuine desire, the willpower to sustain isn\'t there.',
    reflection: 'What have you committed to that you don\'t actually want? What would shift if you only promised what your heart truly desires?'
  },
  'Self-Projected': {
    explanation: [
      'Your clarity comes through your voice—specifically, through hearing yourself talk about your decisions with others. Not for their opinion, but to hear your own truth spoken aloud.',
      'When you speak about a decision, pay attention to how it feels to say it. Your voice carries your truth. The words reveal what\'s correct for you.',
      'The practice is finding trusted people to talk things through with, not for advice, but as sounding boards for your own knowing to emerge.'
    ],
    patterns: [
      'Clarity that comes through speaking aloud',
      'Recognizing truth in your own voice',
      'Confusion when processing internally without speaking',
      'Need for trusted people to talk things through with',
      'Recognition of what\'s true while hearing yourself say it'
    ],
    challenge: 'The biggest challenge is trying to figure things out silently in your head, or seeking advice rather than simply speaking your own process aloud.',
    reflection: 'When did you last talk through a decision with someone? Did clarity come from hearing yourself, or did you get lost in their opinions?'
  },
  'Mental': {
    explanation: [
      'Your clarity emerges through conversation and environment over time. You need to discuss decisions in different contexts with different people, not for answers, but to find your own.',
      'This isn\'t about mental analysis—it\'s about the process of dialogue. Something shifts when you talk things through in varied settings with trusted others.',
      'The practice is cultivating a network of sounding boards and being willing to discuss without rushing to conclusion.'
    ],
    patterns: [
      'Clarity that emerges through discussion over time',
      'Need for varied perspectives and environments',
      'Confusion when trying to decide in isolation',
      'Wisdom that comes from the process of dialogue',
      'Decisions that solidify through conversation'
    ],
    challenge: 'The biggest challenge is either deciding in isolation or expecting others to give you the answer. The clarity is yours—conversation is just the process.',
    reflection: 'What decision would benefit from more conversation? Who are your trusted sounding boards, and when did you last use them?'
  },
  'Lunar': {
    explanation: [
      'Your clarity unfolds over a complete lunar cycle—approximately 28 days. Major decisions need this full period to truly know what\'s correct.',
      'During this time, you experience the decision in different energetic environments as the moon moves through the gates. Clarity emerges from this sampling.',
      'The practice is patience and trust. Mark when a decision appears, give it a full cycle, and notice how your knowing evolves.'
    ],
    patterns: [
      'Clarity that takes approximately 28 days to emerge',
      'Different feelings about decisions throughout the cycle',
      'Wisdom that comes from sampling varied energies',
      'Knowing that solidifies over time rather than instantly',
      'Trust in the process despite external pressure'
    ],
    challenge: 'The biggest challenge is the pressure to decide quickly in a world that values fast answers. Your design requires patience that others may not understand.',
    reflection: 'What major decision are you currently facing? What would change if you gave yourself a full lunar cycle before committing?'
  },
  'None': {
    explanation: [
      'Without a defined inner authority, your clarity comes from your environment—the places and people around you. Where you feel most clear indicates what\'s correct.',
      'This makes you highly sensitive to environment. A decision might feel completely different in your home versus at work, with certain people versus others.',
      'The practice is paying attention to where and with whom you feel most clarity, and making important decisions in those settings.'
    ],
    patterns: [
      'Clarity that varies by environment and company',
      'Sensitivity to how places and people affect your knowing',
      'Need for trusted environments and relationships',
      'Wisdom that comes from noticing environmental influence',
      'Decisions that hold when made in correct settings'
    ],
    challenge: 'The biggest challenge is not recognizing how much your environment affects your clarity. A choice that feels right in one place may feel wrong in another—both are valid data.',
    reflection: 'Where do you feel most clear? What would happen if you made important decisions only in that environment?'
  }
};

// Profile Stories
const PROFILE_STORIES: { [key: string]: MechanicStory } = {
  '1/3': {
    explanation: [
      'The 1/3 profile combines the Investigator (Line 1) with the Martyr (Line 3). You\'re designed to build deep foundations through research and learn through direct trial and error.',
      'Your process involves both study and experimentation—understanding things deeply, then testing them in real life. What doesn\'t work is just as valuable as what does.',
      'This creates a life of learning that may appear chaotic to others but is actually building profound practical wisdom.'
    ],
    patterns: [
      'Deep need to understand before committing',
      'Learning most from direct experience and mistakes',
      'Wisdom that comes from both study and trial',
      'Resilience built through what hasn\'t worked',
      'Authority that comes from tested knowledge'
    ],
    challenge: 'The challenge is feeling like you\'re always starting over, or judging your experiments as failures rather than necessary learning.',
    reflection: 'What recent "failure" actually taught you something essential? How might you honor the trial-and-error nature of your path?'
  },
  '1/4': {
    explanation: [
      'The 1/4 profile combines the Investigator (Line 1) with the Opportunist (Line 4). You build deep foundations and share your knowledge through close networks and relationships.',
      'Your influence moves through trusted connections. Once you\'ve thoroughly researched something, you share it with your inner circle—and it spreads from there.',
      'Security comes from both solid knowledge and solid relationships.'
    ],
    patterns: [
      'Deep research before forming or sharing opinions',
      'Influence that moves through close relationships',
      'Need for both intellectual and social security',
      'Wisdom shared through trusted networks',
      'Friendships that carry your message outward'
    ],
    challenge: 'The challenge is trying to influence beyond your natural network, or feeling pressured to share before your research is complete.',
    reflection: 'Who are your trusted people? When did you last share hard-won knowledge with them rather than trying to broadcast it widely?'
  },
  '2/4': {
    explanation: [
      'The 2/4 profile combines the Hermit (Line 2) with the Opportunist (Line 4). You have natural gifts that others see before you do, and your influence moves through close relationships.',
      'Part of you needs solitude to develop your talents; part of you needs social connection to share them. Both are essential.',
      'Your gifts often emerge when called out by others rather than through conscious development.'
    ],
    patterns: [
      'Natural talents that others recognize first',
      'Need for both solitude and social connection',
      'Gifts that emerge when called upon',
      'Influence through close, trusted relationships',
      'Tension between hermit tendencies and social needs'
    ],
    challenge: 'The challenge is either isolating too much or depleting yourself socially—finding the rhythm between retreat and connection.',
    reflection: 'What gift have others called out in you that you hadn\'t fully seen? How do you balance your need for solitude with your relationships?'
  },
  '2/5': {
    explanation: [
      'The 2/5 profile combines the Hermit (Line 2) with the Heretic (Line 5). You have natural gifts that emerge when called, and others project savior-like expectations onto you.',
      'You need solitude to develop your talents, yet you\'re often thrust into situations where others expect you to solve problems or provide solutions.',
      'Managing projections and maintaining your hermit time are both essential for your wellbeing.'
    ],
    patterns: [
      'Natural talents that emerge when called upon',
      'Others projecting expectations and needs onto you',
      'Need for significant solitude and retreat time',
      'Capacity to deliver practical solutions when ready',
      'Sensitivity to whether you can actually meet expectations'
    ],
    challenge: 'The challenge is carrying others\' projections—especially when you can\'t deliver what they expect. Clear boundaries and selective engagement are essential.',
    reflection: 'Where are others projecting expectations onto you that don\'t match your actual gifts? What would honoring your hermit needs look like?'
  },
  '3/5': {
    explanation: [
      'The 3/5 profile combines the Martyr (Line 3) with the Heretic (Line 5). You learn through trial and error, and others project expectations onto you to solve problems.',
      'Your path involves many experiments, some that work and many that don\'t—and you carry the reputation of someone who can fix things when called.',
      'The combination creates someone who knows what works through direct experience and can share that wisdom when truly needed.'
    ],
    patterns: [
      'Learning primarily through trial and error',
      'Others expecting you to have solutions',
      'Wisdom built from what hasn\'t worked',
      'Capacity to help when projections are realistic',
      'Resilience from experimentation and external expectations'
    ],
    challenge: 'The challenge is both the constant experimentation and the weight of others\' projections. Neither your experiments nor their expectations define your worth.',
    reflection: 'What experiment recently taught you something valuable? How do you handle when others\' expectations don\'t match what you can actually deliver?'
  },
  '3/6': {
    explanation: [
      'The 3/6 profile combines the Martyr (Line 3) with the Role Model (Line 6). Your life moves through three phases: experimentation until around 30, processing on the "roof" until around 50, then stepping into wisdom.',
      'The first third of life involves intense trial and error. The second third is about observing and integrating. The final phase is living as an example.',
      'Your authority comes from having lived through experiments and emerged with perspective.'
    ],
    patterns: [
      'Life divided into three distinct phases',
      'Early experimentation and trial-and-error learning',
      'Middle phase of observation and integration',
      'Later emergence as a natural role model',
      'Wisdom earned through lived experience'
    ],
    challenge: 'The challenge depends on your life phase—either the exhaustion of experimentation, the aloofness of the roof period, or the pressure of being an example.',
    reflection: 'Which phase of life are you in? What does honoring that phase look like rather than rushing to the next?'
  },
  '4/6': {
    explanation: [
      'The 4/6 profile combines the Opportunist (Line 4) with the Role Model (Line 6). Your influence moves through networks, and your life follows the three-phase pattern ending in natural authority.',
      'Relationships are central throughout all phases. Even your eventual role model status emerges through trusted connections rather than broad broadcasting.',
      'Your authority is intimate and relational rather than distant and universal.'
    ],
    patterns: [
      'Influence through close relationships and networks',
      'Life moving through three distinct phases',
      'Authority that emerges through connection',
      'Need for stable friendships throughout all phases',
      'Role model energy expressed through intimacy'
    ],
    challenge: 'The challenge is maintaining relationships through the different life phases, especially the aloof "roof" period when connection feels less natural.',
    reflection: 'How have your key relationships evolved through different phases of your life? Who remains constant?'
  },
  '4/1': {
    explanation: [
      'The 4/1 profile combines the Opportunist (Line 4) with the Investigator (Line 1). You influence through close networks, and you build deep foundations of knowledge.',
      'Your authority comes from thoroughly researched understanding shared through trusted relationships. You need both intellectual depth and social connection.',
      'Change is challenging for you—foundations and relationships both require stability to thrive.'
    ],
    patterns: [
      'Deep research and investigation into interests',
      'Influence through close, trusted relationships',
      'Need for both intellectual and relational security',
      'Resistance to change once foundations are set',
      'Authority built on solid knowledge and connections'
    ],
    challenge: 'The challenge is rigidity—difficulty adapting when foundations need to shift or when relationships change.',
    reflection: 'Where in your life are you holding onto foundations that might need updating? Which relationships carry your truest influence?'
  },
  '5/1': {
    explanation: [
      'The 5/1 profile combines the Heretic (Line 5) with the Investigator (Line 1). Others project expectations onto you, and you build deep foundations to meet those expectations when appropriate.',
      'Your research supports your capacity to deliver. When you truly understand something, you can provide practical solutions that meet projections.',
      'The challenge is discerning which projections are worth meeting and which aren\'t aligned with your actual knowledge.'
    ],
    patterns: [
      'Others projecting expectations and needs',
      'Deep investigation before providing solutions',
      'Capacity to deliver when foundations are solid',
      'Universal appeal that attracts strangers',
      'Need for thorough preparation before engagement'
    ],
    challenge: 'The challenge is carrying projections without the foundation to meet them, or over-preparing and never engaging.',
    reflection: 'What are others currently expecting from you? Which expectations align with your actual research and knowledge?'
  },
  '5/2': {
    explanation: [
      'The 5/2 profile combines the Heretic (Line 5) with the Hermit (Line 2). Others project savior expectations onto you, while you have natural gifts that emerge when called from solitude.',
      'You need significant alone time to develop your gifts, yet you\'re regularly called out of retreat to help others. Managing this rhythm is essential.',
      'Your solutions often come from natural talent that you haven\'t consciously developed—gifts that others see before you do.'
    ],
    patterns: [
      'Strong projections from others about what you can provide',
      'Natural talents that emerge when called upon',
      'Deep need for solitude and retreat',
      'Gifts that you may not fully recognize yourself',
      'Tension between hermit needs and external demands'
    ],
    challenge: 'The challenge is being pulled from necessary solitude by others\' expectations, especially when you can\'t deliver what they project.',
    reflection: 'How do you protect your hermit time? What natural gift have others called out that you hadn\'t fully recognized?'
  },
  '6/2': {
    explanation: [
      'The 6/2 profile combines the Role Model (Line 6) with the Hermit (Line 2). Your life moves through three phases ending in natural authority, while you carry innate gifts that emerge when called.',
      'Solitude is essential throughout all phases. Your eventual role model energy comes not from seeking attention but from naturally embodying wisdom when called out of retreat.',
      'Others recognize your gifts before you do, calling you into expression.'
    ],
    patterns: [
      'Life moving through three distinct phases',
      'Natural talents that others recognize first',
      'Deep need for solitude throughout all phases',
      'Role model energy that emerges naturally, not through effort',
      'Being called out of retreat to share gifts'
    ],
    challenge: 'The challenge is balancing the three-phase journey with your hermit needs, especially when others want more from you than you\'re ready to give.',
    reflection: 'Which phase of life are you in? How do you balance being called out with honoring your need for retreat?'
  },
  '6/3': {
    explanation: [
      'The 6/3 profile combines the Role Model (Line 6) with the Martyr (Line 3). Your life follows the three-phase pattern, and throughout all phases you learn primarily through trial and error.',
      'The combination creates a life of intense experimentation—first actively, then observationally, then as a wise example of someone who\'s lived through it all.',
      'Your authority comes from having tried so much and learned what works and what doesn\'t.'
    ],
    patterns: [
      'Life moving through three distinct phases',
      'Learning through trial and error throughout',
      'Many experiments, relationships, and directions tried',
      'Wisdom built from extensive direct experience',
      'Role model energy earned through lived experimentation'
    ],
    challenge: 'The challenge is the sheer volume of experimentation—especially in the first phase—and trusting that it all contributes to eventual wisdom.',
    reflection: 'What has your experimentation taught you that only direct experience could? How has this shaped your perspective?'
  }
};

// Incarnation Cross Stories (generic by angle, can be expanded)
const CROSS_STORIES: { [key: string]: MechanicStory } = {
  'Right Angle': {
    explanation: [
      'A Right Angle Cross indicates a personal destiny focused on your own journey. Your life purpose unfolds through personal growth and self-discovery rather than through others.',
      'This doesn\'t mean you won\'t impact others—you will. But your primary curriculum is internal. You\'re here to work through your own karma.',
      'The specific gates of your cross describe the themes of this personal journey.'
    ],
    patterns: [
      'Life lessons that are primarily internal and personal',
      'Growth that happens through your own journey',
      'Impact on others as a byproduct rather than main focus',
      'Karma worked through in this lifetime',
      'Themes that may seem self-centered but are meant to be'
    ],
    challenge: 'The challenge is thinking you should be more focused on others, or judging your personal journey as selfish.',
    reflection: 'What themes keep appearing in your personal life? How might these be the curriculum you\'re here to work through?'
  },
  'Left Angle': {
    explanation: [
      'A Left Angle Cross indicates a transpersonal destiny woven into the lives of others. Your life purpose unfolds through relationships, encounters, and the karma you share with others.',
      'This doesn\'t mean you lose yourself in others—your journey is your own. But it\'s inherently connected to others\' journeys in ways that may only make sense in retrospect.',
      'The specific gates describe how you\'re designed to impact and be impacted by others.'
    ],
    patterns: [
      'Life shaped significantly by key relationships and meetings',
      'Purpose that unfolds through connection with others',
      'Karma that\'s transpersonal—involving others\' journeys',
      'Encounters that prove meaningful only later',
      'A sense that your path is intertwined with others\''
    ],
    challenge: 'The challenge is either losing yourself in others\' paths or trying to control the transpersonal unfolding.',
    reflection: 'Which relationships have most shaped your path? How might encounters you haven\'t understood yet be part of your purpose?'
  },
  'Juxtaposition': {
    explanation: [
      'A Juxtaposition Cross is rare—indicating a fixed, geometric destiny with a specific role to play. Your life purpose is highly focused and doesn\'t have the flexibility of other crosses.',
      'This can feel limiting or liberating depending on your perspective. You\'re here for a very specific reason, and your life will keep steering you toward it.',
      'The specific gates describe this fixed role with great precision.'
    ],
    patterns: [
      'A life that keeps returning to the same themes',
      'Less flexibility in direction than others seem to have',
      'A sense of fixed purpose or destiny',
      'Encounters and experiences that feel "meant to be"',
      'A role that becomes clearer over time'
    ],
    challenge: 'The challenge is fighting against the fixedness of your path, or not recognizing the specific role you\'re here to play.',
    reflection: 'What themes keep pulling you back no matter how much you try to move away? What might your fixed role actually be?'
  }
};

// Helper to get cross angle from cross name
const getCrossAngle = (crossName: string): string => {
  if (crossName?.toLowerCase().includes('right angle')) return 'Right Angle';
  if (crossName?.toLowerCase().includes('left angle')) return 'Left Angle';
  if (crossName?.toLowerCase().includes('juxtaposition')) return 'Juxtaposition';
  return 'Right Angle'; // default fallback
};

interface HumanDesignSection {
  label: string;
  body: string;
}

// Gene Keys sequence position
interface GeneKeyPosition {
  gate: number;
  line: number;
  source_planet: string;
  source_chart: 'personality' | 'design';
  // Optional UI-layer fields (not from compute)
  theme_label?: string;
  reflection_prompt?: string;
}

// Gene Keys data structure
interface GeneKeysData {
  gene_keys_version: string;
  purpose_arc: {
    lifes_work: GeneKeyPosition;
    evolution: GeneKeyPosition;
    radiance: GeneKeyPosition;
    purpose: GeneKeyPosition;
  };
  love_arc: {
    attraction: GeneKeyPosition;
    iq: GeneKeyPosition;
    eq: GeneKeyPosition;
    sq: GeneKeyPosition;
    core_wound: GeneKeyPosition;
  };
  prosperity_arc: {
    brand: GeneKeyPosition;
    culture: GeneKeyPosition;
    vocation: GeneKeyPosition;
    pearl: GeneKeyPosition;
  };
}

interface IncarnationCrossStructured {
  cross_name: string;
  cross_family: string;
  angle: string;
  angle_full: string;
  variant: number;
  gate_quartet: {
    personality_sun: number;
    personality_earth: number;
    design_sun: number;
    design_earth: number;
    display: string;
  };
  themes: string[];
  orientation_flavor: string;
}

interface HumanDesignData {
  title: string;
  sections: HumanDesignSection[];
  mirror_prompt: string;
  core_mechanics?: {
    type: string;
    strategy: string;
    authority: string;
    profile?: string;
    definition?: string;
    incarnation_cross?: string;
    incarnation_cross_gates?: string;
  };
  // MASTER LEVEL DATA from enhanced mechanics endpoint
  channels?: Array<{
    gates?: string;
    name?: string;
    circuit?: string;
    centers?: string[];
  }>;
  defined_centers?: string[];
  undefined_centers?: string[];
  conscious_gates?: number[];
  unconscious_gates?: number[];
  personality_sun?: number | { gate: number; line: number };
  personality_earth?: number | { gate: number; line: number };
  design_sun?: number | { gate: number; line: number };
  design_earth?: number | { gate: number; line: number };
  variables?: {
    environment?: string;
    cognition?: string;
    determination?: string;
    motivation?: string;
    transference?: string;
    perspective?: string;
    view?: string;
  } | null;
  // Structured Incarnation Cross (deterministic)
  incarnation_cross_structured?: IncarnationCrossStructured | null;
  // Gene Keys sequences (deterministic compute)
  gene_keys?: GeneKeysData | null;
  date?: string;
  // Version fields from backend (frozen compute)
  computation_version?: string;
  astronomy_version?: string;
  human_design_version?: string;
  // Debug fields from API
  debug_stamp?: {
    fallback_used?: boolean;
    source?: string;
    timestamp?: string;
    cached?: boolean;
  };
  // Keystone explanation for Deep Dive tab
  keystone_explanation?: {
    keystone_pattern_id: string;
    keystone_label: string;
    keystone_sequence: string[];
    lens_role: string;
    lens_explanation_title: string;
    lens_explanation_body: string;
    supports_keystone: boolean;
  } | null;
}

interface Props {
  userId: string;
  onOpenChat: (initialMessage?: string) => void;
}

type TabType = 'summary' | 'at_a_glance' | 'deep_dive' | 'today';

export default function HumanDesignLensView({ userId, onOpenChat }: Props) {
  // Theme support
  const { theme, isDark } = useTheme();
  
  // Forum context for bidirectional integration
  const { isInForumContext, forumId, forumName, setPrefilledSource } = useForumContext();
  const router = useRouter();
  
  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [data, setData] = useState<HumanDesignData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  
  // Accordion states for Structure tab
  const [expandedCenters, setExpandedCenters] = useState<string[]>([]);
  const [gatesExpanded, setGatesExpanded] = useState(false);
  const [channelsExpanded, setChannelsExpanded] = useState(false);
  
  // Centers definition data for bodygraph highlighting
  const [centersDefinition, setCentersDefinition] = useState<Record<string, boolean>>({});
  
  // Data for Deep Dive tab - centers, gates, sequences
  const [centersData, setCentersData] = useState<any>(null);
  const [gatesData, setGatesData] = useState<any>(null);
  const [activationSequence, setActivationSequence] = useState<any>(null);
  const [venusSequence, setVenusSequence] = useState<any>(null);
  const [pearlSequence, setPearlSequence] = useState<any>(null);
  
  // Mechanic detail modal state
  const [activeMechanicDetail, setActiveMechanicDetail] = useState<string | null>(null);
  
  // Ref for CentersView to open a specific center
  const centersViewRef = useRef<CentersViewHandle>(null);
  
  // Gene Keys expansion state
  const [expandedArc, setExpandedArc] = useState<string | null>(null);
  
  // Sequence tab state for Deep Dive
  const [activeSequenceTab, setActiveSequenceTab] = useState<'core' | 'relationship' | 'work'>('core');
  
  // Accordion state for Core Mechanics in Deep Dive (collapsed by default, one at a time)
  const [expandedMechanic, setExpandedMechanic] = useState<string | null>(null);
  
  // Parent accordion states for Centers and Gates (collapsed by default)
  const [centersAccordionExpanded, setCentersAccordionExpanded] = useState(false);
  const [gatesAccordionExpanded, setGatesAccordionExpanded] = useState(false);
  
  // Deep Dive Mode toggle: 'explore' (cards) or 'reading' (narrative)
  const [deepDiveMode, setDeepDiveMode] = useState<'explore' | 'reading'>('explore');
  
  // Reflection modal state
  const [showReflectionModal, setShowReflectionModal] = useState(false);
  const [reflectionSource, setReflectionSource] = useState<ReflectionSource | null>(null);
  const [reflectionPrompt, setReflectionPrompt] = useState<string>('');
  
  // Transit signals for Today tab
  const [transitSignals, setTransitSignals] = useState<any>(null);
  const [transitLoading, setTransitLoading] = useState(false);
  
  // Field signals for Today tab (macro astrological context)
  const [fieldSignals, setFieldSignals] = useState<any>(null);
  const [fieldLoading, setFieldLoading] = useState(false);
  
  // Debug: track raw API response length
  const [rawDataLength, setRawDataLength] = useState<number>(0);
  
  // Track mount count for debugging
  const mountCount = useRef(0);

  // Load transit signals when Today tab is active
  useEffect(() => {
    if (activeTab === 'today' && userId) {
      loadTransitSignals();
      loadFieldSignals();
    }
  }, [activeTab, userId]);

  const loadTransitSignals = async () => {
    try {
      setTransitLoading(true);
      const response = await api.get(`/human-design/transit-signals/${userId}`);
      setTransitSignals(response.data);
    } catch (error) {
      console.error('[HD] Failed to load transit signals:', error);
    } finally {
      setTransitLoading(false);
    }
  };

  const loadFieldSignals = async () => {
    try {
      setFieldLoading(true);
      const response = await api.get(`/human-design/field-signals/${userId}`);
      setFieldSignals(response.data);
    } catch (error) {
      console.error('[HD] Failed to load field signals:', error);
    } finally {
      setFieldLoading(false);
    }
  };

  // Load data when tab or user changes
  useEffect(() => {
    loadTabData(activeTab);
  }, [activeTab, userId]);

  // Load centers definition for bodygraph highlighting when Deep Dive tab is active
  useEffect(() => {
    if (activeTab === 'deep_dive') {
      loadCentersDefinition();
      loadDeepDiveData();
    }
  }, [activeTab, userId]);

  const loadCentersDefinition = async () => {
    try {
      const response = await api.get(`/human-design/centers/${userId}`);
      const centersDef: Record<string, boolean> = {};
      response.data.centers?.forEach((c: any) => {
        // Map center_name to boolean defined status
        const name = c.center_name || c.name;
        if (name) {
          centersDef[name.toLowerCase()] = c.defined === true;
        }
      });
      
      setCentersDefinition(centersDef);
      setCentersData(response.data); // Store full centers data for Deep Dive
    } catch (err) {
      console.error('Failed to load centers definition:', err);
    }
  };

  // Load all Deep Dive data (gates, sequences)
  const loadDeepDiveData = async () => {
    try {
      // Load gates data
      const gatesResponse = await api.get(`/human-design/gates/${userId}`);
      setGatesData(gatesResponse.data);
    } catch (err) {
      console.error('Failed to load gates:', err);
    }

    try {
      // Load Gene Keys profile with all sequences
      const sequencesResponse = await api.get(`/gene-keys/profile/${userId}`);
      if (sequencesResponse.data) {
        setActivationSequence(sequencesResponse.data.activation_sequence || null);
        setVenusSequence(sequencesResponse.data.venus_sequence || null);
        setPearlSequence(sequencesResponse.data.pearl_sequence || null);
      }
    } catch (err) {
      console.error('Failed to load sequences:', err);
    }
  };

  // Handle bodygraph center tap - opens Centers accordion and expands specific center
  const handleBodygraphCenterTap = (centerName: string) => {
    // The CentersView component needs to expose a method to open a specific center
    // For now, we'll use a callback pattern - this will be connected via props
    if (centersViewRef.current?.openCenter) {
      centersViewRef.current.openCenter(centerName);
    }
  };

  // Handle "Reflect in Forum" from a specific HD insight
  const handleReflectInForum = (insightId: string, insightName: string, insightValue: string) => {
    if (!isInForumContext || !forumId) return;
    
    // Get guidance content based on insight type
    const getInsightGuidance = (id: string, value: string) => {
      const typeGuidance: Record<string, { theme: string; strength: string; challenge: string; guidance: string }> = {
        'type': {
          theme: TYPE_ENERGY_PATTERNS[value] || 'Your unique energy pattern shapes how you engage with the world.',
          strength: TYPE_MANIFESTATIONS[value]?.work || 'Unique gifts that emerge when you are aligned.',
          challenge: TYPE_MANIFESTATIONS[value]?.energy?.split(';')[1]?.trim() || 'Patterns that arise when out of alignment.',
          guidance: STRATEGY_TRANSLATIONS[data?.core_mechanics?.strategy || ''] || 'Follow your natural rhythm.',
        },
        'strategy': {
          theme: STRATEGY_TRANSLATIONS[value] || 'Your natural way of engaging with life.',
          strength: 'Following this approach brings flow and reduces resistance.',
          challenge: 'Acting against this strategy creates friction and frustration.',
          guidance: 'Notice when you naturally follow this pattern vs. when you override it.',
        },
        'authority': {
          theme: AUTHORITY_TRANSLATIONS[value]?.expanded || 'Your unique way of arriving at clarity.',
          strength: 'Reliable clarity when you follow your process.',
          challenge: 'Not trusting your natural decision-making process.',
          guidance: AUTHORITY_TRANSLATIONS[value]?.short || 'Honor your unique clarity process.',
        },
        'profile': {
          theme: 'Your life theme and way of learning.',
          strength: 'Embracing your profile brings natural fulfillment.',
          challenge: 'Resisting it creates friction with your purpose.',
          guidance: 'Consider how this profile shapes your relationships and work.',
        },
        'incarnation_cross': {
          theme: 'Your life purpose and contribution.',
          strength: 'Living aligned with this theme brings deep satisfaction.',
          challenge: 'Ignoring it leads to a sense of meaninglessness.',
          guidance: 'Reflect on how this purpose shows up in your current life chapter.',
        },
      };
      return typeGuidance[id] || {
        theme: 'An aspect of your Human Design.',
        strength: 'Gifts that emerge when aligned.',
        challenge: 'Patterns when out of alignment.',
        guidance: 'Honor your unique design.',
      };
    };

    const guidance = getInsightGuidance(insightId, insightValue);
    
    // Set the prefilled source
    const source: PrefilledSource = {
      sourceType: 'mirror',
      lens: 'human-design',
      insightId,
      insightName,
      insightValue,
      theme: guidance.theme,
      strength: guidance.strength,
      challenge: guidance.challenge,
      guidance: guidance.guidance,
    };
    setPrefilledSource(source);
    
    // Navigate to exercise with prefilled flag
    router.push(`/forums/exercise?forumId=${forumId}&prefilled=true`);
  };

  const loadTabData = async (tab: TabType) => {
    setIsLoading(true);
    setError(null);

    try {
      // Overview uses fast deterministic endpoint (no LLM)
      // Today uses LLM-generated endpoint
      // Deep Dive uses deep-dive for mechanics data
      const endpoint = tab === 'today' 
        ? `/human-design/today/${userId}`
        : (tab === 'deep_dive')
        ? `/human-design/deep-dive/${userId}`
        : `/human-design/mechanics/${userId}`;  // Fast endpoint for Overview

      const response = await api.get(endpoint);
      setData(response.data);
      
      // Debug: Calculate raw data length for comparison
      if (isDebugEnabled() && response.data?.sections) {
        const totalChars = response.data.sections.reduce(
          (sum: number, s: HumanDesignSection) => sum + (s.body?.length || 0), 
          0
        );
        setRawDataLength(totalChars);
        console.log(`[DEBUG_MIRROR] HumanDesign ${tab}: API returned ${totalChars} chars across ${response.data.sections.length} sections`);
      }
    } catch (err: any) {
      console.error(`Human Design ${tab} error:`, err);
      setError('Unable to load this view right now.');
    } finally {
      setIsLoading(false);
    }
  };

  // Tab blurbs for each tab
  const TAB_BLURBS: Record<TabType, { title: string; blurb: string }> = {
    overview: {
      title: "Your Core Pattern",
      blurb: "How your energy, decisions, and interactions naturally operate.",
    },
    today: {
      title: "Your Design Today",
      blurb: "Real-time signals from your chart and the current transits.",
    },
    deep_dive: {
      title: "Deeper Mechanics",
      blurb: "The structures and patterns that shape your experience.",
    },
  };

  const renderTabs = () => (
    <View style={[styles.tabSection, { borderBottomColor: theme.border }]}>
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'summary' && styles.activeTab]}
          onPress={() => setActiveTab('summary')}
        >
          <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'summary' && { color: theme.text }]}>
            Summary
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'at_a_glance' && styles.activeTab]}
          onPress={() => setActiveTab('at_a_glance')}
        >
          <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'at_a_glance' && { color: theme.text }]}>
            At a Glance
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'deep_dive' && styles.activeTab]}
          onPress={() => setActiveTab('deep_dive')}
        >
          <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'deep_dive' && { color: theme.text }]}>
            Deep Dive
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'today' && styles.activeTab]}
          onPress={() => setActiveTab('today')}
        >
          <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'today' && { color: theme.text }]}>
            Today
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderTabBlurb = () => {
    const content = TAB_BLURBS[activeTab];
    return (
      <View style={styles.tabBlurbContainer}>
        <Text style={[styles.tabBlurbTitle, { color: theme.text }]}>{content.title}</Text>
        <Text style={[styles.tabBlurbText, { color: theme.textTertiary }]}>{content.blurb}</Text>
      </View>
    );
  };

  // Default prompts per tab for Ask CTA
  const getDefaultPromptForTab = (tab: TabType): string => {
    switch (tab) {
      case 'summary':
        return "What stands out most in my Human Design?";
      case 'at_a_glance':
        return "Tell me more about my design structure.";
      case 'deep_dive':
        return "What deeper Human Design pattern matters most for me to understand?";
      case 'today':
        return "What is my design asking me to pay attention to right now?";
      default:
        return "Tell me about my Human Design.";
    }
  };

  // Suggested questions for each tab
  const getSuggestedQuestions = (tab: TabType): string[] => {
    switch (tab) {
      case 'summary':
        return [
          "How should I approach major decisions?",
          "Why do I feel drained in certain situations?",
          "What's my natural way of engaging with others?",
        ];
      case 'at_a_glance':
        return [
          "What do my defined centers tell me?",
          "How do I use my authority correctly?",
          "What does my profile mean?",
        ];
      case 'deep_dive':
        return [
          "What does my profile reveal about how I learn?",
          "How do my centers work together?",
          "What patterns show up in my relationships?",
        ];
      case 'today':
        return [
          "What energy is most active for me today?",
          "Where should I be patient right now?",
          "What am I being asked to notice?",
        ];
      default:
        return [];
    }
  };

  // Unified Ask Section (matches BaZi pattern)
  const renderUnifiedAskSection = (tab: TabType) => {
    const suggestedQuestions = getSuggestedQuestions(tab);
    
    return (
      <View style={[styles.unifiedAskSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        {/* Primary CTA - Open-ended Ask */}
        <TouchableOpacity
          style={[styles.primaryAskButton, { backgroundColor: theme.accent }]}
          onPress={() => onOpenChat()}
          activeOpacity={0.8}
        >
          <Ionicons name="chatbubble-outline" size={20} color="#FFFFFF" />
          <Text style={styles.primaryAskButtonText}>Ask About This Lens</Text>
        </TouchableOpacity>
        
        <Text style={[styles.primaryAskSubtext, { color: theme.textTertiary }]}>
          Ask anything about your design, your decisions, or how this shows up in your life.
        </Text>
        
        {/* Suggested Questions - Optional Starters */}
        {suggestedQuestions.length > 0 && (
          <View style={styles.suggestedQuestionsSection}>
            <Text style={[styles.suggestedQuestionsLabel, { color: theme.textTertiary }]}>
              SUGGESTED QUESTIONS
            </Text>
            <View style={styles.suggestedQuestionsList}>
              {suggestedQuestions.map((question, idx) => (
                <TouchableOpacity
                  key={idx}
                  style={[styles.suggestedQuestionChip, { backgroundColor: theme.background, borderColor: theme.border }]}
                  onPress={() => onOpenChat(question)}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.suggestedQuestionText, { color: theme.text }]} numberOfLines={2}>
                    {question}
                  </Text>
                  <Ionicons name="arrow-forward" size={14} color={theme.textTertiary} style={{ marginLeft: 8 }} />
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}
      </View>
    );
  };

  // Removed separate renderTabDescription - now integrated into renderTabs

  // Strategy content by type
  const STRATEGY_STORIES: { [key: string]: MechanicStory } = {
    'Generator': {
      explanation: [
        'Your strategy is to Wait to Respond. This doesn\'t mean being passive—it means allowing life to bring opportunities to you rather than initiating from mental ideas.',
        'Response happens in your body, not your mind. Something in the world catches your attention, and your sacral center responds with excitement or resistance.',
        'When you wait for something to respond to, your decisions are aligned with your life force. When you initiate without response, you often hit resistance and frustration.'
      ],
      patterns: [
        'Noticing what makes your gut respond with energy',
        'Waiting for opportunities rather than chasing them',
        'Responding to questions, offers, and invitations',
        'Finding your way by trial and response rather than planning',
        'Energy that sustains when you\'ve responded correctly'
      ],
      challenge: 'The biggest challenge is the cultural conditioning to initiate. You may feel lazy or passive waiting to respond, but forcing initiation leads to frustration.',
      reflection: 'When was the last time you waited for life to bring you something to respond to? What happened when you did?'
    },
    'Manifesting Generator': {
      explanation: [
        'Your strategy is to Wait to Respond, then Inform before acting. Like Generators, you wait for something to respond to. Unlike pure Generators, once you respond, you can move fast.',
        'The responding keeps you from wasting energy on wrong directions. The informing keeps others from resisting your sudden movements.',
        'You may need to skip steps and pivot quickly. This isn\'t inconsistency—it\'s efficiency. Trust your response, then move.'
      ],
      patterns: [
        'Waiting for genuine response before committing',
        'Moving quickly once something resonates',
        'Informing others before sudden changes in direction',
        'Following energy even when it seems non-linear',
        'Pivoting without guilt when response shifts'
      ],
      challenge: 'The challenge is either forcing initiation (Generator frustration) or not informing before acting (Manifestor resistance). Both strategies matter.',
      reflection: 'When you last moved fast on something, had you truly responded to it first? Did you inform those affected by your movement?'
    },
    'Projector': {
      explanation: [
        'Your strategy is to Wait for the Invitation. This doesn\'t mean waiting passively—it means recognizing when your guidance is truly wanted.',
        'Invitations come in many forms: being asked your opinion, being offered a role, being recognized for your insight. When invited, your guidance lands. When uninvited, it doesn\'t.',
        'This waiting isn\'t about big life invitations only. It\'s about daily interactions—noticing when you\'re truly asked versus when you\'re imposing.'
      ],
      patterns: [
        'Waiting until you\'re genuinely asked before advising',
        'Recognizing formal and informal invitations',
        'Guidance that lands when properly invited',
        'Bitterness when offering unsolicited input',
        'Success through recognition rather than self-promotion'
      ],
      challenge: 'The biggest challenge is seeing so clearly what others need and not being able to share it until invited. Patience and strategic positioning help.',
      reflection: 'Where have you been offering guidance without being invited? What might happen if you waited to be asked?'
    },
    'Manifestor': {
      explanation: [
        'Your strategy is to Inform before you act. This isn\'t asking permission—it\'s letting people know what you\'re about to do so they can adjust.',
        'Manifestors have a powerful impact on others. When you act without informing, people feel blindsided and resist. When you inform, resistance dissolves.',
        'Informing creates peace—your signature. Not informing creates anger—both from others and eventually from you.'
      ],
      patterns: [
        'Letting others know before taking significant action',
        'Creating space for your impulses by reducing resistance',
        'Peace that comes from proactive communication',
        'Anger when feeling controlled or blocked',
        'Freedom through responsibility rather than isolation'
      ],
      challenge: 'The biggest challenge is the impulse to just act without informing. It feels slower, but it actually speeds things up by removing resistance.',
      reflection: 'What significant action are you about to take? Who needs to be informed before you move?'
    },
    'Reflector': {
      explanation: [
        'Your strategy is to Wait a Lunar Cycle for major decisions. With all centers undefined, you sample the energy of everyone around you.',
        'In 28 days, the moon moves through all 64 gates, giving you the opportunity to experience a decision from every possible energetic perspective.',
        'This isn\'t indecision—it\'s thorough evaluation. You see what others miss because you take in everything.'
      ],
      patterns: [
        'Allowing 28 days for major life decisions',
        'Experiencing different perspectives over the lunar cycle',
        'Wisdom from thorough energetic sampling',
        'Disappointment when rushing or when environments don\'t match potential',
        'Clarity that emerges from patience'
      ],
      challenge: 'The biggest challenge is the pressure to decide quickly. Others don\'t understand your process, and you may doubt yourself for needing more time.',
      reflection: 'What decision are you currently facing? How might your knowing change over the next 28 days?'
    }
  };

  const getStrategyContent = (type: string | undefined): MechanicStory => {
    return STRATEGY_STORIES[type || 'Generator'] || STRATEGY_STORIES['Generator'];
  };

  const getCentersContent = (): MechanicStory => {
    const definedCount = Object.values(centersDefinition).filter(v => v === true).length;
    const undefinedCount = 9 - definedCount;
    const defType = data?.core_mechanics?.definition || 'Unknown';
    
    return {
      explanation: [
        `You have ${definedCount} defined centers and ${undefinedCount} undefined centers. Your definition type is "${defType}."`,
        'Defined centers (colored in your chart) operate consistently—this is energy you can rely on and that others experience from you. These are your fixed traits.',
        'Undefined centers (white in your chart) are where you take in and amplify the energy of others. These are your areas of wisdom through experience, but also where you can be conditioned.'
      ],
      patterns: [
        `${definedCount} centers operating with consistent energy`,
        `${undefinedCount} centers open to external influence`,
        'Wisdom gained through undefined centers over time',
        'Conditioning and amplification in open centers',
        'Reliability and consistency from defined centers'
      ],
      challenge: 'The biggest challenge is mistaking the amplified energy of undefined centers for your own. What feels intense may be what you\'re taking in from others.',
      reflection: 'Which of your undefined centers do you notice most strongly? Where might you be amplifying someone else\'s energy?'
    };
  };

  // State for which Deep Dive accordion is expanded
  const [expandedDeepDive, setExpandedDeepDive] = useState<string | null>(null);

  // NEW: Render Mirror Language card (Recognition, Tension, Real-life Moments, Truth Shift, Try This Instead)
  const renderMirrorCard = (key: string, mirrorCard: MirrorCard | null, sourceValue: string) => {
    const isExpanded = expandedDeepDive === key;
    
    if (!mirrorCard) return null;
    
    return (
      <View key={key} style={[styles.deepDiveAccordion, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Pressable
          style={({ pressed }) => [
            styles.deepDiveHeader,
            pressed && { opacity: 0.7 }
          ]}
          onPress={() => {
            setExpandedDeepDive(isExpanded ? null : key);
          }}
        >
          <View style={styles.deepDiveHeaderText}>
            <Text style={[styles.deepDiveTitle, { color: theme.text }]}>{mirrorCard.title}</Text>
            <Text style={[styles.deepDiveSubtitle, { color: theme.textTertiary }]}>{mirrorCard.subtitle}</Text>
          </View>
          <Text style={[styles.deepDiveChevron, { color: theme.textTertiary }]}>
            {isExpanded ? '▲' : '▼'}
          </Text>
        </Pressable>
        
        {isExpanded && (
          <View style={styles.deepDiveContent}>
            {/* RECOGNITION - The opening hook */}
            <Text style={[styles.mirrorRecognition, { color: theme.text }]}>
              {mirrorCard.recognition}
            </Text>
            
            {/* TENSION - The inner conflict */}
            <View style={[styles.mirrorSection, { borderTopColor: theme.border }]}>
              <Text style={[styles.mirrorSectionLabel, { color: theme.accent }]}>TENSION</Text>
              <Text style={[styles.mirrorSectionText, { color: theme.text }]}>
                {mirrorCard.tension}
              </Text>
            </View>
            
            {/* REAL LIFE MOMENTS */}
            <View style={styles.mirrorSection}>
              <Text style={[styles.mirrorSectionLabel, { color: theme.accent }]}>REAL LIFE MOMENTS</Text>
              {mirrorCard.realLifeMoments.map((moment, i) => (
                <View key={`moment-${i}`} style={styles.mirrorBulletRow}>
                  <Text style={[styles.mirrorBullet, { color: theme.textTertiary }]}>•</Text>
                  <Text style={[styles.mirrorBulletText, { color: theme.textSecondary }]}>{moment}</Text>
                </View>
              ))}
            </View>
            
            {/* TRUTH SHIFT - The reframe */}
            <View style={[styles.mirrorTruthShift, { backgroundColor: theme.background, borderLeftColor: theme.accent }]}>
              <Text style={[styles.mirrorSectionLabel, { color: theme.accent }]}>TRUTH SHIFT</Text>
              <Text style={[styles.mirrorTruthShiftText, { color: theme.text }]}>
                {mirrorCard.truthShift}
              </Text>
            </View>
            
            {/* TRY THIS INSTEAD - The practical tip */}
            <View style={[styles.mirrorTryThis, { borderColor: theme.border }]}>
              <Text style={[styles.mirrorSectionLabel, { color: theme.success || '#4CAF50' }]}>TRY THIS INSTEAD</Text>
              <Text style={[styles.mirrorTryThisText, { color: theme.text }]}>
                {mirrorCard.tryThisInstead}
              </Text>
            </View>

            {/* Reflect Button */}
            <InlineReflectButton
              source={{
                lens: 'human_design',
                type: key,
                name: mirrorCard.title,
                value: sourceValue,
                id: `hd_${key}`,
              }}
              prompt={mirrorCard.truthShift}
            />
          </View>
        )}
      </View>
    );
  };

  // NEW: Render Core Mechanics using CollapsibleCard with Mirror Language
  const renderMechanicCollapsibleCard = (
    key: string, 
    mirrorCard: MirrorCard | null, 
    sourceValue: string,
    defaultOpen: boolean = false
  ) => {
    if (!mirrorCard) return null;
    
    return (
      <CollapsibleCard
        key={key}
        title={mirrorCard.title}
        subtitle={mirrorCard.subtitle}
        defaultOpen={defaultOpen}
        priority={defaultOpen ? 'high' : 'low'}
        lazyRender={true}
      >
        <View style={{ gap: 16 }}>
          {/* RECOGNITION - The opening hook */}
          <Text style={[styles.mirrorRecognition, { color: theme.text }]}>
            {mirrorCard.recognition}
          </Text>
          
          {/* TENSION - The inner conflict */}
          <View>
            <Text style={[styles.mirrorSectionLabel, { color: theme.warning || '#FF9800' }]}>TENSION</Text>
            <Text style={[styles.mirrorSectionText, { color: theme.text }]}>
              {mirrorCard.tension}
            </Text>
          </View>
          
          {/* REAL LIFE MOMENTS */}
          <View>
            <Text style={[styles.mirrorSectionLabel, { color: theme.textTertiary }]}>REAL LIFE MOMENTS</Text>
            {mirrorCard.realLifeMoments.map((moment, i) => (
              <View key={`moment-${i}`} style={styles.mirrorBulletRow}>
                <Text style={[styles.mirrorBullet, { color: theme.textTertiary }]}>•</Text>
                <Text style={[styles.mirrorBulletText, { color: theme.textSecondary }]}>{moment}</Text>
              </View>
            ))}
          </View>
          
          {/* TRUTH SHIFT - The reframe */}
          <View style={[styles.mirrorTruthShift, { backgroundColor: theme.background, borderLeftColor: theme.accent }]}>
            <Text style={[styles.mirrorSectionLabel, { color: theme.accent }]}>TRUTH SHIFT</Text>
            <Text style={[styles.mirrorTruthShiftText, { color: theme.text }]}>
              {mirrorCard.truthShift}
            </Text>
          </View>
          
          {/* TRY THIS INSTEAD - The practical tip */}
          <View style={[styles.mirrorTryThis, { borderColor: theme.border }]}>
            <Text style={[styles.mirrorSectionLabel, { color: theme.success || '#4CAF50' }]}>TRY THIS INSTEAD</Text>
            <Text style={[styles.mirrorTryThisText, { color: theme.text }]}>
              {mirrorCard.tryThisInstead}
            </Text>
          </View>

          {/* Reflect Button */}
          <InlineReflectButton
            source={{
              lens: 'human_design',
              type: key,
              name: mirrorCard.title,
              value: sourceValue,
              id: `hd_${key}`,
            }}
            prompt={mirrorCard.truthShift}
          />
        </View>
      </CollapsibleCard>
    );
  };

  // NEW: Render Pattern Thread - The unified narrative at the top
  const renderPatternThread = (patternThread: PatternThread) => {
    return (
      <View style={[styles.patternThreadContainer, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.patternThreadTitle, { color: theme.text }]}>
          {patternThread.title}
        </Text>
        <Text style={[styles.patternThreadBody, { color: theme.textSecondary }]}>
          {patternThread.body}
        </Text>
        <View style={[styles.patternThreadLoop, { backgroundColor: theme.background, borderLeftColor: theme.accent }]}>
          <Text style={[styles.patternThreadLoopText, { color: theme.textTertiary }]}>
            {patternThread.coreLoop}
          </Text>
        </View>
      </View>
    );
  };

  // NEW: Render Pattern State - Real-time positioning ("Where You Are Right Now")
  const renderPatternState = (patternState: PatternState) => {
    return (
      <View style={[styles.patternStateContainer, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.patternStateTitle, { color: theme.textTertiary }]}>
          WHERE YOU ARE RIGHT NOW
        </Text>
        
        {/* Current Phase - Primary text */}
        <Text style={[styles.patternStateBody, { color: theme.text }]}>
          {patternState.currentPhase}
        </Text>
        
        {/* What This Leads To - Slightly dimmed */}
        <Text style={[styles.patternStateSub, { color: theme.textSecondary }]}>
          {patternState.whatThisLeadsTo}
        </Text>
        
        {/* Shift Available - Accent highlight */}
        <View style={[styles.patternStateShiftContainer, { backgroundColor: theme.background, borderLeftColor: theme.success || '#4CAF50' }]}>
          <Text style={[styles.patternStateShift, { color: theme.success || '#4CAF50' }]}>
            {patternState.shiftAvailable}
          </Text>
        </View>
      </View>
    );
  };

  // NEW: Render Core Mechanics with Cross-Link support
  const renderMechanicCollapsibleCardWithCrossLink = (
    key: string, 
    mirrorCard: MirrorCard | null, 
    sourceValue: string,
    defaultOpen: boolean = false,
    crossLink: string | null
  ) => {
    if (!mirrorCard) return null;
    
    return (
      <CollapsibleCard
        key={key}
        title={mirrorCard.title}
        subtitle={mirrorCard.subtitle}
        defaultOpen={defaultOpen}
        priority={defaultOpen ? 'high' : 'low'}
        lazyRender={true}
      >
        <View style={{ gap: 16 }}>
          {/* RECOGNITION - The opening hook */}
          <Text style={[styles.mirrorRecognition, { color: theme.text }]}>
            {mirrorCard.recognition}
          </Text>
          
          {/* TENSION - The inner conflict */}
          <View>
            <Text style={[styles.mirrorSectionLabel, { color: theme.warning || '#FF9800' }]}>TENSION</Text>
            <Text style={[styles.mirrorSectionText, { color: theme.text }]}>
              {mirrorCard.tension}
            </Text>
          </View>
          
          {/* REAL LIFE MOMENTS */}
          <View>
            <Text style={[styles.mirrorSectionLabel, { color: theme.textTertiary }]}>REAL LIFE MOMENTS</Text>
            {mirrorCard.realLifeMoments.map((moment, i) => (
              <View key={`moment-${i}`} style={styles.mirrorBulletRow}>
                <Text style={[styles.mirrorBullet, { color: theme.textTertiary }]}>•</Text>
                <Text style={[styles.mirrorBulletText, { color: theme.textSecondary }]}>{moment}</Text>
              </View>
            ))}
          </View>
          
          {/* TRUTH SHIFT - The reframe */}
          <View style={[styles.mirrorTruthShift, { backgroundColor: theme.background, borderLeftColor: theme.accent }]}>
            <Text style={[styles.mirrorSectionLabel, { color: theme.accent }]}>TRUTH SHIFT</Text>
            <Text style={[styles.mirrorTruthShiftText, { color: theme.text }]}>
              {mirrorCard.truthShift}
            </Text>
          </View>
          
          {/* CROSS-LINK - Subtle connection (before Try This Instead) */}
          {crossLink && (
            <Text style={[styles.crossLinkText, { color: theme.textTertiary }]}>
              {crossLink}
            </Text>
          )}
          
          {/* TRY THIS INSTEAD - The practical tip */}
          <View style={[styles.mirrorTryThis, { borderColor: theme.border }]}>
            <Text style={[styles.mirrorSectionLabel, { color: theme.success || '#4CAF50' }]}>TRY THIS INSTEAD</Text>
            <Text style={[styles.mirrorTryThisText, { color: theme.text }]}>
              {mirrorCard.tryThisInstead}
            </Text>
          </View>

          {/* Reflect Button */}
          <InlineReflectButton
            source={{
              lens: 'human_design',
              type: key,
              name: mirrorCard.title,
              value: sourceValue,
              id: `hd_${key}`,
            }}
            prompt={mirrorCard.truthShift}
          />
        </View>
      </CollapsibleCard>
    );
  };

  // NEW: Render Centers Cards with Cross-Links
  const renderCentersCardsWithCrossLinks = (context: CrossLinkContext) => {
    // DEFENSIVE GUARD: Validate centers data
    if (!centersData?.centers || !Array.isArray(centersData.centers)) {
      console.log('[HD_DEBUG] Invalid centers data:', centersData);
      return null;
    }
    
    const safeCenters = Array.isArray(centersData.centers) ? centersData.centers : [];
    if (safeCenters.length === 0) {
      return null;
    }
    
    const definedCenters = safeCenters.filter((c: any) => c && c.defined);
    const undefinedCenters = safeCenters.filter((c: any) => c && !c.defined);
    
    return (
      <View style={{ gap: 8 }}>
        {/* Defined Centers */}
        {definedCenters.length > 0 && (
          <View>
            <SectionHeader title="Defined" count={definedCenters.length} icon="●" />
            {definedCenters.map((center: any, idx: number) => 
              renderCenterCardWithCrossLink(center, true, idx === 0, context)
            )}
          </View>
        )}
        
        {/* Undefined Centers */}
        {undefinedCenters.length > 0 && (
          <View>
            <SectionHeader title="Undefined" count={undefinedCenters.length} icon="○" />
            {undefinedCenters.map((center: any, idx: number) => 
              renderCenterCardWithCrossLink(center, false, false, context)
            )}
          </View>
        )}
      </View>
    );
  };

  // Helper: Render single center card with cross-link
  const renderCenterCardWithCrossLink = (center: any, isDefined: boolean, defaultOpen: boolean, context: CrossLinkContext) => {
    // DEFENSIVE GUARD: Validate center data
    if (!center) {
      console.log('[HD_DEBUG] Invalid center - null/undefined:', center);
      return null;
    }
    
    const rawCenterName = center.center || center.name || center;
    
    // DEFENSIVE GUARD: Ensure centerName is a string
    if (typeof rawCenterName !== 'string' || !rawCenterName) {
      console.log('[HD_DEBUG] Invalid center name - not a string:', rawCenterName, 'full center:', center);
      return null;
    }
    
    const centerName = rawCenterName;
    const safeCenterName = centerName.toLowerCase().replace(/\s/g, '_');
    const crossLink = getCenterCrossLink(centerName, isDefined, context);
    
    // Generate Mirror Language content for centers
    const getRecognition = (): string => {
      if (isDefined) {
        return `This is consistent energy for you—always present, always running the same way.`;
      }
      return `This isn't fixed for you. It amplifies and shifts based on who's around you.`;
    };
    
    const getTension = (): string => {
      if (isDefined) {
        return `You can't turn this off. The challenge is recognizing when this fixed way of operating doesn't serve the situation.`;
      }
      return `The trap is thinking this is your own energy. When it feels intense, you might be amplifying someone else's.`;
    };
    
    const getRealLife = (): string => {
      if (isDefined) {
        return `You probably have a consistent way of processing this energy that others notice.`;
      }
      return `You've probably felt this more strongly in certain relationships or environments.`;
    };
    
    const getTryThis = (): string => {
      if (isDefined) {
        return `Notice when your consistent way of operating creates friction. That's information.`;
      }
      return `Before reacting, pause and ask: is this mine, or am I picking it up from somewhere?`;
    };
    
    return (
      <NestedCollapsible
        key={`center-${centerName}`}
        title={`${centerName} Center`}
        subtitle={isDefined ? 'Consistent, fixed energy' : 'Open, amplifying energy'}
        defaultOpen={defaultOpen}
        status={isDefined ? 'defined' : 'undefined'}
        lazyRender={true}
      >
        <View style={{ gap: 12 }}>
          {/* Recognition */}
          <View>
            <Text style={[styles.mirrorSectionLabel, { color: theme.accent }]}>RECOGNITION</Text>
            <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
              {getRecognition()}
            </Text>
          </View>
          
          {/* Tension */}
          <View>
            <Text style={[styles.mirrorSectionLabel, { color: theme.warning || '#FF9800' }]}>TENSION</Text>
            <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
              {getTension()}
            </Text>
          </View>
          
          {/* Real Life Moments */}
          <View>
            <Text style={[styles.mirrorSectionLabel, { color: theme.textTertiary }]}>REAL LIFE MOMENTS</Text>
            <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
              {getRealLife()}
            </Text>
          </View>
          
          {/* Cross-Link (before Try This Instead) */}
          {crossLink && (
            <Text style={[styles.crossLinkText, { color: theme.textTertiary }]}>
              {crossLink}
            </Text>
          )}
          
          {/* Try This Instead */}
          <View>
            <Text style={[styles.mirrorSectionLabel, { color: theme.success || '#4CAF50' }]}>TRY THIS INSTEAD</Text>
            <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
              {getTryThis()}
            </Text>
          </View>
          
          {/* Reflect CTA */}
          <TouchableOpacity
            style={[styles.deepDiveAskCta, { borderTopColor: theme.border }]}
            onPress={() => openReflection(
              `${isDefined ? 'Defined' : 'Undefined'} ${centerName}`,
              'center',
              getCenterReflectionPrompt(centerName, isDefined),
              'deep_dive',
              `center_${safeCenterName}`,
              isDefined ? 'defined' : 'undefined'
            )}
            activeOpacity={0.7}
          >
            <Text style={[styles.deepDiveAskCtaText, { color: theme.accent }]}>Reflect on this →</Text>
          </TouchableOpacity>
        </View>
      </NestedCollapsible>
    );
  };

  // NEW: Render Gates Cards with Cross-Links
  const renderGatesCardsWithCrossLinks = (context: CrossLinkContext) => {
    // DEFENSIVE GUARD: Validate gates data
    if (!gatesData?.gates || !Array.isArray(gatesData.gates)) {
      console.log('[HD_DEBUG] Invalid gates data:', gatesData);
      return null;
    }
    
    // DEFENSIVE GUARD: Safe array spread
    const safeGates = Array.isArray(gatesData.gates) ? gatesData.gates : [];
    if (safeGates.length === 0) {
      return null;
    }
    
    // Sort gates by priority
    const sortedGates = [...safeGates].sort((a: any, b: any) => {
      const getPriority = (gate: any): number => {
        const gateNum = gate.gate_number || gate.gate;
        const pSunGate = typeof data?.personality_sun === 'object' ? data.personality_sun?.gate : data?.personality_sun;
        const dSunGate = typeof data?.design_sun === 'object' ? data.design_sun?.gate : data?.design_sun;
        
        if (gateNum === pSunGate) return 0;
        if (gateNum === dSunGate) return 1;
        const isChannelGate = data?.channels?.some((ch: any) => {
          const gatesInChannel = ch.gates?.split('-').map((g: string) => parseInt(g));
          return gatesInChannel?.includes(gateNum);
        });
        if (isChannelGate) return 2;
        return 3;
      };
      return getPriority(a) - getPriority(b);
    });
    
    const topGates = sortedGates.slice(0, 12);
    
    return (
      <View style={{ gap: 8 }}>
        {topGates.map((gate: any, idx: number) => {
          const gateNum = gate.gate_number || gate.gate;
          const gateName = gate.name || gate.gate_name || gate.theme || `Gate ${gateNum}`;
          const crossLink = getGateCrossLink(gateNum, context);
          
          const pSunGate = typeof data?.personality_sun === 'object' ? data.personality_sun?.gate : data?.personality_sun;
          const dSunGate = typeof data?.design_sun === 'object' ? data.design_sun?.gate : data?.design_sun;
          const isPriority = gateNum === pSunGate || gateNum === dSunGate;
          
          const getGateRole = (): string => {
            if (gateNum === pSunGate) return 'Personality Sun - Your conscious expression';
            if (gateNum === dSunGate) return 'Design Sun - Your unconscious drive';
            const channel = data?.channels?.find((ch: any) => {
              const gatesInChannel = ch.gates?.split('-').map((g: string) => parseInt(g));
              return gatesInChannel?.includes(gateNum);
            });
            if (channel) return `Part of ${channel.name || 'Channel'}`;
            return 'Activated energy';
          };
          
          return (
            <NestedCollapsible
              key={`gate-${gateNum}`}
              title={`Gate ${gateNum}: ${gateName}`}
              subtitle={getGateRole()}
              defaultOpen={idx < 3}
              status={isPriority ? 'active' : 'defined'}
              lazyRender={true}
            >
              {renderGateContentWithCrossLink(gate, crossLink)}
            </NestedCollapsible>
          );
        })}
      </View>
    );
  };

  // Helper: Render gate content with cross-link
  const renderGateContentWithCrossLink = (gate: any, crossLink: string | null) => {
    // DEFENSIVE GUARD: Validate gate
    if (!gate) {
      console.log('[HD_DEBUG] Invalid gate:', gate);
      return null;
    }
    
    const gateNum = gate.gate_number || gate.gate || 0;
    const gateName = gate.name || gate.gate_name || gate.theme || `Gate ${gateNum}`;
    
    // DEFENSIVE GUARD: Safely get shadow and gift
    const safeShadow = typeof gate.shadow === 'string' ? gate.shadow.toLowerCase() : '';
    const safeGift = typeof gate.gift === 'string' ? gate.gift.toLowerCase() : '';
    
    // Recognition
    const getGateRecognition = (): string => {
      if (gate.what_this_means && typeof gate.what_this_means === 'string') {
        const text = gate.what_this_means;
        const firstSentence = text.split('.')[0] + '.';
        return firstSentence.length < 120 ? firstSentence : firstSentence.slice(0, 117) + '...';
      }
      return `You keep coming back to this energy. It's part of your wiring—not something you chose.`;
    };

    // Tension
    const getGateTension = (): string => {
      if (gate.your_challenge && typeof gate.your_challenge === 'string') {
        const text = gate.your_challenge;
        const firstSentence = text.split('.')[0] + '.';
        return firstSentence.length < 120 ? firstSentence : firstSentence.slice(0, 117) + '...';
      }
      if (safeShadow) {
        return `The trap is ${safeShadow}—it shows up when you're stressed or unaware.`;
      }
      return "The challenge is staying conscious with this energy.";
    };

    // Real Life
    const getGateRealLife = (): string => {
      if (safeGift) {
        return `You tend toward ${safeGift}—people probably notice this about you.`;
      }
      return 'In real life, this shows up in how you handle certain situations.';
    };

    // Try This Instead
    const getGateTryThis = (): string => {
      if (gate.practical_experiments?.[0]) return gate.practical_experiments[0];
      if (safeShadow && safeGift) {
        return `Catch ${safeShadow} early. Then ask: what would ${safeGift} do here?`;
      }
      return "Notice how this plays out in your daily life.";
    };

    return (
      <View style={{ gap: 12 }}>
        {/* Recognition */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.accent }]}>RECOGNITION</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getGateRecognition()}
          </Text>
        </View>
        
        {/* Tension */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.warning || '#FF9800' }]}>TENSION</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getGateTension()}
          </Text>
        </View>
        
        {/* Real Life Moments */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.textTertiary }]}>REAL LIFE MOMENTS</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getGateRealLife()}
          </Text>
        </View>
        
        {/* Cross-Link (before Try This Instead) */}
        {crossLink && (
          <Text style={[styles.crossLinkText, { color: theme.textTertiary }]}>
            {crossLink}
          </Text>
        )}
        
        {/* Try This Instead */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.success || '#4CAF50' }]}>TRY THIS INSTEAD</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getGateTryThis()}
          </Text>
        </View>
        
        {/* Reflect CTA */}
        <TouchableOpacity
          style={[styles.deepDiveAskCta, { borderTopColor: theme.border }]}
          onPress={() => openReflection(
            `Gate ${gateNum}: ${gateName}`,
            'gate',
            getGateReflectionPrompt(gateNum, gateName),
            'deep_dive',
            `gate_${gateNum}`,
            gateName
          )}
          activeOpacity={0.7}
        >
          <Text style={[styles.deepDiveAskCtaText, { color: theme.accent }]}>Reflect on this →</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // NEW: Upgraded Gene Keys Section with Shadow/Gift/Siddhi structure
  const renderGeneKeysUpgraded = () => {
    const hasSequences = activationSequence || venusSequence || pearlSequence;
    if (!hasSequences) return null;
    
    return (
      <CollapsibleCard
        title="Gene Keys"
        subtitle="Your deeper purpose sequences"
        badge="3 arcs"
        defaultOpen={false}
        priority="medium"
      >
        <View style={{ gap: 16 }}>
          {/* Purpose Arc - Default OPEN (first sphere) */}
          {activationSequence && (
            <View>
              <SectionHeader title="Purpose Arc" icon="◎" count={activationSequence.spheres?.length || 0} />
              {(activationSequence.spheres || []).map((sphere: any, idx: number) => (
                <NestedCollapsible
                  key={`purpose-${idx}`}
                  title={sphere.sphere_name}
                  subtitle={sphere.gene_key ? `Gene Key ${sphere.gene_key}` : 'Core sequence'}
                  defaultOpen={idx === 0}
                  status="active"
                  lazyRender={true}
                >
                  {renderSphereUpgraded(sphere)}
                </NestedCollapsible>
              ))}
            </View>
          )}
          
          {/* Love Arc */}
          {venusSequence && (
            <View>
              <SectionHeader title="Love Arc" icon="♡" count={venusSequence.spheres?.length || 0} />
              {(venusSequence.spheres || []).map((sphere: any, idx: number) => (
                <NestedCollapsible
                  key={`love-${idx}`}
                  title={sphere.sphere_name}
                  subtitle={sphere.gene_key ? `Gene Key ${sphere.gene_key}` : 'Relationship sequence'}
                  defaultOpen={false}
                  status="defined"
                  lazyRender={true}
                >
                  {renderSphereUpgraded(sphere)}
                </NestedCollapsible>
              ))}
            </View>
          )}
          
          {/* Prosperity Arc */}
          {pearlSequence && (
            <View>
              <SectionHeader title="Prosperity Arc" icon="◇" count={pearlSequence.spheres?.length || 0} />
              {(pearlSequence.spheres || []).map((sphere: any, idx: number) => (
                <NestedCollapsible
                  key={`prosperity-${idx}`}
                  title={sphere.sphere_name}
                  subtitle={sphere.gene_key ? `Gene Key ${sphere.gene_key}` : 'Vocation sequence'}
                  defaultOpen={false}
                  status="defined"
                  lazyRender={true}
                >
                  {renderSphereUpgraded(sphere)}
                </NestedCollapsible>
              ))}
            </View>
          )}
        </View>
      </CollapsibleCard>
    );
  };

  // Helper: Render upgraded sphere content with Shadow/Gift/Siddhi
  const renderSphereUpgraded = (sphere: any) => {
    // DEFENSIVE GUARD: Safely get shadow, gift, siddhi strings
    const safeShadow = typeof sphere?.shadow === 'string' ? sphere.shadow.toLowerCase() : '';
    const safeGift = typeof sphere?.gift === 'string' ? sphere.gift.toLowerCase() : '';
    const safeSiddhi = typeof sphere?.siddhi === 'string' ? sphere.siddhi.toLowerCase() : '';
    
    // Recognition (from Shadow - current pattern)
    const getRecognition = (): string => {
      if (safeShadow) {
        const patterns = [
          `You keep running into ${safeShadow}—especially when pressure builds.`,
          `There's a pattern of ${safeShadow} that shows up when you're off-center.`,
          `When things feel stuck, ${safeShadow} is often somewhere in the mix.`
        ];
        return patterns[Math.floor((sphere.gene_key || 1) % patterns.length)];
      }
      return "You have a pattern that shows up when you're not fully aligned.";
    };
    
    // Tension (the pull between Shadow and Gift)
    const getTension = (): string => {
      if (safeShadow && safeGift) {
        return `Part of you keeps falling into ${safeShadow}. Another part knows ${safeGift} is possible. The gap between them is where growth happens.`;
      }
      return "The tension is between where you are and where you're becoming.";
    };
    
    // Truth Shift (Gift - the shift)
    const getTruthShift = (): string => {
      if (safeGift) {
        const shifts = [
          `When you catch ${safeShadow || 'the pattern'}, ${safeGift} becomes accessible.`,
          `The shift is toward ${safeGift}—not as effort, but as recognition.`,
          `${sphere.gift || 'The gift'} isn't something you do. It's what emerges when ${safeShadow || 'the old pattern'} releases.`
        ];
        return shifts[Math.floor((sphere.gene_key || 1) % shifts.length)];
      }
      return "The shift happens when you stop pushing and start noticing.";
    };
    
    // Try This Instead (practical movement toward Gift)
    const getTryThis = (): string => {
      if (safeShadow && safeGift) {
        const tips = [
          `When ${safeShadow} shows up, name it. That creates space for ${safeGift}.`,
          `Notice the moment before ${safeShadow} takes over. That's where choice lives.`,
          `Try: pause when you feel ${safeShadow} rising. Ask what ${safeGift} would look like here.`
        ];
        return tips[Math.floor((sphere.gene_key || 1) % tips.length)];
      }
      return "Start by noticing when the old pattern kicks in. That awareness is the first step.";
    };
    
    return (
      <View style={{ gap: 12 }}>
        {/* Recognition (Shadow as current pattern) */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.accent }]}>RECOGNITION</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getRecognition()}
          </Text>
        </View>
        
        {/* Tension (Shadow ↔ Gift) */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.warning || '#FF9800' }]}>TENSION</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getTension()}
          </Text>
        </View>
        
        {/* Truth Shift (Gift as the shift) */}
        <View style={[styles.mirrorTruthShift, { backgroundColor: theme.background, borderLeftColor: theme.accent }]}>
          <Text style={[styles.mirrorSectionLabel, { color: theme.accent }]}>TRUTH SHIFT</Text>
          <Text style={[styles.mirrorTruthShiftText, { color: theme.text }]}>
            {getTruthShift()}
          </Text>
        </View>
        
        {/* Try This Instead */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.success || '#4CAF50' }]}>TRY THIS INSTEAD</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getTryThis()}
          </Text>
        </View>
        
        {/* Siddhi hint (subtle, not labeled) */}
        {safeSiddhi && (
          <Text style={[styles.crossLinkText, { color: theme.textTertiary }]}>
            At its deepest, this energy moves toward {safeSiddhi}—not as achievement, but as natural unfolding.
          </Text>
        )}
        
        {/* Reflect CTA */}
        <TouchableOpacity
          style={[styles.deepDiveAskCta, { borderTopColor: theme.border }]}
          onPress={() => openReflection(
            sphere.sphere_name,
            'sphere',
            getSphereReflectionPrompt(sphere.sphere_name, sphere.gene_key || 0),
            'deep_dive',
            `sphere_${sphere.gene_key}`,
            `GK ${sphere.gene_key}`
          )}
          activeOpacity={0.7}
        >
          <Text style={[styles.deepDiveAskCtaText, { color: theme.accent }]}>Reflect on this →</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // NEW: Render Core Synthesis section
  const renderCoreSynthesis = () => {
    if (!data?.core_mechanics) return null;
    
    // Generate synthesis
    const synthesisInput: HDSynthesisInput = {
      type: data.core_mechanics.type || '',
      authority: data.core_mechanics.authority || 'Sacral',
      profile: data.core_mechanics.profile || '1/3',
      definition: data.core_mechanics.definition,
      incarnationCross: data.core_mechanics.incarnation_cross,
      channels: data.channels,
      definedCenters: data.defined_centers,
      undefinedCenters: data.undefined_centers,
      consciousGates: data.conscious_gates,
      unconsciousGates: data.unconscious_gates,
      personalitySun: data.personality_sun,
      designSun: data.design_sun,
    };
    const synthesis = generateHDSynthesis(synthesisInput);
    
    if (!synthesis) return null;
    
    return (
      <CollapsibleCard
        title="Your Core Synthesis"
        subtitle="How your design operates as one system"
        defaultOpen={true}
        priority="high"
      >
        <View style={{ gap: 16 }}>
          {/* Core Pattern */}
          <Text style={[styles.mirrorRecognition, { color: theme.text }]}>
            {synthesis.corePattern}
          </Text>
          
          {/* Core Tension */}
          <View>
            <Text style={[styles.mirrorSectionLabel, { color: theme.warning || '#FF9800' }]}>THE TENSION</Text>
            <Text style={[styles.mirrorSectionText, { color: theme.text }]}>
              {synthesis.coreTension}
            </Text>
          </View>
          
          {/* How This Plays Out */}
          <View>
            <Text style={[styles.mirrorSectionLabel, { color: theme.textTertiary }]}>HOW THIS PLAYS OUT</Text>
            {synthesis.howThisPlaysOut.map((item: string, i: number) => (
              <View key={`plays-${i}`} style={styles.mirrorBulletRow}>
                <Text style={[styles.mirrorBullet, { color: theme.textTertiary }]}>•</Text>
                <Text style={[styles.mirrorBulletText, { color: theme.textSecondary }]}>{item}</Text>
              </View>
            ))}
          </View>
          
          {/* Blind Spot */}
          <View style={[styles.mirrorTruthShift, { backgroundColor: theme.background, borderLeftColor: theme.warning || '#FF9800' }]}>
            <Text style={[styles.mirrorSectionLabel, { color: theme.warning || '#FF9800' }]}>BLIND SPOT</Text>
            <Text style={[styles.mirrorTruthShiftText, { color: theme.text }]}>
              {synthesis.blindSpot}
            </Text>
          </View>
          
          {/* Edge */}
          <View style={[styles.mirrorTruthShift, { backgroundColor: theme.background, borderLeftColor: theme.success || '#4CAF50' }]}>
            <Text style={[styles.mirrorSectionLabel, { color: theme.success || '#4CAF50' }]}>YOUR EDGE</Text>
            <Text style={[styles.mirrorTruthShiftText, { color: theme.text }]}>
              {synthesis.edge}
            </Text>
          </View>
        </View>
      </CollapsibleCard>
    );
  };

  // Legacy render function for old format (fallback)
  const renderDeepDiveAccordion = (key: string, title: string, subtitle: string, story: MechanicStory | undefined) => {
    const isExpanded = expandedDeepDive === key;
    
    if (!story) return null;

    // Get the source value for the Reflect button
    const getSourceValue = () => {
      switch (key) {
        case 'type': return data?.core_mechanics?.type || '';
        case 'strategy': return data?.core_mechanics?.strategy || '';
        case 'authority': return data?.core_mechanics?.authority || '';
        case 'profile': return data?.core_mechanics?.profile || '';
        case 'cross': return data?.core_mechanics?.incarnation_cross || '';
        default: return '';
      }
    };
    
    return (
      <View key={key} style={[styles.deepDiveAccordion, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Pressable
          style={({ pressed }) => [
            styles.deepDiveHeader,
            pressed && { opacity: 0.7 }
          ]}
          onPress={() => {
            setExpandedDeepDive(isExpanded ? null : key);
          }}
        >
          <View style={styles.deepDiveHeaderText}>
            <Text style={[styles.deepDiveTitle, { color: theme.text }]}>{title}</Text>
            <Text style={[styles.deepDiveSubtitle, { color: theme.textTertiary }]}>{subtitle}</Text>
          </View>
          <Text style={[styles.deepDiveChevron, { color: theme.textTertiary }]}>
            {isExpanded ? '▲' : '▼'}
          </Text>
        </Pressable>
        
        {isExpanded && (
          <View style={styles.deepDiveContent}>
            {/* Explanation */}
            {story.explanation.map((para, i) => (
              <Text key={`exp-${i}`} style={[styles.deepDiveParagraph, { color: theme.text }]}>{para}</Text>
            ))}
            
            {/* Patterns */}
            <Text style={[styles.deepDiveSectionLabel, { color: theme.accent }]}>HOW THIS SHOWS UP</Text>
            {story.patterns.map((pattern, i) => (
              <View key={`pat-${i}`} style={styles.deepDiveBulletRow}>
                <Text style={[styles.deepDiveBullet, { color: theme.textTertiary }]}>•</Text>
                <Text style={[styles.deepDiveBulletText, { color: theme.text }]}>{pattern}</Text>
              </View>
            ))}
            
            {/* Challenge */}
            <Text style={[styles.deepDiveSectionLabel, { color: theme.accent }]}>COMMON CHALLENGE</Text>
            <Text style={[styles.deepDiveParagraph, { color: theme.text }]}>{story.challenge}</Text>
            
            {/* Reflection */}
            <View style={[styles.deepDiveReflection, { backgroundColor: theme.background, borderLeftColor: theme.accent }]}>
              <Text style={[styles.deepDiveSectionLabel, { color: theme.accent }]}>REFLECTION</Text>
              <Text style={[styles.deepDiveReflectionText, { color: theme.text }]}>{story.reflection}</Text>
            </View>

            {/* Reflect Button */}
            {key !== 'centers' && (
              <InlineReflectButton
                source={{
                  lens: 'human_design',
                  type: key,
                  name: title,
                  value: getSourceValue(),
                  id: `hd_${key}`,
                }}
                prompt={story.reflection}
              />
            )}
          </View>
        )}
      </View>
    );
  };

  // Always render core mechanics for deep dive, even with fallback values
  const renderCoreMechanics = () => {
    // Default fallback if no data
    const mechanics = data?.core_mechanics || {
      type: 'Unknown',
      strategy: 'Unknown',
      authority: 'Unknown',
      profile: 'Unknown',
      definition: 'Unknown',
      incarnation_cross: 'Unknown',
      incarnation_cross_gates: null
    };

    // Helper to format unknown gracefully - DO NOT TRANSFORM canonical labels
    const formatMechanic = (value: string | undefined | null) => {
      if (!value || value === 'Unknown') return '—';
      // Display canonical label exactly as received from backend
      return value;
    };

    // Format incarnation cross - show the full name
    const formatCross = () => {
      if (!mechanics.incarnation_cross || mechanics.incarnation_cross === 'Unknown') {
        return '—';
      }
      // If it's a numbered cross like "Right Angle Cross of 37/40", extract just the type
      // If it's a named cross like "Right Angle Cross of Migration", show the full name
      const numbered = /\s*of\s*\d+\/\d+/;
      if (numbered.test(mechanics.incarnation_cross)) {
        // It's still numbered (old format) - just show the cross type
        return mechanics.incarnation_cross.replace(/\s*of\s*\d+\/\d+.*$/, '').trim();
      }
      // It's a named cross - show it fully (e.g., "Right Angle Cross of Migration")
      return mechanics.incarnation_cross;
    };

    const getCrossGates = () => {
      return mechanics.incarnation_cross_gates || '—';
    };

    // Navigate to mechanic detail modal
    const handleMechanicTap = (mechanicType: string) => {
      // Debug logging
      // Open the mechanics detail modal
      setActiveMechanicDetail(mechanicType);
    };

    return (
      <View style={[styles.coreMechanicsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.coreMechanicsTitle, { color: theme.textTertiary }]}>CORE MECHANICS</Text>
        
        {/* Row 1: Type + Authority - Tappable for drill-down */}
        <View style={styles.mechanicsGrid}>
          <Pressable 
            style={({ pressed }) => [
              styles.mechanicItem,
              pressed && { opacity: 0.7 }
            ]}
            onPress={() => {
              handleMechanicTap('type');
            }}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={{ fontSize: 14, color: theme.accent }}>⚡</Text>
            <Text style={[styles.mechanicLabel, { color: theme.textTertiary }]}>Type</Text>
            <Text style={[styles.mechanicValue, { color: theme.text }]}>{formatMechanic(mechanics.type)}</Text>
            <Text style={[styles.mechanicDrillDown, { color: theme.accent }]}>Explore →</Text>
          </Pressable>
          <View style={[styles.mechanicDivider, { backgroundColor: theme.border }]} />
          <Pressable 
            style={({ pressed }) => [
              styles.mechanicItem,
              pressed && { opacity: 0.7 }
            ]}
            onPress={() => {
              handleMechanicTap('authority');
            }}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={{ fontSize: 14, color: theme.accent }}>◎</Text>
            <Text style={[styles.mechanicLabel, { color: theme.textTertiary }]}>Authority</Text>
            <Text style={[styles.mechanicValue, { color: theme.text }]}>{formatMechanic(mechanics.authority)}</Text>
            <Text style={[styles.mechanicDrillDown, { color: theme.accent }]}>Explore →</Text>
          </Pressable>
        </View>
        
        {/* Row 2: Profile + Definition - Tappable for drill-down */}
        <View style={[styles.mechanicsGrid, { marginTop: 16 }]}>
          <Pressable 
            style={({ pressed }) => [
              styles.mechanicItem,
              pressed && { opacity: 0.7 }
            ]}
            onPress={() => {
              handleMechanicTap('profile');
            }}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={{ fontSize: 14, color: theme.accent }}>👤</Text>
            <Text style={[styles.mechanicLabel, { color: theme.textTertiary }]}>Profile</Text>
            <Text style={[styles.mechanicValue, { color: theme.text }]}>{mechanics.profile || '—'}</Text>
            <Text style={[styles.mechanicDrillDown, { color: theme.accent }]}>Explore →</Text>
          </Pressable>
          <View style={[styles.mechanicDivider, { backgroundColor: theme.border }]} />
          <View style={styles.mechanicItem}>
            <Text style={{ fontSize: 14, color: theme.accent }}>☰</Text>
            <Text style={[styles.mechanicLabel, { color: theme.textTertiary }]}>Definition</Text>
            <Text style={[styles.mechanicValue, { color: theme.text }]}>{formatMechanic(mechanics.definition)}</Text>
          </View>
        </View>
        
        {/* Row 3: Incarnation Cross - Tappable for drill-down */}
        <View style={[styles.mechanicsGrid, { marginTop: 16 }]}>
          <Pressable 
            style={({ pressed }) => [
              styles.mechanicItem,
              { flex: 1 },
              pressed && { opacity: 0.7 }
            ]}
            onPress={() => {
              handleMechanicTap('incarnation');
            }}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={{ fontSize: 14, color: theme.accent }}>✦</Text>
            <Text style={[styles.mechanicLabel, { color: theme.textTertiary }]}>Incarnation Cross</Text>
            <Text style={[styles.mechanicValue, styles.mechanicValueSmall, { color: theme.text }]}>{formatCross()}</Text>
            <Text style={[styles.mechanicGates, { color: theme.textTertiary }]}>{getCrossGates()}</Text>
            <Text style={[styles.mechanicDrillDown, { color: theme.accent }]}>Explore →</Text>
          </Pressable>
        </View>
      </View>
    );
  };

  // Render version debug panel (only in dev mode)
  const renderVersionDebug = () => {
    if (!isDebugEnabled() || !data) return null;
    
    return (
      <View style={styles.versionDebugCard}>
        <Text style={styles.versionDebugTitle}>COMPUTE VERSIONS (DEV)</Text>
        <View style={styles.versionDebugRow}>
          <Text style={styles.versionDebugLabel}>computation:</Text>
          <Text style={styles.versionDebugValue}>{data.computation_version || '—'}</Text>
        </View>
        <View style={styles.versionDebugRow}>
          <Text style={styles.versionDebugLabel}>astronomy:</Text>
          <Text style={styles.versionDebugValue}>{data.astronomy_version || '—'}</Text>
        </View>
        <View style={styles.versionDebugRow}>
          <Text style={styles.versionDebugLabel}>human_design:</Text>
          <Text style={styles.versionDebugValue}>{data.human_design_version || '—'}</Text>
        </View>
      </View>
    );
  };

  // Render the Mechanic Detail Modal
  const renderMechanicDetailModal = () => {
    
    if (!activeMechanicDetail || !data?.core_mechanics) {
      return null;
    }
    
    
    const mechanics = data.core_mechanics;
    let title = '';
    let subtitle = '';
    let story: MechanicStory | null = null;
    
    // Get the appropriate story content based on mechanic type
    switch (activeMechanicDetail) {
      case 'type':
        const typeVal = mechanics.type || 'Generator';
        title = `Type: ${typeVal}`;
        subtitle = 'How you engage with life';
        story = TYPE_STORIES[typeVal] || TYPE_STORIES['Generator'];
        break;
      case 'authority':
        const authVal = mechanics.authority || 'Emotional';
        title = `Authority: ${authVal}`;
        subtitle = 'How you make decisions';
        story = AUTHORITY_STORIES[authVal] || AUTHORITY_STORIES['Emotional'];
        break;
      case 'profile':
        const profileVal = mechanics.profile || '1/3';
        title = `Profile: ${profileVal}`;
        subtitle = 'Your life theme and role';
        story = PROFILE_STORIES[profileVal] || PROFILE_STORIES['1/3'];
        break;
      case 'incarnation':
        const crossVal = mechanics.incarnation_cross || 'Right Angle Cross';
        const angle = getCrossAngle(crossVal);
        title = crossVal;
        subtitle = 'Your life purpose theme';
        story = CROSS_STORIES[angle] || CROSS_STORIES['Right Angle'];
        break;
    }
    
    if (!story) {
      return null;
    }
    
    const screenWidth = Dimensions.get('window').width;
    const screenHeight = Dimensions.get('window').height;
    const modalWidth = Math.min(screenWidth - 32, 500);
    const modalMaxHeight = screenHeight * 0.85;
    
    
    return (
      <Modal
        visible={true}
        transparent={true}
        animationType="fade"
        onRequestClose={() => {
          setActiveMechanicDetail(null);
        }}
        statusBarTranslucent={Platform.OS === 'android'}
      >
        <Pressable 
          style={styles.modalOverlay}
          onPress={() => {
            setActiveMechanicDetail(null);
          }}
        >
          <Pressable 
            style={[styles.modalContent, { backgroundColor: theme.surface, width: modalWidth, maxHeight: modalMaxHeight }]}
            onPress={(e) => {
              // Prevent closing when tapping the modal content
              e.stopPropagation();
            }}
          >
            <ScrollView 
              style={styles.modalScrollView}
              showsVerticalScrollIndicator={false}
              contentContainerStyle={styles.modalScrollContent}
            >
              {/* Header */}
              <View style={styles.modalHeader}>
                <Text style={[styles.modalTitle, { color: theme.text }]}>{title}</Text>
                <Text style={[styles.modalSubtitle, { color: theme.textTertiary }]}>{subtitle}</Text>
              </View>
              
              {/* Explanation Section */}
              <View style={styles.modalSection}>
                <Text style={[styles.modalSectionTitle, { color: theme.accent }]}>UNDERSTANDING</Text>
                {story.explanation.map((para, i) => (
                  <Text key={i} style={[styles.modalParagraph, { color: theme.text }]}>{para}</Text>
                ))}
              </View>
              
              {/* Patterns Section */}
              <View style={styles.modalSection}>
                <Text style={[styles.modalSectionTitle, { color: theme.accent }]}>HOW THIS TENDS TO SHOW UP</Text>
                {story.patterns.map((pattern, i) => (
                  <View key={i} style={styles.modalBulletRow}>
                    <Text style={[styles.modalBullet, { color: theme.textTertiary }]}>•</Text>
                    <Text style={[styles.modalBulletText, { color: theme.text }]}>{pattern}</Text>
                  </View>
                ))}
              </View>
              
              {/* Challenge Section */}
              <View style={styles.modalSection}>
                <Text style={[styles.modalSectionTitle, { color: theme.accent }]}>COMMON CHALLENGE</Text>
                <Text style={[styles.modalParagraph, { color: theme.text }]}>{story.challenge}</Text>
              </View>
              
              {/* Reflection Section */}
              <View style={[styles.modalSection, styles.modalReflectionSection, { backgroundColor: theme.background, borderLeftColor: theme.accent }]}>
                <Text style={[styles.modalSectionTitle, { color: theme.accent }]}>REFLECTION</Text>
                <Text style={[styles.modalReflectionText, { color: theme.text }]}>{story.reflection}</Text>
              </View>
            </ScrollView>
            
            {/* Close Button */}
            <Pressable
              style={({ pressed }) => [
                styles.modalCloseButton, 
                { backgroundColor: theme.background, borderTopColor: theme.border },
                pressed && { opacity: 0.7 }
              ]}
              onPress={() => {
                setActiveMechanicDetail(null);
              }}
            >
              <Text style={[styles.modalCloseText, { color: theme.text }]}>Close</Text>
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>
    );
  };

  // Render a single Gene Key sphere position with MEANING-FIRST design
  const renderGeneKeySphere = (name: string, position: GeneKeyPosition) => {
    const chartLabel = position.source_chart === 'personality' ? 'Conscious' : 'Unconscious';
    const interp = generateSphereInterpretation(name, position.gate, position.line);
    const sourceInfo = `${position.source_planet} • ${chartLabel}`;
    const gateLineDisplay = `${position.gate}.${position.line}`;
    
    // MEANING-FIRST VIEW: sphere name → gate.line → descriptor → interpretation → metadata
    return (
      <View key={name} style={[styles.sphereCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        {/* 1. Sphere Name - prominent */}
        <Text style={[styles.sphereTitle, { color: theme.text }]}>{interp.sphereTitle}</Text>
        
        {/* 2. Gate.Line - technical identifier right under title */}
        <Text style={[styles.sphereGateLine, { color: theme.accent }]}>{gateLineDisplay}</Text>
        
        {/* 3. Plain-English Descriptor - one line */}
        <Text style={[styles.sphereDescriptor, { color: theme.textSecondary }]}>{interp.sphereDescriptor}</Text>
        
        {/* 4. Meaning-First Interpretation - short paragraph */}
        <Text style={[styles.sphereInterpretation, { color: theme.textSecondary }]}>{interp.meaningInterpretation}</Text>
        
        {/* 5. Technical Details - subtle metadata at bottom */}
        <View style={[styles.sphereMetadata, { borderTopColor: theme.border }]}>
          <Text style={[styles.sphereMetaText, { color: theme.textTertiary }]}>{sourceInfo}</Text>
        </View>
      </View>
    );
  };

  // Format sphere name from snake_case to Title Case
  const formatSphereName = (name: string): string => {
    // Special cases for better readability
    const specialNames: Record<string, string> = {
      'lifes_work': "Life's Work",
      'iq': 'IQ',
      'eq': 'EQ', 
      'sq': 'SQ',
      'core_wound': 'Core Wound',
    };
    if (specialNames[name]) return specialNames[name];
    
    return name
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Render Gene Keys Arc card with collapse/expand
  const renderGeneKeysArc = (
    arcName: string, 
    arcKey: string,
    arcData: Record<string, GeneKeyPosition> | undefined,
    iconText: string,
    subtitle: string
  ) => {
    if (!arcData) return null;
    
    const isExpanded = expandedArc === arcKey;
    const sphereCount = Object.keys(arcData).length;
    const arcDescription = getArcDescription(arcKey);
    
    return (
      <View style={styles.gkArcCard}>
        <TouchableOpacity
          style={[styles.gkArcHeader, { borderBottomColor: theme.border }]}
          onPress={() => setExpandedArc(isExpanded ? null : arcKey)}
          activeOpacity={0.7}
        >
          <View style={styles.gkArcHeaderLeft}>
            <Text style={{ fontSize: 16, color: theme.accent }}>{iconText}</Text>
            <View>
              <Text style={[styles.gkArcTitle, { color: theme.text }]}>{arcDescription.title || arcName}</Text>
              <Text style={[styles.gkArcSubtitle, { color: theme.textTertiary }]}>
                {arcDescription.description}
              </Text>
            </View>
          </View>
          <View style={styles.gkArcHeaderRight}>
            <Text style={[styles.gkArcCount, { color: theme.textTertiary }]}>{sphereCount} spheres</Text>
            <Text style={{ fontSize: 16, color: theme.textTertiary }}>
              {isExpanded ? '▲' : '▼'}
            </Text>
          </View>
        </TouchableOpacity>
        {isExpanded && (
          <View style={styles.gkArcContent}>
            {arcDescription.helperText && (
              <Text style={[styles.gkArcHelper, { color: theme.textTertiary }]}>{arcDescription.helperText}</Text>
            )}
            {Object.entries(arcData).map(([name, position]) => 
              renderGeneKeySphere(name, position)
            )}
          </View>
        )}
      </View>
    );
  };

  // Render all Gene Keys sequences with improved visual hierarchy
  const renderGeneKeys = () => {
    if (!data?.gene_keys) return null;
    
    const gk = data.gene_keys;
    
    return (
      <View style={styles.gkContainer}>
        {/* Section Header with integrated toggle */}
        <View style={styles.gkSectionHeaderWrapper}>
          <View style={styles.gkSectionHeaderTop}>
            <View style={styles.gkSectionTitleRow}>
              <Text style={{ fontSize: 16, color: theme.accent }}>🔑</Text>
              <Text style={[styles.gkSectionMainTitle, { color: theme.textTertiary }]}>YOUR SEQUENCES</Text>
            </View>
          </View>
          <Text style={[styles.gkSectionIntro, { color: theme.textSecondary }]}>
            Derived from your Human Design chart, these sequences illuminate different dimensions of your experience.
          </Text>
        </View>
        
        {/* Arc Cards Container */}
        <View style={styles.gkArcsContainer}>
          {renderGeneKeysArc('Purpose', 'purpose', gk.purpose_arc, '◎', 'Your life direction')}
          {renderGeneKeysArc('Love', 'love', gk.love_arc, '♡', 'Relationships & relating')}
          {renderGeneKeysArc('Prosperity', 'prosperity', gk.prosperity_arc, '◇', 'Abundance & vocation')}
          
          {isDebugEnabled() && (
            <Text style={[styles.gkVersion, { color: theme.textTertiary }]}>v: {gk.gene_keys_version}</Text>
          )}
        </View>
      </View>
    );
  };

  // ============================================
  // SUMMARY TAB - Emotional hook, fast recognition
  // Purpose: User feels seen in 5 seconds
  // Max 2 cards visible
  // ============================================
  
  const renderSummaryTab = () => {
    if (!data?.core_mechanics) return null;
    
    const { type, authority, profile, definition } = data.core_mechanics;
    const hdType = type || 'Unknown';
    
    // Get pattern synthesis for emotional hook
    const typePattern = TYPE_PATTERNS[hdType] || TYPE_PATTERNS['Generator'];
    
    // Generate master synthesis for core pattern
    const synthesisInput: HDSynthesisInput = {
      type: hdType,
      authority: authority || 'Sacral',
      profile: profile || '1/3',
      definition: definition,
      channels: data.channels,
      definedCenters: data.defined_centers,
      undefinedCenters: data.undefined_centers,
    };
    const masterSynthesis = generateHDSynthesis(synthesisInput);
    
    return (
      <>
        {/* Identity Card - Type + Profile */}
        <View style={[styles.hdSummaryIdentityCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdSummaryType, { color: theme.text }]}>{hdType}</Text>
          {profile && <Text style={[styles.hdSummaryProfile, { color: theme.textSecondary }]}>{profile} Profile</Text>}
          <Text style={[styles.hdSummaryNote, { color: theme.textTertiary }]}>
            This lens reflects energy patterns, not identity.
          </Text>
        </View>

        {/* Core Pattern Card - The emotional hook */}
        {masterSynthesis && (
          <View style={[styles.hdSummaryPatternCard, { backgroundColor: theme.surface, borderColor: theme.accent, borderLeftWidth: 3 }]}>
            <Text style={[styles.hdSummaryPatternLabel, { color: theme.accent }]}>YOUR CORE PATTERN</Text>
            <Text style={[styles.hdSummaryPatternText, { color: theme.text }]}>
              {masterSynthesis.corePattern}
            </Text>
            
            {/* Core Tension - 1 line */}
            <View style={styles.hdSummaryTensionSection}>
              <Text style={[styles.hdSummaryTensionLabel, { color: theme.warning || '#FF9800' }]}>THE TENSION</Text>
              <Text style={[styles.hdSummaryTensionText, { color: theme.textSecondary }]} numberOfLines={2}>
                {masterSynthesis.coreTension}
              </Text>
            </View>
          </View>
        )}

        {/* Reflection Question */}
        <View style={[styles.hdSummaryReflectionCard, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
          <Text style={[styles.hdSummaryReflectionLabel, { color: theme.accent }]}>A QUESTION</Text>
          <Text style={[styles.hdSummaryReflectionText, { color: theme.text }]}>
            "{TYPE_REFLECTIONS[hdType] || TYPE_REFLECTIONS['Generator']}"
          </Text>
        </View>

        {/* Link to At a Glance */}
        <TouchableOpacity
          style={styles.hdSummaryLink}
          onPress={() => setActiveTab('at_a_glance')}
        >
          <Text style={[styles.hdSummaryLinkText, { color: theme.textTertiary }]}>See full design snapshot</Text>
          <Text style={{ fontSize: 12, color: theme.textTertiary }}>›</Text>
        </TouchableOpacity>
      </>
    );
  };

  // ============================================
  // AT A GLANCE TAB - Structured data snapshot
  // Purpose: Scannable in <5 seconds
  // NO paragraphs, max 1 line per item
  // ============================================
  
  const renderAtAGlanceTab = () => {
    if (!data?.core_mechanics) return null;
    
    const { type, strategy, authority, profile, definition, incarnation_cross } = data.core_mechanics;
    const hdType = type || 'Unknown';
    
    // Safely get centers arrays
    const safeCenters = Array.isArray(centersData?.centers) ? centersData.centers : [];
    const definedCentersList = safeCenters.filter((c: any) => c && c.defined).map((c: any) => c.center);
    const undefinedCentersList = safeCenters.filter((c: any) => c && !c.defined).map((c: any) => c.center);
    
    // Safely get gates
    const safeGates = Array.isArray(gatesData?.gates) ? gatesData.gates : [];
    const topGates = safeGates.slice(0, 5);
    
    // Safely get channels
    const channels = Array.isArray(data.channels) ? data.channels : [];
    
    return (
      <>
        {/* SECTION 1: CORE */}
        <View style={[styles.hdGlanceCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdGlanceTitle, { color: theme.accent }]}>CORE</Text>
          <View style={styles.hdGlanceGrid}>
            <View style={styles.hdGlanceRow}>
              <Text style={[styles.hdGlanceLabel, { color: theme.textTertiary }]}>Type</Text>
              <Text style={[styles.hdGlanceValue, { color: theme.text }]}>{hdType}</Text>
            </View>
            <View style={styles.hdGlanceRow}>
              <Text style={[styles.hdGlanceLabel, { color: theme.textTertiary }]}>Strategy</Text>
              <Text style={[styles.hdGlanceValue, { color: theme.text }]} numberOfLines={1}>{strategy || '—'}</Text>
            </View>
            <View style={styles.hdGlanceRow}>
              <Text style={[styles.hdGlanceLabel, { color: theme.textTertiary }]}>Authority</Text>
              <Text style={[styles.hdGlanceValue, { color: theme.text }]}>{authority || '—'}</Text>
            </View>
            <View style={styles.hdGlanceRow}>
              <Text style={[styles.hdGlanceLabel, { color: theme.textTertiary }]}>Profile</Text>
              <Text style={[styles.hdGlanceValue, { color: theme.text }]}>{profile || '—'}</Text>
            </View>
            <View style={styles.hdGlanceRow}>
              <Text style={[styles.hdGlanceLabel, { color: theme.textTertiary }]}>Definition</Text>
              <Text style={[styles.hdGlanceValue, { color: theme.text }]}>{definition || '—'}</Text>
            </View>
          </View>
        </View>

        {/* SECTION 2: ENERGY STRUCTURE */}
        <View style={[styles.hdGlanceCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdGlanceTitle, { color: theme.accent }]}>ENERGY STRUCTURE</Text>
          <View style={styles.hdGlanceCenterSection}>
            <Text style={[styles.hdGlanceCenterLabel, { color: theme.success || '#4CAF50' }]}>Defined</Text>
            <Text style={[styles.hdGlanceCenterList, { color: theme.text }]}>
              {definedCentersList.length > 0 ? definedCentersList.join(', ') : 'None'}
            </Text>
          </View>
          <View style={styles.hdGlanceCenterSection}>
            <Text style={[styles.hdGlanceCenterLabel, { color: theme.textTertiary }]}>Undefined</Text>
            <Text style={[styles.hdGlanceCenterList, { color: theme.textSecondary }]}>
              {undefinedCentersList.length > 0 ? undefinedCentersList.join(', ') : 'None'}
            </Text>
          </View>
        </View>

        {/* SECTION 3: KEY ACTIVATIONS */}
        {topGates.length > 0 && (
          <View style={[styles.hdGlanceCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.hdGlanceTitle, { color: theme.accent }]}>KEY ACTIVATIONS</Text>
            {topGates.map((gate: any, i: number) => (
              <View key={i} style={styles.hdGlanceGateRow}>
                <Text style={[styles.hdGlanceGateNumber, { color: theme.accent }]}>
                  Gate {gate.gate_number || gate.gate}
                </Text>
                <Text style={[styles.hdGlanceGateName, { color: theme.text }]} numberOfLines={1}>
                  {gate.name || getGateTheme(gate.gate_number || gate.gate) || ''}
                </Text>
              </View>
            ))}
            {channels.length > 0 && (
              <View style={styles.hdGlanceChannelSection}>
                <Text style={[styles.hdGlanceChannelLabel, { color: theme.textTertiary }]}>Channels</Text>
                <Text style={[styles.hdGlanceChannelList, { color: theme.textSecondary }]} numberOfLines={2}>
                  {channels.map((c: any) => c.name || `${c.gate_1}-${c.gate_2}`).join(', ')}
                </Text>
              </View>
            )}
          </View>
        )}

        {/* SECTION 4: IDENTITY AXIS */}
        {incarnation_cross && (
          <View style={[styles.hdGlanceCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.hdGlanceTitle, { color: theme.accent }]}>IDENTITY AXIS</Text>
            <Text style={[styles.hdGlanceCrossName, { color: theme.text }]}>{incarnation_cross}</Text>
            <Text style={[styles.hdGlanceCrossDesc, { color: theme.textSecondary }]} numberOfLines={1}>
              The question life keeps bringing you back to.
            </Text>
          </View>
        )}

        {/* SECTION 5: HOW THIS SHOWS UP - Calibrated behavioral observations with Forward Pull */}
        <View style={[styles.hdGlanceCard, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
          <Text style={[styles.hdGlanceTitle, { color: theme.accent }]}>HOW THIS SHOWS UP</Text>
          {/* RECOGNITION tone (60%) with Forward Pull */}
          <Text style={[styles.hdGlanceInsight, { color: theme.text }]}>
            • {hdType === 'Projector' ? 'You tend to wait for others to come to you—pushing often doesn\'t feel right. When recognition comes, things flow.' : 
               hdType === 'Generator' || hdType === 'Manifesting Generator' ? 'You often know what\'s right by how your body responds—not your head. That signal is getting clearer.' : 
               hdType === 'Manifestor' ? 'You may find yourself starting things others won\'t—informing first tends to help. Something is wanting to begin.' : 
               'Big decisions usually need time to settle—a full cycle often brings more clarity. Something is forming.'}
          </Text>
          {/* TENSION tone (30%) with Forward Pull */}
          <Text style={[styles.hdGlanceInsight, { color: theme.text }]}>
            • {authority === 'Emotional' || authority === 'Solar Plexus' ? 'What feels right today may shift tomorrow—waiting for the wave to pass can help. The clarity is coming.' :
               authority === 'Sacral' ? 'Your gut tends to respond quickly—the first response is often the clearest. That response is becoming more trustworthy.' :
               authority === 'Splenic' ? 'Your instincts can hit fast and not repeat—catching them in the moment matters. You\'re learning to trust it.' :
               authority === 'Self-Projected' || authority === 'Self Projected' ? 'You may need to hear yourself talk it through with others to find clarity. The right words are coming.' :
               authority === 'Ego' || authority === 'Heart' ? 'When you don\'t genuinely want something, follow-through can be difficult. What you actually want is becoming clearer.' :
               authority === 'Mental' || authority === 'Sounding Board' ? 'You often process by bouncing ideas off trusted people. The right sounding board is emerging.' :
               authority === 'Lunar' ? 'Major decisions tend to need more time—rushing can backfire. Something is settling into place.' :
               'Clarity often comes through the body rather than mental analysis. That channel is opening.'}
          </Text>
          {/* RECOGNITION tone for centers with Forward Pull */}
          {definedCentersList.length > 0 && (
            <Text style={[styles.hdGlanceInsight, { color: theme.text }]}>
              • {definedCentersList.includes('Sacral') ? 'You tend to have consistent work energy—though it helps when you love what you do. That alignment is developing.' :
                 definedCentersList.includes('Heart') || definedCentersList.includes('Ego') ? 'You can push through, but usually only for things that genuinely matter to you. What matters is becoming clearer.' :
                 definedCentersList.includes('Root') ? 'You may handle pressure well—though it can sometimes make you rush others. Your timing is refining.' :
                 definedCentersList.includes('Solar Plexus') || definedCentersList.includes('Emotional') ? 'Your moods tend to be real and powerful—they\'re not always about fixing. Something is integrating.' :
                 definedCentersList.includes('Throat') ? 'You often have a consistent voice—people tend to hear you. What you\'re saying is crystallizing.' :
                 definedCentersList.includes('Ajna') ? 'You may think in consistent patterns—not everyone does. Your understanding is deepening.' :
                 definedCentersList.includes('Head') ? 'Questions often come to you naturally—they tend to drive your process. An answer is forming.' :
                 `Your energy tends to be consistent in certain areas—others may feel it. That presence is strengthening.`}
            </Text>
          )}
        </View>

        {/* Link to Deep Dive */}
        <TouchableOpacity
          style={styles.hdSummaryLink}
          onPress={() => setActiveTab('deep_dive')}
        >
          <Text style={[styles.hdSummaryLinkText, { color: theme.textTertiary }]}>Explore in depth</Text>
          <Text style={{ fontSize: 12, color: theme.textTertiary }}>›</Text>
        </TouchableOpacity>
      </>
    );
  };

  // ============================================
  // OVERVIEW TAB (OLD - keeping for reference, not used)
  // ============================================
  
  const renderOverviewTab = () => {
    if (!data?.core_mechanics) return null;
    
    const { type, strategy, authority, profile, definition } = data.core_mechanics;
    const hdType = type || 'Unknown';
    const manifestations = TYPE_MANIFESTATIONS[hdType] || TYPE_MANIFESTATIONS['Generator'];
    const authorityData = AUTHORITY_TRANSLATIONS[authority || ''] || AUTHORITY_TRANSLATIONS['None'];
    
    // Get pattern compression
    const typePattern = TYPE_PATTERNS[hdType] || TYPE_PATTERNS['Generator'];
    const authorityPattern = AUTHORITY_PATTERNS[authority || 'Sacral'] || AUTHORITY_PATTERNS['Sacral'];
    const patternSynthesis = synthesizeHDPattern(hdType, authority || 'Sacral');
    
    // Generate MASTER SYNTHESIS - integrates ALL HD mechanics into unified reading
    // Now includes: channels, conscious/unconscious, environment, motivation/transference
    const synthesisInput: HDSynthesisInput = {
      type: hdType,
      authority: authority || 'Sacral',
      profile: profile || '1/3',
      definition: definition,
      incarnationCross: data.core_mechanics?.incarnation_cross,
      incarnationCrossGates: data.core_mechanics?.incarnation_cross_gates,
      // MASTER LEVEL DATA
      channels: data.channels,
      definedCenters: data.defined_centers,
      undefinedCenters: data.undefined_centers,
      consciousGates: data.conscious_gates,
      unconsciousGates: data.unconscious_gates,
      personalitySun: data.personality_sun,
      personalityEarth: data.personality_earth,
      designSun: data.design_sun,
      designEarth: data.design_earth,
      // Variables (if available)
      environment: data.variables?.environment,
      cognition: data.variables?.cognition,
      determination: data.variables?.determination,
      motivation: data.variables?.motivation,
      transference: data.variables?.transference,
    };
    const masterSynthesis = generateHDSynthesis(synthesisInput);
    
    // Format strategy for lookup
    const strategyKey = Object.keys(STRATEGY_TRANSLATIONS).find(
      key => strategy?.toLowerCase().includes(key.toLowerCase().split(' ')[0])
    );
    const strategyTranslation = strategyKey ? STRATEGY_TRANSLATIONS[strategyKey] : strategy || 'Follow your natural response pattern.';
    
    return (
      <>
        {/* Identity Card */}
        <View style={[styles.hdIdentityCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.hdIdentityMain}>
            <Text style={[styles.hdIdentityType, { color: theme.text }]}>{hdType}</Text>
            {profile && <Text style={[styles.hdIdentityProfile, { color: theme.textSecondary }]}>{profile} Profile</Text>}
          </View>
          <Text style={[styles.hdIdentityNote, { color: theme.textTertiary }]}>
            This lens reflects energy patterns, not identity.
          </Text>
        </View>

        {/* ============================================
            MASTER SYNTHESIS LAYER - Your Core Pattern
            Integrates Type × Authority × Profile into unified reading
            ============================================ */}
        {masterSynthesis && (
          <View style={[styles.hdMasterSynthesisContainer, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <View style={styles.hdMasterSynthesisHeader}>
              <Text style={[styles.hdMasterSynthesisTitle, { color: theme.text }]}>Your Core Pattern</Text>
              <Text style={[styles.hdMasterSynthesisSubtitle, { color: theme.textTertiary }]}>
                The integration of your design mechanics
              </Text>
            </View>
            
            {/* Core Pattern - The main operating dynamic */}
            <View style={[styles.hdSynthesisCoreCard, { borderColor: theme.accent }]}>
              <Text style={[styles.hdSynthesisCoreText, { color: theme.text }]}>
                {masterSynthesis.corePattern}
              </Text>
            </View>
            
            {/* Core Tension - The primary internal conflict */}
            <View style={styles.hdSynthesisTensionSection}>
              <Text style={[styles.hdSynthesisSectionLabel, { color: theme.warning || '#FF9800' }]}>
                THE CORE TENSION
              </Text>
              <Text style={[styles.hdSynthesisSectionText, { color: theme.textSecondary }]}>
                {masterSynthesis.coreTension}
              </Text>
            </View>
            
            {/* How This Plays Out - Real-life manifestations */}
            {masterSynthesis.howThisPlaysOut.length > 0 && (
              <View style={styles.hdSynthesisPlayOutSection}>
                <Text style={[styles.hdSynthesisSectionLabel, { color: theme.textTertiary }]}>
                  HOW THIS PLAYS OUT
                </Text>
                {masterSynthesis.howThisPlaysOut.map((pattern, idx) => (
                  <View key={idx} style={styles.hdSynthesisPlayOutItem}>
                    <Text style={[styles.hdSynthesisPlayOutBullet, { color: theme.accent }]}>•</Text>
                    <Text style={[styles.hdSynthesisPlayOutText, { color: theme.textSecondary }]}>
                      {pattern}
                    </Text>
                  </View>
                ))}
              </View>
            )}
            
            {/* Blind Spot - What you might miss */}
            <View style={styles.hdSynthesisBlindSpotSection}>
              <Text style={[styles.hdSynthesisSectionLabel, { color: theme.error || '#F44336' }]}>
                BLIND SPOT
              </Text>
              <Text style={[styles.hdSynthesisSectionText, { color: theme.textSecondary }]}>
                {masterSynthesis.blindSpot}
              </Text>
            </View>
            
            {/* Edge - Your unique advantage */}
            <View style={styles.hdSynthesisEdgeSection}>
              <Text style={[styles.hdSynthesisSectionLabel, { color: theme.success || '#4CAF50' }]}>
                YOUR EDGE
              </Text>
              <Text style={[styles.hdSynthesisSectionText, { color: theme.textSecondary }]}>
                {masterSynthesis.edge}
              </Text>
            </View>
            
            {/* What Supports You - Conditions for thriving */}
            {masterSynthesis.whatSupportsYou.length > 0 && (
              <View style={styles.hdSynthesisSupportsSection}>
                <Text style={[styles.hdSynthesisSectionLabel, { color: theme.accent }]}>
                  WHAT SUPPORTS YOU
                </Text>
                {masterSynthesis.whatSupportsYou.map((support, idx) => (
                  <View key={idx} style={styles.hdSynthesisPlayOutItem}>
                    <Text style={[styles.hdSynthesisPlayOutBullet, { color: theme.success || '#4CAF50' }]}>+</Text>
                    <Text style={[styles.hdSynthesisPlayOutText, { color: theme.textSecondary }]}>
                      {support}
                    </Text>
                  </View>
                ))}
              </View>
            )}
          </View>
        )}

        {/* EXISTING: Type Pattern Card - Keeps showing the single-mechanic view */}
        <View style={[styles.hdCorePatternCard, { backgroundColor: theme.surface, borderColor: theme.accent, borderLeftWidth: 3 }]}>
          <Text style={[styles.hdCorePatternLabel, { color: theme.accent }]}>THE TYPE PATTERN</Text>
          <Text style={[styles.hdCorePatternText, { color: theme.text }]}>
            {typePattern.compressedPatternLine}
          </Text>
          <Text style={[styles.hdCorePatternFacet, { color: theme.textSecondary }]}>
            {typePattern.facetLine}
          </Text>
        </View>

        {/* NEW: TENSION + GENIUS - What can go wrong / What works */}
        <View style={[styles.hdOverviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.hdTensionGeniusRow}>
            <View style={styles.hdTensionSection}>
              <Text style={[styles.hdTensionLabel, { color: theme.warning || '#FF9800' }]}>WHEN IT GOES WRONG</Text>
              <Text style={[styles.hdTensionText, { color: theme.textSecondary }]}>
                {typePattern.tensionLine}
              </Text>
            </View>
            <View style={styles.hdGeniusSection}>
              <Text style={[styles.hdGeniusLabel, { color: theme.success || '#4CAF50' }]}>WHEN IT WORKS</Text>
              <Text style={[styles.hdGeniusText, { color: theme.textSecondary }]}>
                {typePattern.geniusLine}
              </Text>
            </View>
          </View>
        </View>

        {/* How Clarity Comes Card (Authority) - With pattern compression */}
        <View style={[styles.hdOverviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>HOW YOU DECIDE</Text>
          <Text style={[styles.hdCorePatternText, { color: theme.text, fontSize: 15, lineHeight: 22, marginBottom: 12 }]}>
            {authorityPattern.compressedPatternLine}
          </Text>
          <Text style={[styles.hdOverviewCardBody, { color: theme.textSecondary }]}>
            {authorityPattern.facetLine}
          </Text>
        </View>

        {/* Cross-Lens Pattern Bridge - Shows patterns appearing across lenses */}
        <CrossLensPatternBridge
          hdTypePattern={typePattern.compressedPatternLine}
          hdAuthorityPattern={authorityPattern.compressedPatternLine}
        />

        {/* Where This Helps Card */}
        <View style={[styles.hdOverviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>WHERE THIS SHOWS UP</Text>
          <View style={styles.hdManifestationList}>
            <View style={[styles.hdManifestationItem, { borderBottomColor: theme.border }]}>
              <Text style={[styles.hdManifestationLabel, { color: theme.textTertiary }]}>Decisions</Text>
              <Text style={[styles.hdManifestationText, { color: theme.textSecondary }]}>{manifestations.decisions}</Text>
            </View>
            <View style={[styles.hdManifestationItem, { borderBottomColor: theme.border }]}>
              <Text style={[styles.hdManifestationLabel, { color: theme.textTertiary }]}>Work</Text>
              <Text style={[styles.hdManifestationText, { color: theme.textSecondary }]}>{manifestations.work}</Text>
            </View>
            <View style={[styles.hdManifestationItem, { borderBottomColor: theme.border }]}>
              <Text style={[styles.hdManifestationLabel, { color: theme.textTertiary }]}>Relationships</Text>
              <Text style={[styles.hdManifestationText, { color: theme.textSecondary }]}>{manifestations.relationships}</Text>
            </View>
            <View style={[styles.hdManifestationItem, { borderBottomColor: theme.border }]}>
              <Text style={[styles.hdManifestationLabel, { color: theme.textTertiary }]}>Energy management</Text>
              <Text style={[styles.hdManifestationText, { color: theme.textSecondary }]}>{manifestations.energy}</Text>
            </View>
          </View>
        </View>

        {/* Reflection Card */}
        <View style={[styles.hdReflectionCard, { backgroundColor: theme.surface, borderLeftColor: theme.accent }]}>
          <Text style={[styles.hdReflectionLabel, { color: theme.textTertiary }]}>A QUESTION TO SIT WITH</Text>
          <Text style={[styles.hdReflectionText, { color: theme.text }]}>
            "{TYPE_REFLECTIONS[hdType] || TYPE_REFLECTIONS['Generator']}"
          </Text>
        </View>

        {/* Subtle Link to Deep Dive */}
        <TouchableOpacity
          style={styles.hdSubtleLink}
          onPress={() => setActiveTab('deep_dive')}
        >
          <Text style={[styles.hdSubtleLinkText, { color: theme.textTertiary }]}>Explore Deep Dive</Text>
          <Text style={{ fontSize: 12, color: theme.textTertiary }}>›</Text>
        </TouchableOpacity>
      </>
    );
  };

  // ============================================
  // REFLECTION MODAL HELPER
  // ============================================
  
  // Open reflection modal with context-aware source and prompt
  const openReflection = (
    name: string,
    type: string,
    prompt: string,
    section?: string,
    id?: string,
    value?: string
  ) => {
    setReflectionSource({
      lens: 'human_design',
      section: section || 'deep_dive',
      name,
      type,
      id,
      value,
    });
    setReflectionPrompt(prompt);
    setShowReflectionModal(true);
  };

  // ============================================
  // TODAY TAB - TRANSIT SIGNAL DRIVEN
  // ============================================
  const renderTodayTab = () => {
    if (!data) return null;
    
    const hdType = data.core_mechanics?.type || 'Generator';
    const authority = data.core_mechanics?.authority || '';
    const isEmotional = authority.toLowerCase().includes('emotional');
    
    // Get transit signals (or fallback)
    const signals = transitSignals?.signals;
    const activation = signals?.activation;
    const opportunity = signals?.opportunity;
    const friction = signals?.friction;
    
    // Get field context for coherence
    const fieldContext = transitSignals?.field_context || fieldSignals?.field_context || {
      field_tone: 'clarity',
      clarity_level: 'high',
      pace: 'building',
      dominant_message: '',
    };
    const fieldTone = fieldContext.field_tone;
    const clarityLevel = fieldContext.clarity_level;
    const pace = fieldContext.pace;
    const dominantMessage = fieldContext.dominant_message;
    
    // ============================================
    // DOMINANT SIGNAL - The ONE central theme
    // ============================================
    // All content should orbit this central idea
    const dominantSignal = transitSignals?.dominant_signal || {
      theme: '',
      theme_id: '',
      confidence: 0,
      center_focus: null,
      field_alignment: false,
      today: '',
      week: '',
      month: '',
    };
    
    // ============================================
    // LANGUAGE VARIATION HELPERS (Fix repeated phrases)
    // ============================================
    
    // Vary sentence starters to avoid "You notice..." / "You may notice..." repetition
    const varyPhrasing = (text: string): string => {
      if (!text) return text;
      
      const variations: [RegExp, string[]][] = [
        [/^You notice\s/i, ["What rises now is ", "This lands as ", "The feeling is ", ""]],
        [/^You may notice\s/i, ["This can feel like ", "The pressure shows up as ", "In real life, this lands as ", ""]],
        [/^This is amplified by\s/i, ["This is colored by ", "This deepens with ", "Adding to this, "]],
        [/^This is intensified by\s/i, ["This gains weight from ", "Layered with ", "Made sharper by "]],
        [/^Your emotional waves? is\s/i, ["Your emotional rhythm ", "How you feel ", "Your inner tide "]],
      ];
      
      for (const [pattern, replacements] of variations) {
        if (pattern.test(text)) {
          const replacement = replacements[Math.floor(Math.random() * replacements.length)];
          return text.replace(pattern, replacement);
        }
      }
      return text;
    };
    
    // Clean grammar issues and awkward phrasing
    const cleanLanguage = (text: string): string => {
      if (!text) return text;
      
      return text
        // Fix grammar issues
        .replace(/centeris/gi, 'center is')
        .replace(/how you make correct feelings/gi, 'how you arrive at what feels right')
        .replace(/your emotional waves is/gi, 'your emotional rhythm is')
        .replace(/things are still forming/gi, 'something is taking shape')
        // Remove clunky HD explanations unless truly necessary
        .replace(/—the seat of your inner authority—?/gi, '')
        .replace(/the seat of your inner authority/gi, '')
        .replace(/—the seat of your decision-making—?/gi, '')
        // Make language more direct
        .replace(/You may feel/g, 'You feel')
        .replace(/You might notice/g, 'You notice')
        .replace(/can be more pronounced/gi, 'is heightened')
        .replace(/is more pronounced/gi, 'runs deeper')
        // Trim any resulting double spaces
        .replace(/\s+/g, ' ')
        .trim();
    };
    
    // ============================================
    // SIGNAL-DERIVED CONTENT GENERATORS
    // ============================================
    
    // ============================================
    // TODAY/WEEK/MONTH - DESCENT MODEL: Distinct roles, no repetition
    // ============================================
    
    // TODAY = immediate posture (what to do RIGHT NOW)
    const getTodayFromSignals = () => {
      if (dominantSignal.today) {
        return {
          bestUse: cleanLanguage(dominantSignal.today),
          watchFor: "forcing clarity before it arrives",
          reflectionPrompt: "What showed up today?"
        };
      }
      
      if (!activation) {
        return getTypeFallbackToday(hdType, isEmotional);
      }
      
      return {
        bestUse: cleanLanguage(activation.best_move || "Notice what's here."),
        watchFor: "forcing something before it's ready",
        reflectionPrompt: "What felt most present today?"
      };
    };
    
    // THIS WEEK = repeating pattern (what keeps RETURNING once urgency fades)
    const getWeekFromSignals = () => {
      if (dominantSignal.week) {
        return {
          theme: cleanLanguage(dominantSignal.week),
          frictionPattern: "confusing urgency with importance",
          reflectionPrompt: "What pattern kept showing up?"
        };
      }
      
      if (!activation) {
        return getTypeFallbackWeek(hdType, isEmotional);
      }
      
      return {
        theme: "Notice what keeps coming back once the urgency drops. That's what actually matters.",
        frictionPattern: "trying to resolve too early",
        reflectionPrompt: "What kept showing up this week?"
      };
    };
    
    // THIS MONTH = developmental lesson (what this PHASE is teaching)
    const getMonthFromSignals = () => {
      if (dominantSignal.month) {
        return {
          theme: cleanLanguage(dominantSignal.month),
          commonTrap: "treating how things feel now as permanent",
          reflectionPrompt: "What is this month teaching you?"
        };
      }
      
      if (!activation) {
        return getTypeFallbackMonth(hdType, isEmotional);
      }
      
      return {
        theme: "This phase may feel uncertain longer than you'd like. It's teaching you how to stay steady without full clarity.",
        commonTrap: "mistaking temporary feelings for lasting truth",
        reflectionPrompt: "What is this month teaching me?"
      };
    };
    
    // Type fallbacks for TODAY - Use new pattern compression layer
    const getTypeFallbackToday = (type: string, emotional: boolean) => {
      // Use the new pattern compression layer
      return getHDTodayContent(type, emotional ? 'Emotional' : 'Sacral', false);
    };
    
    // Type fallbacks for THIS WEEK - Use new pattern compression layer
    const getTypeFallbackWeek = (type: string, emotional: boolean) => {
      // Use the new pattern compression layer
      return getHDWeekContent(type, emotional ? 'Emotional' : 'Sacral', false);
    };
    
    // Type fallbacks for THIS MONTH - Use new pattern compression layer
    const getTypeFallbackMonth = (type: string, emotional: boolean) => {
      // Use the new pattern compression layer
      return getHDMonthContent(type, emotional ? 'Emotional' : 'Sacral', false);
    };

    const todayContent = getTodayFromSignals();
    const weekContent = getWeekFromSignals();
    const monthContent = getMonthFromSignals();

    // ============================================
    // RENDER FIELD SECTION (THE BIGGER SHIFT) - LIGHTER VERSION
    // ============================================
    const renderFieldSection = () => {
      // Get field signals
      const fieldSignalsList = fieldSignals?.signals || [];
      const hasMajorEvent = fieldSignals?.has_major_event || false;
      
      if (fieldLoading) {
        return (
          <View style={[styles.fieldLoadingContainer, { backgroundColor: theme.surface }]}>
            <ActivityIndicator color={theme.accent} size="small" />
            <Text style={[styles.fieldLoadingText, { color: theme.textSecondary }]}>
              Reading the sky...
            </Text>
          </View>
        );
      }
      
      if (!fieldSignalsList || fieldSignalsList.length === 0) {
        return null; // No major field events
      }

      return (
        <View style={styles.fieldSection}>
          {/* Field Title */}
          <Text style={[styles.fieldTitle, { color: theme.text }]}>The Bigger Shift</Text>
          
          {/* Field Signal Cards - Simplified: title + single body + CTA */}
          {fieldSignalsList.map((field: any, index: number) => (
            <View 
              key={index} 
              style={[
                styles.fieldCardCompact, 
                { 
                  backgroundColor: theme.surface, 
                  borderColor: hasMajorEvent && index === 0 ? theme.accent : theme.border,
                }
              ]}
            >
              <Text style={[styles.fieldCardTitle, { color: theme.text }]}>
                {field.headline}
              </Text>
              <Text style={[styles.fieldCardBody, { color: theme.textSecondary }]}>
                {field.what_happening}
              </Text>
              <TouchableOpacity
                style={styles.fieldCardCtaCompact}
                onPress={() => openReflection(
                  field.headline,
                  'field_signal',
                  `${field.what_happening} How is this showing up for me?`,
                  'today',
                  `field_${field.signal_type}`,
                  field.signal_type
                )}
                activeOpacity={0.7}
              >
                <Text style={[styles.fieldCardCtaText, { color: theme.accent }]}>Reflect →</Text>
              </TouchableOpacity>
            </View>
          ))}
        </View>
      );
    };

    // ============================================
    // RENDER HERO SECTION (WHAT'S ACTIVE NOW)
    // ============================================
    const renderHeroSection = () => {
      if (transitLoading) {
        return (
          <View style={[styles.heroLoadingContainer, { backgroundColor: theme.surface }]}>
            <ActivityIndicator color={theme.accent} />
            <Text style={[styles.heroLoadingText, { color: theme.textSecondary }]}>
              Computing your current transits...
            </Text>
          </View>
        );
      }
      
      if (!signals) {
        return null; // Fall back to type-only content below
      }

      return (
        <View style={styles.heroSection}>
          {/* Hero Title */}
          <Text style={[styles.heroTitle, { color: theme.text }]}>What's Active Now</Text>
          
          {/* Signal Card 1: Biggest Activation - The core thing happening */}
          {activation && (
            <View style={[styles.signalCard, styles.signalCardActivation, { backgroundColor: theme.surface, borderColor: theme.accent }]}>
              <Text style={[styles.signalCardLabel, { color: theme.accent }]}>ACTIVATION</Text>
              <Text style={[styles.signalCardTitle, { color: theme.text }]}>{activation.title}</Text>
              <Text style={[styles.signalCardBody, { color: theme.textSecondary }]}>
                {activation.how_shows_up}
              </Text>
              <Text style={[styles.signalCardAction, { color: theme.text }]}>
                {activation.best_move}
              </Text>
              <TouchableOpacity
                style={[styles.signalCardCta, { borderTopColor: theme.border }]}
                onPress={() => openReflection(
                  activation.title,
                  'transit_signal',
                  `${activation.how_shows_up} How is this showing up for me?`,
                  'today',
                  'signal_activation',
                  activation.center || ''
                )}
                activeOpacity={0.7}
              >
                <Text style={[styles.signalCardCtaText, { color: theme.accent }]}>Reflect →</Text>
              </TouchableOpacity>
            </View>
          )}
          
          {/* Signal Card 2: Opportunity - How to work with it */}
          {opportunity && (
            <View style={[styles.signalCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.signalCardLabel, { color: theme.success || '#4CAF50' }]}>OPPORTUNITY</Text>
              <Text style={[styles.signalCardTitle, { color: theme.text }]}>{opportunity.title}</Text>
              <Text style={[styles.signalCardBody, { color: theme.textSecondary }]}>
                {opportunity.how_shows_up}
              </Text>
              <Text style={[styles.signalCardAction, { color: theme.text }]}>
                {opportunity.best_move}
              </Text>
              <TouchableOpacity
                style={[styles.signalCardCta, { borderTopColor: theme.border }]}
                onPress={() => openReflection(
                  opportunity.title,
                  'transit_signal',
                  `${opportunity.how_shows_up} How can I work with this?`,
                  'today',
                  'signal_opportunity',
                  opportunity.center || ''
                )}
                activeOpacity={0.7}
              >
                <Text style={[styles.signalCardCtaText, { color: theme.accent }]}>Reflect →</Text>
              </TouchableOpacity>
            </View>
          )}
          
          {/* Signal Card 3: Friction - How you distort it */}
          {friction && (
            <View style={[styles.signalCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.signalCardLabel, { color: theme.warning || '#FF9800' }]}>WATCH FOR</Text>
              <Text style={[styles.signalCardTitle, { color: theme.text }]}>{friction.title}</Text>
              <Text style={[styles.signalCardBody, { color: theme.textSecondary }]}>
                {friction.how_shows_up}
              </Text>
              <Text style={[styles.signalCardAction, { color: theme.text }]}>
                {friction.best_move}
              </Text>
              <TouchableOpacity
                style={[styles.signalCardCta, { borderTopColor: theme.border }]}
                onPress={() => openReflection(
                  friction.title,
                  'transit_signal',
                  `${friction.how_shows_up} Where am I noticing this?`,
                  'today',
                  'signal_friction',
                  friction.center || ''
                )}
                activeOpacity={0.7}
              >
                <Text style={[styles.signalCardCtaText, { color: theme.accent }]}>Reflect →</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      );
    };

    return (
      <View style={styles.todayTabContainer}>
        {/* PAGE TITLE - Single instance only */}
        <View style={styles.todayIntroSection}>
          <Text style={[styles.todayIntroTitle, { color: theme.text }]}>Your Design Today</Text>
          <Text style={[styles.todayIntroSubtitle, { color: theme.textSecondary }]}>
            What's active in your chart right now.
          </Text>
        </View>
        
        {/* 1. DOMINANT THEME - The central truth */}
        {dominantSignal.theme && (
          <View style={styles.dominantThemeSection}>
            <Text style={[styles.dominantThemeLabel, { color: theme.textTertiary }]}>THE THROUGH-LINE</Text>
            <Text style={[styles.dominantThemeText, { color: theme.text }]}>
              {dominantSignal.theme.replace('—', '. ').replace('don\'t', 'Don\'t')}
            </Text>
          </View>
        )}
        
        {/* 2. WHAT'S ACTIVE NOW - Personal HD signals first (experience before explanation) */}
        {renderHeroSection()}
        
        {/* Divider */}
        <View style={[styles.todayDivider, { backgroundColor: theme.border }]} />
        
        {/* 3. THE BIGGER SHIFT - Sky context after personal experience */}
        {renderFieldSection()}
        
        {/* Divider if field signals exist */}
        {fieldSignals?.signals?.length > 0 && (
          <View style={[styles.todayDivider, { backgroundColor: theme.border }]} />
        )}
        
        {/* 4. YOUR TIMING - How it unfolds */}
        <View style={styles.timingSectionHeader}>
          <Text style={[styles.timingSectionTitle, { color: theme.text }]}>Your Timing</Text>
        </View>

        {/* TODAY */}
        <View style={[styles.timingCardCompact, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.timingCardTitleCompact, { color: theme.text }]}>Today</Text>
          <Text style={[styles.timingCardMainText, { color: theme.textSecondary }]}>{todayContent.bestUse}</Text>
          <Text style={[styles.timingCardWatchText, { color: theme.textTertiary }]}>Watch for: {todayContent.watchFor}</Text>
          <TouchableOpacity
            style={styles.timingReflectCtaCompact}
            onPress={() => openReflection('Today', 'timing', todayContent.reflectionPrompt, 'today', 'today_timing', hdType)}
            activeOpacity={0.7}
          >
            <Text style={[styles.timingReflectCtaText, { color: theme.accent }]}>Reflect →</Text>
          </TouchableOpacity>
        </View>

        {/* THIS WEEK */}
        <View style={[styles.timingCardCompact, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.timingCardTitleCompact, { color: theme.text }]}>This Week</Text>
          <Text style={[styles.timingCardMainText, { color: theme.textSecondary }]}>{weekContent.theme}</Text>
          <Text style={[styles.timingCardWatchText, { color: theme.textTertiary }]}>Watch for: {weekContent.frictionPattern}</Text>
          <TouchableOpacity
            style={styles.timingReflectCtaCompact}
            onPress={() => openReflection('This Week', 'timing', weekContent.reflectionPrompt, 'today', 'week_timing', hdType)}
            activeOpacity={0.7}
          >
            <Text style={[styles.timingReflectCtaText, { color: theme.accent }]}>Reflect →</Text>
          </TouchableOpacity>
        </View>

        {/* THIS MONTH */}
        <View style={[styles.timingCardCompact, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.timingCardTitleCompact, { color: theme.text }]}>This Month</Text>
          <Text style={[styles.timingCardMainText, { color: theme.textSecondary }]}>{monthContent.theme}</Text>
          <Text style={[styles.timingCardWatchText, { color: theme.textTertiary }]}>Watch for: {monthContent.commonTrap}</Text>
          <TouchableOpacity
            style={styles.timingReflectCtaCompact}
            onPress={() => openReflection('This Month', 'timing', monthContent.reflectionPrompt, 'today', 'month_timing', hdType)}
            activeOpacity={0.7}
          >
            <Text style={[styles.timingReflectCtaText, { color: theme.accent }]}>Reflect →</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  // ============================================
  // DEEP DIVE TAB - NEW CARD-BASED STRUCTURE
  // ============================================
  
  // Accordion Card Component for Core Mechanics in Deep Dive
  const renderMechanicAccordion = (
    id: string,
    title: string,
    subtitle: string | null,
    content: { story: string; showsUp: string; challenge: string; tips: string },
    askContext: string,
    reflectionPrompt: string
  ) => {
    const isExpanded = expandedMechanic === id;
    
    return (
      <View style={[styles.accordionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        {/* Collapsed Header - always visible */}
        <TouchableOpacity
          style={styles.accordionHeader}
          onPress={() => setExpandedMechanic(isExpanded ? null : id)}
          activeOpacity={0.7}
        >
          <View style={styles.accordionHeaderContent}>
            <Text style={[styles.accordionTitle, { color: theme.text }]}>{title}</Text>
            {subtitle && (
              <Text style={[styles.accordionSubtitle, { color: theme.textSecondary }]}>{subtitle}</Text>
            )}
          </View>
          <Ionicons 
            name={isExpanded ? 'chevron-up' : 'chevron-down'} 
            size={20} 
            color={theme.textTertiary} 
          />
        </TouchableOpacity>
        
        {/* Expanded Content */}
        {isExpanded && (
          <View style={[styles.accordionContent, { borderTopColor: theme.border }]}>
            {/* Story */}
            <View style={styles.accordionSection}>
              <Text style={[styles.accordionSectionLabel, { color: theme.textTertiary }]}>STORY</Text>
              <Text style={[styles.accordionSectionText, { color: theme.textSecondary }]}>{content.story}</Text>
            </View>
            
            {/* How This Shows Up */}
            <View style={styles.accordionSection}>
              <Text style={[styles.accordionSectionLabel, { color: theme.textTertiary }]}>HOW THIS SHOWS UP</Text>
              <Text style={[styles.accordionSectionText, { color: theme.textSecondary }]}>{content.showsUp}</Text>
            </View>
            
            {/* Challenge */}
            <View style={styles.accordionSection}>
              <Text style={[styles.accordionSectionLabel, { color: theme.textTertiary }]}>CHALLENGE</Text>
              <Text style={[styles.accordionSectionText, { color: theme.textSecondary }]}>{content.challenge}</Text>
            </View>
            
            {/* Practical Tips */}
            <View style={styles.accordionSection}>
              <Text style={[styles.accordionSectionLabel, { color: theme.textTertiary }]}>PRACTICAL TIPS</Text>
              <Text style={[styles.accordionSectionText, { color: theme.textSecondary }]}>{content.tips}</Text>
            </View>
            
            {/* Reflect CTA */}
            <TouchableOpacity
              style={[styles.accordionAskCta, { borderTopColor: theme.border }]}
              onPress={() => openReflection(
                title,
                id,
                reflectionPrompt,
                'deep_dive',
                `mechanic_${id}`,
                subtitle || undefined
              )}
              activeOpacity={0.7}
            >
              <Text style={[styles.accordionAskCtaText, { color: theme.accent }]}>Reflect on this →</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };

  // Get Type card content - Mirror pattern language
  const getTypeCardContent = (type: string) => {
    const content: Record<string, { story: string; showsUp: string; challenge: string; tips: string }> = {
      'Generator': {
        story: 'You run on a motor that needs the right fuel. When you\'re doing work you actually love, you could go all day.',
        showsUp: 'In real life, you light up when something lands right. Your gut pulls you toward things—or pushes back hard.',
        challenge: 'The trap is saying yes to keep the peace. Then you\'re grinding on something that drains you.',
        tips: 'Wait for the gut pull before you commit. If it\'s not a hell yes, it\'s probably a no.'
      },
      'Manifesting Generator': {
        story: 'You move fast when you\'re lit up. You skip steps, change lanes, and don\'t always finish what you start—and that\'s fine.',
        showsUp: 'People notice your speed. You bounce between things. You find shortcuts others miss.',
        challenge: 'The trap is forcing yourself to stay on one track. Or feeling guilty for pivoting.',
        tips: 'Respond first, then move. Let people know when you\'re about to shift—it saves friction.'
      },
      'Projector': {
        story: 'You see things others don\'t. Systems, people, what\'s really going on underneath.',
        showsUp: 'People come to you when they\'re stuck. You have a way of cutting through noise—when they\'re ready to hear it.',
        challenge: 'The trap is offering insight before anyone asked. That\'s when it backfires.',
        tips: 'Wait until you\'re invited. Rest more than feels normal. Your value isn\'t about output.'
      },
      'Manifestor': {
        story: 'You\'re built to start things. Urges hit you and you move—often before anyone else sees why.',
        showsUp: 'People feel your impact. You create ripples, whether you mean to or not.',
        challenge: 'The trap is holding back to avoid conflict. Or moving without telling anyone and creating chaos.',
        tips: 'Inform before you act. Not for permission—just so people aren\'t blindsided.'
      },
      'Reflector': {
        story: 'You take in everything around you. You\'re a mirror—what you feel often isn\'t yours.',
        showsUp: 'You shift depending on where you are and who\'s there. Your wisdom comes from sampling, not certainty.',
        challenge: 'The trap is deciding too fast. You need time—real time—to know what\'s true for you.',
        tips: 'Big decisions need a full month. Your environment matters more than most people\'s. Choose it carefully.'
      }
    };
    return content[type] || content['Generator'];
  };

  // Get Authority card content - Mirror pattern language
  const getAuthorityCardContent = (authority: string) => {
    const normalizedAuth = authority?.toLowerCase() || '';
    const content: Record<string, { story: string; showsUp: string; challenge: string; tips: string }> = {
      'emotional': {
        story: 'You ride waves. Your clarity doesn\'t come instantly—it builds over time as emotions settle.',
        showsUp: 'You feel differently about the same thing on different days. That\'s not confusion—that\'s your process.',
        challenge: 'The trap is deciding when you\'re high or low. Both distort what\'s actually true.',
        tips: 'Sleep on it. Check again tomorrow. Real clarity feels calm, not urgent.'
      },
      'sacral': {
        story: 'Your body knows before your mind does. There\'s a pull toward yes—or a wall that says no.',
        showsUp: 'You make sounds. You feel expansion or contraction in your gut. It\'s physical.',
        challenge: 'The trap is overriding that response because it doesn\'t make logical sense.',
        tips: 'Trust the first hit. Ask yourself yes/no questions out loud and feel the response.'
      },
      'splenic': {
        story: 'Your knowing comes fast and quiet. Once. In the moment. Then it\'s gone.',
        showsUp: 'You get instincts. Subtle hits about timing, safety, what\'s off.',
        challenge: 'The trap is second-guessing that first hit. Once you analyze, you\'ve lost it.',
        tips: 'Act on the first knowing. Don\'t wait for your mind to agree.'
      },
      'ego': {
        story: 'Your clarity lives in what you actually want. Not what you should want—what you really desire.',
        showsUp: 'When your heart is in it, you can move mountains. When it\'s not, everything stalls.',
        challenge: 'The trap is committing to things you don\'t actually want. Then you can\'t sustain them.',
        tips: 'Ask: Do I actually want this? If your heart says no, don\'t promise it.'
      },
      'self-projected': {
        story: 'You find clarity by hearing yourself speak. Not thinking—talking.',
        showsUp: 'You say something out loud and suddenly know if it\'s true. Your voice carries your truth.',
        challenge: 'The trap is processing alone or asking for advice. You need to hear yourself, not others.',
        tips: 'Talk through decisions with someone who listens. Pay attention to your own words, not their opinions.'
      },
      'mental': {
        story: 'Your clarity comes through conversation over time. Different places, different talks.',
        showsUp: 'You process out loud. The answer emerges through dialogue—not internal analysis.',
        challenge: 'The trap is isolating or expecting immediate certainty. Neither works for you.',
        tips: 'Talk to trusted people. In different settings. Let clarity build across conversations.'
      },
      'lunar': {
        story: 'Your clarity takes a full cycle. About a month. That\'s not slow—that\'s thorough.',
        showsUp: 'You feel different about things as the month moves. That\'s information, not indecision.',
        challenge: 'The trap is pressure to decide fast. That almost always backfires.',
        tips: 'Mark when decisions show up. Give them 28 days before you commit.'
      },
      'none': {
        story: 'Your clarity is environmental. Where you are changes what you know.',
        showsUp: 'Some places make you clear. Others muddy everything.',
        challenge: 'The trap is not recognizing how much your setting affects your knowing.',
        tips: 'Only make important decisions in places where you feel grounded.'
      }
    };
    
    for (const [key, value] of Object.entries(content)) {
      if (normalizedAuth.includes(key)) return value;
    }
    return content['emotional'];
  };

  // Get Profile card content - more human tone
  const getProfileCardContent = (profile: string) => {
    const content: Record<string, { story: string; showsUp: string; challenge: string; tips: string }> = {
      '1/3': {
        story: 'You need to understand things deeply before you move. Then you learn by doing—often the hard way.',
        showsUp: 'Researching before committing. Learning most from mistakes. Starting over doesn\'t scare you.',
        challenge: 'The trap is feeling like you\'re always behind or always fixing what went wrong.',
        tips: 'Both phases matter—the research AND the bumps. Neither is wasted.'
      },
      '1/4': {
        story: 'You dig into things deeply, then share what you know through the people closest to you.',
        showsUp: 'You don\'t broadcast—you influence through real relationships. Your network trusts your depth.',
        challenge: 'The trap is trying to reach people you don\'t actually know, or sharing before you\'re ready.',
        tips: 'Build the foundation first. Your people will carry it forward when it\'s solid.'
      },
      '2/4': {
        story: 'You have natural talents that others often see before you do. Your gifts emerge through connection.',
        showsUp: 'People call on you for things you didn\'t even know you were good at. You\'re seen.',
        challenge: 'The trap is being pulled out of needed alone time, or not believing your own gifts.',
        tips: 'Protect your retreat. Trust that what you have is enough—others already see it.'
      },
      '2/5': {
        story: 'You have quiet gifts, but people project expectations onto you—often ones you didn\'t ask for.',
        showsUp: 'Being called out of solitude to help. Others seeing you as the answer to their problem.',
        challenge: 'The trap is meeting projections you can\'t deliver on, or losing all your alone time.',
        tips: 'Guard your solitude. Say no to projections that aren\'t actually yours to carry.'
      },
      '3/5': {
        story: 'You learn by trial and error, and people tend to see you as someone who can fix things.',
        showsUp: 'Wisdom from what hasn\'t worked. Being asked to solve problems you didn\'t create.',
        challenge: 'The trap is endless experimentation plus unrealistic expectations from others.',
        tips: 'Your experiments are your education. Choose which projections are worth engaging.'
      },
      '3/6': {
        story: 'Your life has phases: experiment hard early, step back and observe, then embody what you\'ve learned.',
        showsUp: 'Intense trial-and-error in youth. Growing objectivity. Eventually becoming the example.',
        challenge: 'The trap is exhaustion in the early phase, or pressure to be perfect once you\'re seen as wise.',
        tips: 'Trust your current phase. Don\'t rush—each stage builds on the last.'
      },
      '4/6': {
        story: 'Relationships matter deeply throughout your life. Your wisdom grows through connection and time.',
        showsUp: 'Key relationships that shape each phase. Authority that emerges through people who know you.',
        challenge: 'The trap is pulling away from your network when you need them most.',
        tips: 'Your people carry you through all phases. Keep nurturing the relationships that matter.'
      },
      '4/1': {
        story: 'You build deep knowledge and share it through close relationships. Security matters.',
        showsUp: 'Research shared through trusted people. Needing both intellectual and social stability.',
        challenge: 'The trap is rigidity when your foundations or relationships need to shift.',
        tips: 'Build strong roots. But stay flexible when the ground moves.'
      },
      '5/1': {
        story: 'People project onto you quickly. You deliver best when you\'ve done the work to back it up.',
        showsUp: 'Strangers trust you before they know you. You can meet their expectations—if you\'ve prepared.',
        challenge: 'The trap is carrying projections you haven\'t built the foundation to meet.',
        tips: 'Research first. Only step into projections your knowledge actually supports.'
      },
      '5/2': {
        story: 'People expect you to save them, but you need significant time alone to stay sane.',
        showsUp: 'Being called out constantly. Natural talents that emerge when genuinely needed.',
        challenge: 'The trap is losing your solitude to demands that weren\'t really yours.',
        tips: 'Hermit time is non-negotiable. Engage only with calls that genuinely fit.'
      },
      '6/2': {
        story: 'Your life has phases, and you have quiet gifts that emerge when people call on you.',
        showsUp: 'Eventual wisdom combined with natural talents. Being recognized and called forward.',
        challenge: 'The trap is not honoring your need for retreat between calls.',
        tips: 'Your gifts will be called when needed. Return to rest so you have something to give.'
      },
      '6/3': {
        story: 'Your life has phases, and you learn through constant experimentation across all of them.',
        showsUp: 'Many things tried. Many things dropped. Eventual authority earned through living it.',
        challenge: 'The trap is exhaustion from the sheer volume of experiments.',
        tips: 'Every experiment contributes to eventual wisdom. Nothing is wasted.'
      }
    };
    return content[profile] || { story: 'You have your own way of moving through life and learning.', showsUp: 'Patterns unique to how you engage with experience.', challenge: 'The trap is resisting your natural rhythm.', tips: 'Pay attention to what consistently works for you.' };
  };

  // Get Incarnation Cross card content - Mirror pattern language
  const getIncarnationCrossCardContent = (crossName: string) => {
    const angle = getCrossAngle(crossName);
    const content: Record<string, { story: string; showsUp: string; challenge: string; tips: string }> = {
      'Right Angle': {
        story: 'Your life is mostly about you. Your own journey, your own growth. That\'s not selfish—that\'s the design.',
        showsUp: 'You keep circling back to your own lessons. The people you meet serve your path, not the other way around.',
        challenge: 'The trap is thinking you should be more outward-focused. You\'re not here to save anyone.',
        tips: 'Stop apologizing for your focus on yourself. That IS the curriculum.'
      },
      'Left Angle': {
        story: 'Your life unfolds through others. Key people change everything. You\'re here for the encounters.',
        showsUp: 'Certain meetings shift your whole trajectory. Your purpose is tangled up with other people\'s.',
        challenge: 'The trap is trying to control who shows up or losing yourself in their agendas.',
        tips: 'Trust the connections. They\'re happening for reasons you may not see yet.'
      },
      'Juxtaposition': {
        story: 'You\'re here to do one specific thing. Your life keeps returning to the same core role.',
        showsUp: 'Themes repeat. You feel most alive when you\'re doing that one thing you\'re built for.',
        challenge: 'The trap is fighting the narrowness. Wanting more flexibility than you have.',
        tips: 'Lean into the focus. The specificity is the gift.'
      }
    };
    return content[angle] || content['Right Angle'];
  };

  // ============================================
  // REFLECTION PROMPT GENERATORS (context-aware)
  // ============================================
  
  const getTypeReflectionPrompt = (type: string): string => {
    const prompts: Record<string, string> = {
      'Generator': 'Where am I saying yes out of obligation instead of genuine response?',
      'Manifesting Generator': 'What am I forcing myself to finish that has already lost its spark?',
      'Projector': 'Where am I giving guidance that wasn\'t actually asked for?',
      'Manifestor': 'What impulse have I been suppressing to keep the peace?',
      'Reflector': 'What am I absorbing from my environment that isn\'t actually mine?'
    };
    return prompts[type] || prompts['Generator'];
  };
  
  const getAuthorityReflectionPrompt = (authority: string): string => {
    const normalizedAuth = authority?.toLowerCase() || '';
    
    if (normalizedAuth.includes('emotional')) {
      return 'What decision am I rushing that needs more time to become clear?';
    }
    if (normalizedAuth.includes('sacral')) {
      return 'When did I last override my gut response—and what happened?';
    }
    if (normalizedAuth.includes('splenic')) {
      return 'What instant knowing have I been second-guessing?';
    }
    if (normalizedAuth.includes('ego')) {
      return 'What have I committed to that my heart was never really in?';
    }
    if (normalizedAuth.includes('self')) {
      return 'What truth do I need to hear myself say out loud?';
    }
    if (normalizedAuth.includes('lunar')) {
      return 'What decision am I rushing that needs a full cycle to reveal itself?';
    }
    if (normalizedAuth.includes('mental')) {
      return 'Who do I need to talk to—not for their answer, but to hear my own?';
    }
    return 'How does my body respond when I consider this choice?';
  };
  
  const getProfileReflectionPrompt = (profile: string): string => {
    const line1 = profile?.split('/')?.[0] || '';
    const line2 = profile?.split('/')?.[1] || '';
    
    const prompts: Record<string, string> = {
      '1': 'What foundation do I need before I can move forward with confidence?',
      '2': 'What natural gift are others seeing in me that I haven\'t fully owned?',
      '3': 'What have I learned from a recent \'failure\' that is actually wisdom?',
      '4': 'Which relationship is most important to nurture right now?',
      '5': 'What projection am I carrying that isn\'t mine to fulfill?',
      '6': 'What phase of life am I in, and what does this stage require of me?'
    };
    
    return prompts[line1] || prompts[line2] || 'How is my profile showing up in my life right now?';
  };
  
  const getCenterReflectionPrompt = (centerName: string, isDefined: boolean): string => {
    const name = (centerName || '').toLowerCase();
    const prompts: Record<string, { defined: string; undefined: string }> = {
      'head': { 
        defined: 'What question keeps returning because it truly matters?',
        undefined: 'Which mental pressures am I absorbing that aren\'t mine to solve?'
      },
      'ajna': { 
        defined: 'Where am I clinging to my way of thinking when flexibility would serve better?',
        undefined: 'Whose certainty am I borrowing? What would I think if I gave myself space?'
      },
      'throat': { 
        defined: 'When am I speaking just to fill space instead of saying what matters?',
        undefined: 'What needs to be said that I\'ve been holding back?'
      },
      'g': { 
        defined: 'Am I following my own direction, or someone else\'s path?',
        undefined: 'What environment brings out the version of me I want to be?'
      },
      'heart': { 
        defined: 'What have I promised that I need to either honor or release?',
        undefined: 'Where am I trying to prove my worth instead of simply being?'
      },
      'ego': { 
        defined: 'What have I promised that I need to either honor or release?',
        undefined: 'Where am I trying to prove my worth instead of simply being?'
      },
      'spleen': { 
        defined: 'What instinct have I been ignoring?',
        undefined: 'Which fears am I holding that aren\'t actually mine?'
      },
      'solar plexus': { 
        defined: 'What decision needs more time before I can see it clearly?',
        undefined: 'Whose emotions am I carrying right now?'
      },
      'sacral': { 
        defined: 'What is my gut telling me about where to put my energy?',
        undefined: 'Am I resting enough, or borrowing energy I don\'t have?'
      },
      'root': { 
        defined: 'What pressure is mine to handle—and what is not my emergency?',
        undefined: 'What urgency am I feeling that isn\'t actually urgent?'
      }
    };
    
    const key = Object.keys(prompts).find(k => name.includes(k));
    if (key) {
      return isDefined ? prompts[key].defined : prompts[key].undefined;
    }
    return isDefined 
      ? 'How does this consistent energy show up in my life?'
      : 'What am I amplifying from others that isn\'t mine?';
  };
  
  const getGateReflectionPrompt = (gateNum: number | string, gateName: string): string => {
    // Default reflection prompt for gates - can be expanded with specific prompts per gate
    return `How does the energy of ${gateName} (Gate ${gateNum}) show up in my patterns?`;
  };
  
  const getSphereReflectionPrompt = (sphereName: string, geneKey: number): string => {
    const sphere = (sphereName || '').toLowerCase();
    const prompts: Record<string, string> = {
      'life\'s work': 'Where is this pattern already unfolding in my life—whether I intended it or not?',
      'evolution': 'What would change if I lived more from the gift than the shadow?',
      'radiance': 'How does this energy want to express through me when I\'m most authentic?',
      'purpose': 'What purpose keeps showing up, even when I\'m not trying?',
      'attraction': 'What am I drawing toward me—and is it aligned with who I\'m becoming?',
      'iq': 'How do I naturally process information and what patterns emerge?',
      'eq': 'What emotional intelligence wants to develop through me?',
      'vocation': 'What work feels like play when I\'m in alignment?',
      'culture': 'What contribution am I here to make to the collective?',
      'brand': 'What do I want to be known for?',
      'pearl': 'What prosperity pattern is trying to emerge?',
      'core': 'What is the essential wound I\'m here to transform?',
      'genius': 'What natural gift am I not fully owning?'
    };
    
    for (const [key, prompt] of Object.entries(prompts)) {
      if (sphere.includes(key)) return prompt;
    }
    return `What is Gene Key ${geneKey} trying to teach me through this sphere?`;
  };

  // DEEP DIVE TAB - with mode toggle (Explore / Reading)
  const renderDeepDiveTab = () => {
    if (!data) return null;
    
    return (
      <>
        {/* KEYSTONE EXPLANATION: Where this pattern comes from */}
        {renderKeystoneExplanation()}
        
        {/* Mode Toggle */}
        <View style={[styles.deepDiveModeToggle, { backgroundColor: theme.background, borderColor: theme.border }]}>
          <TouchableOpacity
            style={[styles.deepDiveModeButton, deepDiveMode === 'explore' && { backgroundColor: theme.surface }]}
            onPress={() => setDeepDiveMode('explore')}
            activeOpacity={0.7}
          >
            <Text style={[styles.deepDiveModeButtonText, { color: deepDiveMode === 'explore' ? theme.text : theme.textTertiary }]}>Explore</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.deepDiveModeButton, deepDiveMode === 'reading' && { backgroundColor: theme.surface }]}
            onPress={() => setDeepDiveMode('reading')}
            activeOpacity={0.7}
          >
            <Text style={[styles.deepDiveModeButtonText, { color: deepDiveMode === 'reading' ? theme.text : theme.textTertiary }]}>Reading</Text>
          </TouchableOpacity>
        </View>
        
        {/* Conditional render based on mode */}
        {deepDiveMode === 'explore' ? renderExploreMode() : renderReadingMode()}
      </>
    );
  };
  
  // ARCHITECTURE LOCK: Lenses explain the Keystone, they don't display it.
  // This renders ONLY the lens-specific explanation (WHERE THIS COMES FROM)
  // The full Keystone card lives on Home. KeystoneReferenceLink handles navigation.
  const renderKeystoneExplanation = () => {
    if (!data?.keystone_explanation) return null;
    
    const { 
      lens_explanation_title, 
      lens_explanation_body 
    } = data.keystone_explanation;

    return (
      <View style={[styles.keystoneExplanationCard, { backgroundColor: theme.surface, borderColor: theme.accent }]}>
        {/* HD Mechanism Explanation ONLY - No Keystone anchor/sequence */}
        <View style={styles.keystoneExplanation}>
          <Text style={[styles.keystoneRoleLabel, { color: theme.accent }]}>
            WHERE THIS COMES FROM
          </Text>
          <Text style={[styles.keystoneExplanationTitle, { color: theme.text }]}>
            {lens_explanation_title}
          </Text>
          <Text style={[styles.keystoneExplanationBody, { color: theme.textSecondary }]}>
            {lens_explanation_body}
          </Text>
        </View>
      </View>
    );
  };
  
  // EXPLORE MODE - Using CollapsibleCard system for progressive disclosure
  const renderExploreMode = () => {
    // DEFENSIVE GUARD: Check if data exists
    if (!data) {
      console.log('[HD_DEBUG] renderExploreMode - data is null');
      return (
        <View style={[styles.loadingFallback, { backgroundColor: theme.surface }]}>
          <Text style={[styles.loadingFallbackText, { color: theme.textSecondary }]}>
            Your design data is still loading...
          </Text>
        </View>
      );
    }
    
    // DEBUG LOGGING
    console.log('[HD_DEBUG] renderExploreMode', {
      hasData: !!data,
      hasCentersData: !!centersData,
      centersCount: Array.isArray(centersData?.centers) ? centersData.centers.length : 'not array',
      hasGatesData: !!gatesData,
      gatesCount: Array.isArray(gatesData?.gates) ? gatesData.gates.length : 'not array',
      type: data.core_mechanics?.type,
      authority: data.core_mechanics?.authority,
    });
    
    // DEFENSIVE GUARD: Safely get centers array
    const safeCenters = Array.isArray(centersData?.centers) ? centersData.centers : [];
    const safeGates = Array.isArray(gatesData?.gates) ? gatesData.gates : [];
    
    // Get Mirror cards for core mechanics
    const typeMirrorCard = getTypeMirrorCard(data.core_mechanics?.type || '');
    const authorityMirrorCard = getAuthorityMirrorCard(data.core_mechanics?.authority || '');
    const profileMirrorCard = getProfileMirrorCard(data.core_mechanics?.profile || '');
    const crossMirrorCard = getCrossMirrorCard(data.core_mechanics?.incarnation_cross || '');
    
    // Get dominant gate for Pattern State
    const dominantGate = typeof data.personality_sun === 'object' 
      ? data.personality_sun?.gate 
      : (typeof data.personality_sun === 'number' ? data.personality_sun : null);
    
    // Generate Pattern Thread
    const patternThread = generatePatternThread({
      type: data.core_mechanics?.type || '',
      authority: data.core_mechanics?.authority || '',
      profile: data.core_mechanics?.profile || '',
      personalitySun: data.personality_sun,
      designSun: data.design_sun,
      channels: Array.isArray(data.channels) ? data.channels : [],
      definedCenters: safeCenters.filter((c: any) => c && c.defined).map((c: any) => c.center) || [],
      undefinedCenters: safeCenters.filter((c: any) => c && !c.defined).map((c: any) => c.center) || [],
    });
    
    // Generate Pattern State (Real-Time Positioning)
    const patternState = generatePatternState({
      type: data.core_mechanics?.type || '',
      authority: data.core_mechanics?.authority || '',
      dominantGate: dominantGate,
    });
    
    // Build cross-link context for cards
    const crossLinkContext: CrossLinkContext = {
      type: data.core_mechanics?.type || '',
      authority: data.core_mechanics?.authority || '',
      profile: data.core_mechanics?.profile || '',
      definedCenters: safeCenters.filter((c: any) => c && c.defined).map((c: any) => c.center) || [],
      undefinedCenters: safeCenters.filter((c: any) => c && !c.defined).map((c: any) => c.center) || [],
      channels: Array.isArray(data.channels) ? data.channels : [],
      personalitySun: data.personality_sun,
      designSun: data.design_sun,
      consciousGates: safeGates.filter((g: any) => g && g.is_conscious).map((g: any) => g.gate_number || g.gate) || [],
      unconsciousGates: safeGates.filter((g: any) => g && !g.is_conscious).map((g: any) => g.gate_number || g.gate) || [],
    };
    
    return (
      <>
        {/* 1. PATTERN THREAD - The unified narrative */}
        {patternThread && renderPatternThread(patternThread)}
        
        {/* 2. PATTERN STATE - Where you are right now (NEW) */}
        {patternState && renderPatternState(patternState)}
        
        {/* 3. CORE SYNTHESIS - The existing synthesis card */}
        {renderCoreSynthesis()}
        
        {/* 4. BODY GRAPH - Visual overview */}
        {renderImprovedBodygraph()}
        
        {/* 5. TYPE / AUTHORITY / PROFILE - Core Mechanics */}
        <SectionHeader title="Core Mechanics" count={4} icon="◎" />
        
        {/* Type Card - Default OPEN (most important) */}
        {typeMirrorCard && renderMechanicCollapsibleCardWithCrossLink(
          'type',
          typeMirrorCard,
          data.core_mechanics?.type || '',
          true, // Default open
          getTypeCrossLink(data.core_mechanics?.type || '', data.core_mechanics?.authority || '')
        )}
        
        {/* Authority Card - Default CLOSED */}
        {authorityMirrorCard && renderMechanicCollapsibleCardWithCrossLink(
          'authority',
          authorityMirrorCard,
          data.core_mechanics?.authority || '',
          false,
          getAuthorityCrossLink(data.core_mechanics?.authority || '', data.core_mechanics?.type || '')
        )}
        
        {/* Profile Card - Default CLOSED */}
        {profileMirrorCard && renderMechanicCollapsibleCardWithCrossLink(
          'profile',
          profileMirrorCard,
          data.core_mechanics?.profile || '',
          false,
          null // No cross-link for profile
        )}
        
        {/* Incarnation Cross Card - Default CLOSED */}
        {crossMirrorCard && renderMechanicCollapsibleCardWithCrossLink(
          'cross',
          crossMirrorCard,
          data.core_mechanics?.incarnation_cross || '',
          false,
          null // No cross-link for cross
        )}
        
        {/* 5. CENTERS SECTION */}
        {centersData && (
          <CollapsibleCard
            title="Centers"
            subtitle="Your consistent vs. open energies"
            badge={`${centersData.centers?.length || 0}`}
            defaultOpen={false}
            priority="medium"
          >
            {renderCentersCardsWithCrossLinks(crossLinkContext)}
          </CollapsibleCard>
        )}
        
        {/* 6. GATES SECTION */}
        {gatesData && (
          <CollapsibleCard
            title="Gates"
            subtitle="Your activated energies"
            badge={`${gatesData.gates?.length || 0}`}
            defaultOpen={false}
            priority="medium"
          >
            {renderGatesCardsWithCrossLinks(crossLinkContext)}
          </CollapsibleCard>
        )}
        
        {/* 7. GENE KEYS SEQUENCES SECTION */}
        {renderGeneKeysUpgraded()}
      </>
    );
  };
  
  // READING MODE - Flowing narrative (PDF-style)
  const renderReadingMode = () => {
    if (!data?.core_mechanics) return null;
    
    const { type, authority, profile, strategy } = data.core_mechanics;
    const notSelf = (data.core_mechanics as any).not_self;
    const definedCenters = centersData?.centers?.filter((c: any) => c.defined) || [];
    const undefinedCenters = centersData?.centers?.filter((c: any) => !c.defined) || [];
    
    return (
      <View style={styles.readingModeContainer}>
        {/* SECTION 1: Your Core Pattern */}
        <View style={styles.readingSection}>
          <Text style={[styles.readingSectionTitle, { color: theme.text }]}>Your Core Pattern</Text>
          <Text style={[styles.readingParagraph, { color: theme.textSecondary }]}>
            {getReadingCorePattern(type || '', profile || '')}
          </Text>
        </View>
        
        {/* SECTION 2: How You Make Decisions */}
        <View style={styles.readingSection}>
          <Text style={[styles.readingSectionTitle, { color: theme.text }]}>How You Make Decisions</Text>
          <Text style={[styles.readingParagraph, { color: theme.textSecondary }]}>
            {getReadingDecisionProcess(authority || '')}
          </Text>
        </View>
        
        {/* SECTION 3: How Others Experience You */}
        <View style={styles.readingSection}>
          <Text style={[styles.readingSectionTitle, { color: theme.text }]}>How Others Experience You</Text>
          <Text style={[styles.readingParagraph, { color: theme.textSecondary }]}>
            {getReadingHowOthersSeeYou(type || '', profile || '')}
          </Text>
        </View>
        
        {/* SECTION 4: Where Things Go Wrong */}
        <View style={styles.readingSection}>
          <Text style={[styles.readingSectionTitle, { color: theme.text }]}>Where Things Go Wrong</Text>
          <Text style={[styles.readingParagraph, { color: theme.textSecondary }]}>
            {getReadingNotSelf(type || '', notSelf)}
          </Text>
        </View>
        
        {/* SECTION 5: What Actually Works For You */}
        <View style={styles.readingSection}>
          <Text style={[styles.readingSectionTitle, { color: theme.text }]}>What Actually Works For You</Text>
          <Text style={[styles.readingParagraph, { color: theme.textSecondary }]}>
            {getReadingStrategy(type || '', strategy || '', authority || '')}
          </Text>
        </View>
        
        {/* SECTION 6: Your Deeper Pattern */}
        <View style={styles.readingSection}>
          <Text style={[styles.readingSectionTitle, { color: theme.text }]}>Your Deeper Pattern</Text>
          <Text style={[styles.readingParagraph, { color: theme.textSecondary }]}>
            {getReadingDeeperPattern(definedCenters, undefinedCenters, gatesData?.gates, activationSequence)}
          </Text>
        </View>
      </View>
    );
  };
  
  // Reading Mode content generators - Bodygraph PDF style: empathetic, flowing, validating
  const getReadingCorePattern = (type: string, profile: string): string => {
    const typePatterns: Record<string, string> = {
      'Generator': `If you have Generator energy, one of your unique gifts is your sustainable life force—a deep reservoir of energy that's available when you're doing work you genuinely love. You're designed to find what lights you up and commit to it fully. When you're engaged with the right things, you can work with remarkable endurance and satisfaction.

The key words here are response and satisfaction.

You may have spent your life saying yes to things out of obligation, guilt, or social pressure—and feeling increasingly frustrated as a result. The traditional approach of "just push through" doesn't work for you. Your body needs to respond with a genuine "yes" before committing. When you override that gut response, frustration builds. This isn't a character flaw—it's your body telling you something isn't aligned.

Your invitation: Start paying attention to your gut responses. Notice the difference between an expansive "uh-huh" and a contracting "unh-uh." Give yourself permission to wait for that genuine pull before committing. Your satisfaction is the compass—when you're lit up, you're on track.`,
      
      'Manifesting Generator': `If you have Manifesting Generator energy, you're a rare hybrid—combining sustainable work energy with the ability to initiate and move fast. You're designed to respond to what lights you up, then act quickly. You skip steps, change directions, and pivot when something stops feeling right. This isn't inconsistency—it's efficiency.

The key words here are response, inform, and satisfaction.

You may have spent your life being told to "stick with things" or "finish what you start"—and feeling wrong for wanting to move on when the energy died. The truth is, you're not designed for linear paths. You're designed to sample, engage deeply when it resonates, then move when it doesn't. Forcing yourself to continue past genuine interest leads to frustration and resentment.

Your invitation: Trust your non-linear process. When you feel the pull to respond, go. When the energy dies, it's okay to pivot. Just inform the people affected before you shift—not for permission, but to reduce friction. Your path will look messy to others. It's actually remarkably efficient.`,
      
      'Projector': `If you have Projector energy, one of your unique gifts is your ability to see into people and systems with remarkable clarity. You're designed to guide others—to see what they can't see about themselves. When you're recognized and invited to share your insights, your guidance lands with profound impact.

The key words here are recognition, invitation, and success.

You may have spent your life feeling unseen or undervalued, working harder than everyone else to prove your worth. The bitterness that builds is a signal—you're operating against your design. You're not here to hustle like others. Your energy works differently. You need more rest, more alone time, and you need to wait for genuine recognition before offering guidance.

Your invitation: Stop initiating. Start waiting for recognition. This feels counterintuitive, but when you're truly seen and invited, your guidance becomes magnetic. Focus on your own mastery, rest deeply, and trust that the right invitations will come. Your success depends on being selective, not productive.`,
      
      'Manifestor': `If you have Manifestor energy, you're designed to initiate—to start things, to set change in motion, to act on urges that others don't yet understand. You have a powerful impact on the world around you. When you walk into a room, people feel your presence before you say anything.

The key words here are informing and peace.

You may have spent your life either suppressing your initiating urges (to avoid conflict) or acting without warning (creating chaos). Both lead to anger—either turned inward or outward. The challenge is that people feel your impact whether you intend it or not. When you act without informing, resistance builds. When you suppress your urges, resentment builds.

Your invitation: Inform before you act. Not asking permission—simply letting people know what's coming. This isn't about diminishing your power; it's about using it more effectively. Trust your urges. When you feel the impulse to start something, that's your design working. Your peace comes from honoring that initiating energy while reducing unnecessary friction.`,
      
      'Reflector': `If you have Reflector energy, you are incredibly rare—less than 1% of the population. One of your unique gifts is being a mirror for the collective, reflecting back the health and energy of the communities and environments you're in. Your openness allows you to experience life in a profoundly unique way.

The key words here are reflection and discernment.

You may have spent your life feeling like you don't quite fit anywhere, or that something is fundamentally wrong with you because you're so different from everyone else. The pressure to be consistent—to show up the same way every day—can be exhausting and impossible for you to maintain. Because all of your centers are open, you are constantly taking in and amplifying the energy around you. This makes it difficult to know what's truly yours versus what you're absorbing from others.

Your genius emerges when you embrace your role as a mirror and honor your need for time and space to gain clarity. When you're in the right environment with the right people, you flourish. When you're in the wrong environment, you feel it deeply—and that's valuable information.

Your invitation: Start tracking the lunar cycle and noticing how you shift and change throughout the month. Give yourself permission to be inconsistent. Pay attention to how different environments make you feel—your body is constantly giving you feedback about what's healthy for you and what isn't. For major decisions, allow a full 28-day cycle. This isn't slow—it's wise.`
    };
    
    const baseType = typePatterns[type] || typePatterns['Generator'];
    
    // Add profile layer if available
    const profilePatterns: Record<string, string> = {
      '1': `\n\nYour 1-line profile brings a foundation of investigation to your design. You need to understand things deeply before you feel secure. Research, study, and building a solid foundation of knowledge aren't optional for you—they're essential. When you skip this phase, insecurity follows.`,
      '2': `\n\nYour 2-line profile carries natural gifts that others often see before you do. You may be called to share talents you didn't know you had. The challenge is honoring your need for alone time while responding to the world's calls on your gifts.`,
      '3': `\n\nYour 3-line profile means you learn through direct experience—trial and error. What looks like "mistakes" to others is actually your process. You're designed to discover what doesn't work, and this experiential wisdom becomes invaluable.`,
      '4': `\n\nYour 4-line profile operates through networks and relationships. Your influence moves through the people who know and trust you. Opportunity comes through connection, not cold outreach.`,
      '5': `\n\nYour 5-line profile attracts projections. People see you as a potential savior or solution before they know you. This can be exhausting when you can't meet expectations, and powerful when you can. Managing these projections is a lifelong practice.`,
      '6': `\n\nYour 6-line profile unfolds in three phases: experimentation and trial until around 30, a period of observation and stepping back until around 50, then embodying the wisdom you've gathered. Trust whatever phase you're in.`
    };
    
    const firstLine = profile?.split('/')?.[0] || '';
    const secondLine = profile?.split('/')?.[1] || '';
    
    let profileText = profilePatterns[firstLine] || '';
    if (secondLine && profilePatterns[secondLine]) {
      profileText += profilePatterns[secondLine];
    }
    
    return baseType + profileText;
  };
  
  const getReadingDecisionProcess = (authority: string): string => {
    const auth = authority?.toLowerCase() || '';
    
    if (auth.includes('emotional')) {
      return `Your decision-making process is deeply tied to your emotional wave. Unlike others who can know in an instant, your clarity builds over time. You need to ride the wave—experiencing a decision through emotional highs, lows, and the calm in between.

What This Means: You don't have access to truth in the moment. When you're emotionally high, everything looks good. When you're low, everything looks bad. Neither state gives you accurate information. Your clarity comes when the wave settles and you feel calm—not excited, not depressed, just clear.

The Challenge: Society rewards fast decisions. "Trust your gut" doesn't work for you. You may have spent your life regretting choices made in emotional heat—either the high of excitement or the low of desperation. The pressure to decide quickly is your greatest enemy.

Your Wisdom: When you honor your wave, you make profoundly wise decisions. You've experienced the choice from every emotional angle. You know how it feels in the morning and at night, on good days and hard days. This depth of knowing is unavailable to those who decide quickly.

Practical Tips:
• Never make important decisions in one sitting. Sleep on it—multiple times if needed.
• Track your emotional wave. Notice when you're high, low, and neutral.
• When you feel neutral and still clear about something—that's likely your truth.
• Tell people: "I need time to feel into this." The right opportunities will wait.`;
    }
    
    if (auth.includes('sacral')) {
      return `Your decision-making lives in your gut. There's a physical response—an expansion toward yes, a contraction toward no. It's not logical. It doesn't explain itself. It just knows.

What This Means: Your Sacral Center speaks through sounds and sensations. An "uh-huh" of opening, an "unh-uh" of closing. This response happens faster than thought. Your job is to trust it, even when your mind disagrees.

The Challenge: You may have been taught to override this knowing—to "think it through" or "be reasonable." Every time you override the gut response, you move away from what's correct for you. The frustration that follows is your body telling you it wasn't right.

Your Wisdom: Your gut knows what your mind can't figure out. It's reading energy, not logic. When you follow it, life flows. When you don't, you grind.

Practical Tips:
• Pay attention to your first physical response. That's the signal.
• Ask yourself yes/no questions. Notice whether your body opens or closes.
• Your gut responds to things outside you—wait for something to respond TO.
• Don't commit when you feel nothing. A neutral response means wait.`;
    }
    
    if (auth.includes('splenic')) {
      return `Your knowing comes in the moment—fast, quiet, and once. It's an instinct about timing, safety, what's right and what's off. The Spleen speaks once, then moves on.

What This Means: Your intuition doesn't repeat itself or explain itself. It's a subtle hit—a knowing that something is right or wrong, now or not now. If you catch it, you have the information. If you miss it or override it, it doesn't come back.

The Challenge: Your mind is slower than your intuition. By the time you've "thought it through," the splenic knowing has passed. You may have a history of overriding quiet instincts with loud logic—and regretting it.

Your Wisdom: When you trust the first hit, you navigate life with remarkable accuracy. Your instincts are reading survival-level information that your conscious mind can't access.

Practical Tips:
• Act on the first knowing. Don't wait to "think about it."
• Learn to distinguish gut instinct from fear. Intuition is quiet; fear is loud.
• Your timing is in the moment. "Let me think about it" often means missing the window.
• Practice trusting small instincts to build confidence for bigger ones.`;
    }
    
    if (auth.includes('lunar')) {
      return `Your clarity unfolds over a full lunar cycle—approximately 28 days. This isn't indecisiveness; it's wisdom. You experience decisions through every energetic configuration the moon brings.

What This Means: As the moon moves through each gate in the Human Design wheel, you have access to different energies, perspectives, and ways of experiencing a choice. What feels right during one phase may feel different during another. You need the full cycle to gather complete information.

The Challenge: The world moves fast. People want answers now. You may have made decisions under pressure that you later regretted, or felt there was something wrong with you for needing so much time. There's nothing wrong—you're designed for depth, not speed.

Your Wisdom: When you honor the full cycle, your decisions have been tested against every possible energy. You've experienced how the choice feels in every state. No one else has access to this depth of knowing.

Practical Tips:
• Mark when a major decision enters your life. Give it 28 days.
• Track how you feel about it throughout the month. Notice patterns.
• Talk to different people in different environments throughout the cycle.
• Trust that what survives 28 days of sampling is truly correct for you.`;
    }
    
    return `Your clarity emerges through conversation and environment. You find truth by talking things through with others—not for their opinion, but to hear yourself speak in different contexts.

What This Means: Your process is external. Clarity doesn't come from sitting alone and thinking. It comes from dialogue—hearing how you talk about a decision, noticing what your voice sounds like when you describe different options.

The Challenge: You may have been told to "trust yourself" and figure it out alone. This doesn't work for you. Without conversation, decisions stay foggy.

Practical Tips:
• Talk to trusted people—not for advice, but for the mirror of conversation.
• Notice how you feel in different environments when discussing decisions.
• Pay attention to your voice. When you're speaking truth, it sounds different.`;
  };
  
  const getReadingHowOthersSeeYou = (type: string, profile: string): string => {
    const typeAura: Record<string, string> = {
      'Generator': `People feel your energy before you speak. When you're genuinely engaged, there's a warmth and magnetism that draws others in. Your aura is open and enveloping—it invites response. People feel comfortable initiating with you, sharing ideas, asking questions. 

When you're lit up about something, it's contagious. Others want to be around your energy. When you're frustrated or doing something that doesn't align, people feel that too—there's a heaviness, a "don't bother me" quality.`,
      
      'Manifesting Generator': `People experience you as dynamic, fast-moving, and sometimes hard to predict. You bring energy and pace into any room. Your aura combines the Generator's welcoming quality with a Manifestor's impact—people feel drawn to engage with you AND feel your initiating force.

You may notice people trying to keep up with you, or feeling disoriented by your changes in direction. Some find your pace exciting and inspiring. Others find it overwhelming. Both responses are about them, not you.`,
      
      'Projector': `People feel seen by you—sometimes uncomfortably so. Your aura is focused and penetrating. When you give someone your attention, they feel it deeply. You naturally read people, systems, the dynamics underneath the surface.

This intensity makes you a powerful guide when invited. It can also make people feel exposed when they're not ready. You may have experienced people pulling away from your perception, or being drawn to it. The difference usually comes down to whether they feel recognized first.`,
      
      'Manifestor': `People feel your impact before you say anything. Your aura is closed and repelling in a specific way—not unfriendly, but self-contained. You don't pull people in the way Generators do. Instead, you push energy outward.

When you walk into a room, the dynamic shifts. Some people are drawn to your initiating force—they want to be part of what you're starting. Others feel pushed or controlled, even when you don't intend it. Informing helps people relax around you.`,
      
      'Reflector': `People experience you differently depending on when and where they meet you. You're a mirror—reflecting back the energy, health, and dynamics of whatever environment you're in. This means you can seem like a different person in different contexts.

In healthy environments, you reflect that health back—people feel good around you. In unhealthy environments, you reflect the dysfunction—which isn't always welcome. Your inconsistency isn't a problem; it's information about where you are.`
    };
    
    const profileLayers: Record<string, string> = {
      '1': `\n\nYour 1-line adds depth. People sense there's more beneath the surface—that you've done your research, built your foundation, understand things more thoroughly than you let on.`,
      '2': `\n\nYour 2-line carries natural talents that others see before you do. People may call on you for things you didn't know you were good at. This can feel surprising or uncomfortable when you don't see what they see.`,
      '3': `\n\nYour 3-line brings experiential wisdom. People sense you've tried things, failed, learned, and accumulated practical knowledge through direct experience. You know what doesn't work.`,
      '4': `\n\nYour 4-line makes you influential through networks. People experience you through your connections—who you know, who trusts you, who you're affiliated with.`,
      '5': `\n\nYour 5-line attracts projections. People see you as a potential solution or savior before they know you. They project their hopes—and disappointments—onto you. Managing this is a constant practice.`,
      '6': `\n\nYour 6-line carries an eventual wisdom. People sense there's something you're here to embody over time—a living example of something. This authority grows as you age.`
    };
    
    let result = typeAura[type] || typeAura['Generator'];
    
    const firstLine = profile?.split('/')?.[0] || '';
    const secondLine = profile?.split('/')?.[1] || '';
    
    if (profileLayers[firstLine]) result += profileLayers[firstLine];
    if (profileLayers[secondLine]) result += profileLayers[secondLine];
    
    return result;
  };
  
  const getReadingNotSelf = (type: string, notSelf: string): string => {
    const notSelfPatterns: Record<string, string> = {
      'Generator': `When you're living out of alignment with your design, frustration builds. This is your signal—not a flaw, but feedback.

The Challenge: Frustration shows up when you're doing work that doesn't light you up, saying yes out of obligation, or trying to initiate things instead of responding to what's in front of you. You may feel stuck, heavy, like you're grinding without getting anywhere. "Why am I even doing this?" becomes a constant question.

What It Looks Like: Working on projects that drain you. Commitments that feel like prison sentences. Saying yes because you should, not because your gut said yes. Feeling like a workhorse with no satisfaction. Envying people who seem energized while you feel depleted.

The Wisdom in Frustration: This feeling isn't telling you you're broken. It's telling you something isn't right. It's your body's way of saying "not this." The frustration itself is the guide—follow it backward to find what needs to change.`,
      
      'Manifesting Generator': `When you're living out of alignment with your design, a mix of frustration and anger builds. You feel stuck, blocked, unable to move the way you're designed to move.

The Challenge: Frustration comes from doing things that don't light you up. Anger comes from suppressing your initiating urges or being blocked from acting. You may feel trapped in commitments that stopped being exciting, or forced to finish things your energy has already left.

What It Looks Like: Staying in jobs, relationships, or projects past their expiration date. Forcing yourself to complete things just to "be responsible." Not informing others and creating friction. Holding back impulses to keep the peace. A buzzing, trapped energy with no outlet.

The Wisdom in Frustration and Anger: These signals are telling you something needs to change. Either you're doing something that isn't correct, or you're being blocked from something that is. The feelings themselves are the guide.`,
      
      'Projector': `When you're living out of alignment with your design, bitterness accumulates. This sour feeling is your signal—not a character flaw, but feedback about how you're operating.

The Challenge: Bitterness comes from working too hard without recognition, offering guidance that wasn't invited, or trying to keep up with energy types (Generators, Manifestors) who have more fuel than you. You may feel invisible, undervalued, exhausted from trying to prove your worth.

What It Looks Like: Initiating instead of waiting for recognition. Giving advice no one asked for. Working long hours to demonstrate value. Feeling resentful when others don't see your contributions. Burnout from trying to match others' energy levels.

The Wisdom in Bitterness: This feeling is telling you that your strategy is off. You're either working too hard, not being recognized, or offering guidance that wasn't invited. The bitterness points you back toward waiting, resting, and focusing on your own mastery.`,
      
      'Manifestor': `When you're living out of alignment with your design, anger surfaces—either explosive or imploded. This is your signal that something in your initiating process needs attention.

The Challenge: Anger comes from suppressing urges to keep the peace, or from acting without informing and creating resistance. You may feel controlled by others who don't understand your need to move, or isolated because your impact keeps pushing people away.

What It Looks Like: Suppressing impulses to avoid conflict. Acting without telling anyone and being met with resistance. Feeling like you can't be yourself without making waves. Carrying resentment toward people who seem to block your movement. Either exploding or withdrawing completely.

The Wisdom in Anger: This feeling tells you something in your informing process is off. Either you're suppressing what needs to be initiated, or you're not giving others the heads-up they need. The anger points back toward honoring your urges AND informing—both are necessary.`,
      
      'Reflector': `When you're living out of alignment with your design, disappointment accumulates. This deep sense that life isn't what it could be is your signal—not proof that something is wrong with you.

The Challenge: Disappointment comes from rushing decisions, staying in wrong environments, or trying to be consistent when you're designed to change. You may feel like you don't fit anywhere, or that you're constantly absorbing everyone else's patterns while losing yourself.

What It Looks Like: Making major decisions too quickly and regretting them. Staying in environments that feel wrong. Trying to be the same person every day. Not having enough alone time to discharge absorbed energy. Feeling lost in other people's emotions and patterns.

The Wisdom in Disappointment: This feeling tells you something about your environment or your pace. You're either in the wrong place, with the wrong people, or you're not giving yourself the time you need. The disappointment points back toward choosing environments wisely and honoring your lunar timing.`
    };
    
    return notSelfPatterns[type] || notSelfPatterns['Generator'];
  };
  
  const getReadingStrategy = (type: string, strategy: string, authority: string): string => {
    const strategyPatterns: Record<string, string> = {
      'Generator': `Your strategy is to respond. Not initiate. Not push. Wait for life to bring you something—a request, an opportunity, a situation—and then check your gut response.

What This Means: You're not designed to make things happen from scratch. You're designed to respond to what shows up. This doesn't mean passive waiting—it means engaged attention. Notice what's in front of you. Check your gut. When you feel that "yes," commit fully. When you feel "no," honor it.

How It Works: Something appears in your world—a job posting, a question from someone, an invitation. Before your mind analyzes pros and cons, notice your body. Is there expansion? Contraction? An "uh-huh" or "unh-uh"? That response is your guide.

What Actually Works: Following the gut response, even when it doesn't make logical sense. Waiting for things to respond to rather than forcing action. Trusting that the right opportunities will appear. Giving yourself permission to say no when your body says no.

Remember: Your satisfaction comes from correct work. Correct work comes from responding correctly. The gut is the guide—not the mind, not obligation, not what you "should" do.`,
      
      'Manifesting Generator': `Your strategy is to respond, then inform, then act. The response comes first—you need something to respond TO. But once your gut says yes, you can move fast. Just let people know before big shifts.

What This Means: Like Generators, you wait for something to respond to. But unlike pure Generators, once you're in, you can initiate and move with speed. Your energy works in bursts—intense engagement followed by the need to pivot when the energy dies.

How It Works: Something shows up. You feel the pull—a strong gut yes. You engage fully and move quickly. When the energy shifts and something else catches your attention, you inform the people affected and pivot. This isn't flaky; it's efficient.

What Actually Works: Trusting your gut response. Moving fast when you're lit up. Informing others before sudden changes. Giving yourself permission to not finish things that stopped resonating. Embracing your non-linear path.

Remember: Your efficiency comes from following energy, not forcing completion. When something stops lighting you up, that's information. Pivot isn't failure—it's design.`,
      
      'Projector': `Your strategy is to wait for the invitation—especially for the big things: relationships, careers, places to live. When you're recognized and invited, your guidance lands. When you're not, it doesn't.

What This Means: You're not designed to initiate or push your way into things. Your success comes from being seen, recognized, and invited. This feels counterintuitive in a culture that rewards hustle, but forcing your way in leads to bitterness.

How It Works: Focus on your own mastery. Develop your skills. Rest. When someone genuinely sees you and invites your involvement—"I'd love your thoughts on this," "Would you consider this opportunity?"—that's the green light.

What Actually Works: Resting more than feels normal. Managing your energy carefully. Waiting for recognition before offering guidance. Focusing on depth of mastery rather than breadth of activity. Being selective about where you invest your limited energy.

Remember: Your value isn't in output. It's in guiding others when they're ready to receive it. The right invitations come when you're focused on being excellent at your thing, not proving yourself to everyone.`,
      
      'Manifestor': `Your strategy is to inform before you act. Not asking permission—simply letting people know what's coming. This reduces the resistance that naturally builds around your impact.

What This Means: Your aura is closed and impactful. When you act without warning, people feel controlled or blindsided—even when that's not your intention. Informing doesn't diminish your power; it helps it land more effectively.

How It Works: When you feel the urge to initiate something, pause just long enough to tell the people who will be affected: "I'm going to..." This isn't asking for approval. It's giving others a chance to adjust, which reduces friction.

What Actually Works: Trusting your initiating urges. Informing others before acting. Not asking for permission. Giving yourself space to move without constant negotiation. Finding people who understand your nature.

Remember: Your peace comes from acting on what you're here to initiate while minimizing unnecessary resistance. The informing isn't about them approving—it's about you moving effectively.`,
      
      'Reflector': `Your strategy is to wait a lunar cycle before major decisions. Not a day, not a week—a full 28-day cycle. This gives you time to experience the decision through every energetic configuration.

What This Means: The moon moves through every gate in the Human Design wheel each month, giving you access to different energies and perspectives. A decision that feels right during one phase may feel different during another. You need the full cycle to know what's true.

How It Works: Mark when a major decision enters your life. Move through the next 28 days, checking in with how it feels at different times. Talk to different people. Be in different environments. Notice the patterns in how you feel about it.

What Actually Works: Giving yourself the full 28 days. Tracking how your feelings shift throughout the cycle. Talking through decisions in different contexts. Choosing environments carefully—they shape everything for you. Taking plenty of alone time to discharge absorbed energy.

Remember: Your wisdom comes from sampling. You're not designed for quick certainty—you're designed for deep knowing that comes from experiencing all the angles. What survives 28 days of sampling is correct for you.`
    };
    
    let result = strategyPatterns[type] || strategyPatterns['Generator'];
    
    const auth = authority?.toLowerCase() || '';
    if (auth.includes('emotional') && !type?.includes('Reflector')) {
      result += `\n\nImportant: Because you have emotional authority, layer this on top of your strategy. Even after your gut responds, give yourself time. Sleep on it. Check how it feels tomorrow, and the next day. Your truth emerges when the emotional wave settles.`;
    }
    
    return result;
  };
  
  const getReadingDeeperPattern = (definedCenters: any[], undefinedCenters: any[], gates: any[], activation: any): string => {
    const definedCount = definedCenters?.length || 0;
    const undefinedCount = undefinedCenters?.length || 0;
    const gateCount = gates?.length || 0;
    
    let narrative = `Beyond your type, authority, and strategy, your design contains specific energetic patterns—consistent and variable—that shape how you experience life.\n\n`;
    
    if (definedCount > 0) {
      const definedNames = definedCenters.map(c => c.name || c.center_name).filter(Boolean);
      narrative += `**Your Defined Centers:** You have consistent, reliable energy in ${definedNames.join(', ')}. These centers operate the same way regardless of who you're around. They're your fixed traits—how you're wired to think, feel, communicate, or act. You can rely on them. Others may be drawn to this consistency, or conditioned by it.\n\n`;
    }
    
    if (undefinedCount > 0) {
      const undefinedNames = undefinedCenters.map(c => c.name || c.center_name).filter(Boolean);
      narrative += `**Your Open Centers:** Your undefined areas—${undefinedNames.slice(0, 4).join(', ')}${undefinedNames.length > 4 ? ' and more' : ''}—are where you take in and amplify energy from your environment. What you experience in these centers is often not yours. Over time, this openness becomes wisdom: you understand these energies more deeply than those who have them consistently, precisely because you experience them variably.\n\n`;
      
      narrative += `The challenge with open centers is conditioning—taking on patterns from others and thinking they're yours. The gift is wisdom about how these energies work, gained through experiencing them in so many different ways.\n\n`;
    }
    
    if (gateCount > 0) {
      narrative += `**Your Gates:** You carry ${gateCount} defined gates—specific themes and energies that are consistently available to you. Each gate has a spectrum from shadow (challenge) to gift (higher expression). These aren't choices; they're wiring. Your work is to become aware of how they show up, notice when you're in shadow, and cultivate the gift expression.\n\n`;
    }
    
    if (activation?.spheres?.length > 0) {
      const lifework = activation.spheres.find((s: any) => s.sphere_name?.toLowerCase().includes('life'));
      const purpose = activation.spheres.find((s: any) => s.sphere_name?.toLowerCase().includes('purpose'));
      
      if (lifework || purpose) {
        narrative += `**Your Deeper Purpose:** Your Gene Keys reveal another layer. `;
        if (lifework?.gift) {
          narrative += `Your Life's Work carries the potential of ${lifework.gift}—this is where your core contribution shows up. `;
        }
        if (purpose?.gift) {
          narrative += `Your Purpose points toward ${purpose.gift}—the underlying theme you're here to embody.`;
        }
        narrative += `\n\n`;
      }
    }
    
    narrative += `Remember: This blueprint isn't prescriptive—it's descriptive. It shows you how you're wired, not who you have to be. Use it as a mirror for self-recognition, a tool for self-acceptance, and a guide for living more aligned with your nature.`;
    
    return narrative;
  };
  
  // Deep Dive Global Ask Section - page level CTA
  const renderDeepDiveAskSection = () => {
    return (
      <View style={[styles.deepDiveAskSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.deepDiveAskTitle, { color: theme.text }]}>Ask About This Lens</Text>
        <Text style={[styles.deepDiveAskSubtext, { color: theme.textSecondary }]}>
          Ask anything about your design, your decisions, your patterns, or how this shows up in your life.
        </Text>
        <TouchableOpacity
          style={[styles.deepDiveAskButton, { backgroundColor: theme.accent }]}
          onPress={() => onOpenChat()}
          activeOpacity={0.8}
        >
          <Ionicons name="chatbubble-outline" size={18} color="#FFFFFF" />
          <Text style={styles.deepDiveAskButtonText}>Start a conversation</Text>
        </TouchableOpacity>
      </View>
    );
  };
  
  // Parent Accordion Component for Centers/Gates
  const renderParentAccordion = (
    title: string,
    subtitle: string,
    isExpanded: boolean,
    onToggle: () => void,
    children: React.ReactNode
  ) => {
    return (
      <View style={[styles.parentAccordion, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        {/* Header - always visible */}
        <TouchableOpacity
          style={styles.parentAccordionHeader}
          onPress={onToggle}
          activeOpacity={0.7}
        >
          <View style={styles.parentAccordionHeaderContent}>
            <Text style={[styles.parentAccordionTitle, { color: theme.text }]}>{title}</Text>
            <Text style={[styles.parentAccordionSubtitle, { color: theme.textTertiary }]}>{subtitle}</Text>
          </View>
          <Ionicons 
            name={isExpanded ? 'chevron-up' : 'chevron-down'} 
            size={22} 
            color={theme.textTertiary} 
          />
        </TouchableOpacity>
        
        {/* Expanded Content */}
        {isExpanded && (
          <View style={[styles.parentAccordionContent, { borderTopColor: theme.border }]}>
            {children}
          </View>
        )}
      </View>
    );
  };
  
  // Design Summary Graph - Visual overview at top
  const renderDesignSummaryGraph = () => {
    if (!data?.core_mechanics) return null;
    
    const { type, authority, profile, definition, incarnation_cross } = data.core_mechanics;
    
    // MUTED type colors - premium, calm, sophisticated
    const typeColors: Record<string, string> = {
      'Generator': '#B8956B',      // muted gold/bronze
      'Manifesting Generator': '#C4915C',  // muted amber
      'Projector': '#7B9AA9',      // muted blue-grey
      'Manifestor': '#A67C6D',     // muted clay/rust (NOT bright red)
      'Reflector': '#A099AA'       // muted lavender-grey
    };
    
    const typeColor = typeColors[type || ''] || theme.textSecondary;
    
    return (
      <View style={[styles.summaryGraphCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        {/* Header */}
        <View style={styles.summaryGraphHeader}>
          <Text style={[styles.summaryGraphTitle, { color: theme.textTertiary }]}>YOUR DESIGN</Text>
        </View>
        
        {/* Main Type - Premium subtle badge */}
        <View style={[styles.summaryGraphTypeBadge, { borderColor: typeColor }]}>
          <Text style={[styles.summaryGraphTypeText, { color: theme.text }]}>{type || 'Unknown Type'}</Text>
        </View>
        
        {/* Key Attributes Grid */}
        <View style={styles.summaryGraphGrid}>
          {/* Authority */}
          <View style={styles.summaryGraphItem}>
            <Text style={[styles.summaryGraphItemLabel, { color: theme.textTertiary }]}>AUTHORITY</Text>
            <Text style={[styles.summaryGraphItemValue, { color: theme.text }]}>{authority || 'Unknown'}</Text>
          </View>
          
          {/* Profile */}
          <View style={styles.summaryGraphItem}>
            <Text style={[styles.summaryGraphItemLabel, { color: theme.textTertiary }]}>PROFILE</Text>
            <Text style={[styles.summaryGraphItemValue, { color: theme.text }]}>{profile || 'Unknown'}</Text>
          </View>
          
          {/* Definition */}
          <View style={styles.summaryGraphItem}>
            <Text style={[styles.summaryGraphItemLabel, { color: theme.textTertiary }]}>DEFINITION</Text>
            <Text style={[styles.summaryGraphItemValue, { color: theme.text }]}>{definition || 'Unknown'}</Text>
          </View>
          
          {/* Strategy */}
          <View style={styles.summaryGraphItem}>
            <Text style={[styles.summaryGraphItemLabel, { color: theme.textTertiary }]}>STRATEGY</Text>
            <Text style={[styles.summaryGraphItemValue, { color: theme.text }]}>{getShortStrategy(type)}</Text>
          </View>
        </View>
        
        {/* Incarnation Cross */}
        <View style={[styles.summaryGraphCross, { borderTopColor: theme.border }]}>
          <Text style={[styles.summaryGraphCrossLabel, { color: theme.textTertiary }]}>INCARNATION CROSS</Text>
          <Text style={[styles.summaryGraphCrossValue, { color: theme.text }]}>{incarnation_cross || 'Unknown'}</Text>
        </View>
      </View>
    );
  };
  
  // Helper for short strategy text
  const getShortStrategy = (type: string | undefined): string => {
    const strategies: Record<string, string> = {
      'Generator': 'Wait to Respond',
      'Manifesting Generator': 'Wait to Respond, then Inform',
      'Projector': 'Wait for Invitation',
      'Manifestor': 'Inform before Acting',
      'Reflector': 'Wait a Lunar Cycle'
    };
    return strategies[type || ''] || 'Unknown';
  };

  // SEQUENCES TABS - Core / Relationship / Work
  const renderSequencesTabs = () => {
    return (
      <View style={styles.sequencesTabsContainer}>
        <Text style={[styles.deepDiveSectionHeader, { color: theme.textTertiary, marginTop: 24 }]}>SEQUENCES</Text>
        
        {/* Tab Bar */}
        <View style={[styles.sequencesTabBar, { backgroundColor: theme.background, borderColor: theme.border }]}>
          <TouchableOpacity
            style={[styles.sequenceTab, activeSequenceTab === 'core' && { backgroundColor: theme.surface }]}
            onPress={() => setActiveSequenceTab('core')}
            activeOpacity={0.7}
          >
            <Text style={[styles.sequenceTabText, { color: activeSequenceTab === 'core' ? theme.text : theme.textTertiary }]}>Core</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.sequenceTab, activeSequenceTab === 'relationship' && { backgroundColor: theme.surface }]}
            onPress={() => setActiveSequenceTab('relationship')}
            activeOpacity={0.7}
          >
            <Text style={[styles.sequenceTabText, { color: activeSequenceTab === 'relationship' ? theme.text : theme.textTertiary }]}>Relationship</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.sequenceTab, activeSequenceTab === 'work' && { backgroundColor: theme.surface }]}
            onPress={() => setActiveSequenceTab('work')}
            activeOpacity={0.7}
          >
            <Text style={[styles.sequenceTabText, { color: activeSequenceTab === 'work' ? theme.text : theme.textTertiary }]}>Work</Text>
          </TouchableOpacity>
        </View>
        
        {/* Tab Content */}
        <View style={styles.sequencesTabContent}>
          {activeSequenceTab === 'core' && renderActivationSequence()}
          {activeSequenceTab === 'relationship' && renderVenusSequence()}
          {activeSequenceTab === 'work' && renderPearlSequence()}
        </View>
      </View>
    );
  };

  // Render Activation Sequence (Core tab)
  const renderActivationSequence = () => {
    const spheres = activationSequence?.spheres || [];
    const accentColor = '#FFD700'; // Gold
    
    return (
      <View style={styles.sequenceContent}>
        <Text style={[styles.sequenceDescription, { color: theme.textSecondary }]}>
          Your core life theme and purpose
        </Text>
        {spheres.map((sphere: any, idx: number) => (
          <View key={idx}>
            {idx > 0 && <View style={[styles.sphereConnectorLine, { backgroundColor: theme.border }]} />}
            {renderSphereCard(sphere, accentColor)}
          </View>
        ))}
        {spheres.length === 0 && (
          <Text style={[styles.noDataText, { color: theme.textTertiary }]}>Sequence data loading...</Text>
        )}
      </View>
    );
  };

  // Render Venus Sequence (Relationship tab)
  const renderVenusSequence = () => {
    const spheres = venusSequence?.spheres || [];
    const accentColor = '#FF69B4'; // Pink
    
    return (
      <View style={styles.sequenceContent}>
        <Text style={[styles.sequenceDescription, { color: theme.textSecondary }]}>
          How you connect and relate
        </Text>
        {spheres.map((sphere: any, idx: number) => (
          <View key={idx}>
            {idx > 0 && <View style={[styles.sphereConnectorLine, { backgroundColor: theme.border }]} />}
            {renderSphereCard(sphere, accentColor)}
          </View>
        ))}
        {spheres.length === 0 && (
          <Text style={[styles.noDataText, { color: theme.textTertiary }]}>Sequence data loading...</Text>
        )}
      </View>
    );
  };

  // Render Pearl Sequence (Work tab)
  const renderPearlSequence = () => {
    const spheres = pearlSequence?.spheres || [];
    const accentColor = '#90EE90'; // Green
    
    return (
      <View style={styles.sequenceContent}>
        <Text style={[styles.sequenceDescription, { color: theme.textSecondary }]}>
          Your work and contribution path
        </Text>
        {spheres.map((sphere: any, idx: number) => (
          <View key={idx}>
            {idx > 0 && <View style={[styles.sphereConnectorLine, { backgroundColor: theme.border }]} />}
            {renderSphereCard(sphere, accentColor)}
          </View>
        ))}
        {spheres.length === 0 && (
          <Text style={[styles.noDataText, { color: theme.textTertiary }]}>Sequence data loading...</Text>
        )}
      </View>
    );
  };

  // Sphere Card (for sequences) - conversational tone
  const renderSphereCard = (sphere: any, accentColor: string) => {
    // Get short, direct interpretation
    const getDirectInterpretation = (text: string | undefined, sphereName: string): string => {
      if (text) {
        const firstSentence = text.split('.')[0] + '.';
        return firstSentence.length < 90 ? firstSentence : firstSentence.slice(0, 87) + '...';
      }
      // More varied fallbacks based on sphere name
      const fallbacks: Record<string, string> = {
        "Life's Work": "This is where your core purpose tends to show up most clearly.",
        "Evolution": "This shapes how you grow and transform over time.",
        "Radiance": "This influences how others experience your presence.",
        "Purpose": "This points to what you're really here to do.",
        "Attraction": "This shapes who and what you draw into your life.",
        "IQ": "This colors how you process and understand things.",
        "EQ": "This influences how you navigate emotions and connection.",
        "SQ": "This touches your sense of meaning and spirit.",
        "Core": "This sits at the heart of your relational patterns.",
        "Brand": "This shapes how others see and remember you.",
        "Culture": "This influences the environments you create.",
        "Vocation": "This points to work that feels genuinely meaningful.",
        "Pearl": "This is about your lasting contribution."
      };
      return fallbacks[sphereName] || "This energy shapes a key part of who you are.";
    };

    // More varied challenge phrases
    const getChallengeText = (shadow: string | undefined, gift: string | undefined): string => {
      if (!shadow) return "The trap is going unconscious with this energy.";
      const patterns = [
        `The trap is ${shadow.toLowerCase()}—especially when stressed.`,
        `When you're off-center, ${shadow.toLowerCase()} tends to take over.`,
        `Watch for ${shadow.toLowerCase()}. That's usually the sign something's off.`,
        `At its worst, this becomes ${shadow.toLowerCase()}.`
      ];
      return patterns[Math.floor(shadow.length % patterns.length)];
    };

    // More varied practical tips
    const getPracticalTip = (sphere: any): string => {
      if (sphere.practical_tips?.[0]) return sphere.practical_tips[0];
      if (sphere.gift && sphere.shadow) {
        const tips = [
          `When you notice ${sphere.shadow.toLowerCase()}, pause. What would ${sphere.gift} look like here?`,
          `Try: catch yourself in ${sphere.shadow.toLowerCase()} mode, then ask what ${sphere.gift} would do.`,
          `Practice: name it when ${sphere.shadow.toLowerCase()} shows up. Just that creates space.`
        ];
        return tips[Math.floor((sphere.gene_key || 1) % tips.length)];
      }
      return "Notice when this energy feels off—that's useful information.";
    };

    return (
      <View style={[styles.deepDiveCard, { backgroundColor: theme.surface, borderColor: theme.border, borderLeftColor: accentColor, borderLeftWidth: 3 }]}>
        <View style={styles.deepDiveCardHeader}>
          <View>
            <Text style={[styles.deepDiveCardTitle, { color: theme.text }]}>{sphere.sphere_name}</Text>
            {sphere.gene_key && (
              <Text style={[styles.deepDiveCardSubtitle, { color: accentColor }]}>GK {sphere.gene_key}</Text>
            )}
          </View>
        </View>
        
        <View style={styles.deepDiveCardContent}>
          {/* Story */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>STORY</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {getDirectInterpretation(sphere.what_this_means, sphere.sphere_name)}
            </Text>
          </View>
          
          {/* How This Shows Up */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>HOW THIS SHOWS UP</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {sphere.gift ? `You tend toward ${sphere.gift.toLowerCase()}—people probably notice this about you.` : 'You have your own way of expressing this energy.'}
            </Text>
          </View>
          
          {/* Challenge */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>CHALLENGE</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {getChallengeText(sphere.shadow, sphere.gift)}
            </Text>
          </View>
          
          {/* Practical Tips */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>PRACTICAL TIPS</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {getPracticalTip(sphere)}
            </Text>
          </View>
        </View>
        
        {/* Reflect CTA */}
        <TouchableOpacity
          style={[styles.deepDiveAskCta, { borderTopColor: theme.border }]}
          onPress={() => openReflection(
            sphere.sphere_name,
            'sphere',
            getSphereReflectionPrompt(sphere.sphere_name, sphere.gene_key || 0),
            'deep_dive',
            `sphere_${sphere.gene_key}`,
            `GK ${sphere.gene_key}`
          )}
          activeOpacity={0.7}
        >
          <Text style={[styles.deepDiveAskCtaText, { color: theme.accent }]}>Reflect on this →</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // Centers Cards - each center as its own card
  const renderCentersCards = () => {
    if (!centersData?.centers) return null;
    
    // Separate defined and undefined centers
    const definedCenters = centersData.centers.filter((c: any) => c.defined === true);
    const undefinedCenters = centersData.centers.filter((c: any) => c.defined !== true);
    
    return (
      <View style={{ gap: 8 }}>
        {/* Defined Centers First */}
        {definedCenters.length > 0 && (
          <>
            <SectionHeader title="Defined Centers" count={definedCenters.length} icon="◉" />
            {definedCenters.map((center: any, idx: number) => (
              <NestedCollapsible
                key={`def-${idx}`}
                title={center.name || center.center_name}
                subtitle="Consistent access to this energy"
                defaultOpen={idx === 0} // First defined center open
                status="defined"
                lazyRender={true}
              >
                {renderCenterContent(center)}
              </NestedCollapsible>
            ))}
          </>
        )}
        
        {/* Undefined Centers */}
        {undefinedCenters.length > 0 && (
          <>
            <SectionHeader title="Undefined Centers" count={undefinedCenters.length} icon="○" />
            {undefinedCenters.map((center: any, idx: number) => (
              <NestedCollapsible
                key={`undef-${idx}`}
                title={center.name || center.center_name}
                subtitle="Amplifies energy from others"
                defaultOpen={false} // All closed by default
                status="undefined"
                lazyRender={true}
              >
                {renderCenterContent(center)}
              </NestedCollapsible>
            ))}
          </>
        )}
      </View>
    );
  };
  
  // Extracted center content for lazy rendering
  const renderCenterContent = (center: any) => {
    const centerName = center.name || center.center_name;
    const isDefined = center.defined === true;
    
    return (
      <View style={{ gap: 12 }}>
        {/* Recognition */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.accent }]}>RECOGNITION</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getShortCenterStory(center)}
          </Text>
        </View>
        
        {/* Tension */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.warning || '#FF9800' }]}>TENSION</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getShortText(center.your_challenge) || getDefaultCenterChallenge(centerName, isDefined)}
          </Text>
        </View>
        
        {/* Real Life Moments */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.textTertiary }]}>REAL LIFE MOMENTS</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {center.your_genius || getDefaultCenterShowsUp(centerName, isDefined)}
          </Text>
        </View>
        
        {/* Try This Instead */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.success || '#4CAF50' }]}>TRY THIS INSTEAD</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {center.practical_experiments?.[0] || getDefaultCenterTip(centerName, isDefined)}
          </Text>
        </View>
        
        {/* Reflect CTA */}
        <TouchableOpacity
          style={[styles.deepDiveAskCta, { borderTopColor: theme.border }]}
          onPress={() => openReflection(
            `${isDefined ? 'Defined' : 'Undefined'} ${centerName}`,
            'center',
            getCenterReflectionPrompt(centerName, isDefined),
            'deep_dive',
            `center_${centerName.toLowerCase().replace(/\s/g, '_')}`,
            isDefined ? 'defined' : 'undefined'
          )}
          activeOpacity={0.7}
        >
          <Text style={[styles.deepDiveAskCtaText, { color: theme.accent }]}>Reflect on this →</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // Individual Center Card
  const renderCenterCard = (center: any, idx: number) => {
    const centerName = center.name || center.center_name;
    const isDefined = center.defined === true;
    const accentColor = isDefined ? '#FFD700' : theme.textTertiary;
    
    return (
      <View key={idx} style={[styles.deepDiveCard, { backgroundColor: theme.surface, borderColor: theme.border, borderLeftColor: accentColor, borderLeftWidth: 3 }]}>
        <View style={styles.deepDiveCardHeader}>
          <View>
            <Text style={[styles.deepDiveCardTitle, { color: theme.text }]}>{centerName}</Text>
            <Text style={[styles.deepDiveCardSubtitle, { color: accentColor }]}>{isDefined ? 'Defined' : 'Undefined'}</Text>
          </View>
        </View>
        
        <View style={styles.deepDiveCardContent}>
          {/* Story */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>STORY</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {getShortCenterStory(center)}
            </Text>
          </View>
          
          {/* How This Shows Up */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>HOW THIS SHOWS UP</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {center.your_genius || getDefaultCenterShowsUp(centerName, isDefined)}
            </Text>
          </View>
          
          {/* Challenge */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>CHALLENGE</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {getShortText(center.your_challenge) || getDefaultCenterChallenge(centerName, isDefined)}
            </Text>
          </View>
          
          {/* Practical Tips */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>PRACTICAL TIPS</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {center.practical_experiments?.[0] || getDefaultCenterTip(centerName, isDefined)}
            </Text>
          </View>
        </View>
        
        {/* Reflect CTA */}
        <TouchableOpacity
          style={[styles.deepDiveAskCta, { borderTopColor: theme.border }]}
          onPress={() => openReflection(
            `${isDefined ? 'Defined' : 'Undefined'} ${centerName}`,
            'center',
            getCenterReflectionPrompt(centerName, isDefined),
            'deep_dive',
            `center_${centerName.toLowerCase().replace(/\s/g, '_')}`,
            isDefined ? 'defined' : 'undefined'
          )}
          activeOpacity={0.7}
        >
          <Text style={[styles.deepDiveAskCtaText, { color: theme.accent }]}>Reflect on this →</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // Helper functions for center content - more human tone
  const getShortCenterStory = (center: any): string => {
    if (center.what_this_means) {
      const text = center.what_this_means;
      const firstSentence = text.split('.')[0] + '.';
      return firstSentence.length < 90 ? firstSentence : firstSentence.slice(0, 87) + '...';
    }
    const name = (center.name || center.center_name || '').toLowerCase();
    // More human fallbacks based on center
    const stories: Record<string, { defined: string; undefined: string }> = {
      'head': { defined: 'Your mind consistently generates questions and ideas—it doesn\'t turn off easily.', undefined: 'You pick up on the mental energy around you. Not all those questions are yours.' },
      'ajna': { defined: 'You have your own reliable way of thinking things through.', undefined: 'You can see things from multiple angles—your thinking shifts depending on context.' },
      'throat': { defined: 'You have a consistent voice and way of expressing yourself.', undefined: 'Your expression adapts to your environment. Sometimes you have a lot to say, sometimes not.' },
      'g': { defined: 'You carry a stable sense of who you are and where you\'re going.', undefined: 'Your sense of self shifts with your environment and the people around you.' },
      'g center': { defined: 'You carry a stable sense of who you are and where you\'re going.', undefined: 'Your sense of self shifts with your environment and the people around you.' },
      'heart': { defined: 'You have consistent willpower when you commit to something.', undefined: 'Your willpower fluctuates. Careful what you promise.' },
      'ego': { defined: 'You have consistent willpower when you commit to something.', undefined: 'Your willpower fluctuates. Careful what you promise.' },
      'spleen': { defined: 'Your intuition speaks clearly—quick knowing about what\'s right or not.', undefined: 'You absorb fears from your environment. Learn to tell which ones are actually yours.' },
      'solar plexus': { defined: 'You ride emotional waves—highs, lows, and everything between.', undefined: 'You absorb others\' emotions deeply. Not all that feeling belongs to you.' },
      'sacral': { defined: 'You have sustainable energy for work you love. Your gut knows what\'s right.', undefined: 'You don\'t have consistent work energy. Rest isn\'t optional—it\'s required.' },
      'root': { defined: 'You handle pressure in a consistent way. It doesn\'t control you.', undefined: 'You amplify pressure from outside. Not everything is as urgent as it feels.' }
    };
    return stories[name]?.[center.defined ? 'defined' : 'undefined'] || (center.defined 
      ? 'You have consistent access to this energy.'
      : 'You take in this energy from others and amplify it.');
  };

  const getShortText = (text: string | undefined): string => {
    if (!text) return '';
    const firstSentence = text.split('.')[0] + '.';
    return firstSentence.length < 100 ? firstSentence : firstSentence.slice(0, 97) + '...';
  };

  const getDefaultCenterShowsUp = (centerName: string, isDefined: boolean): string => {
    const name = centerName.toLowerCase();
    const defaults: Record<string, { defined: string; undefined: string }> = {
      'head': { defined: 'You\'re always thinking. The questions keep coming, whether you want them to or not.', undefined: 'You pick up other people\'s questions. Not all that mental noise is yours.' },
      'ajna': { defined: 'You think in consistent patterns. You have your own way of making sense of things.', undefined: 'Your thinking shifts with the room. You can see things from many angles.' },
      'throat': { defined: 'You have a voice that\'s distinctly yours. Expression comes consistently.', undefined: 'Sometimes you have a lot to say, sometimes nothing. It depends on where you are.' },
      'g': { defined: 'You know who you are. That doesn\'t change much no matter where you go.', undefined: 'You shift with your environment. Different places, different people, different you.' },
      'g center': { defined: 'You know who you are. That doesn\'t change much no matter where you go.', undefined: 'You shift with your environment. Different places, different people, different you.' },
      'heart': { defined: 'When you say you\'ll do something, you mean it. You have willpower to burn.', undefined: 'Your willpower comes and goes. Be careful what you promise.' },
      'ego': { defined: 'When you say you\'ll do something, you mean it. You have willpower to burn.', undefined: 'Your willpower comes and goes. Be careful what you promise.' },
      'spleen': { defined: 'You get gut hits about what\'s right, safe, off. Quick knowing.', undefined: 'You absorb fears from your environment. Hard to tell which ones are real.' },
      'solar plexus': { defined: 'You ride emotional waves. Highs, lows, and everything in between—that\'s your weather.', undefined: 'You absorb what others feel. Someone else\'s mood can feel like your own.' },
      'sacral': { defined: 'You have a motor for work. When you\'re lit up, you can go all day.', undefined: 'You don\'t have sustainable work energy. Rest isn\'t lazy—it\'s necessary.' },
      'root': { defined: 'Pressure doesn\'t rattle you the same way. You handle stress consistently.', undefined: 'You amplify external pressure. Everything feels urgent even when it\'s not.' }
    };
    return defaults[name]?.[isDefined ? 'defined' : 'undefined'] || 'In real life, this shows up in how you handle this energy.';
  };

  const getDefaultCenterChallenge = (centerName: string, isDefined: boolean): string => {
    const name = centerName.toLowerCase();
    const defaults: Record<string, { defined: string; undefined: string }> = {
      'head': { defined: 'The trap is overthinking—running on questions that don\'t actually need answering.', undefined: 'The trap is chasing questions that aren\'t yours. Mental clutter that belongs to someone else.' },
      'ajna': { defined: 'The trap is rigidity. Insisting your way of thinking is the only way.', undefined: 'The trap is feeling like you need a fixed opinion. You don\'t.' },
      'throat': { defined: 'The trap is speaking before the timing is right.', undefined: 'The trap is forcing words when you have nothing real to say.' },
      'g': { defined: 'The trap is being inflexible about who you are.', undefined: 'The trap is identity confusion—not knowing who you are without context.' },
      'g center': { defined: 'The trap is being inflexible about who you are.', undefined: 'The trap is identity confusion—not knowing who you are without context.' },
      'heart': { defined: 'The trap is overcommitting—using willpower on things that don\'t matter.', undefined: 'The trap is making promises your borrowed willpower can\'t keep.' },
      'ego': { defined: 'The trap is overcommitting—using willpower on things that don\'t matter.', undefined: 'The trap is making promises your borrowed willpower can\'t keep.' },
      'spleen': { defined: 'The trap is ignoring those quick hits because your mind disagrees.', undefined: 'The trap is acting on fears that aren\'t yours.' },
      'solar plexus': { defined: 'The trap is deciding at emotional peaks or valleys. Both distort reality.', undefined: 'The trap is confusing someone else\'s emotion for your own.' },
      'sacral': { defined: 'The trap is burnout—working past what your body actually wants.', undefined: 'The trap is trying to keep up with people who have more fuel than you.' },
      'root': { defined: 'The trap is getting addicted to pressure—always needing more.', undefined: 'The trap is letting other people\'s urgency set your pace.' }
    };
    return defaults[name]?.[isDefined ? 'defined' : 'undefined'] || 'The trap is going unconscious with this energy.';
  };

  const getDefaultCenterTip = (centerName: string, isDefined: boolean): string => {
    const name = centerName.toLowerCase();
    const defaults: Record<string, { defined: string; undefined: string }> = {
      'head': { defined: 'Before chasing a question, ask: does this actually need solving?', undefined: 'Try: check if this question was in your head before you walked into the room.' },
      'ajna': { defined: 'Share your view, but stay curious. Your way isn\'t the only way.', undefined: 'It\'s okay to not have a position. "I don\'t know yet" is valid.' },
      'throat': { defined: 'Wait for the right moment. Not everything needs to be said immediately.', undefined: 'When you have nothing to say, don\'t fill the silence. That\'s fine.' },
      'g': { defined: 'You know where you\'re going. Trust it—even when others question it.', undefined: 'Notice which places make you feel most like yourself. Go there more.' },
      'g center': { defined: 'You know where you\'re going. Trust it—even when others question it.', undefined: 'Notice which places make you feel most like yourself. Go there more.' },
      'heart': { defined: 'Only commit when you mean it. Willpower is finite.', undefined: 'Don\'t promise things that require willpower you don\'t consistently have.' },
      'ego': { defined: 'Only commit when you mean it. Willpower is finite.', undefined: 'Don\'t promise things that require willpower you don\'t consistently have.' },
      'spleen': { defined: 'Trust the first hit. The analysis usually just talks you out of what you knew.', undefined: 'When fear shows up, ask: is this mine? Sometimes it isn\'t.' },
      'solar plexus': { defined: 'Wait. Check how you feel about it tomorrow. And the day after.', undefined: 'When you feel emotional, ask: whose feeling is this?' },
      'sacral': { defined: 'Follow what lights you up. Say no when your gut isn\'t in it.', undefined: 'Rest before you\'re exhausted. You don\'t get a warning light.' },
      'root': { defined: 'Pressure can be fuel—but you don\'t need it to function.', undefined: 'When everything feels urgent, slow down. It\'s probably not.' }
    };
    return defaults[name]?.[isDefined ? 'defined' : 'undefined'] || 'Notice how this energy moves through you.';
  };

  // Gates Cards - each gate as its own card with unique content
  const renderGatesCards = () => {
    if (!gatesData?.gates) return null;
    
    return (
      <View style={{ gap: 8 }}>
        {gatesData.gates.slice(0, 12).map((gate: any, idx: number) => renderGateCard(gate, idx))}
      </View>
    );
  };

  // NEW: Gates with NestedCollapsible, sorted by priority (Personality Sun, Design Sun, Channels, others)
  const renderGatesCardsCollapsible = () => {
    if (!gatesData?.gates) return null;
    
    // Sort gates by priority
    const sortedGates = [...gatesData.gates].sort((a: any, b: any) => {
      const getPriority = (gate: any): number => {
        const gateNum = gate.gate_number || gate.gate;
        const personalitySun = data?.personality_sun;
        const designSun = data?.design_sun;
        const pSunGate = typeof personalitySun === 'object' ? personalitySun?.gate : personalitySun;
        const dSunGate = typeof designSun === 'object' ? designSun?.gate : designSun;
        
        // Priority: Personality Sun (0), Design Sun (1), Channel gates (2), others (3)
        if (gateNum === pSunGate) return 0;
        if (gateNum === dSunGate) return 1;
        // Check if gate is part of a channel
        const isChannelGate = data?.channels?.some((ch: any) => {
          const gatesInChannel = ch.gates?.split('-').map((g: string) => parseInt(g));
          return gatesInChannel?.includes(gateNum);
        });
        if (isChannelGate) return 2;
        return 3;
      };
      return getPriority(a) - getPriority(b);
    });
    
    // Only show top 12 gates
    const topGates = sortedGates.slice(0, 12);
    
    return (
      <View style={{ gap: 8 }}>
        {topGates.map((gate: any, idx: number) => {
          const gateName = gate.name || gate.gate_name || gate.theme || `Gate ${gate.gate_number || gate.gate}`;
          const gateNum = gate.gate_number || gate.gate;
          
          // Determine if this is a priority gate
          const personalitySun = data?.personality_sun;
          const designSun = data?.design_sun;
          const pSunGate = typeof personalitySun === 'object' ? personalitySun?.gate : personalitySun;
          const dSunGate = typeof designSun === 'object' ? designSun?.gate : designSun;
          const isPriority = gateNum === pSunGate || gateNum === dSunGate;
          
          // Subtitle based on role
          const getGateRole = (): string => {
            if (gateNum === pSunGate) return 'Personality Sun - Your conscious expression';
            if (gateNum === dSunGate) return 'Design Sun - Your unconscious drive';
            const channel = data?.channels?.find((ch: any) => {
              const gatesInChannel = ch.gates?.split('-').map((g: string) => parseInt(g));
              return gatesInChannel?.includes(gateNum);
            });
            if (channel) return `Part of ${channel.name || 'Channel'}`;
            return 'Activated energy';
          };
          
          return (
            <NestedCollapsible
              key={`gate-${gateNum}`}
              title={`Gate ${gateNum}: ${gateName}`}
              subtitle={getGateRole()}
              defaultOpen={idx < 3} // Top 3 open by default
              status={isPriority ? 'active' : 'defined'}
              lazyRender={true}
            >
              {renderGateContentMirrorLanguage(gate)}
            </NestedCollapsible>
          );
        })}
      </View>
    );
  };

  // Gate content with Mirror Language labels
  const renderGateContentMirrorLanguage = (gate: any) => {
    const gateName = gate.name || gate.gate_name || gate.theme || `Gate ${gate.gate_number || gate.gate}`;
    const gateNum = gate.gate_number || gate.gate;
    
    // Recognition - The opening hook
    const getGateRecognition = (): string => {
      if (gate.what_this_means) {
        const text = gate.what_this_means;
        const firstSentence = text.split('.')[0] + '.';
        return firstSentence.length < 120 ? firstSentence : firstSentence.slice(0, 117) + '...';
      }
      const fallbacks = [
        `You keep coming back to ${gateName.toLowerCase()}. It's part of your wiring.`,
        `There's something about ${gateName.toLowerCase()} that runs through you.`,
        `${gateName} is built into you—not something you chose.`
      ];
      return fallbacks[gateNum % fallbacks.length];
    };

    // Tension - The challenge
    const getGateTension = (): string => {
      if (gate.your_challenge) {
        const text = gate.your_challenge;
        const firstSentence = text.split('.')[0] + '.';
        return firstSentence.length < 120 ? firstSentence : firstSentence.slice(0, 117) + '...';
      }
      if (gate.shadow) {
        const patterns = [
          `The trap is ${gate.shadow.toLowerCase()}—it shows up when you're stressed or unaware.`,
          `Watch for ${gate.shadow.toLowerCase()}. That's the signal something's off.`,
          `When pressure builds, this can become ${gate.shadow.toLowerCase()}.`
        ];
        return patterns[gateNum % patterns.length];
      }
      return "The challenge is staying conscious with this energy.";
    };

    // Real Life Moments
    const getGateRealLife = (): string => {
      if (gate.your_genius) {
        const text = gate.your_genius;
        const firstSentence = text.split('.')[0] + '.';
        return firstSentence.length < 120 ? firstSentence : firstSentence.slice(0, 117) + '...';
      }
      if (gate.gift) {
        const patterns = [
          `People probably notice your ${gate.gift.toLowerCase()} more than you do.`,
          `In real life, you tend toward ${gate.gift.toLowerCase()}. It's your default.`,
          `You do ${gate.gift.toLowerCase()} without thinking—it's just how you operate.`
        ];
        return patterns[gateNum % patterns.length];
      }
      return 'In real life, this shows up in how you handle certain situations.';
    };

    // Try This Instead
    const getGateTryThis = (): string => {
      if (gate.practical_experiments?.[0]) return gate.practical_experiments[0];
      if (gate.shadow && gate.gift) {
        const tips = [
          `Catch ${gate.shadow.toLowerCase()} early. Then ask: what would ${gate.gift.toLowerCase()} do here?`,
          `Try: name it when ${gate.shadow.toLowerCase()} shows up. That creates choice.`,
          `When ${gate.shadow.toLowerCase()} appears, pause. ${gate.gift} is the alternative.`
        ];
        return tips[gateNum % tips.length];
      }
      return "Notice how this plays out in your daily life.";
    };

    return (
      <View style={{ gap: 12 }}>
        {/* Recognition */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.accent }]}>RECOGNITION</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getGateRecognition()}
          </Text>
        </View>
        
        {/* Tension */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.warning || '#FF9800' }]}>TENSION</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getGateTension()}
          </Text>
        </View>
        
        {/* Real Life Moments */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.textTertiary }]}>REAL LIFE MOMENTS</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getGateRealLife()}
          </Text>
        </View>
        
        {/* Try This Instead */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.success || '#4CAF50' }]}>TRY THIS INSTEAD</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getGateTryThis()}
          </Text>
        </View>
        
        {/* Reflect CTA */}
        <TouchableOpacity
          style={[styles.deepDiveAskCta, { borderTopColor: theme.border }]}
          onPress={() => openReflection(
            `Gate ${gateNum}: ${gateName}`,
            'gate',
            getGateReflectionPrompt(gateNum, gateName),
            'deep_dive',
            `gate_${gateNum}`,
            gateName
          )}
          activeOpacity={0.7}
        >
          <Text style={[styles.deepDiveAskCtaText, { color: theme.accent }]}>Reflect on this →</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // NEW: Gene Keys Sequences as Collapsible Section with NestedCollapsibles
  const renderGeneKeysCollapsibleSection = () => {
    const hasSequences = activationSequence || venusSequence || pearlSequence;
    if (!hasSequences) return null;
    
    return (
      <CollapsibleCard
        title="Gene Keys"
        subtitle="Your deeper purpose sequences"
        badge="3 arcs"
        defaultOpen={false}
        priority="medium"
      >
        <View style={{ gap: 16 }}>
          {/* Purpose Arc - Default OPEN */}
          {activationSequence && (
            <View>
              <SectionHeader title="Purpose Arc" icon="◎" count={activationSequence.spheres?.length || 0} />
              {(activationSequence.spheres || []).map((sphere: any, idx: number) => (
                <NestedCollapsible
                  key={`purpose-${idx}`}
                  title={sphere.sphere_name}
                  subtitle={sphere.gene_key ? `GK ${sphere.gene_key}` : 'Core sequence'}
                  defaultOpen={idx === 0} // First sphere open
                  status="active"
                  lazyRender={true}
                >
                  {renderSphereContentMirrorLanguage(sphere)}
                </NestedCollapsible>
              ))}
            </View>
          )}
          
          {/* Love Arc - Default CLOSED */}
          {venusSequence && (
            <View>
              <SectionHeader title="Love Arc" icon="♡" count={venusSequence.spheres?.length || 0} />
              {(venusSequence.spheres || []).map((sphere: any, idx: number) => (
                <NestedCollapsible
                  key={`love-${idx}`}
                  title={sphere.sphere_name}
                  subtitle={sphere.gene_key ? `GK ${sphere.gene_key}` : 'Relationship sequence'}
                  defaultOpen={false}
                  status="defined"
                  lazyRender={true}
                >
                  {renderSphereContentMirrorLanguage(sphere)}
                </NestedCollapsible>
              ))}
            </View>
          )}
          
          {/* Prosperity Arc - Default CLOSED */}
          {pearlSequence && (
            <View>
              <SectionHeader title="Prosperity Arc" icon="◇" count={pearlSequence.spheres?.length || 0} />
              {(pearlSequence.spheres || []).map((sphere: any, idx: number) => (
                <NestedCollapsible
                  key={`prosperity-${idx}`}
                  title={sphere.sphere_name}
                  subtitle={sphere.gene_key ? `GK ${sphere.gene_key}` : 'Vocation sequence'}
                  defaultOpen={false}
                  status="defined"
                  lazyRender={true}
                >
                  {renderSphereContentMirrorLanguage(sphere)}
                </NestedCollapsible>
              ))}
            </View>
          )}
        </View>
      </CollapsibleCard>
    );
  };

  // Sphere content with Mirror Language labels
  const renderSphereContentMirrorLanguage = (sphere: any) => {
    // Recognition
    const getSphereRecognition = (): string => {
      if (sphere.what_this_means) {
        const text = sphere.what_this_means;
        const firstSentence = text.split('.')[0] + '.';
        return firstSentence.length < 120 ? firstSentence : firstSentence.slice(0, 117) + '...';
      }
      const fallbacks: Record<string, string> = {
        "Life's Work": "This is where your core purpose tends to show up most clearly.",
        "Evolution": "This shapes how you grow and transform over time.",
        "Radiance": "This influences how others experience your presence.",
        "Purpose": "This points to what you're really here to do.",
        "Attraction": "This shapes who and what you draw into your life.",
        "IQ": "This colors how you process and understand things.",
        "EQ": "This influences how you navigate emotions and connection.",
        "SQ": "This touches your sense of meaning and spirit.",
        "Core": "This sits at the heart of your relational patterns.",
        "Brand": "This shapes how others see and remember you.",
        "Culture": "This influences the environments you create.",
        "Vocation": "This points to work that feels genuinely meaningful.",
        "Pearl": "This is about your lasting contribution."
      };
      return fallbacks[sphere.sphere_name] || "This energy shapes a key part of who you are.";
    };

    // Tension
    const getSphereTension = (): string => {
      if (!sphere.shadow) return "The trap is going unconscious with this energy.";
      const patterns = [
        `The trap is ${sphere.shadow.toLowerCase()}—especially when stressed.`,
        `When you're off-center, ${sphere.shadow.toLowerCase()} tends to take over.`,
        `Watch for ${sphere.shadow.toLowerCase()}. That's usually the sign something's off.`
      ];
      return patterns[Math.floor((sphere.gene_key || 1) % patterns.length)];
    };

    // Real Life Moments
    const getSphereRealLife = (): string => {
      if (sphere.gift) {
        return `You tend toward ${sphere.gift.toLowerCase()}—people probably notice this about you.`;
      }
      return 'You have your own way of expressing this energy.';
    };

    // Try This Instead
    const getSphereTryThis = (): string => {
      if (sphere.practical_tips?.[0]) return sphere.practical_tips[0];
      if (sphere.gift && sphere.shadow) {
        const tips = [
          `When you notice ${sphere.shadow.toLowerCase()}, pause. What would ${sphere.gift} look like here?`,
          `Try: catch yourself in ${sphere.shadow.toLowerCase()} mode, then ask what ${sphere.gift} would do.`,
          `Practice: name it when ${sphere.shadow.toLowerCase()} shows up. Just that creates space.`
        ];
        return tips[Math.floor((sphere.gene_key || 1) % tips.length)];
      }
      return "Notice when this energy feels off—that's useful information.";
    };

    return (
      <View style={{ gap: 12 }}>
        {/* Recognition */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.accent }]}>RECOGNITION</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getSphereRecognition()}
          </Text>
        </View>
        
        {/* Tension */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.warning || '#FF9800' }]}>TENSION</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getSphereTension()}
          </Text>
        </View>
        
        {/* Real Life Moments */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.textTertiary }]}>REAL LIFE MOMENTS</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getSphereRealLife()}
          </Text>
        </View>
        
        {/* Try This Instead */}
        <View>
          <Text style={[styles.mirrorSectionLabel, { color: theme.success || '#4CAF50' }]}>TRY THIS INSTEAD</Text>
          <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>
            {getSphereTryThis()}
          </Text>
        </View>
        
        {/* Reflect CTA */}
        <TouchableOpacity
          style={[styles.deepDiveAskCta, { borderTopColor: theme.border }]}
          onPress={() => openReflection(
            sphere.sphere_name,
            'sphere',
            getSphereReflectionPrompt(sphere.sphere_name, sphere.gene_key || 0),
            'deep_dive',
            `sphere_${sphere.gene_key}`,
            `GK ${sphere.gene_key}`
          )}
          activeOpacity={0.7}
        >
          <Text style={[styles.deepDiveAskCtaText, { color: theme.accent }]}>Reflect on this →</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // Individual Gate Card - Mirror pattern language
  const renderGateCard = (gate: any, idx: number) => {
    const gateName = gate.name || gate.gate_name || gate.theme || `Gate ${gate.gate_number || gate.gate}`;
    const gateNum = gate.gate_number || gate.gate;
    
    // Direct story - human pattern first
    const getGateStory = (): string => {
      if (gate.what_this_means) {
        const text = gate.what_this_means;
        const firstSentence = text.split('.')[0] + '.';
        return firstSentence.length < 85 ? firstSentence : firstSentence.slice(0, 82) + '...';
      }
      const fallbacks = [
        `You keep coming back to ${gateName.toLowerCase()}. It's part of your wiring.`,
        `There's something about ${gateName.toLowerCase()} that runs through you.`,
        `${gateName} is built into you—not something you chose.`
      ];
      return fallbacks[gateNum % fallbacks.length];
    };

    // Behavioral "shows up" - real life patterns
    const getGateShowsUp = (): string => {
      if (gate.your_genius) {
        const text = gate.your_genius;
        const firstSentence = text.split('.')[0] + '.';
        return firstSentence.length < 85 ? firstSentence : firstSentence.slice(0, 82) + '...';
      }
      if (gate.gift) {
        const patterns = [
          `People probably notice your ${gate.gift.toLowerCase()} more than you do.`,
          `In real life, you tend toward ${gate.gift.toLowerCase()}. It's your default.`,
          `You do ${gate.gift.toLowerCase()} without thinking—it's just how you operate.`
        ];
        return patterns[gateNum % patterns.length];
      }
      return 'In real life, this shows up in how you handle certain situations.';
    };

    // More direct challenge phrases
    const getGateChallenge = (): string => {
      if (gate.your_challenge) {
        const text = gate.your_challenge;
        const firstSentence = text.split('.')[0] + '.';
        return firstSentence.length < 85 ? firstSentence : firstSentence.slice(0, 82) + '...';
      }
      if (gate.shadow) {
        const patterns = [
          `The trap is ${gate.shadow.toLowerCase()}.`,
          `Watch for ${gate.shadow.toLowerCase()}—that's the signal.`,
          `When stressed, this can turn into ${gate.shadow.toLowerCase()}.`
        ];
        return patterns[gateNum % patterns.length];
      }
      return "The challenge is staying conscious with this energy.";
    };

    // More actionable tips
    const getGateTip = (): string => {
      if (gate.practical_experiments?.[0]) return gate.practical_experiments[0];
      if (gate.shadow && gate.gift) {
        const tips = [
          `Catch ${gate.shadow.toLowerCase()} early. Then ask: what would ${gate.gift.toLowerCase()} do here?`,
          `Try: name it when ${gate.shadow.toLowerCase()} shows up. That creates choice.`,
          `When ${gate.shadow.toLowerCase()} appears, pause. ${gate.gift} is the alternative.`
        ];
        return tips[gateNum % tips.length];
      }
      return "Notice how this plays out in your daily life.";
    };
    
    return (
      <View key={idx} style={[styles.deepDiveCard, { backgroundColor: theme.surface, borderColor: theme.border, borderLeftColor: theme.accent, borderLeftWidth: 3 }]}>
        <View style={styles.deepDiveCardHeader}>
          <View>
            <Text style={[styles.deepDiveCardTitle, { color: theme.text }]}>Gate {gateNum}</Text>
            <Text style={[styles.deepDiveCardSubtitle, { color: theme.accent }]}>{gateName}</Text>
          </View>
        </View>
        
        <View style={styles.deepDiveCardContent}>
          {/* Story */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>STORY</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {getGateStory()}
            </Text>
          </View>
          
          {/* How This Shows Up */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>HOW THIS SHOWS UP</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {getGateShowsUp()}
            </Text>
          </View>
          
          {/* Challenge */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>CHALLENGE</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {getGateChallenge()}
            </Text>
          </View>
          
          {/* Practical Tips */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>PRACTICAL TIPS</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {getGateTip()}
            </Text>
          </View>
        </View>
        
        {/* Reflect CTA */}
        <TouchableOpacity
          style={[styles.deepDiveAskCta, { borderTopColor: theme.border }]}
          onPress={() => openReflection(
            `Gate ${gateNum}: ${gateName}`,
            'gate',
            getGateReflectionPrompt(gateNum, gateName),
            'deep_dive',
            `gate_${gateNum}`,
            gateName
          )}
          activeOpacity={0.7}
        >
          <Text style={[styles.deepDiveAskCtaText, { color: theme.accent }]}>Reflect on this →</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // Meaning Bridge - connects mechanics to lived experience
  const renderMeaningBridge = () => {
    if (!data?.core_mechanics) return null;
    
    const { type, strategy, authority, profile } = data.core_mechanics;
    
    // Generate a contextual meaning bridge based on type + authority
    const getMeaningBridge = (): string => {
      const typeInsight: Record<string, string> = {
        'Generator': `As a ${type}, your life unfolds through response—waiting for what genuinely excites your energy before committing.`,
        'Manifesting Generator': `As a ${type}, you're designed to respond quickly and pivot freely, but informing others keeps your path clear.`,
        'Projector': `As a ${type}, your wisdom is your gift. Recognition and invitation are how your guidance finds its place.`,
        'Manifestor': `As a ${type}, you're here to initiate and create impact. Informing others before action reduces the resistance you encounter.`,
        'Reflector': `As a ${type}, you sample and mirror the world around you. Time and environment are everything in your process.`,
      };
      
      const authorityInsight: Record<string, string> = {
        'Emotional': 'Your clarity comes in waves—never rush major decisions. Wait for emotional neutrality.',
        'Sacral': "Your gut response tells you what's correct. Trust the immediate 'uh-huh' or 'uh-uh.'",
        'Splenic': "Your instincts speak once and quickly. Trust the first knowing—it won't repeat.",
        'Ego': "What do you truly want? Your willpower guides when you're honest about desire.",
        'Self-Projected': 'Hear yourself speak to find clarity. Your truth reveals itself through your voice.',
        'Mental': 'Talk through decisions with trusted others—but the final knowing is yours alone.',
        'Lunar': 'Major decisions need a full moon cycle. Your clarity emerges over time, not in a moment.',
      };
      
      const base = typeInsight[type || 'Generator'] || '';
      const authorityKey = Object.keys(authorityInsight).find(k => authority?.includes(k));
      const auth = authorityKey ? authorityInsight[authorityKey] : '';
      
      return `${base} ${auth}`.trim();
    };
    
    return (
      <View style={[styles.meaningBridgeCard, { backgroundColor: theme.surface, borderColor: theme.border, borderLeftColor: theme.accent }]}>
        <Text style={[styles.meaningBridgeTitle, { color: theme.textTertiary }]}>HOW THESE MECHANICS SHAPE YOUR LIFE</Text>
        <Text style={[styles.meaningBridgeText, { color: theme.text }]}>
          {getMeaningBridge()}
        </Text>
      </View>
    );
  };

  // Core Mechanics as a clean summary block (NOT accordion)
  const renderCoreMechanicsBlock = () => {
    if (!data?.core_mechanics) return null;
    
    const { type, strategy, authority, profile, definition, incarnation_cross } = data.core_mechanics;
    
    return (
      <View style={[styles.hdOverviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>CORE MECHANICS</Text>
        
        <View style={styles.coreMechanicsGrid}>
          <View style={styles.coreMechanicsItem}>
            <Text style={[styles.coreMechanicsLabel, { color: theme.textTertiary }]}>Type</Text>
            <Text style={[styles.coreMechanicsValue, { color: theme.text }]}>{type}</Text>
          </View>
          
          <View style={styles.coreMechanicsItem}>
            <Text style={[styles.coreMechanicsLabel, { color: theme.textTertiary }]}>Strategy</Text>
            <Text style={[styles.coreMechanicsValue, { color: theme.text }]}>{strategy}</Text>
          </View>
          
          <View style={styles.coreMechanicsItem}>
            <Text style={[styles.coreMechanicsLabel, { color: theme.textTertiary }]}>Authority</Text>
            <Text style={[styles.coreMechanicsValue, { color: theme.text }]}>{authority}</Text>
          </View>
          
          <View style={styles.coreMechanicsItem}>
            <Text style={[styles.coreMechanicsLabel, { color: theme.textTertiary }]}>Profile</Text>
            <Text style={[styles.coreMechanicsValue, { color: theme.text }]}>{profile}</Text>
          </View>
          
          <View style={styles.coreMechanicsItem}>
            <Text style={[styles.coreMechanicsLabel, { color: theme.textTertiary }]}>Definition</Text>
            <Text style={[styles.coreMechanicsValue, { color: theme.text }]}>{definition || 'Single'}</Text>
          </View>
          
          <View style={[styles.coreMechanicsItem, { flex: 2 }]}>
            <Text style={[styles.coreMechanicsLabel, { color: theme.textTertiary }]}>Incarnation Cross</Text>
            <Text style={[styles.coreMechanicsValue, { color: theme.text }]}>{incarnation_cross || 'Not calculated'}</Text>
          </View>
        </View>
      </View>
    );
  };

  // Profile summaries for Deep Dive
  const PROFILE_SUMMARIES: Record<string, string> = {
    '1/3': 'You learn through deep research followed by trial and error. Foundation and experience are your teachers.',
    '1/4': 'You need solid foundations and close networks. Research first, then share through trusted connections.',
    '2/4': 'You have natural talents others recognize. Wait for the call, then share with your network.',
    '2/5': 'Your natural gifts attract projection. People see you as a solution before you do.',
    '3/5': 'You learn through breaking things and being seen as someone who can fix them.',
    '3/6': 'First you experiment, then observe, then model wisdom. Three distinct life phases.',
    '4/6': 'Your network is your foundation. First you connect, then observe, then become a role model.',
    '4/1': 'You share your research through your network. Foundation and community work together.',
    '5/1': 'You attract projections of being a savior. Ground yourself in research.',
    '5/2': 'Others see you as a problem-solver. You have natural talents you may not recognize.',
    '6/2': 'You move through three phases while carrying natural talent. Role model with inherent gifts.',
    '6/3': 'You experiment early, observe mid-life, then become a role model of wisdom.',
  };

  // Collapsible section wrapper
  const renderCollapsibleSection = (title: string, key: string, content: React.ReactNode) => {
    const isExpanded = expandedSection === key;
    
    return (
      <View style={[styles.structureAccordion, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <TouchableOpacity
          style={styles.structureAccordionHeader}
          onPress={() => setExpandedSection(isExpanded ? null : key)}
          activeOpacity={0.7}
        >
          <Text style={[styles.structureAccordionTitle, { color: theme.text }]}>{title}</Text>
          <Text style={[styles.structureAccordionChevron, { color: theme.textTertiary }]}>
            {isExpanded ? '▲' : '▼'}
          </Text>
        </TouchableOpacity>
        {isExpanded && (
          <View style={styles.structureAccordionContent}>
            {content}
          </View>
        )}
      </View>
    );
  };

  // Improved Body graph with better proportions and trustworthy appearance
  const renderImprovedBodygraph = () => {
    const definedStyle = { backgroundColor: 'rgba(255, 215, 0, 0.5)', borderColor: '#FFD700', borderWidth: 2 };
    const undefinedStyle = { backgroundColor: 'transparent', borderColor: theme.border, borderWidth: 1.5 };
    
    const getStyle = (centerKey: string) => centersDefinition[centerKey] ? definedStyle : undefinedStyle;
    
    // Count defined vs undefined centers
    const definedCount = Object.values(centersDefinition).filter(Boolean).length;
    const undefinedCount = 9 - definedCount;
    
    return (
      <View style={[styles.improvedBodygraphCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>YOUR BODY GRAPH</Text>
        <Text style={[styles.bodygraphSubtitle, { color: theme.textSecondary }]}>
          {definedCount} defined • {undefinedCount} undefined centers
        </Text>
        
        <View style={styles.improvedBodygraphVisual}>
          {/* HEAD - Triangle at top */}
          <TouchableOpacity onPress={() => handleBodygraphCenterTap('Head')} activeOpacity={0.7}>
            <View style={[styles.bgHead, getStyle('head')]} />
          </TouchableOpacity>
          
          {/* AJNA - Triangle pointing down */}
          <TouchableOpacity onPress={() => handleBodygraphCenterTap('Ajna')} activeOpacity={0.7}>
            <View style={[styles.bgAjna, getStyle('ajna')]} />
          </TouchableOpacity>
          
          {/* THROAT - Square */}
          <TouchableOpacity onPress={() => handleBodygraphCenterTap('Throat')} activeOpacity={0.7}>
            <View style={[styles.bgThroat, getStyle('throat')]} />
          </TouchableOpacity>
          
          {/* G CENTER - Diamond */}
          <TouchableOpacity onPress={() => handleBodygraphCenterTap('G')} activeOpacity={0.7}>
            <View style={[styles.bgG, getStyle('g')]} />
          </TouchableOpacity>
          
          {/* MIDDLE ROW - Heart, Spleen, Solar Plexus */}
          <View style={styles.bgMiddleRow}>
            <TouchableOpacity onPress={() => handleBodygraphCenterTap('Heart')} activeOpacity={0.7}>
              <View style={[styles.bgHeart, getStyle('heart')]} />
            </TouchableOpacity>
            
            <View style={styles.bgMiddleSpacer} />
            
            <TouchableOpacity onPress={() => handleBodygraphCenterTap('Spleen')} activeOpacity={0.7}>
              <View style={[styles.bgSpleen, getStyle('spleen')]} />
            </TouchableOpacity>
            
            <TouchableOpacity onPress={() => handleBodygraphCenterTap('Solar Plexus')} activeOpacity={0.7}>
              <View style={[styles.bgSolarPlexus, getStyle('solar_plexus')]} />
            </TouchableOpacity>
          </View>
          
          {/* SACRAL - Square */}
          <TouchableOpacity onPress={() => handleBodygraphCenterTap('Sacral')} activeOpacity={0.7}>
            <View style={[styles.bgSacral, getStyle('sacral')]} />
          </TouchableOpacity>
          
          {/* ROOT - Square at bottom */}
          <TouchableOpacity onPress={() => handleBodygraphCenterTap('Root')} activeOpacity={0.7}>
            <View style={[styles.bgRoot, getStyle('root')]} />
          </TouchableOpacity>
        </View>
        
        <View style={styles.bodygraphLegend}>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: 'rgba(255, 215, 0, 0.5)', borderColor: '#FFD700' }]} />
            <Text style={[styles.legendText, { color: theme.textTertiary }]}>Defined</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: 'transparent', borderColor: theme.border }]} />
            <Text style={[styles.legendText, { color: theme.textTertiary }]}>Undefined</Text>
          </View>
        </View>
        
        <Text style={[styles.bodygraphHint, { color: theme.textTertiary }]}>
          Tap a center to explore
        </Text>
      </View>
    );
  };

  // Sequences section - Sphere-based flow (ALWAYS EXPANDED)
  const renderSequencesSectionExpanded = () => {
    return (
      <View style={[styles.sequencesCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>YOUR SEQUENCES</Text>
        <Text style={[styles.sequencesSubtitle, { color: theme.textSecondary }]}>
          How your life patterns unfold
        </Text>
        
        {/* ACTIVATION SEQUENCE - Core Life Theme */}
        {renderSphereSequence(
          'Core Life Theme',
          'Activation Sequence',
          activationSequence?.spheres || getDefaultActivationSpheres(),
          '#FFD700', // Gold
        )}
        
        {/* VENUS SEQUENCE - Relationship Pattern */}
        {renderSphereSequence(
          'Relationship Pattern',
          'Venus Sequence',
          venusSequence?.spheres || getDefaultVenusSpheres(),
          '#FF69B4', // Pink
        )}
        
        {/* PEARL SEQUENCE - Work & Contribution */}
        {renderSphereSequence(
          'Work & Contribution',
          'Pearl Sequence',
          pearlSequence?.spheres || getDefaultPearlSpheres(),
          '#90EE90', // Green
        )}
      </View>
    );
  };

  // Render a single sequence with its spheres
  const renderSphereSequence = (
    title: string, 
    subtitle: string, 
    spheres: any[], 
    accentColor: string
  ) => {
    return (
      <View style={styles.sphereSequenceContainer}>
        <View style={styles.sequenceHeaderRow}>
          <View style={[styles.sequenceAccentDot, { backgroundColor: accentColor }]} />
          <View>
            <Text style={[styles.sphereSequenceTitle, { color: theme.text }]}>{title}</Text>
            <Text style={[styles.sphereSequenceSubtitle, { color: theme.textTertiary }]}>{subtitle}</Text>
          </View>
        </View>
        
        <View style={styles.sphereFlowContainer}>
          {spheres.map((sphere, index) => (
            <View key={index}>
              {/* Connector line (except for first) */}
              {index > 0 && (
                <View style={[styles.sphereConnector, { backgroundColor: theme.border }]} />
              )}
              
              {/* Sphere card */}
              <View style={[styles.sequenceSphereCard, { borderColor: theme.border, borderLeftColor: accentColor }]}>
                <View style={styles.sequenceSphereHeader}>
                  <Text style={[styles.sequenceSphereName, { color: theme.text }]}>
                    {sphere.sphere_name}
                  </Text>
                  {sphere.gene_key && (
                    <Text style={[styles.sequenceSphereGeneKey, { color: accentColor }]}>
                      GK {sphere.gene_key}
                    </Text>
                  )}
                </View>
                
                {/* Shadow → Gift flow */}
                {(sphere.shadow || sphere.gift) && (
                  <View style={styles.sequenceSphereGiftFlow}>
                    {sphere.shadow && (
                      <Text style={[styles.sequenceSphereShadow, { color: theme.textTertiary }]}>
                        {sphere.shadow}
                      </Text>
                    )}
                    {sphere.shadow && sphere.gift && (
                      <Text style={[styles.sequenceSphereArrow, { color: theme.textTertiary }]}> → </Text>
                    )}
                    {sphere.gift && (
                      <Text style={[styles.sequenceSphereGift, { color: theme.accent }]}>
                        {sphere.gift}
                      </Text>
                    )}
                  </View>
                )}
                
                {/* Behavioral interpretation */}
                <Text style={[styles.sequenceSphereInterpretation, { color: theme.textSecondary }]}>
                  {getSphereInterpretation(sphere)}
                </Text>
              </View>
            </View>
          ))}
        </View>
      </View>
    );
  };

  // Get behavioral interpretation for a sphere (max 2 lines)
  const getSphereInterpretation = (sphere: any): string => {
    // Use specific interpretation if available
    if (sphere.what_this_means) {
      // Take first sentence only
      const firstSentence = sphere.what_this_means.split('.')[0] + '.';
      if (firstSentence.length < 120) return firstSentence;
      return firstSentence.slice(0, 117) + '...';
    }
    
    // Generate behavioral fallback based on sphere name and gift
    const fallbacks: Record<string, string> = {
      "Life's Work": `This is where your natural contribution emerges through ${sphere.gift || 'your unique gifts'}.`,
      "Evolution": `Your growth edge—where ${sphere.shadow || 'challenge'} transforms into ${sphere.gift || 'strength'}.`,
      "Radiance": `What naturally shines when you're at ease: ${sphere.gift || 'your authentic presence'}.`,
      "Purpose": `The deeper direction your life moves toward through ${sphere.gift || 'alignment'}.`,
      "Attraction": `How you draw others in—through ${sphere.gift || 'your natural magnetism'}.`,
      "IQ": `Your mental style in relationships, tending toward ${sphere.gift || 'clarity'}.`,
      "EQ": `How you process emotions in connection, moving through ${sphere.gift || 'awareness'}.`,
      "SQ": `Your spiritual or intuitive style in bonds: ${sphere.gift || 'depth'}.`,
      "Core": `The center of your relating pattern: ${sphere.gift || 'your essential way of connecting'}.`,
      "Vocation": `Your natural calling emerges through ${sphere.gift || 'authentic expression'}.`,
      "Culture": `How you contribute to collective spaces via ${sphere.gift || 'your unique perspective'}.`,
      "Brand": `What others recognize in your work: ${sphere.gift || 'your signature quality'}.`,
      "Pearl": `Where prosperity flows when aligned: ${sphere.gift || 'your natural abundance'}.`,
    };
    
    return fallbacks[sphere.sphere_name] || `This sphere shapes how you experience ${sphere.gift || 'this aspect of life'}.`;
  };

  // Default sphere structures when API data is missing
  const getDefaultActivationSpheres = () => [
    { sphere_name: "Life's Work", gene_key: null, shadow: null, gift: null },
    { sphere_name: "Evolution", gene_key: null, shadow: null, gift: null },
    { sphere_name: "Radiance", gene_key: null, shadow: null, gift: null },
    { sphere_name: "Purpose", gene_key: null, shadow: null, gift: null },
  ];

  const getDefaultVenusSpheres = () => [
    { sphere_name: "Attraction", gene_key: null, shadow: null, gift: null },
    { sphere_name: "IQ", gene_key: null, shadow: null, gift: null },
    { sphere_name: "EQ", gene_key: null, shadow: null, gift: null },
    { sphere_name: "SQ", gene_key: null, shadow: null, gift: null },
    { sphere_name: "Core", gene_key: null, shadow: null, gift: null },
  ];

  const getDefaultPearlSpheres = () => [
    { sphere_name: "Vocation", gene_key: null, shadow: null, gift: null },
    { sphere_name: "Culture", gene_key: null, shadow: null, gift: null },
    { sphere_name: "Brand", gene_key: null, shadow: null, gift: null },
    { sphere_name: "Pearl", gene_key: null, shadow: null, gift: null },
  ];

  // Keep old body graph as fallback (renamed)
  const renderBodygraph = () => {
    return (
      <View style={[styles.bodygraphCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary, marginBottom: 12 }]}>YOUR BODY GRAPH</Text>
        <View style={styles.bodygraphVisual}>
          {/* Row 1: Head */}
          <TouchableOpacity onPress={() => handleBodygraphCenterTap('Head')} activeOpacity={0.7}>
            <View style={[styles.bodygraphHead, centersDefinition['head'] 
              ? { backgroundColor: 'rgba(255, 215, 0, 0.4)', borderColor: '#FFD700', borderWidth: 3 }
              : { borderColor: theme.border, borderWidth: 2 }]} />
          </TouchableOpacity>
          
          {/* Row 2: Ajna */}
          <TouchableOpacity onPress={() => handleBodygraphCenterTap('Ajna')} activeOpacity={0.7}>
            <View style={[styles.bodygraphAjna, centersDefinition['ajna'] 
              ? { backgroundColor: 'rgba(255, 215, 0, 0.4)', borderColor: '#FFD700', borderWidth: 3 }
              : { borderColor: theme.border, borderWidth: 2 }]} />
          </TouchableOpacity>
          
          {/* Row 3: Throat */}
          <TouchableOpacity onPress={() => handleBodygraphCenterTap('Throat')} activeOpacity={0.7}>
            <View style={[styles.bodygraphThroat, centersDefinition['throat'] 
              ? { backgroundColor: 'rgba(255, 215, 0, 0.4)', borderColor: '#FFD700', borderWidth: 3 }
              : { borderColor: theme.border, borderWidth: 2 }]} />
          </TouchableOpacity>
          
          {/* Row 4: G/Identity */}
          <TouchableOpacity onPress={() => handleBodygraphCenterTap('G')} activeOpacity={0.7}>
            <View style={[styles.bodygraphGCenter, centersDefinition['g'] 
              ? { backgroundColor: 'rgba(255, 215, 0, 0.4)', borderColor: '#FFD700', borderWidth: 3 }
              : { borderColor: theme.border, borderWidth: 2 }]} />
          </TouchableOpacity>
          
          {/* Row 5: Heart + Spleen + Solar Plexus */}
          <View style={styles.bodygraphMiddle}>
            <TouchableOpacity onPress={() => handleBodygraphCenterTap('Heart')} activeOpacity={0.7}>
              <View style={[styles.bodygraphHeart, centersDefinition['heart'] 
                ? { backgroundColor: 'rgba(255, 215, 0, 0.4)', borderColor: '#FFD700', borderWidth: 3 }
                : { borderColor: theme.border, borderWidth: 2 }]} />
            </TouchableOpacity>
            <TouchableOpacity onPress={() => handleBodygraphCenterTap('Spleen')} activeOpacity={0.7}>
              <View style={[styles.bodygraphSpleen, centersDefinition['spleen'] 
                ? { backgroundColor: 'rgba(255, 215, 0, 0.4)', borderColor: '#FFD700', borderWidth: 3 }
                : { borderColor: theme.border, borderWidth: 2 }]} />
            </TouchableOpacity>
            <TouchableOpacity onPress={() => handleBodygraphCenterTap('Solar Plexus')} activeOpacity={0.7}>
              <View style={[styles.bodygraphSolarPlexus, centersDefinition['solar_plexus'] 
                ? { backgroundColor: 'rgba(255, 215, 0, 0.4)', borderColor: '#FFD700', borderWidth: 3 }
                : { borderColor: theme.border, borderWidth: 2 }]} />
            </TouchableOpacity>
          </View>
          
          {/* Row 6: Sacral */}
          <TouchableOpacity onPress={() => handleBodygraphCenterTap('Sacral')} activeOpacity={0.7}>
            <View style={[styles.bodygraphSacral, centersDefinition['sacral'] 
              ? { backgroundColor: 'rgba(255, 215, 0, 0.4)', borderColor: '#FFD700', borderWidth: 3 }
              : { borderColor: theme.border, borderWidth: 2 }]} />
          </TouchableOpacity>
          
          {/* Row 7: Root */}
          <TouchableOpacity onPress={() => handleBodygraphCenterTap('Root')} activeOpacity={0.7}>
            <View style={[styles.bodygraphRoot, centersDefinition['root'] 
              ? { backgroundColor: 'rgba(255, 215, 0, 0.4)', borderColor: '#FFD700', borderWidth: 3 }
              : { borderColor: theme.border, borderWidth: 2 }]} />
          </TouchableOpacity>
        </View>
        <Text style={[styles.bodygraphHint, { color: theme.textTertiary }]}>
          Tap a center to learn more
        </Text>
      </View>
    );
  };

  // Centers section for deep dive - with correct defined/undefined copy
  const renderCentersSection = () => {
    if (!centersData?.centers) return null;
    
    // Correct center descriptions based on defined/undefined state
    const getCenterDescription = (center: any): string => {
      const centerName = (center.name || center.center_name || '').toLowerCase();
      const isDefined = center.defined === true;
      
      const descriptions: Record<string, { defined: string; undefined: string; governs: string }> = {
        'head': {
          governs: 'mental pressure, inspiration, and questioning',
          defined: 'You have consistent mental pressure and inspiration. Your mind reliably generates questions and ideas.',
          undefined: 'You amplify mental pressure from your environment. You sample different ways of thinking and can get overwhelmed by questions that aren\'t yours.'
        },
        'ajna': {
          governs: 'conceptualization, processing, and mental certainty',
          defined: 'You have a consistent way of thinking and processing information. Your mental certainty is reliable.',
          undefined: 'You\'re mentally flexible and can see things from many perspectives. Don\'t pressure yourself to have fixed opinions.'
        },
        'throat': {
          governs: 'communication, expression, and manifestation',
          defined: 'You have a consistent voice and way of expressing yourself. Communication flows naturally.',
          undefined: 'Your voice and communication style adapts to your environment. Wait for the right timing to speak.'
        },
        'g': {
          governs: 'identity, direction, and love',
          defined: 'You have a fixed sense of identity and direction. You know who you are and where you\'re going.',
          undefined: 'Your identity is fluid and you sample different directions in life. Let your environment show you where to go.'
        },
        'heart': {
          governs: 'willpower, ego, and self-worth',
          defined: 'You have consistent access to willpower. You naturally make and keep promises.',
          undefined: 'Your willpower fluctuates. Don\'t make promises based on borrowed will—it won\'t sustain.'
        },
        'spleen': {
          governs: 'survival instinct, intuition, and immune system',
          defined: 'You have reliable instinctual awareness. You naturally sense what\'s healthy and what isn\'t.',
          undefined: 'You amplify fears and survival energy from others. Learn to distinguish your instincts from absorbed fears.'
        },
        'solar plexus': {
          governs: 'emotions, feelings, and emotional clarity',
          defined: 'You have a consistent emotional wave. Your emotions cycle through highs and lows. Wait for clarity over time.',
          undefined: 'You absorb and amplify emotions from others. You can sense how others feel more intensely than they do.'
        },
        'sacral': {
          governs: 'life force energy, sexuality, and work capacity',
          defined: 'You have consistent access to life force energy. You\'re designed to work and create sustainably.',
          undefined: 'You don\'t have consistent energy for work. Rest when needed and don\'t try to keep up with Generators.'
        },
        'root': {
          governs: 'adrenaline, pressure, and drive',
          defined: 'You have consistent pressure and drive. You operate well under deadlines.',
          undefined: 'You amplify pressure from your environment. Don\'t let external urgency rush your process.'
        }
      };
      
      const centerInfo = descriptions[centerName];
      if (!centerInfo) {
        return center.description || `The ${center.name} center governs specific aspects of your experience.`;
      }
      
      return isDefined ? centerInfo.defined : centerInfo.undefined;
    };
    
    return (
      <View style={{ gap: 12 }}>
        {centersData.centers.map((center: any, idx: number) => (
          <View key={idx} style={[styles.centerCard, { backgroundColor: theme.background, borderColor: theme.border }]}>
            <View style={styles.centerHeader}>
              <Text style={[styles.centerName, { color: theme.text }]}>{center.name || center.center_name}</Text>
              <Text style={[styles.centerStatus, { 
                color: center.defined ? '#FFD700' : theme.textTertiary 
              }]}>
                {center.defined ? 'Defined' : 'Undefined'}
              </Text>
            </View>
            <Text style={[styles.centerDescription, { color: theme.textSecondary }]}>
              {getCenterDescription(center)}
            </Text>
          </View>
        ))}
      </View>
    );
  };

  // Gates section for deep dive
  const renderGatesSection = () => {
    if (!gatesData?.gates) return null;
    
    return (
      <View style={{ gap: 12 }}>
        {gatesData.gates.slice(0, 10).map((gate: any, idx: number) => (
          <View key={idx} style={[styles.gateCard, { backgroundColor: theme.background, borderColor: theme.border }]}>
            <View style={styles.gateHeader}>
              <Text style={[styles.gateName, { color: theme.accent }]}>Gate {gate.gate}</Text>
              <Text style={[styles.gateCenter, { color: theme.textTertiary }]}>{gate.center}</Text>
            </View>
            <Text style={[styles.gateTheme, { color: theme.text }]}>{gate.name || gate.theme}</Text>
            <Text style={[styles.gateDescription, { color: theme.textSecondary }]}>
              {gate.behavioral_description || gate.description || `You naturally express Gate ${gate.gate} energy.`}
            </Text>
          </View>
        ))}
        {gatesData.gates.length > 10 && (
          <Text style={[styles.moreText, { color: theme.textTertiary }]}>
            + {gatesData.gates.length - 10} more gates
          </Text>
        )}
      </View>
    );
  };

  // Sequences section (unified narrative)
  const renderSequencesSection = () => {
    if (!activationSequence && !venusSequence && !pearlSequence) return null;
    
    return (
      <View style={[styles.structureAccordion, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <TouchableOpacity
          style={styles.structureAccordionHeader}
          onPress={() => setExpandedSection(expandedSection === 'sequences' ? null : 'sequences')}
          activeOpacity={0.7}
        >
          <Text style={[styles.structureAccordionTitle, { color: theme.text }]}>Your Life Sequences</Text>
          <Text style={[styles.structureAccordionChevron, { color: theme.textTertiary }]}>
            {expandedSection === 'sequences' ? '▲' : '▼'}
          </Text>
        </TouchableOpacity>
        {expandedSection === 'sequences' && (
          <View style={styles.structureAccordionContent}>
            <Text style={[styles.sequencesIntro, { color: theme.textSecondary }]}>
              These sequences reveal how your life patterns unfold across different domains.
            </Text>
            
            {/* Activation Sequence - Core Life Theme */}
            {activationSequence && (
              <View style={[styles.sequenceBlock, { borderLeftColor: theme.accent }]}>
                <Text style={[styles.sequenceTitle, { color: theme.text }]}>Core Life Theme</Text>
                <Text style={[styles.sequenceSubtitle, { color: theme.textTertiary }]}>What you're here to develop</Text>
                {activationSequence.purpose && (
                  <Text style={[styles.sequenceBody, { color: theme.textSecondary }]}>
                    {activationSequence.purpose.interpretation || `Gate ${activationSequence.purpose.gate} shapes your life purpose.`}
                  </Text>
                )}
              </View>
            )}
            
            {/* Venus Sequence - Relationship Pattern */}
            {venusSequence && (
              <View style={[styles.sequenceBlock, { borderLeftColor: '#FF69B4' }]}>
                <Text style={[styles.sequenceTitle, { color: theme.text }]}>Relationship Pattern</Text>
                <Text style={[styles.sequenceSubtitle, { color: theme.textTertiary }]}>Emotional patterns and dynamics</Text>
                {venusSequence.attraction && (
                  <Text style={[styles.sequenceBody, { color: theme.textSecondary }]}>
                    {venusSequence.attraction.interpretation || `Gate ${venusSequence.attraction.gate} influences how you attract and relate.`}
                  </Text>
                )}
              </View>
            )}
            
            {/* Pearl Sequence - Work & Contribution */}
            {pearlSequence && (
              <View style={[styles.sequenceBlock, { borderLeftColor: '#90EE90' }]}>
                <Text style={[styles.sequenceTitle, { color: theme.text }]}>Work & Contribution</Text>
                <Text style={[styles.sequenceSubtitle, { color: theme.textTertiary }]}>How value and prosperity flow</Text>
                {pearlSequence.vocation && (
                  <Text style={[styles.sequenceBody, { color: theme.textSecondary }]}>
                    {pearlSequence.vocation.interpretation || `Gate ${pearlSequence.vocation.gate} defines your natural vocation.`}
                  </Text>
                )}
              </View>
            )}
          </View>
        )}
      </View>
    );
  };

  const renderSection = (section: HumanDesignSection, index: number) => {
    const isExpanded = expandedSection === section.label;

    return (
      <View key={index} style={[styles.sectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => setExpandedSection(isExpanded ? null : section.label)}
          activeOpacity={0.7}
        >
          <Text style={[styles.sectionLabel, { color: theme.text }]}>{section.label}</Text>
          <Text style={{ fontSize: 16, color: theme.textTertiary }}>
            {isExpanded ? '▲' : '▼'}
          </Text>
        </TouchableOpacity>
        {isExpanded && (
          <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>{section.body}</Text>
        )}
      </View>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Forum Context Banner - shows when user came from a forum */}
      <ForumContextBanner />
      
      {renderTabs()}

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.textTertiary} />
            <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
              {activeTab === 'deep_dive' 
                ? 'Generating your personalized reading...\nThis may take 30-45 seconds'
                : 'Loading...'}
            </Text>
          </View>
        ) : error ? (
          <View style={styles.errorContainer}>
            <Text style={{ fontSize: 28, color: theme.textTertiary }}>⚠</Text>
            <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
            <TouchableOpacity
              style={[styles.retryButton, { backgroundColor: theme.surface }]}
              onPress={() => loadTabData(activeTab)}
            >
              <Text style={[styles.retryText, { color: theme.text }]}>Try Again</Text>
            </TouchableOpacity>
          </View>
        ) : data ? (
          <>
            {/* ARCHITECTURE LOCK: Keystone Reference Link at top of all tabs */}
            {/* Navigates to Home where the full Keystone card lives */}
            <KeystoneReferenceLink patternLabel={data?.keystone_explanation?.keystone_label} />
            
            {/* SUMMARY TAB - Emotional hook, fast recognition */}
            {activeTab === 'summary' && (
              <>
                {renderSummaryTab()}
                {renderUnifiedAskSection('summary')}
              </>
            )}

            {/* AT A GLANCE TAB - Structured data snapshot */}
            {activeTab === 'at_a_glance' && (
              <>
                {renderAtAGlanceTab()}
                {renderUnifiedAskSection('at_a_glance')}
              </>
            )}

            {/* DEEP DIVE TAB */}
            {activeTab === 'deep_dive' && (
              <>
                {renderDeepDiveTab()}
                {/* Global Ask CTA - page level */}
                {renderDeepDiveAskSection()}
              </>
            )}

            {/* TODAY TAB - Short-term timing / today-week-month cards */}
            {activeTab === 'today' && (
              <>
                {renderTodayTab()}
                {/* Today has per-card reflection CTAs, no global Ask block */}
              </>
            )}
            
            {/* Build Version Label */}
            <Text style={[styles.buildVersion, { color: theme.textTertiary }]}>
              v{process.env.EXPO_PUBLIC_BUILD_VERSION || 'dev'} • {process.env.EXPO_PUBLIC_BUILD_ID || 'local'}
            </Text>
          </>
        ) : null}
      </ScrollView>
      
      {/* Mechanic Detail Modal */}
      {renderMechanicDetailModal()}
      
      {/* Reflection Modal - only render when source is defined */}
      {showReflectionModal && reflectionSource && (
        <UniversalReflectionModal
          visible={showReflectionModal}
          onClose={() => {
            setShowReflectionModal(false);
            setReflectionSource(null);
            setReflectionPrompt('');
          }}
          source={reflectionSource}
          initialPrompt={reflectionPrompt}
        />
      )}
    </View>
  );
}
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "transparent",
  },
  // Unified tab section with inline description
  tabSection: {
    paddingTop: 8,
    paddingBottom: 4,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "transparent",
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: "transparent",
    alignItems: 'center',
  },
  activeTab: {
    backgroundColor: "transparent",
  },
  tabText: {
    fontSize: 13,
    fontWeight: '500',
    color: "inherit",
  },
  activeTabText: {
    color: "inherit",
  },
  // Inline tab description - tightly coupled to tabs
  tabDescriptionInline: {
    fontSize: 12,
    color: "inherit",
    textAlign: 'center',
    paddingHorizontal: 20,
    paddingBottom: 8,
  },
  // Legacy styles kept for backward compatibility
  tabDescriptionContainer: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: 'rgba(255,255,255,0.02)',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "transparent",
  },
  tabDescription: {
    fontSize: 13,
    color: "inherit",
    textAlign: 'center',
    lineHeight: 18,
    fontStyle: 'italic',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    color: "inherit",
  },
  errorContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 14,
    color: "inherit",
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    backgroundColor: "transparent",
    borderRadius: 8,
  },
  retryText: {
    fontSize: 14,
    color: "inherit",
    fontWeight: '500',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 8,
  },
  dateLabel: {
    fontSize: 12,
    color: "inherit",
    marginBottom: 20,
  },
  coreMechanicsCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
  },
  coreMechanicsTitle: {
    fontSize: 10,
    fontWeight: '600',
    color: "inherit",
    letterSpacing: 1.5,
    textAlign: 'center',
    marginBottom: 16,
  },
  mechanicsGrid: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  mechanicItem: {
    alignItems: 'center',
    paddingHorizontal: 16,
    gap: 4,
  },
  mechanicLabel: {
    fontSize: 10,
    color: "inherit",
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  mechanicValue: {
    fontSize: 14,
    fontWeight: '500',
    color: "inherit",
    textAlign: 'center',
  },
  mechanicValueSmall: {
    fontSize: 12,
    lineHeight: 16,
  },
  mechanicGates: {
    fontSize: 11,
    color: "inherit",
    textAlign: 'center',
    marginTop: 2,
  },
  mechanicDrillDown: {
    fontSize: 11,
    fontWeight: '500',
    marginTop: 6,
    textAlign: 'center',
  },
  mechanicDivider: {
    width: 1,
    height: 40,
    backgroundColor: "transparent",
  },
  expandButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    marginBottom: 16,
  },
  expandButtonText: {
    fontSize: 14,
    color: "inherit",
    fontWeight: '500',
  },
  sectionCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: "inherit",
    letterSpacing: 0.3,
    flex: 1,
  },
  sectionBody: {
    fontSize: 15,
    lineHeight: 24,
    color: "inherit",
    marginTop: 12,
  },
  sectionReflectContainer: {
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.1)',
    alignItems: 'flex-start',
  },
  mirrorPromptCard: {
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 12,
    padding: 20,
    marginTop: 8,
    marginBottom: 20,
    borderLeftWidth: 2,
    borderLeftColor: "transparent",
    opacity: 0.9,
  },
  mirrorPromptLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: "inherit",
    letterSpacing: 1.2,
    marginBottom: 8,
    opacity: 0.6,
  },
  mirrorPromptText: {
    fontSize: 15,
    lineHeight: 24,
    color: "inherit",
    fontStyle: 'italic',
  },
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    backgroundColor: "transparent",
    borderRadius: 12,
    marginBottom: 20,
  },
  askMirrorText: {
    fontSize: 15,
    color: "inherit",
    fontWeight: '500',
  },
  footer: {
    fontSize: 12,
    color: "inherit",
    textAlign: 'center',
    fontStyle: 'italic',
    opacity: 0.7,
  },
  buildVersion: {
    fontSize: 10,
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 16,
    opacity: 0.5,
  },

  // ============================================
  // OVERVIEW TAB STYLES (Reflective Summary)
  // ============================================

  // HD Identity Card
  hdIdentityCard: {
    backgroundColor: "transparent",
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
    marginBottom: 10,
  },
  hdIdentityMain: {
    alignItems: 'center',
    marginBottom: 6,
  },
  hdIdentityType: {
    fontSize: 22,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 2,
  },
  hdIdentityProfile: {
    fontSize: 14,
    color: "inherit",
  },
  hdIdentityNote: {
    fontSize: 11,
    color: "inherit",
    marginTop: 6,
    fontStyle: 'italic',
  },

  // HD Overview Cards
  hdOverviewCard: {
    backgroundColor: "transparent",
    borderRadius: 10,
    padding: 14,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
    marginBottom: 10,
  },
  hdOverviewCardTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 8,
    letterSpacing: 0.5,
  },
  hdOverviewCardSubtitle: {
    fontSize: 12,
    fontWeight: '500',
    color: "inherit",
    marginBottom: 6,
  },
  hdOverviewCardBody: {
    fontSize: 14,
    lineHeight: 21,
    color: "inherit",
  },

  // HD Core Pattern Card (New pattern compression styles)
  hdCorePatternCard: {
    backgroundColor: "transparent",
    borderRadius: 10,
    padding: 16,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 14,
  },
  hdCorePatternLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 10,
  },
  hdCorePatternText: {
    fontSize: 16,
    lineHeight: 24,
    fontWeight: '400',
    marginBottom: 10,
  },
  hdCorePatternFacet: {
    fontSize: 13,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  
  // ============================================
  // MASTER SYNTHESIS LAYER STYLES
  // ============================================
  hdMasterSynthesisContainer: {
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
  },
  hdMasterSynthesisHeader: {
    marginBottom: 20,
  },
  hdMasterSynthesisTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 4,
  },
  hdMasterSynthesisSubtitle: {
    fontSize: 13,
    lineHeight: 18,
  },
  hdSynthesisCoreCard: {
    borderLeftWidth: 3,
    paddingLeft: 14,
    marginBottom: 20,
  },
  hdSynthesisCoreText: {
    fontSize: 17,
    lineHeight: 26,
    fontWeight: '400',
  },
  hdSynthesisTensionSection: {
    marginBottom: 18,
  },
  hdSynthesisSectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 8,
  },
  hdSynthesisSectionText: {
    fontSize: 14,
    lineHeight: 21,
  },
  hdSynthesisPlayOutSection: {
    marginBottom: 18,
  },
  hdSynthesisPlayOutItem: {
    flexDirection: 'row',
    marginBottom: 8,
    paddingRight: 10,
  },
  hdSynthesisPlayOutBullet: {
    fontSize: 14,
    marginRight: 10,
    marginTop: 1,
  },
  hdSynthesisPlayOutText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },
  hdSynthesisBlindSpotSection: {
    marginBottom: 18,
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(128,128,128,0.2)',
  },
  hdSynthesisEdgeSection: {
    marginBottom: 18,
  },
  hdSynthesisSupportsSection: {
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(128,128,128,0.2)',
  },
  // ============================================
  // END MASTER SYNTHESIS STYLES
  // ============================================
  
  // Tension + Genius section
  hdTensionGeniusRow: {
    gap: 16,
  },
  hdTensionSection: {
    marginBottom: 14,
    paddingBottom: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  hdGeniusSection: {
    marginBottom: 0,
  },
  hdTensionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  hdGeniusLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  hdTensionText: {
    fontSize: 13,
    lineHeight: 19,
  },
  hdGeniusText: {
    fontSize: 13,
    lineHeight: 19,
  },

  // HD Manifestation List
  hdManifestationList: {
    gap: 10,
  },
  hdManifestationItem: {
    paddingBottom: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "transparent",
  },
  hdManifestationLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 3,
  },
  hdManifestationText: {
    fontSize: 13,
    lineHeight: 19,
    color: "inherit",
  },

  // HD Reflection Card
  hdReflectionCard: {
    backgroundColor: 'rgba(255,255,255,0.02)',
    borderRadius: 10,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 2,
    borderLeftColor: "transparent",
  },
  hdReflectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: "inherit",
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  hdReflectionText: {
    fontSize: 14,
    lineHeight: 22,
    color: "inherit",
    fontStyle: 'italic',
  },

  // HD Subtle Link
  hdSubtleLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 12,
  },
  hdSubtleLinkText: {
    fontSize: 13,
    color: "inherit",
  },

  // ============================================
  // TODAY TAB CONTAINER - Responsive layout for iPad/tablet
  // ============================================
  
  todayTabContainer: {
    width: '100%',
    maxWidth: 720,  // Tighter max-width for more editorial feel
    alignSelf: 'center',
    paddingHorizontal: 0,
  },
  todayIntroSection: {
    marginBottom: 8,  // Reduced vertical spacing
  },
  todayIntroTitle: {
    fontSize: 24,
    fontWeight: '700',
    letterSpacing: -0.5,
    marginBottom: 4,
  },
  todayIntroSubtitle: {
    fontSize: 14,
    lineHeight: 20,
    opacity: 0.6,
  },
  // Dominant Theme - The spine of the page (visually light)
  dominantThemeSection: {
    marginTop: 8,
    marginBottom: 16,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  dominantThemeLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 1.2,
    marginBottom: 4,
    textTransform: 'uppercase',
    opacity: 0.5,
  },
  dominantThemeText: {
    fontSize: 17,
    fontWeight: '600',
    lineHeight: 22,
    marginBottom: 2,
  },
  dominantThemeSupport: {
    fontSize: 13,
    lineHeight: 18,
    opacity: 0.6,
  },
  timingSectionHeader: {
    marginBottom: 12,
    marginTop: 4,
  },
  timingSectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 0,
  },
  timingSectionSubtitle: {
    fontSize: 13,
    opacity: 0.7,
    lineHeight: 18,
  },

  // ============================================
  // FIELD SECTION: The Bigger Shift
  // ============================================
  
  fieldSection: {
    marginBottom: 16,
  },
  fieldTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: "inherit",
    marginBottom: 4,
  },
  fieldSubtitle: {
    fontSize: 13,
    color: "inherit",
    opacity: 0.7,
    marginBottom: 16,
    lineHeight: 18,
  },
  fieldLoadingContainer: {
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    gap: 10,
    marginBottom: 16,
  },
  fieldLoadingText: {
    fontSize: 12,
    color: "inherit",
  },
  fieldCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
    marginBottom: 12,
    overflow: 'hidden',
  },
  // Compact field card for The Bigger Shift
  fieldCardCompact: {
    backgroundColor: "transparent",
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
    marginBottom: 8,
    padding: 10,
  },
  fieldCardTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  fieldCardBody: {
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 6,
    opacity: 0.8,
  },
  fieldCardCtaCompact: {
    alignItems: 'flex-start',
  },
  fieldCardHeadline: {
    fontSize: 17,
    fontWeight: '600',
    paddingHorizontal: 14,
    paddingTop: 14,
    paddingBottom: 8,
  },
  // Simplified field card text styles
  fieldCardWhatText: {
    fontSize: 14,
    lineHeight: 20,
    paddingHorizontal: 14,
    marginBottom: 8,
    opacity: 0.8,
  },
  fieldCardHowText: {
    fontSize: 14,
    lineHeight: 20,
    paddingHorizontal: 14,
    marginBottom: 4,
  },
  fieldCardSection: {
    paddingHorizontal: 14,
    marginBottom: 10,
  },
  fieldCardSectionLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  fieldCardSectionText: {
    fontSize: 14,
    lineHeight: 20,
  },
  fieldCardCta: {
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingVertical: 10,
    paddingHorizontal: 14,
    alignItems: 'flex-start',
    marginTop: 2,
  },
  fieldCardCtaText: {
    fontSize: 13,
    fontWeight: '500',
  },

  // ============================================
  // HERO SECTION: What's Active Now
  // ============================================
  
  heroSection: {
    marginBottom: 16,
  },
  heroTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: "inherit",
    marginBottom: 4,
  },
  heroSubtitle: {
    fontSize: 13,
    color: "inherit",
    opacity: 0.7,
    marginBottom: 16,
    lineHeight: 18,
  },
  heroLoadingContainer: {
    padding: 24,
    borderRadius: 12,
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  heroLoadingText: {
    fontSize: 13,
    color: "inherit",
  },
  
  // ============================================
  // SIGNAL CARDS (Activation / Opportunity / Friction)
  // ============================================
  
  signalCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "transparent",
    marginBottom: 12,
    overflow: 'hidden',
  },
  signalCardActivation: {
    borderWidth: 1.5,
  },
  signalCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 14,
    paddingBottom: 8,
  },
  signalCardLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  signalCardBadge: {
    fontSize: 10,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    overflow: 'hidden',
  },
  signalCardTitle: {
    fontSize: 16,
    fontWeight: '600',
    paddingHorizontal: 14,
    paddingBottom: 6,
  },
  signalCardBody: {
    fontSize: 14,
    lineHeight: 20,
    paddingHorizontal: 14,
    paddingBottom: 8,
    opacity: 0.85,
  },
  signalCardAction: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '500',
    paddingHorizontal: 14,
    paddingBottom: 12,
    paddingTop: 4,
  },
  signalCardMove: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '500',
    paddingHorizontal: 14,
    paddingBottom: 4,
  },
  signalSection: {
    marginBottom: 12,
  },
  signalSectionLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  signalSectionText: {
    fontSize: 13,
    lineHeight: 19,
  },
  signalCardCta: {
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingVertical: 10,
    paddingHorizontal: 14,
    alignItems: 'flex-start',
    marginTop: 4,
  },
  signalCardCtaText: {
    fontSize: 13,
    fontWeight: '500',
  },
  
  // ============================================
  // TODAY DIVIDER
  // ============================================
  
  todayDivider: {
    height: 1,
    marginVertical: 14,  // Tighter vertical spacing
    opacity: 0.15,
  },

  // ============================================
  // TIMING CARDS (Today / This Week / This Month)
  // ============================================
  
  timingCard: {
    backgroundColor: "transparent",
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
    marginBottom: 12,
    overflow: 'hidden',
  },
  timingCardHeader: {
    padding: 16,
    paddingBottom: 12,
  },
  timingCardTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 2,
  },
  timingCardSubtitle: {
    fontSize: 12,
    color: "inherit",
    opacity: 0.7,
  },
  timingCardContent: {
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  timingSection: {
    marginBottom: 14,
  },
  timingSectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.8,
    color: "inherit",
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  timingSectionText: {
    fontSize: 14,
    lineHeight: 20,
    color: "inherit",
  },
  timingReflectCta: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "transparent",
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'flex-start',
  },
  timingReflectCtaText: {
    fontSize: 13,
    fontWeight: '500',
    color: "inherit",
  },
  // Compact timing cards (Today/Week/Month)
  timingCardCompact: {
    backgroundColor: "transparent",
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
    marginBottom: 10,
    padding: 14,
  },
  timingCardTitleCompact: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
    textTransform: 'uppercase',
  },
  timingCardMainText: {
    fontSize: 15,
    lineHeight: 21,
    marginBottom: 8,
  },
  timingCardWatchText: {
    fontSize: 13,
    lineHeight: 18,
    opacity: 0.7,
  },
  timingReflectCtaCompact: {
    marginTop: 10,
    alignItems: 'flex-start',
  },

  // Version Debug Panel styles (non-production)
  versionDebugCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 8,
    padding: 12,
    marginTop: 16,
    borderWidth: 1,
    borderColor: '#2a2a4e',
  },
  versionDebugTitle: {
    fontSize: 10,
    fontWeight: '600',
    color: '#6a6a8a',
    letterSpacing: 1,
    marginBottom: 8,
  },
  versionDebugRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 2,
  },
  versionDebugLabel: {
    fontSize: 11,
    color: '#8a8aaa',
    fontFamily: 'monospace',
  },
  versionDebugValue: {
    fontSize: 11,
    color: '#aaaacc',
    fontFamily: 'monospace',
  },
  // ============================================
  // INCARNATION CROSS STYLES
  // ============================================
  crossContainer: {
    marginTop: 32,
    marginBottom: 24,
  },
  crossSectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  crossSectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: "inherit",
    letterSpacing: 1.5,
  },
  crossCard: {
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 12,
    padding: 20,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'rgba(255,255,255,0.06)',
  },
  crossName: {
    fontSize: 20,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 8,
    letterSpacing: 0.3,
  },
  crossFlavor: {
    fontSize: 15,
    color: "inherit",
    lineHeight: 22,
    marginBottom: 16,
    fontStyle: 'italic',
  },
  crossThemes: {
    marginBottom: 16,
    paddingLeft: 4,
  },
  crossThemeRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  crossThemeBullet: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: "transparent",
    marginTop: 7,
    marginRight: 12,
  },
  crossThemeText: {
    flex: 1,
    fontSize: 14,
    color: "inherit",
    lineHeight: 20,
  },
  crossMetadata: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.08)',
  },
  crossMetaLabel: {
    fontSize: 11,
    color: "inherit",
    marginRight: 8,
    opacity: 0.7,
  },
  crossMetaValue: {
    fontSize: 12,
    color: "inherit",
    fontFamily: 'monospace',
    letterSpacing: 0.5,
  },
  // Gene Keys styles - Editorial, spacious design
  gkContainer: {
    marginTop: 32,
    marginBottom: 24,
  },
  // New consolidated section header
  gkSectionHeaderWrapper: {
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'rgba(255,255,255,0.06)',
  },
  gkSectionHeaderTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  gkSectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  gkSectionMainTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: "inherit",
    letterSpacing: 1.5,
  },
  gkSectionIntro: {
    fontSize: 13,
    color: "inherit",
    lineHeight: 19,
    paddingRight: 8,
  },
  // Legacy styles kept for reference
  gkDivider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 16,
  },
  gkDividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.08)',
  },
  gkDividerText: {
    fontSize: 10,
    fontWeight: '600',
    color: "inherit",
    letterSpacing: 2.5,
    opacity: 0.7,
  },
  gkHelperText: {
    fontSize: 13,
    color: "inherit",
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 19,
    fontStyle: 'italic',
    paddingHorizontal: 8,
    opacity: 0.8,
  },
  gkSectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.02)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  gkSectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  gkSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: "inherit",
  },
  gkSectionSubtitle: {
    fontSize: 12,
    color: "inherit",
    marginTop: 2,
  },
  gkArcsContainer: {
    gap: 24,
  },
  // Arc Card - light, editorial feel
  gkArcCard: {
    backgroundColor: 'transparent',
    borderRadius: 0,
    overflow: 'visible',
    borderWidth: 0,
    marginBottom: 8,
  },
  gkArcHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 4,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.06)',
  },
  gkArcHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  gkArcHeaderRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  gkArcTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: "inherit",
  },
  gkArcSubtitle: {
    fontSize: 12,
    color: "inherit",
    marginTop: 2,
    maxWidth: 200,
    lineHeight: 16,
  },
  gkArcCount: {
    fontSize: 11,
    color: "inherit",
    opacity: 0.7,
  },
  gkArcContent: {
    paddingTop: 24,
    paddingHorizontal: 0,
    paddingBottom: 8,
  },
  gkArcHelper: {
    fontSize: 12,
    color: "inherit",
    fontStyle: 'italic',
    marginBottom: 24,
    lineHeight: 17,
    opacity: 0.8,
  },
  // ============================================
  // MEANING-FIRST SPHERE CARD STYLES
  // ============================================
  sphereCard: {
    backgroundColor: 'rgba(255,255,255,0.02)',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  sphereTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 2,
    letterSpacing: 0.2,
  },
  sphereGateLine: {
    fontSize: 13,
    color: "inherit",
    fontFamily: 'monospace',
    marginBottom: 10,
    opacity: 0.7,
  },
  sphereDescriptor: {
    fontSize: 13,
    color: "inherit",
    fontWeight: '500',
    marginBottom: 14,
    opacity: 0.9,
  },
  sphereInterpretation: {
    fontSize: 15,
    color: "inherit",
    lineHeight: 23,
    marginBottom: 16,
  },
  sphereMetadata: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.06)',
  },
  sphereMetaText: {
    fontSize: 11,
    color: "inherit",
    opacity: 0.6,
    letterSpacing: 0.3,
  },
  sphereMetaDot: {
    fontSize: 11,
    color: "inherit",
    opacity: 0.4,
    marginHorizontal: 8,
  },
  // Everyday language sphere item - spacious, editorial (legacy)
  gkSphereItemExpanded: {
    paddingVertical: 8,
    paddingHorizontal: 0,
    marginBottom: 28,
  },
  gkSphereTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 8,
    letterSpacing: 0.2,
  },
  gkSphereTheme: {
    fontSize: 13,
    color: "inherit",
    fontWeight: '500',
    marginBottom: 10,
    opacity: 0.9,
  },
  gkSphereDescription: {
    fontSize: 14,
    color: "inherit",
    lineHeight: 21,
    marginBottom: 0,
  },
  // Reflection prompt - separated, softer
  gkReflectionContainer: {
    marginTop: 14,
    paddingTop: 12,
  },
  gkReflectionDivider: {
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.04)',
    marginBottom: 12,
  },
  gkSpherePrompt: {
    fontSize: 13,
    color: "inherit",
    fontStyle: 'italic',
    lineHeight: 18,
    opacity: 0.75,
  },
  // Technical value - very subtle, secondary
  gkSphereTechnical: {
    fontSize: 11,
    color: "inherit",
    marginTop: 16,
    opacity: 0.5,
    letterSpacing: 0.5,
  },
  gkVersion: {
    fontSize: 10,
    color: "inherit",
    textAlign: 'center',
    marginTop: 16,
    fontFamily: 'monospace',
    opacity: 0.5,
  },
  // ============================================
  // STRUCTURE TAB STYLES
  // ============================================
  structureSubtitle: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
    fontStyle: 'italic',
  },
  structureAccordion: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
    overflow: 'hidden',
  },
  structureAccordionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  structureAccordionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  structureAccordionChevron: {
    fontSize: 12,
  },
  structureAccordionContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    paddingTop: 4,
  },
  structureAccordionText: {
    fontSize: 14,
    lineHeight: 21,
  },
  
  // Core Mechanics Grid (for Deep Dive)
  coreMechanicsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginTop: 12,
  },
  coreMechanicsItem: {
    flex: 1,
    minWidth: '45%',
  },
  coreMechanicsLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  coreMechanicsValue: {
    fontSize: 15,
    fontWeight: '500',
  },
  
  // Bodygraph Visual Card
  bodygraphCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginTop: 16,
    marginBottom: 8,
    alignItems: 'center',
  },
  bodygraphVisual: {
    alignItems: 'center',
    paddingVertical: 8,
    gap: 4,
  },
  bodygraphHead: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
  },
  bodygraphAjna: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
  },
  bodygraphThroat: {
    width: 28,
    height: 24,
    borderRadius: 4,
    borderWidth: 2,
  },
  bodygraphGCenter: {
    width: 28,
    height: 28,
    transform: [{ rotate: '45deg' }],
    borderWidth: 2,
    marginVertical: 2,
  },
  bodygraphMiddle: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 20,
  },
  bodygraphHeart: {
    width: 20,
    height: 20,
    borderRadius: 3,
    borderWidth: 2,
  },
  bodygraphSpleen: {
    width: 20,
    height: 20,
    borderRadius: 3,
    borderWidth: 2,
  },
  bodygraphSolarPlexus: {
    width: 20,
    height: 20,
    borderRadius: 3,
    borderWidth: 2,
  },
  bodygraphSacral: {
    width: 28,
    height: 24,
    borderRadius: 4,
    borderWidth: 2,
  },
  bodygraphRoot: {
    width: 28,
    height: 24,
    borderRadius: 4,
    borderWidth: 2,
  },
  bodygraphCaption: {
    fontSize: 11,
    marginTop: 12,
    fontStyle: 'italic',
  },
  // Modal styles for Mechanic Details
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  modalContent: {
    borderRadius: 16,
    maxHeight: '85%',
    overflow: 'hidden',
  },
  modalScrollView: {
    maxHeight: '100%',
  },
  modalScrollContent: {
    padding: 20,
    paddingBottom: 8,
  },
  modalHeader: {
    marginBottom: 20,
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 4,
  },
  modalSubtitle: {
    fontSize: 13,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  modalSection: {
    marginBottom: 20,
  },
  modalSectionTitle: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 10,
  },
  modalParagraph: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 10,
  },
  modalBulletRow: {
    flexDirection: 'row',
    marginBottom: 8,
    paddingRight: 8,
  },
  modalBullet: {
    fontSize: 15,
    marginRight: 8,
    marginTop: 2,
  },
  modalBulletText: {
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
  },
  modalReflectionSection: {
    padding: 14,
    borderRadius: 8,
    borderLeftWidth: 3,
    marginTop: 4,
  },
  modalReflectionText: {
    fontSize: 15,
    lineHeight: 22,
    fontStyle: 'italic',
  },
  modalCloseButton: {
    paddingVertical: 16,
    alignItems: 'center',
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  modalCloseText: {
    fontSize: 16,
    fontWeight: '600',
  },
  // Deep Dive Tab Styles
  deepDiveAccordion: {
    marginBottom: 12,
    borderRadius: 12,
    borderWidth: 1,
    overflow: 'hidden',
  },
  deepDiveHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  deepDiveHeaderText: {
    flex: 1,
  },
  deepDiveTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  deepDiveSubtitle: {
    fontSize: 13,
  },
  deepDiveChevron: {
    fontSize: 14,
    marginLeft: 12,
  },
  deepDiveContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  deepDiveParagraph: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 12,
  },
  deepDiveSectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
    marginTop: 12,
    marginBottom: 8,
  },
  deepDiveBulletRow: {
    flexDirection: 'row',
    marginBottom: 6,
    paddingRight: 8,
  },
  deepDiveBullet: {
    fontSize: 14,
    marginRight: 8,
    marginTop: 2,
  },
  deepDiveBulletText: {
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
  },
  deepDiveReflection: {
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
    marginTop: 12,
  },
  deepDiveReflectionText: {
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  
  // Mirror Card Styles (New Pattern Recognition format)
  mirrorRecognition: {
    fontSize: 16,
    lineHeight: 24,
    fontWeight: '400',
    marginBottom: 16,
  },
  mirrorSection: {
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  mirrorSectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 8,
  },
  mirrorSectionText: {
    fontSize: 14,
    lineHeight: 21,
  },
  mirrorBulletRow: {
    flexDirection: 'row',
    marginBottom: 8,
    paddingRight: 8,
  },
  mirrorBullet: {
    fontSize: 14,
    marginRight: 10,
    marginTop: 2,
  },
  mirrorBulletText: {
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
  },
  mirrorTruthShift: {
    padding: 14,
    borderRadius: 8,
    borderLeftWidth: 3,
    marginTop: 16,
  },
  mirrorTruthShiftText: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '500',
  },
  mirrorTryThis: {
    padding: 14,
    borderRadius: 8,
    borderWidth: 1,
    marginTop: 16,
  },
  mirrorTryThisText: {
    fontSize: 14,
    lineHeight: 21,
  },
  
  // Forum context: Reflect in Forum button
  reflectInForumButton: {
    marginTop: 14,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  reflectInForumText: {
    fontSize: 14,
    fontWeight: '500',
  },
  
  // Tab Blurb
  tabBlurbContainer: {
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  tabBlurbTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 4,
  },
  tabBlurbText: {
    fontSize: 14,
    lineHeight: 20,
  },
  
  // Unified Ask Section
  unifiedAskSection: {
    padding: 20,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
    marginTop: 8,
  },
  primaryAskButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    gap: 10,
  },
  primaryAskButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  primaryAskSubtext: {
    fontSize: 13,
    textAlign: 'center',
    marginTop: 12,
    marginBottom: 20,
    lineHeight: 18,
  },
  suggestedQuestionsSection: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(128, 128, 128, 0.2)',
    paddingTop: 20,
  },
  suggestedQuestionsLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  suggestedQuestionsList: {
    gap: 10,
  },
  suggestedQuestionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  suggestedQuestionText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },
  
  // Deep Dive Styles
  centerCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
  },
  centerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  centerName: {
    fontSize: 15,
    fontWeight: '600',
  },
  centerStatus: {
    fontSize: 12,
    fontWeight: '500',
  },
  centerDescription: {
    fontSize: 13,
    lineHeight: 19,
  },
  gateCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
  },
  gateHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  gateName: {
    fontSize: 14,
    fontWeight: '600',
  },
  gateCenter: {
    fontSize: 11,
    fontWeight: '500',
  },
  gateTheme: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 6,
  },
  gateDescription: {
    fontSize: 13,
    lineHeight: 19,
  },
  moreText: {
    fontSize: 13,
    textAlign: 'center',
    marginTop: 8,
  },
  sequencesIntro: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
  },
  sequenceBlock: {
    paddingLeft: 14,
    borderLeftWidth: 3,
    marginBottom: 20,
  },
  sequenceTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  sequenceSubtitle: {
    fontSize: 12,
    marginBottom: 8,
  },
  sequenceBody: {
    fontSize: 14,
    lineHeight: 21,
  },
  bodygraphHint: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 12,
    fontStyle: 'italic',
  },
  
  // Meaning Bridge
  meaningBridgeCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderLeftWidth: 4,
    marginBottom: 16,
  },
  meaningBridgeTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  meaningBridgeText: {
    fontSize: 15,
    lineHeight: 23,
  },
  
  // Improved Body Graph
  improvedBodygraphCard: {
    padding: 20,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
    alignItems: 'center',
  },
  bodygraphSubtitle: {
    fontSize: 13,
    marginTop: 4,
    marginBottom: 16,
  },
  improvedBodygraphVisual: {
    alignItems: 'center',
    paddingVertical: 10,
  },
  bgHead: {
    width: 36,
    height: 36,
    borderRadius: 18,
    marginBottom: 8,
  },
  bgAjna: {
    width: 36,
    height: 36,
    borderRadius: 18,
    marginBottom: 8,
  },
  bgThroat: {
    width: 40,
    height: 40,
    borderRadius: 8,
    marginBottom: 8,
  },
  bgG: {
    width: 44,
    height: 44,
    borderRadius: 22,
    marginBottom: 10,
  },
  bgMiddleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
    width: '100%',
    paddingHorizontal: 20,
  },
  bgMiddleSpacer: {
    width: 30,
  },
  bgHeart: {
    width: 32,
    height: 32,
    borderRadius: 6,
  },
  bgSpleen: {
    width: 32,
    height: 32,
    borderRadius: 6,
    marginHorizontal: 10,
  },
  bgSolarPlexus: {
    width: 32,
    height: 32,
    borderRadius: 6,
  },
  bgSacral: {
    width: 44,
    height: 44,
    borderRadius: 8,
    marginBottom: 8,
  },
  bgRoot: {
    width: 40,
    height: 40,
    borderRadius: 8,
  },
  bodygraphLegend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 20,
    marginTop: 16,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 1.5,
  },
  legendText: {
    fontSize: 12,
  },
  
  // Sequences Card (Always expanded)
  sequencesCard: {
    padding: 20,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  sequencesSubtitle: {
    fontSize: 13,
    marginTop: 4,
    marginBottom: 24,
  },
  
  // Sphere-based Sequence Flow
  sphereSequenceContainer: {
    marginBottom: 28,
  },
  sequenceHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  sequenceAccentDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 12,
  },
  sphereSequenceTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  sphereSequenceSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  sphereFlowContainer: {
    paddingLeft: 5,
  },
  sphereConnector: {
    width: 2,
    height: 12,
    marginLeft: 15,
    marginVertical: 2,
  },
  sequenceSphereCard: {
    paddingVertical: 12,
    paddingHorizontal: 14,
    paddingLeft: 16,
    borderLeftWidth: 3,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 8,
    marginLeft: 6,
  },
  sequenceSphereHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  sequenceSphereName: {
    fontSize: 14,
    fontWeight: '600',
  },
  sequenceSphereGeneKey: {
    fontSize: 12,
    fontWeight: '600',
  },
  sequenceSphereGiftFlow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  sequenceSphereShadow: {
    fontSize: 12,
    fontStyle: 'italic',
  },
  sequenceSphereArrow: {
    fontSize: 12,
  },
  sequenceSphereGift: {
    fontSize: 12,
    fontWeight: '500',
  },
  sequenceSphereInterpretation: {
    fontSize: 13,
    lineHeight: 19,
  },
  
  // Legacy styles (keep for compatibility)
  sequenceBlockExpanded: {
    paddingLeft: 16,
    borderLeftWidth: 4,
    marginBottom: 20,
  },
  sequenceBlockTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  sequenceBlockSubtitle: {
    fontSize: 12,
    marginBottom: 8,
  },
  sequenceBlockBody: {
    fontSize: 14,
    lineHeight: 21,
  },
  
  // NEW Deep Dive Card System - Compact & Premium
  deepDiveSectionHeader: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 8,
    marginTop: 10,
    paddingHorizontal: 4,
  },
  deepDiveCard: {
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 8,
    overflow: 'hidden',
  },
  deepDiveCardHeader: {
    padding: 10,
    paddingBottom: 4,
  },
  deepDiveCardTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 1,
  },
  deepDiveCardSubtitle: {
    fontSize: 11,
    fontWeight: '500',
  },
  deepDiveCardContent: {
    paddingHorizontal: 10,
    paddingBottom: 4,
  },
  deepDiveCardSection: {
    marginBottom: 6,
  },
  deepDiveCardSectionLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 1,
  },
  deepDiveCardSectionText: {
    fontSize: 12,
    lineHeight: 17,
  },
  deepDiveAskCta: {
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingVertical: 10,
    paddingHorizontal: 12,
    alignItems: 'flex-end',
  },
  deepDiveAskCtaText: {
    fontSize: 12,
    fontWeight: '500',
  },
  
  // Sequences Tabs - Lighter
  sequencesTabsContainer: {
    marginTop: 16,
  },
  sequencesTabBar: {
    flexDirection: 'row',
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 3,
    marginBottom: 12,
  },
  sequenceTab: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: 'center',
  },
  sequenceTabText: {
    fontSize: 12,
    fontWeight: '500',
  },
  sequencesTabContent: {
    minHeight: 150,
  },
  sequenceContent: {
    gap: 0,
  },
  sequenceDescription: {
    fontSize: 12,
    marginBottom: 12,
    fontStyle: 'italic',
  },
  sphereConnectorLine: {
    width: 1,
    height: 12,
    marginLeft: 20,
    marginVertical: 2,
    opacity: 0.5,
  },
  noDataText: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
    padding: 16,
  },
  
  // Summary Graph Styles - Premium & Calm
  summaryGraphCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 12,
  },
  summaryGraphHeader: {
    marginBottom: 12,
  },
  summaryGraphTitle: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
  },
  summaryGraphTypeBadge: {
    alignSelf: 'center',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 16,
  },
  summaryGraphTypeText: {
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
  },
  summaryGraphGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 12,
  },
  summaryGraphItem: {
    width: '50%',
    paddingVertical: 6,
    paddingHorizontal: 4,
  },
  summaryGraphItemLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  summaryGraphItemValue: {
    fontSize: 13,
    fontWeight: '500',
  },
  summaryGraphCross: {
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingTop: 10,
  },
  summaryGraphCrossLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  summaryGraphCrossValue: {
    fontSize: 13,
    fontWeight: '500',
  },
  
  // Accordion Card Styles for Core Mechanics - Compact
  accordionCard: {
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 6,
    overflow: 'hidden',
  },
  accordionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
  },
  accordionHeaderContent: {
    flex: 1,
  },
  accordionTitle: {
    fontSize: 14,
    fontWeight: '600',
  },
  accordionSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  accordionContent: {
    paddingHorizontal: 14,
    paddingBottom: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  accordionSection: {
    marginTop: 10,
  },
  accordionSectionLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 3,
  },
  accordionSectionText: {
    fontSize: 13,
    lineHeight: 18,
  },
  accordionAskCta: {
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingVertical: 10,
    marginTop: 10,
    alignItems: 'flex-end',
  },
  accordionAskCtaText: {
    fontSize: 12,
    fontWeight: '500',
  },
  
  // Parent Accordion Styles (for Centers & Gates wrapper)
  parentAccordion: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginTop: 16,
    marginBottom: 8,
    overflow: 'hidden',
  },
  parentAccordionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  parentAccordionHeaderContent: {
    flex: 1,
  },
  parentAccordionTitle: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  parentAccordionSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  parentAccordionContent: {
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingHorizontal: 12,
    paddingTop: 12,
    paddingBottom: 4,
  },
  
  // Deep Dive Global Ask Section
  deepDiveAskSection: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
    marginTop: 24,
    marginBottom: 16,
    alignItems: 'center',
  },
  deepDiveAskTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  deepDiveAskSubtext: {
    fontSize: 13,
    lineHeight: 19,
    textAlign: 'center',
    marginBottom: 16,
  },
  deepDiveAskButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    gap: 8,
  },
  deepDiveAskButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  
  // Deep Dive Mode Toggle
  deepDiveModeToggle: {
    flexDirection: 'row',
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 3,
    marginBottom: 20,
  },
  deepDiveModeButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: 'center',
  },
  deepDiveModeButtonText: {
    fontSize: 13,
    fontWeight: '500',
  },
  
  // Reading Mode Styles
  readingModeContainer: {
    paddingTop: 8,
  },
  readingSection: {
    marginBottom: 28,
  },
  readingSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
    letterSpacing: 0.3,
  },
  readingParagraph: {
    fontSize: 15,
    lineHeight: 24,
  },
  // Keystone Explanation Card styles
  keystoneExplanationCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderLeftWidth: 3,
  },
  keystoneAnchor: {
    marginBottom: 16,
  },
  keystoneEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  keystoneLabel: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 12,
  },
  keystoneSequence: {
    gap: 6,
  },
  keystoneSequenceLine: {
    fontSize: 15,
    lineHeight: 22,
  },
  keystoneDivider: {
    height: 1,
    marginVertical: 16,
  },
  keystoneExplanation: {
    gap: 8,
  },
  keystoneRoleLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  keystoneExplanationTitle: {
    fontSize: 17,
    fontWeight: '600',
    marginTop: 4,
  },
  keystoneExplanationBody: {
    fontSize: 15,
    lineHeight: 23,
    marginTop: 4,
  },
  // Pattern Thread styles
  patternThreadContainer: {
    padding: 20,
    marginBottom: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  patternThreadTitle: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginBottom: 16,
  },
  patternThreadBody: {
    fontSize: 16,
    lineHeight: 26,
    marginBottom: 16,
  },
  patternThreadLoop: {
    paddingLeft: 16,
    paddingVertical: 12,
    borderLeftWidth: 3,
    marginTop: 8,
  },
  patternThreadLoopText: {
    fontSize: 14,
    fontStyle: 'italic',
    lineHeight: 20,
  },
  // Pattern State styles - Real-time positioning
  patternStateContainer: {
    padding: 20,
    marginBottom: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  patternStateTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    marginBottom: 16,
  },
  patternStateBody: {
    fontSize: 16,
    lineHeight: 26,
    marginBottom: 16,
  },
  patternStateSub: {
    fontSize: 15,
    lineHeight: 24,
    marginBottom: 16,
  },
  patternStateShiftContainer: {
    paddingLeft: 16,
    paddingVertical: 12,
    borderLeftWidth: 3,
    marginTop: 4,
  },
  patternStateShift: {
    fontSize: 15,
    lineHeight: 23,
    fontWeight: '500',
  },
  // Cross-Link styles (subtle, italic)
  crossLinkText: {
    fontSize: 14,
    fontStyle: 'italic',
    lineHeight: 21,
    marginVertical: 8,
    paddingLeft: 4,
  },
  // Fail-safe loading fallback
  loadingFallback: {
    padding: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 100,
  },
  loadingFallbackText: {
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
  },
  // ============================================
  // SUMMARY TAB STYLES - Emotional hook
  // ============================================
  hdSummaryIdentityCard: {
    marginHorizontal: 16,
    marginTop: 16,
    marginBottom: 12,
    padding: 18,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: 'center',
  },
  hdSummaryType: {
    fontSize: 26,
    fontWeight: '700',
    marginBottom: 4,
  },
  hdSummaryProfile: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
  },
  hdSummaryNote: {
    fontSize: 12,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  hdSummaryPatternCard: {
    marginHorizontal: 16,
    marginBottom: 12,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  hdSummaryPatternLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  hdSummaryPatternText: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 12,
  },
  hdSummaryTensionSection: {
    marginTop: 4,
  },
  hdSummaryTensionLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  hdSummaryTensionText: {
    fontSize: 14,
    lineHeight: 20,
  },
  hdSummaryReflectionCard: {
    marginHorizontal: 16,
    marginBottom: 12,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  hdSummaryReflectionLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  hdSummaryReflectionText: {
    fontSize: 15,
    fontStyle: 'italic',
    lineHeight: 22,
  },
  hdSummaryLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    gap: 4,
  },
  hdSummaryLinkText: {
    fontSize: 13,
  },
  // ============================================
  // AT A GLANCE TAB STYLES - Structured data
  // ============================================
  hdGlanceCard: {
    marginHorizontal: 16,
    marginTop: 12,
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
  },
  hdGlanceTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  hdGlanceGrid: {
    gap: 6,
  },
  hdGlanceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  hdGlanceLabel: {
    fontSize: 13,
    flex: 0.4,
  },
  hdGlanceValue: {
    fontSize: 14,
    fontWeight: '500',
    flex: 0.6,
    textAlign: 'right',
  },
  hdGlanceCenterSection: {
    marginBottom: 10,
  },
  hdGlanceCenterLabel: {
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 4,
  },
  hdGlanceCenterList: {
    fontSize: 13,
    lineHeight: 18,
  },
  hdGlanceGateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4,
    gap: 10,
  },
  hdGlanceGateNumber: {
    fontSize: 12,
    fontWeight: '600',
    width: 55,
  },
  hdGlanceGateName: {
    fontSize: 13,
    flex: 1,
  },
  hdGlanceChannelSection: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  hdGlanceChannelLabel: {
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 4,
  },
  hdGlanceChannelList: {
    fontSize: 12,
    lineHeight: 17,
  },
  hdGlanceCrossName: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  hdGlanceCrossDesc: {
    fontSize: 12,
    lineHeight: 17,
  },
  hdGlanceInsight: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 4,
  },
});
