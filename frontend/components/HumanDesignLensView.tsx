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
import GeneKeysView from './GeneKeysView';
import CentersView, { CentersViewHandle } from './CentersView';
import DefinedGatesView from './DefinedGatesView';
import { ForumContextBanner } from './ForumContextBanner';
import { InlineReflectButton } from './UniversalReflectButton';

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
}

interface Props {
  userId: string;
  onOpenChat: (initialMessage?: string) => void;
}

type TabType = 'overview' | 'today' | 'deep_dive';

export default function HumanDesignLensView({ userId, onOpenChat }: Props) {
  // Theme support
  const { theme, isDark } = useTheme();
  
  // Forum context for bidirectional integration
  const { isInForumContext, forumId, forumName, setPrefilledSource } = useForumContext();
  const router = useRouter();
  
  const [activeTab, setActiveTab] = useState<TabType>('overview');
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
  
  // Debug: track raw API response length
  const [rawDataLength, setRawDataLength] = useState<number>(0);
  
  // Track mount count for debugging
  const mountCount = useRef(0);

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
      title: "What's Active Now",
      blurb: "Where to act, where to wait, and what to notice today.",
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
          style={[styles.tab, activeTab === 'overview' && styles.activeTab]}
          onPress={() => setActiveTab('overview')}
        >
          <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'overview' && { color: theme.text }]}>
            Overview
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
        <TouchableOpacity
          style={[styles.tab, activeTab === 'deep_dive' && styles.activeTab]}
          onPress={() => setActiveTab('deep_dive')}
        >
          <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'deep_dive' && { color: theme.text }]}>
            Deep Dive
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
      case 'overview':
        return "What stands out most in my Human Design?";
      case 'today':
        return "What is my design asking me to pay attention to right now?";
      case 'deep_dive':
        return "What deeper Human Design pattern matters most for me to understand?";
      default:
        return "Tell me about my Human Design.";
    }
  };

  // Suggested questions for each tab
  const getSuggestedQuestions = (tab: TabType): string[] => {
    switch (tab) {
      case 'overview':
        return [
          "How should I approach major decisions?",
          "Why do I feel drained in certain situations?",
          "What's my natural way of engaging with others?",
        ];
      case 'today':
        return [
          "What energy is most active for me today?",
          "Where should I be patient right now?",
          "What am I being asked to notice?",
        ];
      case 'deep_dive':
        return [
          "What does my profile reveal about how I learn?",
          "How do my centers work together?",
          "What patterns show up in my relationships?",
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
  // OVERVIEW TAB (Reflective Summary)
  // ============================================
  
  const renderOverviewTab = () => {
    if (!data?.core_mechanics) return null;
    
    const { type, strategy, authority, profile } = data.core_mechanics;
    const hdType = type || 'Unknown';
    const manifestations = TYPE_MANIFESTATIONS[hdType] || TYPE_MANIFESTATIONS['Generator'];
    const authorityData = AUTHORITY_TRANSLATIONS[authority || ''] || AUTHORITY_TRANSLATIONS['None'];
    
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

        {/* Your Energy Pattern Card */}
        <View style={[styles.hdOverviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>Your Energy Pattern</Text>
          <Text style={[styles.hdOverviewCardBody, { color: theme.text }]}>
            {TYPE_ENERGY_PATTERNS[hdType] || TYPE_ENERGY_PATTERNS['Generator']}
          </Text>
        </View>

        {/* How You Engage Card (Strategy) */}
        <View style={[styles.hdOverviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>How You Engage</Text>
          <Text style={[styles.hdOverviewCardBody, { color: theme.text }]}>
            {strategyTranslation}
          </Text>
        </View>

        {/* How Clarity Comes Card (Authority) */}
        <View style={[styles.hdOverviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>How Clarity Comes</Text>
          <Text style={[styles.hdOverviewCardSubtitle, { color: theme.textSecondary }]}>{authorityData.short}</Text>
          <Text style={[styles.hdOverviewCardBody, { color: theme.text }]}>
            {authorityData.expanded}
          </Text>
        </View>

        {/* Where This Helps Card */}
        <View style={[styles.hdOverviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>Where This Helps</Text>
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
          <Text style={[styles.hdReflectionLabel, { color: theme.textTertiary }]}>A REFLECTION</Text>
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

  // TODAY TAB - Type AND Authority-specific guidance
  const renderTodayTab = () => {
    if (!data) return null;
    
    const hdType = data.core_mechanics?.type || 'Generator';
    const authority = data.core_mechanics?.authority || '';
    const isEmotional = authority.toLowerCase().includes('emotional');
    
    // Get type-specific base guidance
    const typeGuidance: Record<string, { active: string; act: string; wait: string; avoid: string }> = {
      'Generator': {
        active: "Your sacral energy is looking for something to respond to. Notice what lights up your gut today.",
        act: "Respond to what genuinely excites you. Your 'yes' or 'no' lives in your body, not your mind.",
        wait: "Avoid initiating from mental ideas. Wait for something external to respond to.",
        avoid: "Don't force yourself through tasks that drain your energy. Frustration is a signal, not a failure."
      },
      'Manifesting Generator': {
        active: "Your multi-passionate energy wants to move. Notice what pulls your attention today.",
        act: "Respond first, then move quickly. Inform others before sudden pivots.",
        wait: "Wait for genuine response before committing. Speed comes after clarity.",
        avoid: "Don't feel guilty about changing direction. Efficiency sometimes looks like inconsistency."
      },
      'Projector': {
        active: "Your wisdom is sharp today. Notice where you're being genuinely invited to contribute.",
        act: "Wait for recognition and invitation. Your guidance lands when it's truly wanted.",
        wait: "Hold back unsolicited advice. Bitterness signals you're giving where you weren't asked.",
        avoid: "Don't try to match Generator energy. Rest when needed—your power is in precision, not endurance."
      },
      'Manifestor': {
        active: "Your initiating energy is ready to move. Notice the internal urges that want expression today.",
        act: "Inform others before you act. It's not asking permission—it reduces resistance and clears your path.",
        wait: "After big initiations, rest. Your energy comes in powerful bursts, not sustained flow.",
        avoid: "Don't suppress your impact to keep peace. True peace comes from informed action, not withdrawal."
      },
      'Reflector': {
        active: "You're sampling the energy around you. Notice what feels authentically yours versus absorbed.",
        act: "For major decisions, wait through a full lunar cycle. Today, observe rather than conclude.",
        wait: "Don't rush yourself. Your wisdom needs time to reveal what's truly correct.",
        avoid: "Avoid environments and people that feel off. You amplify whatever surrounds you."
      }
    };
    
    // Emotional Authority override - adds timing layer
    const emotionalOverride: Record<string, { act: string; wait: string }> = {
      'Generator': {
        act: "Respond to what excites you, then sleep on it. Emotional clarity comes in waves, not instant hits.",
        wait: "Feel your response, then wait through the emotional wave before committing."
      },
      'Manifesting Generator': {
        act: "Respond first, then wait for emotional clarity before fully committing. Speed can come after the wave settles.",
        wait: "Your gut knows, but your emotions need time. Wait for the wave to settle before big moves."
      },
      'Projector': {
        act: "When invited, don't answer immediately. Let your emotional wave settle before giving guidance.",
        wait: "Invitations don't expire. Wait for emotional clarity before deciding."
      },
      'Manifestor': {
        act: "Notice the urge to initiate, but wait for emotional clarity before acting. Impulsive action from emotional peaks or lows creates chaos.",
        wait: "Your initiating power is strongest when you're emotionally clear. Don't act from emotional highs or lows."
      },
      'Reflector': {
        act: "Your emotional wave adds another layer to your lunar process. Give yourself even more time for major decisions.",
        wait: "Notice both the lunar cycle and your emotional wave. Clarity comes when both align."
      }
    };
    
    // Build final guidance
    let guidance = typeGuidance[hdType] || typeGuidance['Generator'];
    
    // Apply emotional authority override
    if (isEmotional && emotionalOverride[hdType]) {
      guidance = {
        ...guidance,
        act: emotionalOverride[hdType].act,
        wait: emotionalOverride[hdType].wait,
      };
    }
    
    // Authority-specific timing note
    const authorityNote = isEmotional 
      ? "With Emotional Authority, clarity comes over time. Never decide from emotional peaks or lows."
      : authority.toLowerCase().includes('sacral')
      ? "With Sacral Authority, trust your gut response in the moment."
      : authority.toLowerCase().includes('splenic')
      ? "With Splenic Authority, trust the instant knowing—it won't repeat."
      : authority.toLowerCase().includes('ego')
      ? "With Ego Authority, act on what you truly want and can commit to."
      : authority.toLowerCase().includes('self')
      ? "With Self-Projected Authority, hear yourself speak to find clarity."
      : authority.toLowerCase().includes('lunar')
      ? "With Lunar Authority, wait through the full moon cycle before deciding."
      : authority.toLowerCase().includes('mental')
      ? "With Mental Authority, talk it through with trusted others—but the decision is yours."
      : "";
    
    return (
      <>
        {/* Type + Authority Context */}
        <View style={[styles.hdOverviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>YOUR DESIGN TODAY</Text>
          <Text style={[styles.hdOverviewCardSubtitle, { color: theme.accent }]}>{hdType} • {authority || 'Authority'}</Text>
          <Text style={[styles.hdOverviewCardBody, { color: theme.textSecondary, marginTop: 8 }]}>
            {authorityNote}
          </Text>
        </View>
        
        {/* What's Active */}
        <View style={[styles.hdOverviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>WHAT'S ACTIVE</Text>
          <Text style={[styles.hdOverviewCardBody, { color: theme.text }]}>
            {guidance.active}
          </Text>
        </View>
        
        {/* Where to Act */}
        <View style={[styles.hdOverviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>WHERE TO ACT</Text>
          <Text style={[styles.hdOverviewCardBody, { color: theme.text }]}>
            {guidance.act}
          </Text>
        </View>
        
        {/* Where to Wait */}
        <View style={[styles.hdOverviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>WHERE TO WAIT</Text>
          <Text style={[styles.hdOverviewCardBody, { color: theme.text }]}>
            {guidance.wait}
          </Text>
        </View>
        
        {/* What to Avoid */}
        <View style={[styles.hdOverviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.hdOverviewCardTitle, { color: theme.textTertiary }]}>WHAT TO AVOID</Text>
          <Text style={[styles.hdOverviewCardBody, { color: theme.text }]}>
            {guidance.avoid}
          </Text>
        </View>
        
        {/* Growth Edge */}
        {data.mirror_prompt && (
          <View style={[styles.hdReflectionCard, { backgroundColor: theme.surface, borderLeftColor: theme.accent }]}>
            <Text style={[styles.hdReflectionLabel, { color: theme.textTertiary }]}>TODAY'S EDGE</Text>
            <Text style={[styles.hdReflectionText, { color: theme.text }]}>
              "{data.mirror_prompt}"
            </Text>
          </View>
        )}
      </>
    );
  };

  // ============================================
  // DEEP DIVE TAB - NEW CARD-BASED STRUCTURE
  // ============================================
  
  // Universal Card Component for Deep Dive
  const renderMechanicCard = (
    title: string,
    subtitle: string | null,
    content: { story: string; showsUp: string; challenge: string; tips: string },
    askContext: string,
    accentColor?: string
  ) => {
    return (
      <View style={[styles.deepDiveCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.deepDiveCardHeader}>
          <View>
            <Text style={[styles.deepDiveCardTitle, { color: theme.text }]}>{title}</Text>
            {subtitle && (
              <Text style={[styles.deepDiveCardSubtitle, { color: accentColor || theme.accent }]}>{subtitle}</Text>
            )}
          </View>
        </View>
        
        <View style={styles.deepDiveCardContent}>
          {/* Story */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>STORY</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>{content.story}</Text>
          </View>
          
          {/* How This Shows Up */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>HOW THIS SHOWS UP</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>{content.showsUp}</Text>
          </View>
          
          {/* Challenge */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>CHALLENGE</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>{content.challenge}</Text>
          </View>
          
          {/* Practical Tips */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>PRACTICAL TIPS</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>{content.tips}</Text>
          </View>
        </View>
        
        {/* Ask CTA */}
        <TouchableOpacity
          style={[styles.deepDiveAskCta, { borderTopColor: theme.border }]}
          onPress={() => onOpenChat(`Tell me more about my ${askContext}`)}
          activeOpacity={0.7}
        >
          <Text style={[styles.deepDiveAskCtaText, { color: theme.accent }]}>Ask about this →</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // Get Type card content
  const getTypeCardContent = (type: string) => {
    const content: Record<string, { story: string; showsUp: string; challenge: string; tips: string }> = {
      'Generator': {
        story: 'You are a life force being, here to find work you love and build mastery through response.',
        showsUp: 'Strong gut responses to opportunities. Deep satisfaction when engaged in meaningful work.',
        challenge: 'Saying yes out of obligation rather than genuine excitement leads to frustration.',
        tips: 'Wait for your gut "uh-huh" before committing. Trust your body over your mind.'
      },
      'Manifesting Generator': {
        story: 'You combine sustainable energy with initiating power. Designed to respond quickly and pivot freely.',
        showsUp: 'Quick bursts of energy when excited. Natural tendency to multi-task and find shortcuts.',
        challenge: 'Forcing yourself to finish what no longer excites you. Judging your non-linear path.',
        tips: 'Respond first, then move fast. Inform others before sudden changes.'
      },
      'Projector': {
        story: 'You are a guide and seer, designed to understand systems and people more deeply than others.',
        showsUp: 'Ability to see what others miss. Natural talent for guiding and advising when invited.',
        challenge: 'Offering guidance that wasn\'t asked for leads to bitterness.',
        tips: 'Wait for recognition and invitation. Rest more than you think you need.'
      },
      'Manifestor': {
        story: 'You are an initiator, here to start things and set change in motion through action.',
        showsUp: 'Strong urges to initiate. Powerful impact that ripples outward and affects others.',
        challenge: 'Suppressing impulses to avoid conflict, or acting without informing creates resistance.',
        tips: 'Inform others before acting. This isn\'t permission—it\'s reducing friction.'
      },
      'Reflector': {
        story: 'You mirror the world around you, sampling and reflecting the health of your environment.',
        showsUp: 'Deep sensitivity to environment. Wisdom from sampling many perspectives over time.',
        challenge: 'Rushing decisions without allowing a full lunar cycle for clarity.',
        tips: 'Give major decisions 28 days. Choose environments carefully—they shape you.'
      }
    };
    return content[type] || content['Generator'];
  };

  // Get Authority card content
  const getAuthorityCardContent = (authority: string) => {
    const normalizedAuth = authority?.toLowerCase() || '';
    const content: Record<string, { story: string; showsUp: string; challenge: string; tips: string }> = {
      'emotional': {
        story: 'Your clarity comes through emotional waves. Decisions gain truth over time, not in the moment.',
        showsUp: 'Strong emotional responses. Changing feelings about the same choice over days.',
        challenge: 'Deciding at emotional peaks or valleys leads to regret.',
        tips: 'Sleep on important decisions. Revisit them over days. Wait for calm clarity.'
      },
      'sacral': {
        story: 'Your body speaks through gut responses—visceral sounds and sensations that indicate yes or no.',
        showsUp: 'Immediate gut reactions to questions. An "uh-huh" of expansion or "unh-uh" of contraction.',
        challenge: 'Ignoring gut response because of mental reasoning or social pressure.',
        tips: 'Pay attention to your first physical response. Ask yes/no questions to clarify.'
      },
      'splenic': {
        story: 'Your intuition speaks once, quietly, in the present moment. It\'s immediate knowing.',
        showsUp: 'Quick, quiet knowing in the moment. Instincts about safety and timing.',
        challenge: 'Second-guessing your immediate knowing with mental analysis.',
        tips: 'Trust your first hit. Don\'t hesitate—the splenic speaks once then moves on.'
      },
      'ego': {
        story: 'Your decisions are clear when connected to what you truly want—what your heart desires.',
        showsUp: 'Clarity when desires are genuinely felt. Strong willpower when heart is committed.',
        challenge: 'Committing to things you should want rather than things you actually want.',
        tips: 'Ask "Do I really want this? Is my heart in it?" before promising anything.'
      },
      'self-projected': {
        story: 'Your clarity comes through your voice—hearing yourself speak reveals your truth.',
        showsUp: 'Clarity that comes through speaking aloud. Recognizing truth in your own voice.',
        challenge: 'Processing silently or seeking advice instead of hearing yourself.',
        tips: 'Talk through decisions with trusted people. Listen to your own words, not their advice.'
      },
      'mental': {
        story: 'Your clarity emerges through conversation and environment over time, not internal analysis.',
        showsUp: 'Clarity through discussion in varied settings. Decisions that solidify through dialogue.',
        challenge: 'Deciding in isolation or expecting others to give you the answer.',
        tips: 'Cultivate trusted sounding boards. Discuss in different environments before deciding.'
      },
      'lunar': {
        story: 'Your clarity unfolds over a complete lunar cycle—28 days to truly know what\'s correct.',
        showsUp: 'Different feelings about decisions throughout the month. Wisdom from sampling varied energies.',
        challenge: 'Pressure to decide quickly in a world that values fast answers.',
        tips: 'Mark when decisions appear. Give them a full moon cycle before committing.'
      },
      'none': {
        story: 'Your clarity comes from your environment—where and with whom you feel most clear.',
        showsUp: 'Decisions that feel different in different places. Sensitivity to setting.',
        challenge: 'Not recognizing how much your environment affects your knowing.',
        tips: 'Make important decisions only in environments where you feel clear and grounded.'
      }
    };
    
    // Match partial authority names
    for (const [key, value] of Object.entries(content)) {
      if (normalizedAuth.includes(key)) return value;
    }
    return content['emotional'];
  };

  // Get Profile card content
  const getProfileCardContent = (profile: string) => {
    const content: Record<string, { story: string; showsUp: string; challenge: string; tips: string }> = {
      '1/3': {
        story: 'The Investigator-Martyr. You build deep foundations through research, then test them through trial.',
        showsUp: 'Deep need to understand before committing. Learning most from mistakes and experiments.',
        challenge: 'Feeling like you\'re always starting over. Judging experiments as failures.',
        tips: 'Honor both your research phase and your trial-and-error process. They work together.'
      },
      '1/4': {
        story: 'The Investigator-Opportunist. You research deeply, then share through close networks.',
        showsUp: 'Deep research before forming opinions. Influence through trusted relationships.',
        challenge: 'Trying to influence beyond your natural network. Sharing before research is complete.',
        tips: 'Build solid foundations first. Your network will carry your message when it\'s ready.'
      },
      '2/4': {
        story: 'The Hermit-Opportunist. You have natural gifts others see first, shared through your network.',
        showsUp: 'Talents that emerge when called upon. Gifts others recognize before you do.',
        challenge: 'Balancing solitude needs with social connection. Being called out too often.',
        tips: 'Honor your need for retreat. Trust that your gifts will be called when needed.'
      },
      '2/5': {
        story: 'The Hermit-Heretic. Natural gifts attract projections. Others see you as a solution.',
        showsUp: 'Being called out of retreat to help. Others expecting you to save the day.',
        challenge: 'Carrying projections you can\'t deliver on. Losing hermit time to demands.',
        tips: 'Protect your solitude fiercely. Only engage with projections you can actually meet.'
      },
      '3/5': {
        story: 'The Martyr-Heretic. You learn through trial and error, and others project expectations onto you.',
        showsUp: 'Wisdom built from what hasn\'t worked. Being seen as someone who can fix things.',
        challenge: 'Constant experimentation plus external expectations. Neither defines your worth.',
        tips: 'Your experiments are your curriculum. Choose which projections are worth meeting.'
      },
      '3/6': {
        story: 'The Martyr-Role Model. Three life phases: experiment until 30, observe until 50, then embody wisdom.',
        showsUp: 'Intense early experimentation. Eventual emergence as a living example.',
        challenge: 'Exhaustion from experimentation. Pressure to be perfect once on the roof.',
        tips: 'Trust your current phase. Don\'t rush to the next one—each builds on the last.'
      },
      '4/6': {
        story: 'The Opportunist-Role Model. Your influence moves through networks across three life phases.',
        showsUp: 'Relationships central throughout life. Authority that emerges through connection.',
        challenge: 'Maintaining relationships through the aloof roof period.',
        tips: 'Your network carries you through all phases. Nurture key relationships always.'
      },
      '4/1': {
        story: 'The Opportunist-Investigator. You share researched knowledge through trusted networks.',
        showsUp: 'Deep research shared through close relationships. Need for both intellectual and social security.',
        challenge: 'Rigidity when foundations or relationships need to shift.',
        tips: 'Build solid foundations and relationships. Both require stability to thrive.'
      },
      '5/1': {
        story: 'The Heretic-Investigator. Others project expectations; your research helps you deliver.',
        showsUp: 'Universal appeal that attracts strangers. Capacity to deliver when foundations are solid.',
        challenge: 'Carrying projections without the foundation to meet them.',
        tips: 'Research thoroughly before engaging. Only meet projections your knowledge supports.'
      },
      '5/2': {
        story: 'The Heretic-Hermit. Others project savior expectations while you need significant solitude.',
        showsUp: 'Being called out of retreat constantly. Natural talents that emerge when needed.',
        challenge: 'Being pulled from necessary solitude by unrealistic expectations.',
        tips: 'Your hermit time is non-negotiable. Engage selectively with worthy calls.'
      },
      '6/2': {
        story: 'The Role Model-Hermit. Three life phases with natural gifts that emerge when called.',
        showsUp: 'Eventual wisdom combined with innate talents. Being called out of retreat.',
        challenge: 'Balancing three-phase journey with hermit needs.',
        tips: 'Your gifts call you out when needed. Return to retreat to regenerate.'
      },
      '6/3': {
        story: 'The Role Model-Martyr. Three life phases with intense trial-and-error throughout.',
        showsUp: 'Many experiments tried. Eventual role model status earned through experience.',
        challenge: 'The sheer volume of experimentation across all phases.',
        tips: 'Every experiment contributes to eventual wisdom. Trust the process.'
      }
    };
    return content[profile] || { story: 'Your profile shapes how you learn and grow.', showsUp: 'Unique patterns in how you engage with life.', challenge: 'Resisting your natural way of being.', tips: 'Embrace how you\'re designed to operate.' };
  };

  // Get Incarnation Cross card content
  const getIncarnationCrossCardContent = (crossName: string) => {
    const angle = getCrossAngle(crossName);
    const content: Record<string, { story: string; showsUp: string; challenge: string; tips: string }> = {
      'Right Angle': {
        story: 'Your destiny is personal—focused on your own journey and growth. Your life purpose unfolds through self-discovery.',
        showsUp: 'Life lessons that are primarily internal. Growth through your own journey.',
        challenge: 'Thinking you should be more focused on others. Judging your path as selfish.',
        tips: 'Your personal curriculum is the point. Trust that your journey serves something larger.'
      },
      'Left Angle': {
        story: 'Your destiny is transpersonal—woven into the lives of others. Purpose unfolds through relationship.',
        showsUp: 'Life shaped by key relationships and meetings. Purpose through connection.',
        challenge: 'Losing yourself in others\' paths. Trying to control the transpersonal unfolding.',
        tips: 'Your encounters matter in ways you may not see yet. Trust the connections.'
      },
      'Juxtaposition': {
        story: 'Your destiny is fixed and geometric—a specific role you\'re here to play. Less flexibility, more focus.',
        showsUp: 'Life that keeps returning to the same themes. A sense of fixed purpose.',
        challenge: 'Fighting the fixedness of your path. Not recognizing your specific role.',
        tips: 'Your focused destiny is a gift, not a limitation. Lean into the specificity.'
      }
    };
    return content[angle] || content['Right Angle'];
  };

  // DEEP DIVE TAB - Card-based structure
  const renderDeepDiveTab = () => {
    if (!data) return null;
    
    return (
      <>
        {/* 1. TOP SUMMARY GRAPH - Visual design overview */}
        {renderDesignSummaryGraph()}
        
        {/* 2. BODY GRAPH */}
        {renderImprovedBodygraph()}
        
        {/* 3. CORE MECHANICS CARDS */}
        <Text style={[styles.deepDiveSectionHeader, { color: theme.textTertiary, marginTop: 24 }]}>CORE MECHANICS</Text>
        
        {/* Type Card */}
        {data.core_mechanics?.type && renderMechanicCard(
          data.core_mechanics.type,
          'Your Energy Type',
          getTypeCardContent(data.core_mechanics.type),
          'Human Design Type'
        )}
        
        {/* Authority Card */}
        {data.core_mechanics?.authority && renderMechanicCard(
          data.core_mechanics.authority,
          'Your Decision Authority',
          getAuthorityCardContent(data.core_mechanics.authority),
          'Human Design Authority'
        )}
        
        {/* Profile Card */}
        {data.core_mechanics?.profile && renderMechanicCard(
          data.core_mechanics.profile,
          'Your Profile',
          getProfileCardContent(data.core_mechanics.profile),
          'Human Design Profile'
        )}
        
        {/* Incarnation Cross Card */}
        {data.core_mechanics?.incarnation_cross && renderMechanicCard(
          data.core_mechanics.incarnation_cross,
          'Your Life Purpose',
          getIncarnationCrossCardContent(data.core_mechanics.incarnation_cross),
          'Incarnation Cross'
        )}
        
        {/* 4. CENTERS SECTION */}
        {centersData && (
          <>
            <Text style={[styles.deepDiveSectionHeader, { color: theme.textTertiary, marginTop: 24 }]}>CENTERS</Text>
            {renderCentersCards()}
          </>
        )}
        
        {/* 5. GATES SECTION */}
        {gatesData && (
          <>
            <Text style={[styles.deepDiveSectionHeader, { color: theme.textTertiary, marginTop: 24 }]}>YOUR GATES</Text>
            {renderGatesCards()}
          </>
        )}
        
        {/* 6. SEQUENCES SECTION - LAST */}
        {renderSequencesTabs()}
      </>
    );
  };
  
  // Design Summary Graph - Visual overview at top
  const renderDesignSummaryGraph = () => {
    if (!data?.core_mechanics) return null;
    
    const { type, authority, profile, definition, incarnation_cross } = data.core_mechanics;
    
    // Type colors
    const typeColors: Record<string, string> = {
      'Generator': '#FFD700',
      'Manifesting Generator': '#FF8C00',
      'Projector': '#87CEEB',
      'Manifestor': '#FF6347',
      'Reflector': '#E6E6FA'
    };
    
    const typeColor = typeColors[type || ''] || theme.accent;
    
    return (
      <View style={[styles.summaryGraphCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        {/* Header */}
        <View style={styles.summaryGraphHeader}>
          <Text style={[styles.summaryGraphTitle, { color: theme.text }]}>Your Design</Text>
        </View>
        
        {/* Main Type Badge */}
        <View style={[styles.summaryGraphTypeBadge, { backgroundColor: typeColor + '20', borderColor: typeColor }]}>
          <Text style={[styles.summaryGraphTypeText, { color: typeColor }]}>{type || 'Unknown Type'}</Text>
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

  // Sphere Card (for sequences) - follows universal card format
  const renderSphereCard = (sphere: any, accentColor: string) => {
    const getShortInterpretation = (text: string | undefined, fallback: string): string => {
      if (!text) return fallback;
      const firstSentence = text.split('.')[0] + '.';
      return firstSentence.length < 100 ? firstSentence : firstSentence.slice(0, 97) + '...';
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
              {getShortInterpretation(sphere.what_this_means, `This sphere shapes your ${sphere.sphere_name?.toLowerCase() || 'expression'}.`)}
            </Text>
          </View>
          
          {/* How This Shows Up - use gift */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>HOW THIS SHOWS UP</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {sphere.gift ? `You express ${sphere.gift} naturally—others often notice this quality in you.` : 'Unique patterns in how this energy flows through you.'}
            </Text>
          </View>
          
          {/* Challenge - use shadow */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>CHALLENGE</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {sphere.shadow ? `Under pressure, ${sphere.shadow} can emerge. This is your growth edge.` : 'Working with this energy consciously takes practice.'}
            </Text>
          </View>
          
          {/* Practical Tips */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>PRACTICAL TIPS</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {sphere.practical_tips?.[0] || (sphere.gift && sphere.shadow 
                ? `Notice when ${sphere.shadow} appears. Ask: "How can I shift toward ${sphere.gift}?"` 
                : 'Pay attention to how this energy manifests in daily life.')}
            </Text>
          </View>
        </View>
        
        {/* Ask CTA */}
        <TouchableOpacity
          style={[styles.deepDiveAskCta, { borderTopColor: theme.border }]}
          onPress={() => onOpenChat(`Tell me about my ${sphere.sphere_name} sphere (Gene Key ${sphere.gene_key})`)}
          activeOpacity={0.7}
        >
          <Text style={[styles.deepDiveAskCtaText, { color: theme.accent }]}>Ask about this →</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // Centers Cards - each center as its own card
  const renderCentersCards = () => {
    if (!centersData?.centers) return null;
    
    return (
      <View style={{ gap: 16 }}>
        {centersData.centers.map((center: any, idx: number) => renderCenterCard(center, idx))}
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
        
        {/* Ask CTA */}
        <TouchableOpacity
          style={[styles.deepDiveAskCta, { borderTopColor: theme.border }]}
          onPress={() => onOpenChat(`Tell me about my ${isDefined ? 'defined' : 'undefined'} ${centerName} center`)}
          activeOpacity={0.7}
        >
          <Text style={[styles.deepDiveAskCtaText, { color: theme.accent }]}>Ask about this →</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // Helper functions for center content
  const getShortCenterStory = (center: any): string => {
    if (center.what_this_means) {
      const text = center.what_this_means;
      const firstSentence = text.split('.')[0] + '.';
      return firstSentence.length < 100 ? firstSentence : firstSentence.slice(0, 97) + '...';
    }
    const name = center.name || center.center_name;
    return center.defined 
      ? `Your ${name} center is defined, giving you consistent access to this energy.`
      : `Your ${name} center is undefined, meaning you take in and amplify this energy from others.`;
  };

  const getShortText = (text: string | undefined): string => {
    if (!text) return '';
    const firstSentence = text.split('.')[0] + '.';
    return firstSentence.length < 100 ? firstSentence : firstSentence.slice(0, 97) + '...';
  };

  const getDefaultCenterShowsUp = (centerName: string, isDefined: boolean): string => {
    const name = centerName.toLowerCase();
    const defaults: Record<string, { defined: string; undefined: string }> = {
      'head': { defined: 'Consistent mental inspiration and questions.', undefined: 'You sample different ways of thinking from your environment.' },
      'ajna': { defined: 'Reliable way of processing and conceptualizing.', undefined: 'Mental flexibility—seeing things from many angles.' },
      'throat': { defined: 'Consistent voice and communication style.', undefined: 'Adaptable expression that matches your context.' },
      'g': { defined: 'Fixed sense of identity and direction.', undefined: 'Fluid identity shaped by where and who you\'re with.' },
      'g center': { defined: 'Fixed sense of identity and direction.', undefined: 'Fluid identity shaped by where and who you\'re with.' },
      'heart': { defined: 'Reliable willpower and ability to commit.', undefined: 'Fluctuating willpower—don\'t over-promise.' },
      'ego': { defined: 'Reliable willpower and ability to commit.', undefined: 'Fluctuating willpower—don\'t over-promise.' },
      'spleen': { defined: 'Consistent intuition and instinctual awareness.', undefined: 'Amplified fears—learn to distinguish yours from others.' },
      'solar plexus': { defined: 'Emotional wave that cycles through highs and lows.', undefined: 'Absorbing and amplifying others\' emotions intensely.' },
      'sacral': { defined: 'Sustainable life force energy for work.', undefined: 'No consistent work energy—rest is essential.' },
      'root': { defined: 'Consistent drive and ability to handle pressure.', undefined: 'Amplified pressure from environment—don\'t rush.' }
    };
    return defaults[name]?.[isDefined ? 'defined' : 'undefined'] || `This center shapes how you experience ${name} energy.`;
  };

  const getDefaultCenterChallenge = (centerName: string, isDefined: boolean): string => {
    const name = centerName.toLowerCase();
    const defaults: Record<string, { defined: string; undefined: string }> = {
      'head': { defined: 'Overthinking or mental pressure.', undefined: 'Chasing questions that aren\'t yours to answer.' },
      'ajna': { defined: 'Rigid thinking patterns.', undefined: 'Feeling pressure to have fixed opinions.' },
      'throat': { defined: 'Speaking without timing.', undefined: 'Forcing expression when you have nothing to say.' },
      'g': { defined: 'Inflexibility about identity.', undefined: 'Confusion about who you really are.' },
      'g center': { defined: 'Inflexibility about identity.', undefined: 'Confusion about who you really are.' },
      'heart': { defined: 'Over-committing willpower.', undefined: 'Making promises you can\'t sustain.' },
      'ego': { defined: 'Over-committing willpower.', undefined: 'Making promises you can\'t sustain.' },
      'spleen': { defined: 'Ignoring subtle intuitive hits.', undefined: 'Acting on borrowed fears.' },
      'solar plexus': { defined: 'Deciding during emotional highs or lows.', undefined: 'Thinking others\' emotions are your own.' },
      'sacral': { defined: 'Overwork and burnout.', undefined: 'Trying to keep up with Generators.' },
      'root': { defined: 'Addiction to pressure and stress.', undefined: 'Letting external urgency dictate your pace.' }
    };
    return defaults[name]?.[isDefined ? 'defined' : 'undefined'] || `Working with this energy consciously.`;
  };

  const getDefaultCenterTip = (centerName: string, isDefined: boolean): string => {
    const name = centerName.toLowerCase();
    const defaults: Record<string, { defined: string; undefined: string }> = {
      'head': { defined: 'Notice which questions actually serve you.', undefined: 'Ask: Would I still care about this alone?' },
      'ajna': { defined: 'Share your perspective without attachment.', undefined: 'Practice saying "I see it differently in different contexts."' },
      'throat': { defined: 'Time your communication for impact.', undefined: 'Be comfortable with silence when you have nothing genuine to say.' },
      'g': { defined: 'Trust your consistent sense of direction.', undefined: 'Let your environment show you where to go.' },
      'g center': { defined: 'Trust your consistent sense of direction.', undefined: 'Let your environment show you where to go.' },
      'heart': { defined: 'Only commit when your heart is truly in it.', undefined: 'Only promise what you can deliver without borrowed will.' },
      'ego': { defined: 'Only commit when your heart is truly in it.', undefined: 'Only promise what you can deliver without borrowed will.' },
      'spleen': { defined: 'Trust your first instinctual hit.', undefined: 'Distinguish your fears from absorbed fears.' },
      'solar plexus': { defined: 'Wait for emotional clarity before deciding.', undefined: 'Notice when you\'re absorbing someone else\'s emotion.' },
      'sacral': { defined: 'Follow your gut response to opportunities.', undefined: 'Honor your need for rest without guilt.' },
      'root': { defined: 'Use pressure productively, then release.', undefined: 'Don\'t let external urgency rush your process.' }
    };
    return defaults[name]?.[isDefined ? 'defined' : 'undefined'] || `Pay attention to how this center affects you.`;
  };

  // Gates Cards - each gate as its own card with unique content
  const renderGatesCards = () => {
    if (!gatesData?.gates) return null;
    
    return (
      <View style={{ gap: 16 }}>
        {gatesData.gates.slice(0, 12).map((gate: any, idx: number) => renderGateCard(gate, idx))}
      </View>
    );
  };

  // Individual Gate Card
  const renderGateCard = (gate: any, idx: number) => {
    const gateName = gate.name || gate.gate_name || gate.theme || `Gate ${gate.gate_number || gate.gate}`;
    const gateNum = gate.gate_number || gate.gate;
    
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
              {getShortText(gate.what_this_means) || `Gate ${gateNum} brings the energy of ${gateName.toLowerCase()} into your design.`}
            </Text>
          </View>
          
          {/* How This Shows Up */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>HOW THIS SHOWS UP</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {gate.gift ? `You naturally express ${gate.gift}—this is your authentic strength.` : (gate.your_genius ? getShortText(gate.your_genius) : `You express Gate ${gateNum} energy in your unique way.`)}
            </Text>
          </View>
          
          {/* Challenge */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>CHALLENGE</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {gate.shadow ? `Under pressure, ${gate.shadow} can surface. This is your shadow pattern.` : (gate.your_challenge ? getShortText(gate.your_challenge) : `Working with Gate ${gateNum} consciously takes practice.`)}
            </Text>
          </View>
          
          {/* Practical Tips */}
          <View style={styles.deepDiveCardSection}>
            <Text style={[styles.deepDiveCardSectionLabel, { color: theme.textTertiary }]}>PRACTICAL TIPS</Text>
            <Text style={[styles.deepDiveCardSectionText, { color: theme.textSecondary }]}>
              {gate.practical_experiments?.[0] || (gate.shadow && gate.gift 
                ? `Notice when ${gate.shadow} appears. How can you shift toward ${gate.gift}?`
                : `Pay attention to how Gate ${gateNum} manifests in your daily experience.`)}
            </Text>
          </View>
        </View>
        
        {/* Ask CTA */}
        <TouchableOpacity
          style={[styles.deepDiveAskCta, { borderTopColor: theme.border }]}
          onPress={() => onOpenChat(`Tell me about Gate ${gateNum} (${gateName}) in my design`)}
          activeOpacity={0.7}
        >
          <Text style={[styles.deepDiveAskCtaText, { color: theme.accent }]}>Ask about this →</Text>
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
            {/* Tab Blurb - Show at top of each tab */}
            {renderTabBlurb()}
            
            {/* OVERVIEW TAB */}
            {activeTab === 'overview' && (
              <>
                {renderOverviewTab()}
                {renderUnifiedAskSection('overview')}
              </>
            )}

            {/* TODAY TAB */}
            {activeTab === 'today' && (
              <>
                {renderTodayTab()}
                {renderUnifiedAskSection('today')}
              </>
            )}

            {/* DEEP DIVE TAB */}
            {activeTab === 'deep_dive' && (
              <>
                {renderDeepDiveTab()}
                {renderUnifiedAskSection('deep_dive')}
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
    fontSize: 13,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 8,
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
  
  // NEW Deep Dive Card System
  deepDiveSectionHeader: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 12,
    marginTop: 16,
    paddingHorizontal: 4,
  },
  deepDiveCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
    overflow: 'hidden',
  },
  deepDiveCardHeader: {
    padding: 16,
    paddingBottom: 8,
  },
  deepDiveCardTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 2,
  },
  deepDiveCardSubtitle: {
    fontSize: 13,
    fontWeight: '500',
  },
  deepDiveCardContent: {
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  deepDiveCardSection: {
    marginBottom: 12,
  },
  deepDiveCardSectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  deepDiveCardSectionText: {
    fontSize: 14,
    lineHeight: 20,
  },
  deepDiveAskCta: {
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'flex-end',
  },
  deepDiveAskCtaText: {
    fontSize: 13,
    fontWeight: '500',
  },
  
  // Sequences Tabs
  sequencesTabsContainer: {
    marginTop: 8,
  },
  sequencesTabBar: {
    flexDirection: 'row',
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 4,
    marginBottom: 16,
  },
  sequenceTab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  sequenceTabText: {
    fontSize: 13,
    fontWeight: '500',
  },
  sequencesTabContent: {
    minHeight: 200,
  },
  sequenceContent: {
    gap: 0,
  },
  sequenceDescription: {
    fontSize: 13,
    marginBottom: 16,
    fontStyle: 'italic',
  },
  sphereConnectorLine: {
    width: 2,
    height: 16,
    marginLeft: 24,
    marginVertical: 4,
  },
  noDataText: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
    padding: 20,
  },
  
  // Summary Graph Styles
  summaryGraphCard: {
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
    marginBottom: 16,
  },
  summaryGraphHeader: {
    marginBottom: 16,
  },
  summaryGraphTitle: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  summaryGraphTypeBadge: {
    alignSelf: 'center',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 24,
    borderWidth: 2,
    marginBottom: 20,
  },
  summaryGraphTypeText: {
    fontSize: 20,
    fontWeight: '700',
    textAlign: 'center',
  },
  summaryGraphGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 16,
  },
  summaryGraphItem: {
    width: '50%',
    paddingVertical: 8,
    paddingHorizontal: 4,
  },
  summaryGraphItemLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  summaryGraphItemValue: {
    fontSize: 14,
    fontWeight: '500',
  },
  summaryGraphCross: {
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingTop: 12,
  },
  summaryGraphCrossLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  summaryGraphCrossValue: {
    fontSize: 14,
    fontWeight: '500',
  },
});
