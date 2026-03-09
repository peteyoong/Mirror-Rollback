import React, { useState } from 'react';
import { 
  View, 
  Text, 
  ScrollView, 
  StyleSheet, 
  TouchableOpacity, 
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { Colors } from '../../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import { useAppStore } from '../../store';
import MirrorChat from '../../components/MirrorChat';
import AstrologyLensView from '../../components/AstrologyLensView';
import HumanDesignLensView from '../../components/HumanDesignLensView';
import NumerologyLensView from '../../components/NumerologyLensView';

// Lens metadata
const LENS_META: { [key: string]: { name: string; icon: string } } = {
  astrology: { name: 'True Sidereal Astrology', icon: 'planet-outline' },
  human_design: { name: 'Human Design', icon: 'body-outline' },
  numerology: { name: 'Numerology', icon: 'calculator-outline' },
  consciousness: { name: 'Consciousness', icon: 'eye-outline' },
};

// Mirror Moment content per lens and mode
const MIRROR_CONTENT: { [key: string]: { [mode: string]: { title: string; intro?: string; body: string[]; reflection: string; footer?: string } } } = {
  astrology: {
    summary: {
      title: "Today's Mirror Moment",
      body: [
        "Some days feel louder than others —",
        "not because something is wrong,",
        "but because attention is being called.",
        "",
        "What demands your presence today",
        "may hold something worth noticing."
      ],
      reflection: "Where is your attention being pulled —\nand what might it reveal?",
      footer: "Take what resonates; leave what doesn't."
    },
    deep_dive: {
      title: "Mirror Moment",
      intro: "\"Does astrology tell me what will happen — or how I meet what happens?\"",
      body: [
        "Astrology doesn't predict your life.",
        "It describes the timing and tone of experience.",
        "",
        "Your chart reflects when certain themes are louder —",
        "not what you must do with them.",
        "",
        "The same sky can be lived many ways.",
        "Awareness changes the relationship.",
        "Choice changes the outcome."
      ],
      reflection: "Where do you feel most free to respond —\nand where do you feel pulled into habit?",
      footer: "Take what resonates; leave what doesn't.\nAstrology marks cycles — not commands."
    }
  },
  human_design: {
    summary: {
      title: "Mirror Moment",
      intro: "\"If this is my design, does that mean I can't be anything else?\"",
      body: [
        "Human Design doesn't describe who you must be.",
        "It describes how energy is most available to you.",
        "",
        "Your design shows recurring patterns —",
        "how you tend to initiate, respond, feel, and process experience.",
        "",
        "But awareness changes the pattern.",
        "And practice changes how the pattern is lived.",
        "",
        "This isn't about fitting yourself into a type.",
        "It's about noticing what feels natural —",
        "and choosing how consciously you live it."
      ],
      reflection: "Where does following your design feel relieving —\nand where does it feel constraining?",
      footer: "Take what resonates; leave what doesn't."
    },
    deep_dive: {
      title: "Mirror Moment",
      body: [
        "Your design is a map of energy flow —",
        "not a limitation on who you can become.",
        "",
        "Notice where you feel resistance.",
        "Notice where you feel alignment.",
        "Both are information."
      ],
      reflection: "What patterns in your design do you recognize in your daily life?",
      footer: "Design is descriptive, not prescriptive."
    }
  },
  numerology: {
    summary: {
      title: "Mirror Moment",
      body: [
        "Numbers describe cycles and themes —",
        "the rhythm beneath the surface.",
        "",
        "Your personal year, month, and day",
        "suggest what energies are present.",
        "",
        "Not what will happen —",
        "but what wants attention."
      ],
      reflection: "What themes keep appearing in your life right now?",
      footer: "Take what resonates; leave what doesn't."
    },
    deep_dive: {
      title: "Mirror Moment",
      body: [
        "Numerology marks cycles.",
        "It doesn't create them.",
        "",
        "The numbers in your chart",
        "are one way to see patterns",
        "you're already living."
      ],
      reflection: "What cycle does it feel like you're in?",
      footer: "Numbers illuminate — they don't dictate."
    }
  },
  consciousness: {
    summary: {
      title: "Mirror Moment",
      body: [
        "Consciousness isn't something to achieve.",
        "It's something to notice.",
        "",
        "Every framework in this app",
        "is a lens for seeing yourself —",
        "not a box to fit into."
      ],
      reflection: "What are you aware of right now\nthat you weren't aware of yesterday?",
      footer: "Take what resonates; leave what doesn't."
    },
    deep_dive: {
      title: "Mirror Moment",
      body: [
        "The goal isn't to understand yourself completely.",
        "It's to stay curious about what you find."
      ],
      reflection: "Where do you feel the most like yourself?",
      footer: "Awareness is the practice."
    }
  }
};

// Personalized Mirror Moment Templates
// Theme keyed by Sun sign - "A theme you might notice"
const SUN_THEMES: { [sign: string]: string } = {
  'Aries': "A sense of urgency might be present today. You may notice a pull toward action, even before clarity arrives.",
  'Taurus': "Stability may feel like a priority right now. You might notice a desire to slow down and ground before deciding.",
  'Gemini': "Multiple ideas might be competing for attention. You may notice a restlessness that wants to explore all options.",
  'Cancer': "Emotional undercurrents might be stronger than usual. You may notice a need for safety before opening up.",
  'Leo': "A desire to be seen might be surfacing. You may notice attention moving toward what feels meaningful to express.",
  'Virgo': "Details might feel more important than usual. You may notice an urge to organize before moving forward.",
  'Libra': "Balance might be calling for attention. You may notice a pull toward harmony, even in small decisions.",
  'Scorpio': "Depth might be preferred over surface right now. You may notice an interest in what lies beneath the obvious.",
  'Sagittarius': "Expansion might feel natural today. You may notice a pull toward meaning, perspective, or new horizons.",
  'Capricorn': "Structure might feel reassuring right now. You may notice a desire to build something lasting.",
  'Aquarius': "Unconventional thinking might come easily today. You may notice ideas that don't fit familiar patterns.",
  'Pisces': "Boundaries might feel more fluid than usual. You may notice sensitivity to atmosphere and unspoken things.",
};

// Watch-for keyed by Moon sign - "What to watch for"
const MOON_WATCHFOR: { [sign: string]: string } = {
  'Aries': "Quick emotional reactions might arise. It may help to pause before responding to strong feelings.",
  'Taurus': "Comfort-seeking might show up under stress. It may help to notice what feels like genuine need versus habit.",
  'Gemini': "Emotions might shift quickly today. It may help to observe without needing to fix or explain each feeling.",
  'Cancer': "Protective instincts might be heightened. It may help to notice when walls go up and what triggered them.",
  'Leo': "Recognition might feel emotionally important. It may help to notice when approval-seeking shapes your choices.",
  'Virgo': "Self-criticism might surface more easily. It may help to notice when analysis becomes anxious rather than helpful.",
  'Libra': "People-pleasing might show up today. It may help to check if your yes is genuine or reflexive.",
  'Scorpio': "Intensity might color emotional responses. It may help to notice when depth becomes fixation.",
  'Sagittarius': "Restlessness might mask deeper feelings. It may help to slow down before seeking escape or distraction.",
  'Capricorn': "Emotional suppression might seem easier. It may help to notice what gets pushed aside for productivity.",
  'Aquarius': "Detachment might feel safer than feeling. It may help to notice when distance is protective versus avoidant.",
  'Pisces': "Absorption of others' emotions might happen. It may help to check which feelings are actually yours.",
};

// Question keyed by Rising sign - "A gentle question"
const RISING_QUESTIONS: { [sign: string]: string } = {
  'Aries': "What might happen if you let yourself pause before acting on the first impulse?",
  'Taurus': "Where might flexibility serve you better than holding your ground today?",
  'Gemini': "What would it feel like to choose depth over breadth, just for today?",
  'Cancer': "Where might you be protecting something that no longer needs defending?",
  'Leo': "What parts of yourself might be waiting for permission to be seen?",
  'Virgo': "What might you notice if you released the need for things to be perfect first?",
  'Libra': "What might your own opinion be, separate from what would please others?",
  'Scorpio': "Where might trust be possible, even if certainty isn't?",
  'Sagittarius': "What might be asking for your attention right here, rather than somewhere else?",
  'Capricorn': "What might rest look like if it didn't have to be earned first?",
  'Aquarius': "Where might connection be available if you moved closer rather than observing?",
  'Pisces': "What boundaries might help you stay present without absorbing everything around you?",
};

// Neutral fallbacks when sign data is missing
const FALLBACK_THEME = "Something might be asking for your attention today. You may notice a quiet pull toward reflection.";
const FALLBACK_WATCHFOR = "Automatic patterns might be running in the background. It may help to notice without needing to change anything yet.";
const FALLBACK_QUESTION = "What might become clearer if you simply observed without judging what you find?";

// ============================================
// Human Design Mirror Moment Templates
// ============================================

// Energy templates keyed by Type - "How your energy may show up"
const HD_ENERGY_TEMPLATES: { [type: string]: string } = {
  'Generator': "This configuration may express itself as a consistent, available energy that responds to what life presents. You might notice momentum building when something genuinely engages you.",
  'Manifesting Generator': "This configuration may express itself as a multi-directional energy that responds quickly and moves between interests. You might notice efficiency when following what feels alive.",
  'Projector': "This configuration may express itself as a focused, penetrating awareness that sees deeply into systems and others. You might notice clarity when given space to observe before engaging.",
  'Manifestor': "This configuration may express itself as an initiating energy that moves independently. You might notice flow when there's room to act without waiting for external permission.",
  'Reflector': "This configuration may express itself as a receptive, sampling awareness that reflects the environment. You might notice shifts as surroundings and company change.",
};

// Authority templates keyed by Authority - "Decision-making to notice"
// CANONICAL LABELS (from backend): Lunar | Emotional | Sacral | Splenic | Ego | Self | None
const HD_AUTHORITY_TEMPLATES: { [authority: string]: string } = {
  // Canonical labels from backend (frozen)
  'Sacral': "You might notice decisions feel clearer when there's a gut-level response — a pull toward or away from something. It could be worth noticing what generates energy versus what drains it.",
  'Emotional': "You might notice decisions feel clearer after riding an emotional wave rather than acting in the heat of the moment. It could be worth allowing time before committing.",
  'Splenic': "You might notice decisions feel clearer as quick, in-the-moment intuitions — a subtle knowing that doesn't repeat. It could be worth trusting first instincts.",
  'Ego': "You might notice decisions feel clearer when there's willpower and personal investment behind them. It could be worth asking what you genuinely want to commit to.",
  'Self': "You might notice decisions feel clearer when you hear yourself talk them through with others. It could be worth speaking your process aloud.",
  'Lunar': "You might notice decisions feel clearer after a full cycle of reflection, allowing different perspectives to arise. It could be worth giving major choices time.",
  'None': "You might notice decisions feel clearer when discussed in different environments with trusted others. It could be worth changing context before deciding.",
};

// Profile questions keyed by Profile - "A gentle question"
const HD_PROFILE_QUESTIONS: { [profile: string]: string } = {
  '1/3': "What might you discover if you gave yourself permission to investigate deeply and learn through direct experience?",
  '1/4': "What might shift if you allowed your natural need to understand things thoroughly before sharing with those close to you?",
  '2/4': "What might emerge if you trusted your natural talents to surface when called upon by those who know you?",
  '2/5': "What might change if you allowed others to see your gifts without needing to prove them first?",
  '3/5': "What might you learn if you saw each experiment — successful or not — as valuable information rather than failure?",
  '3/6': "What might become possible if you honored both your need to experiment now and your growing perspective over time?",
  '4/1': "What might deepen if you allowed your close relationships to be the foundation from which you explore new understanding?",
  '4/6': "What might unfold if you trusted your network to support the wisdom you're developing through observation?",
  '5/1': "What might happen if you focused less on meeting expectations and more on building genuine expertise?",
  '5/2': "What might arise if you allowed your natural abilities to speak for themselves rather than performing for others?",
  '6/2': "What might you notice if you gave yourself permission to observe life from a distance before engaging?",
  '6/3': "What might become clear if you trusted that your varied experiences are building toward something meaningful?",
};

// Human Design fallbacks
const HD_FALLBACK_ENERGY = "This configuration may express itself in ways that become clearer through observation over time. You might notice patterns in how your energy naturally moves.";
const HD_FALLBACK_AUTHORITY = "You might notice decisions feel clearer when you allow your natural process to unfold rather than forcing quick conclusions.";
const HD_FALLBACK_QUESTION = "What might you notice if you simply observed how you naturally move through decisions without judgment?";

export default function LensDetail() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const rawLens = params.lens as string;
  // Normalize lens param: human-design -> human_design
  const lens = rawLens?.replace(/-/g, '_');
  const [activeTab, setActiveTab] = useState<'summary' | 'snapshot' | 'deep_dive'>('deep_dive');
  const [chatInput, setChatInput] = useState('');
  const { user, chart } = useAppStore();
  
  // Lens Chat Modal state
  const [lensChatVisible, setLensChatVisible] = useState(false);
  
  const lensMeta = LENS_META[lens as string] || { name: 'Lens', icon: 'help-outline' };
  const mirrorContent = MIRROR_CONTENT[lens as string]?.[activeTab === 'snapshot' ? 'summary' : activeTab] || MIRROR_CONTENT.astrology.summary;

  // Get profile data based on lens type
  const getProfileData = () => {
    if (!chart) return null;
    
    if (lens === 'astrology') {
      const astro = chart.astrology;
      if (!astro?.planets) return null;
      
      const sun = astro.planets.Sun;
      const moon = astro.planets.Moon;
      const houses = astro.houses;
      const ascendant = houses?.formatted_cusps?.[0];
      
      return {
        title: 'YOUR SIDEREAL PROFILE',
        computed_title: 'YOUR SIDEREAL PROFILE (COMPUTED)',
        items: [
          { label: 'SUN', value: sun?.sign || '—', degree: sun?.formatted?.split(' ')[1] || '' },
          { label: 'MOON', value: moon?.sign || '—', degree: moon?.formatted?.split(' ')[1] || '' },
          { label: 'ASCENDANT', value: ascendant?.sign || '—', degree: ascendant?.formatted?.split(' ')[1] || '' },
        ],
        computed: [
          { label: 'Sun:', value: sun?.formatted || '—' },
          { label: 'Moon:', value: moon?.formatted || '—' },
          { label: 'Ascendant:', value: ascendant?.formatted || '—' },
          { label: 'System:', value: 'True Sidereal — GM Anchor' },
        ],
        source: 'computed_blueprint_v2.astrology',
        chatPlaceholder: 'Ask about your sidereal profile, or ho'
      };
    }
    
    if (lens === 'human_design') {
      const hd = chart.human_design;
      if (!hd) return null;
      
      return {
        title: 'YOUR HUMAN DESIGN PROFILE',
        items: [],
        computed: [
          { label: 'Type:', value: hd.type || '—' },
          { label: 'Strategy:', value: hd.strategy || '—' },
          { label: 'Authority:', value: hd.authority || '—' },
          { label: 'Profile:', value: hd.profile || '—' },
        ],
        chatPlaceholder: 'Ask about your Human Design, or ho'
      };
    }
    
    return null;
  };

  // Get personalized Mirror Moment content for Astrology lens
  const getPersonalizedMirrorMoment = () => {
    if (lens !== 'astrology' || !chart?.astrology) {
      return null;
    }
    
    const astro = chart.astrology;
    const sunSign = astro.planets?.Sun?.sign;
    const moonSign = astro.planets?.Moon?.sign;
    const risingSign = astro.houses?.formatted_cusps?.[0]?.sign;
    
    // Get content with fallbacks
    const theme = sunSign ? SUN_THEMES[sunSign] : FALLBACK_THEME;
    const watchFor = moonSign ? MOON_WATCHFOR[moonSign] : FALLBACK_WATCHFOR;
    // Rising falls back to Sun sign, then to neutral fallback
    const question = risingSign 
      ? RISING_QUESTIONS[risingSign] 
      : (sunSign ? RISING_QUESTIONS[sunSign] : FALLBACK_QUESTION);
    
    return {
      theme: theme || FALLBACK_THEME,
      watchFor: watchFor || FALLBACK_WATCHFOR,
      question: question || FALLBACK_QUESTION,
      sunSign,
      moonSign,
      risingSign,
    };
  };

  // Get personalized Mirror Moment content for Human Design lens
  const getHDMirrorMoment = () => {
    if (lens !== 'human_design' || !chart?.human_design) {
      return null;
    }
    
    const hd = chart.human_design;
    const hdType = hd.type;
    const authority = hd.authority;
    const profile = hd.profile;
    
    // Get content with fallbacks
    const energy = hdType ? HD_ENERGY_TEMPLATES[hdType] : HD_FALLBACK_ENERGY;
    const decisionMaking = authority ? HD_AUTHORITY_TEMPLATES[authority] : HD_FALLBACK_AUTHORITY;
    const question = profile ? HD_PROFILE_QUESTIONS[profile] : HD_FALLBACK_QUESTION;
    
    return {
      energy: energy || HD_FALLBACK_ENERGY,
      decisionMaking: decisionMaking || HD_FALLBACK_AUTHORITY,
      question: question || HD_FALLBACK_QUESTION,
      hdType,
      authority,
      profile,
    };
  };

  const profileData = getProfileData();
  const personalizedMirror = getPersonalizedMirrorMoment();
  const hdMirror = getHDMirrorMoment();

  const renderTabs = () => (
    <View style={styles.tabBar}>
      <TouchableOpacity 
        style={[styles.tab, activeTab === 'summary' && styles.tabActive]}
        onPress={() => setActiveTab('summary')}
      >
        <Text style={[styles.tabText, activeTab === 'summary' && styles.tabTextActive]}>Summary</Text>
      </TouchableOpacity>
      <TouchableOpacity 
        style={[styles.tab, activeTab === 'snapshot' && styles.tabActive]}
        onPress={() => setActiveTab('snapshot')}
      >
        <Text style={[styles.tabText, activeTab === 'snapshot' && styles.tabTextActive]}>Your Snapshot</Text>
      </TouchableOpacity>
      <TouchableOpacity 
        style={[styles.tab, activeTab === 'deep_dive' && styles.tabActive]}
        onPress={() => setActiveTab('deep_dive')}
      >
        <Text style={[styles.tabText, activeTab === 'deep_dive' && styles.tabTextActive]}>Deep Dive</Text>
      </TouchableOpacity>
    </View>
  );

  const renderMirrorMoment = () => (
    <View style={styles.mirrorCard}>
      {mirrorContent.intro && (
        <Text style={styles.mirrorIntro}>{mirrorContent.intro}</Text>
      )}
      
      <View style={styles.mirrorTitleRow}>
        <View style={styles.mirrorIcon}>
          <Ionicons name="radio-button-on-outline" size={16} color={Colors.textSecondary} />
        </View>
        <Text style={styles.mirrorTitle}>{mirrorContent.title}</Text>
      </View>
      
      <View style={styles.mirrorBody}>
        {mirrorContent.body.map((line, index) => (
          <Text key={index} style={[styles.mirrorBodyText, line === '' && { height: 12 }]}>
            {line}
          </Text>
        ))}
      </View>
      
      <View style={styles.mirrorDivider} />
      
      <Text style={styles.reflectionLabel}>REFLECTION</Text>
      <Text style={styles.reflectionText}>{mirrorContent.reflection}</Text>
      
      {mirrorContent.footer && (
        <Text style={styles.mirrorFooter}>{mirrorContent.footer}</Text>
      )}
    </View>
  );

  const renderSiderealProfile = () => {
    if (!profileData) return null;
    
    return (
      <>
        {/* Large Profile Card (for astrology) */}
        {profileData.items.length > 0 && (
          <View style={styles.profileCard}>
            <Text style={styles.profileTitle}>{profileData.title}</Text>
            <View style={styles.profileGrid}>
              {profileData.items.map((item, index) => (
                <View key={index} style={styles.profileGridItem}>
                  <Text style={styles.profileLabel}>{item.label}</Text>
                  <Text style={styles.profileValue}>{item.value}</Text>
                  {item.degree && <Text style={styles.profileDegree}>{item.degree}</Text>}
                </View>
              ))}
            </View>
          </View>
        )}
        
        {/* Computed Profile List */}
        <View style={styles.computedSection}>
          <Text style={styles.computedTitle}>{profileData.computed_title || profileData.title}</Text>
          {profileData.computed.map((item, index) => (
            <View key={index} style={styles.computedRow}>
              <Text style={styles.computedLabel}>{item.label}</Text>
              <Text style={styles.computedValue}>{item.value}</Text>
            </View>
          ))}
          {profileData.source && (
            <Text style={styles.sourceText}>Source: {profileData.source}</Text>
          )}
        </View>
      </>
    );
  };

  // Render personalized Mirror Moment card (Astrology lens only)
  const renderPersonalizedMirrorMoment = () => {
    if (!personalizedMirror) return null;
    
    return (
      <View style={styles.personalizedMirrorCard}>
        <View style={styles.personalizedMirrorHeader}>
          <Ionicons name="sparkles-outline" size={18} color={Colors.accent} />
          <Text style={styles.personalizedMirrorTitle}>Mirror Moment</Text>
        </View>
        
        {/* Theme (Sun sign) */}
        <View style={styles.mirrorBlock}>
          <Text style={styles.mirrorBlockLabel}>A theme you might notice</Text>
          <Text style={styles.mirrorBlockText}>{personalizedMirror.theme}</Text>
          {personalizedMirror.sunSign && (
            <Text style={styles.mirrorBlockSource}>Based on Sun in {personalizedMirror.sunSign}</Text>
          )}
        </View>
        
        {/* Watch for (Moon sign) */}
        <View style={styles.mirrorBlock}>
          <Text style={styles.mirrorBlockLabel}>What to watch for</Text>
          <Text style={styles.mirrorBlockText}>{personalizedMirror.watchFor}</Text>
          {personalizedMirror.moonSign && (
            <Text style={styles.mirrorBlockSource}>Based on Moon in {personalizedMirror.moonSign}</Text>
          )}
        </View>
        
        {/* Question (Rising sign) */}
        <View style={[styles.mirrorBlock, styles.mirrorBlockLast]}>
          <Text style={styles.mirrorBlockLabel}>A gentle question</Text>
          <Text style={styles.mirrorBlockQuestion}>{personalizedMirror.question}</Text>
          {(personalizedMirror.risingSign || personalizedMirror.sunSign) && (
            <Text style={styles.mirrorBlockSource}>
              Based on {personalizedMirror.risingSign ? `Rising in ${personalizedMirror.risingSign}` : `Sun in ${personalizedMirror.sunSign}`}
            </Text>
          )}
        </View>
        
        <Text style={styles.personalizedMirrorFooter}>
          Take what resonates; leave what doesn&apos;t.
        </Text>
      </View>
    );
  };

  // Render personalized Mirror Moment card (Human Design lens only)
  const renderHDMirrorMoment = () => {
    if (!hdMirror) return null;
    
    return (
      <View style={styles.personalizedMirrorCard}>
        <View style={styles.personalizedMirrorHeader}>
          <Ionicons name="sparkles-outline" size={18} color={Colors.accent} />
          <Text style={styles.personalizedMirrorTitle}>Mirror Moment</Text>
        </View>
        
        {/* Energy (Type) */}
        <View style={styles.mirrorBlock}>
          <Text style={styles.mirrorBlockLabel}>How your energy may show up</Text>
          <Text style={styles.mirrorBlockText}>{hdMirror.energy}</Text>
          {hdMirror.hdType && (
            <Text style={styles.mirrorBlockSource}>Based on {hdMirror.hdType} configuration</Text>
          )}
        </View>
        
        {/* Decision-making (Authority) */}
        <View style={styles.mirrorBlock}>
          <Text style={styles.mirrorBlockLabel}>Decision-making to notice</Text>
          <Text style={styles.mirrorBlockText}>{hdMirror.decisionMaking}</Text>
          {hdMirror.authority && (
            <Text style={styles.mirrorBlockSource}>Based on {hdMirror.authority} process</Text>
          )}
        </View>
        
        {/* Question (Profile) */}
        <View style={[styles.mirrorBlock, styles.mirrorBlockLast]}>
          <Text style={styles.mirrorBlockLabel}>A gentle question</Text>
          <Text style={styles.mirrorBlockQuestion}>{hdMirror.question}</Text>
          {hdMirror.profile && (
            <Text style={styles.mirrorBlockSource}>Based on {hdMirror.profile} profile</Text>
          )}
        </View>
        
        <Text style={styles.personalizedMirrorFooter}>
          Take what resonates; leave what doesn&apos;t.
        </Text>
      </View>
    );
  };

  const renderChatInput = () => (
    <View style={styles.chatContainer}>
      <View style={styles.chatInputWrapper}>
        <TextInput
          style={styles.chatInput}
          placeholder={profileData?.chatPlaceholder || `Ask about your ${lensMeta.name}...`}
          placeholderTextColor={Colors.textTertiary}
          value={chatInput}
          onChangeText={setChatInput}
        />
        <TouchableOpacity style={styles.chatSendButton}>
          <Ionicons name="send" size={20} color={Colors.success} />
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar style="dark" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.closeButton}>
          <Ionicons name="close" size={24} color={Colors.text} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Ionicons name={lensMeta.icon as any} size={20} color={Colors.text} />
          <Text style={styles.headerTitle}>{lensMeta.name}</Text>
        </View>
        <View style={styles.headerSpacer} />
      </View>

      {/* ASTROLOGY & HUMAN DESIGN: Use new tabbed views with API endpoints */}
      {lens === 'astrology' && user?.id ? (
        <>
          <AstrologyLensView
            userId={user.id}
            onOpenChat={() => setLensChatVisible(true)}
          />
          
          {/* Lens Chat Modal */}
          <Modal
            visible={lensChatVisible}
            animationType="slide"
            presentationStyle="pageSheet"
            onRequestClose={() => setLensChatVisible(false)}
          >
            <SafeAreaView style={styles.modalContainer} edges={['top', 'bottom']}>
              <MirrorChat
                userId={user.id}
                lens="astrology"
                placeholder="Ask about your sidereal chart…"
                headerTitle="Astrology Chat"
                headerSubtitle="Lens-focused reflection"
                onClose={() => setLensChatVisible(false)}
              />
            </SafeAreaView>
          </Modal>
        </>
      ) : lens === 'human_design' && user?.id ? (
        <>
          <HumanDesignLensView
            userId={user.id}
            onOpenChat={() => setLensChatVisible(true)}
          />
          
          {/* Lens Chat Modal */}
          <Modal
            visible={lensChatVisible}
            animationType="slide"
            presentationStyle="pageSheet"
            onRequestClose={() => setLensChatVisible(false)}
          >
            <SafeAreaView style={styles.modalContainer} edges={['top', 'bottom']}>
              <MirrorChat
                userId={user.id}
                lens="human_design"
                placeholder="Ask about your Human Design…"
                headerTitle="Human Design Chat"
                headerSubtitle="Lens-focused reflection"
                onClose={() => setLensChatVisible(false)}
              />
            </SafeAreaView>
          </Modal>
        </>
      ) : lens === 'numerology' && user?.id ? (
        <>
          <NumerologyLensView
            userId={user.id}
            onOpenChat={() => setLensChatVisible(true)}
          />
          
          {/* Lens Chat Modal */}
          <Modal
            visible={lensChatVisible}
            animationType="slide"
            presentationStyle="pageSheet"
            onRequestClose={() => setLensChatVisible(false)}
          >
            <SafeAreaView style={styles.modalContainer} edges={['top', 'bottom']}>
              <MirrorChat
                userId={user.id}
                lens="numerology"
                placeholder="Ask about your numerology…"
                headerTitle="Numerology Chat"
                headerSubtitle="Lens-focused reflection"
                onClose={() => setLensChatVisible(false)}
              />
            </SafeAreaView>
          </Modal>
        </>
      ) : (
        // OTHER LENSES: Keep original implementation
        <>
          {/* Tabs */}
          {renderTabs()}

          <KeyboardAvoidingView 
            style={styles.flex1}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          >
            <ScrollView 
              style={styles.scrollView}
              contentContainerStyle={styles.scrollContent}
              showsVerticalScrollIndicator={false}
            >
              {/* Mode Label */}
              {activeTab === 'deep_dive' && (
                <Text style={styles.modeLabel}>DEEP DIVE</Text>
              )}

              {/* Mirror Moment Card */}
              {renderMirrorMoment()}

              {/* Profile Data */}
              {renderSiderealProfile()}

              {/* Personalized Mirror Moment (Astrology only) */}
              {renderPersonalizedMirrorMoment()}

              {/* Personalized Mirror Moment (Human Design only) */}
              {renderHDMirrorMoment()}

              {/* Ask About This Lens Button (Other lenses only since astrology and human design use new views) */}
              {lens !== 'astrology' && lens !== 'human_design' && user && (
                <TouchableOpacity 
                  style={styles.askLensButton}
                  onPress={() => setLensChatVisible(true)}
                >
                  <Ionicons name="chatbubble-ellipses-outline" size={18} color={Colors.accent} />
                  <Text style={styles.askLensButtonText}>Ask about this lens</Text>
                </TouchableOpacity>
              )}
            </ScrollView>

            {/* Chat Input */}
            {renderChatInput()}
          </KeyboardAvoidingView>

          {/* Lens Chat Modal */}
          <Modal
            visible={lensChatVisible}
            animationType="slide"
            presentationStyle="pageSheet"
            onRequestClose={() => setLensChatVisible(false)}
          >
            <SafeAreaView style={styles.modalContainer} edges={['top', 'bottom']}>
              <MirrorChat
                userId={user?.id || ''}
                lens={lens as 'astrology' | 'human_design'}
                placeholder={lens === 'astrology' 
                  ? "Ask about your sidereal chart…" 
                  : "Ask about your Human Design…"}
                headerTitle={lens === 'astrology' ? 'Astrology Chat' : 'Human Design Chat'}
                headerSubtitle="Lens-focused reflection"
                onClose={() => setLensChatVisible(false)}
              />
            </SafeAreaView>
          </Modal>
        </>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  flex1: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  closeButton: {
    padding: 4,
  },
  headerCenter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.text,
  },
  headerSpacer: {
    width: 32,
  },
  tabBar: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 20,
    backgroundColor: 'transparent',
    alignItems: 'center',
  },
  tabActive: {
    backgroundColor: Colors.surface,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  tabText: {
    fontSize: 13,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  tabTextActive: {
    color: Colors.text,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 20,
  },
  modeLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textSecondary,
    letterSpacing: 1,
    marginBottom: 12,
  },
  mirrorCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  mirrorIntro: {
    fontSize: 15,
    fontStyle: 'italic',
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 22,
  },
  mirrorTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 16,
  },
  mirrorIcon: {
    opacity: 0.6,
  },
  mirrorTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
  },
  mirrorBody: {
    marginBottom: 20,
  },
  mirrorBodyText: {
    fontSize: 15,
    color: Colors.text,
    textAlign: 'center',
    lineHeight: 24,
  },
  mirrorDivider: {
    height: 1,
    backgroundColor: Colors.border,
    marginVertical: 20,
  },
  reflectionLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textSecondary,
    letterSpacing: 1.5,
    textAlign: 'center',
    marginBottom: 8,
  },
  reflectionText: {
    fontSize: 15,
    fontStyle: 'italic',
    color: Colors.text,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 16,
  },
  mirrorFooter: {
    fontSize: 13,
    color: Colors.textTertiary,
    textAlign: 'center',
    fontStyle: 'italic',
    lineHeight: 20,
  },
  profileCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  profileTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textSecondary,
    letterSpacing: 1,
    textAlign: 'center',
    marginBottom: 16,
  },
  profileGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  profileGridItem: {
    alignItems: 'center',
  },
  profileLabel: {
    fontSize: 11,
    color: Colors.textTertiary,
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  profileValue: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 2,
  },
  profileDegree: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
  computedSection: {
    paddingHorizontal: 4,
    marginBottom: 16,
  },
  computedTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.text,
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  computedRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  computedLabel: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  computedValue: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  sourceText: {
    fontSize: 12,
    color: Colors.success,
    marginTop: 8,
  },
  chatContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    backgroundColor: Colors.background,
  },
  chatInputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  chatInput: {
    flex: 1,
    fontSize: 15,
    color: Colors.text,
    paddingVertical: 10,
  },
  chatSendButton: {
    padding: 8,
    marginLeft: 8,
  },
  // Personalized Mirror Moment styles
  personalizedMirrorCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 20,
    marginTop: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  personalizedMirrorHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 8,
  },
  personalizedMirrorTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    letterSpacing: 0.3,
  },
  mirrorBlock: {
    marginBottom: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  mirrorBlockLast: {
    borderBottomWidth: 0,
    marginBottom: 12,
    paddingBottom: 0,
  },
  mirrorBlockLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.accent,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  mirrorBlockText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.text,
  },
  mirrorBlockQuestion: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.text,
    fontStyle: 'italic',
  },
  mirrorBlockSource: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 8,
    fontStyle: 'italic',
  },
  personalizedMirrorFooter: {
    fontSize: 12,
    color: Colors.textSecondary,
    textAlign: 'center',
    fontStyle: 'italic',
    marginTop: 8,
  },
  // Ask about this lens button
  askLensButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.accent + '12',
    borderRadius: 12,
    paddingVertical: 14,
    marginTop: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: Colors.accent + '30',
  },
  askLensButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.accent,
  },
  // Modal container
  modalContainer: {
    flex: 1,
    backgroundColor: Colors.background,
  },
});
