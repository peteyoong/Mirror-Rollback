import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  ScrollView, 
  StyleSheet, 
  TouchableOpacity, 
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform 
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Colors } from '../../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import { useAppStore } from '../../store';

// Lens metadata
const LENS_META: { [key: string]: { name: string; icon: string } } = {
  astrology: { name: 'True Sidereal Astrology', icon: 'planet-outline' },
  human_design: { name: 'Human Design', icon: 'body-outline' },
  numerology: { name: 'Numerology', icon: 'calculator-outline' },
  consciousness: { name: 'Consciousness', icon: 'eye-outline' },
};

// ============================================================================
// MIRROR MOMENT CONTENT - All lenses, all modes
// ============================================================================
const MIRROR_CONTENT: { [lens: string]: { [mode: string]: any } } = {
  // -------------------------------------------------------------------------
  // ASTROLOGY
  // -------------------------------------------------------------------------
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
    snapshot: {
      title: "Your Snapshot",
      intro: "A quick look at your sidereal positions.",
      body: [
        "Your chart is a snapshot of the sky",
        "at the moment you were born.",
        "",
        "It doesn't define you —",
        "it describes the energetic context",
        "you entered this world with."
      ],
      reflection: "What part of your chart feels most familiar?",
      footer: "The sky doesn't command — it reflects."
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
  // -------------------------------------------------------------------------
  // HUMAN DESIGN
  // -------------------------------------------------------------------------
  human_design: {
    summary: {
      title: "Today's Mirror Moment",
      body: [
        "Your design is always present —",
        "even when you're not thinking about it.",
        "",
        "Today might reveal patterns",
        "you've been living unconsciously.",
        "",
        "Notice what flows.",
        "Notice what resists."
      ],
      reflection: "Where does your energy want to go today?",
      footer: "Take what resonates; leave what doesn't."
    },
    snapshot: {
      title: "Your Snapshot",
      intro: "A quick look at your Human Design profile.",
      body: [
        "Human Design combines astrology,",
        "the I Ching, Kabbalah, and chakra system",
        "into a map of your energetic makeup.",
        "",
        "Your Type, Strategy, and Authority",
        "describe how you're designed to move through the world."
      ],
      reflection: "Does your Strategy feel natural or foreign?",
      footer: "Design is descriptive, not prescriptive."
    },
    deep_dive: {
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
    }
  },
  // -------------------------------------------------------------------------
  // NUMEROLOGY
  // -------------------------------------------------------------------------
  numerology: {
    summary: {
      title: "Today's Mirror Moment",
      body: [
        "Numbers mark time differently.",
        "They describe cycles within cycles —",
        "years within lifetimes,",
        "days within years.",
        "",
        "What cycle are you in?",
        "What does it ask of you?"
      ],
      reflection: "What theme keeps appearing this year?",
      footer: "Take what resonates; leave what doesn't."
    },
    snapshot: {
      title: "Your Snapshot",
      intro: "A quick look at your numerological cycles.",
      body: [
        "Your Life Path number describes",
        "the overarching theme of your journey.",
        "",
        "Your Personal Year, Month, and Day",
        "describe what energies are present now.",
        "",
        "These aren't predictions —",
        "they're descriptions of timing."
      ],
      reflection: "What number keeps appearing in your life?",
      footer: "Numbers illuminate — they don't dictate."
    },
    deep_dive: {
      title: "Mirror Moment",
      intro: "\"Do numbers actually mean something, or is this just pattern-matching?\"",
      body: [
        "Numerology is one of many ways",
        "humans have tried to find meaning in cycles.",
        "",
        "Whether the meaning is inherent",
        "or constructed through attention",
        "may not matter.",
        "",
        "What matters is whether noticing",
        "these patterns helps you live more consciously.",
        "",
        "If it does, use it.",
        "If it doesn't, let it go."
      ],
      reflection: "What patterns do you notice\nwhen you pay attention to numbers?",
      footer: "Take what resonates; leave what doesn't."
    }
  },
  // -------------------------------------------------------------------------
  // CONSCIOUSNESS
  // -------------------------------------------------------------------------
  consciousness: {
    summary: {
      title: "Today's Mirror Moment",
      body: [
        "Consciousness isn't something to achieve.",
        "It's something to notice.",
        "",
        "Right now, you're aware.",
        "That's already enough."
      ],
      reflection: "What are you aware of right now?",
      footer: "Take what resonates; leave what doesn't."
    },
    snapshot: {
      title: "Your Snapshot",
      intro: "A reflection on awareness itself.",
      body: [
        "Every framework in this app —",
        "astrology, Human Design, numerology —",
        "is a lens for seeing yourself.",
        "",
        "None of them are the truth.",
        "All of them can point toward it."
      ],
      reflection: "Which lens helps you see most clearly?",
      footer: "The map is not the territory."
    },
    deep_dive: {
      title: "Mirror Moment",
      intro: "\"What's the point of all these frameworks?\"",
      body: [
        "The goal isn't to understand yourself completely.",
        "That's not possible.",
        "",
        "The goal is to stay curious",
        "about what you find.",
        "",
        "These frameworks are tools —",
        "not cages, not commandments.",
        "",
        "Use what helps.",
        "Release what doesn't.",
        "Stay open to what's next."
      ],
      reflection: "Where do you feel the most like yourself?",
      footer: "Awareness is the practice."
    }
  }
};

export default function LensDetail() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const { lens } = params;
  const [activeTab, setActiveTab] = useState<'summary' | 'snapshot' | 'deep_dive'>('summary');
  const [chatInput, setChatInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const { user, chart } = useAppStore();
  
  const lensMeta = LENS_META[lens as string] || { name: 'Lens', icon: 'help-outline' };
  const mirrorContent = MIRROR_CONTENT[lens as string]?.[activeTab] || MIRROR_CONTENT.astrology.summary;

  // =========================================================================
  // PROFILE DATA EXTRACTION
  // =========================================================================
  const getAstrologyProfile = () => {
    if (!chart?.astrology?.planets) return null;
    
    const planets = chart.astrology.planets;
    const houses = chart.astrology.houses;
    
    const sun = planets.Sun;
    const moon = planets.Moon;
    const ascendant = houses?.formatted_cusps?.[0];
    
    return {
      sun: {
        sign: sun?.sign || '—',
        degree: sun?.formatted?.split(' ').slice(1).join(' ') || '',
        formatted: sun?.formatted || '—'
      },
      moon: {
        sign: moon?.sign || '—',
        degree: moon?.formatted?.split(' ').slice(1).join(' ') || '',
        formatted: moon?.formatted || '—'
      },
      ascendant: {
        sign: ascendant?.sign || '—',
        degree: ascendant?.formatted?.split(' ').slice(1).join(' ') || '',
        formatted: ascendant?.formatted || '—'
      },
      system: 'True Sidereal — GM Anchor'
    };
  };

  const getHumanDesignProfile = () => {
    if (!chart?.human_design) return null;
    
    const hd = chart.human_design;
    return {
      type: hd.type || '—',
      strategy: hd.strategy || '—',
      authority: hd.authority || '—',
      profile: hd.profile || '—',
      definition: hd.definition || '—',
      incarnation_cross: hd.incarnation_cross || '—'
    };
  };

  const getNumerologyProfile = () => {
    if (!chart?.numerology) return null;
    
    const num = chart.numerology;
    return {
      life_path: num.life_path?.number || '—',
      life_path_name: num.life_path?.name || '',
      expression: num.expression?.number || '—',
      personal_year: num.personal_year || '—',
      personal_month: num.personal_month || '—',
      personal_day: num.personal_day || '—'
    };
  };

  const astrologyProfile = getAstrologyProfile();
  const humanDesignProfile = getHumanDesignProfile();
  const numerologyProfile = getNumerologyProfile();

  // =========================================================================
  // RENDER FUNCTIONS
  // =========================================================================
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
        {mirrorContent.body.map((line: string, index: number) => (
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

  // Astrology Profile Cards
  const renderAstrologyProfile = () => {
    if (!astrologyProfile) {
      return (
        <View style={styles.emptyProfileCard}>
          <Text style={styles.emptyProfileText}>Complete onboarding to see your sidereal profile</Text>
        </View>
      );
    }

    return (
      <>
        {/* Large Profile Card */}
        <View style={styles.profileCard}>
          <Text style={styles.profileCardTitle}>YOUR SIDEREAL PROFILE</Text>
          <View style={styles.profileGrid}>
            <View style={styles.profileGridItem}>
              <Text style={styles.profileLabel}>SUN</Text>
              <Text style={styles.profileValue}>{astrologyProfile.sun.sign}</Text>
              <Text style={styles.profileDegree}>{astrologyProfile.sun.degree}</Text>
            </View>
            <View style={styles.profileGridItem}>
              <Text style={styles.profileLabel}>MOON</Text>
              <Text style={styles.profileValue}>{astrologyProfile.moon.sign}</Text>
              <Text style={styles.profileDegree}>{astrologyProfile.moon.degree}</Text>
            </View>
            <View style={styles.profileGridItem}>
              <Text style={styles.profileLabel}>ASCENDANT</Text>
              <Text style={styles.profileValue}>{astrologyProfile.ascendant.sign}</Text>
              <Text style={styles.profileDegree}>{astrologyProfile.ascendant.degree}</Text>
            </View>
          </View>
        </View>

        {/* Computed Details */}
        <View style={styles.computedSection}>
          <Text style={styles.computedTitle}>YOUR SIDEREAL PROFILE (COMPUTED)</Text>
          <View style={styles.computedRow}>
            <Text style={styles.computedLabel}>Sun:</Text>
            <Text style={styles.computedValue}>{astrologyProfile.sun.formatted}</Text>
          </View>
          <View style={styles.computedRow}>
            <Text style={styles.computedLabel}>Moon:</Text>
            <Text style={styles.computedValue}>{astrologyProfile.moon.formatted}</Text>
          </View>
          <View style={styles.computedRow}>
            <Text style={styles.computedLabel}>Ascendant:</Text>
            <Text style={styles.computedValue}>{astrologyProfile.ascendant.formatted}</Text>
          </View>
          <View style={styles.computedRow}>
            <Text style={styles.computedLabel}>System:</Text>
            <Text style={styles.computedValue}>{astrologyProfile.system}</Text>
          </View>
          <Text style={styles.sourceText}>Source: computed_blueprint_v2.astrology</Text>
        </View>
      </>
    );
  };

  // Human Design Profile Cards
  const renderHumanDesignProfile = () => {
    if (!humanDesignProfile) {
      return (
        <View style={styles.emptyProfileCard}>
          <Text style={styles.emptyProfileText}>Complete onboarding to see your Human Design profile</Text>
        </View>
      );
    }

    return (
      <>
        {/* Profile Card */}
        <View style={styles.profileCard}>
          <Text style={styles.profileCardTitle}>YOUR HUMAN DESIGN PROFILE</Text>
          <View style={styles.hdProfileGrid}>
            <View style={styles.hdProfileItem}>
              <Text style={styles.profileLabel}>TYPE</Text>
              <Text style={styles.hdProfileValue}>{humanDesignProfile.type}</Text>
            </View>
            <View style={styles.hdProfileItem}>
              <Text style={styles.profileLabel}>STRATEGY</Text>
              <Text style={styles.hdProfileValue}>{humanDesignProfile.strategy}</Text>
            </View>
            <View style={styles.hdProfileItem}>
              <Text style={styles.profileLabel}>AUTHORITY</Text>
              <Text style={styles.hdProfileValue}>{humanDesignProfile.authority}</Text>
            </View>
            <View style={styles.hdProfileItem}>
              <Text style={styles.profileLabel}>PROFILE</Text>
              <Text style={styles.hdProfileValue}>{humanDesignProfile.profile}</Text>
            </View>
          </View>
        </View>

        {/* Computed Details */}
        <View style={styles.computedSection}>
          <Text style={styles.computedTitle}>YOUR HUMAN DESIGN (COMPUTED)</Text>
          <View style={styles.computedRow}>
            <Text style={styles.computedLabel}>Type:</Text>
            <Text style={styles.computedValue}>{humanDesignProfile.type}</Text>
          </View>
          <View style={styles.computedRow}>
            <Text style={styles.computedLabel}>Strategy:</Text>
            <Text style={styles.computedValue}>{humanDesignProfile.strategy}</Text>
          </View>
          <View style={styles.computedRow}>
            <Text style={styles.computedLabel}>Authority:</Text>
            <Text style={styles.computedValue}>{humanDesignProfile.authority}</Text>
          </View>
          <View style={styles.computedRow}>
            <Text style={styles.computedLabel}>Profile:</Text>
            <Text style={styles.computedValue}>{humanDesignProfile.profile}</Text>
          </View>
          <View style={styles.computedRow}>
            <Text style={styles.computedLabel}>Definition:</Text>
            <Text style={styles.computedValue}>{humanDesignProfile.definition}</Text>
          </View>
          <Text style={styles.sourceText}>Source: computed_blueprint_v2.human_design</Text>
        </View>
      </>
    );
  };

  // Numerology Profile Cards
  const renderNumerologyProfile = () => {
    if (!numerologyProfile) {
      return (
        <View style={styles.emptyProfileCard}>
          <Text style={styles.emptyProfileText}>Complete onboarding to see your numerology profile</Text>
        </View>
      );
    }

    return (
      <>
        {/* Cycles Card */}
        <View style={styles.profileCard}>
          <Text style={styles.profileCardTitle}>TODAY'S CYCLES</Text>
          <View style={styles.cyclesGrid}>
            <View style={styles.cycleItem}>
              <Text style={styles.cycleNumber}>{numerologyProfile.personal_year}</Text>
              <Text style={styles.cycleLabel}>Personal Year</Text>
            </View>
            <View style={styles.cycleItem}>
              <Text style={styles.cycleNumber}>{numerologyProfile.personal_month}</Text>
              <Text style={styles.cycleLabel}>Personal Month</Text>
            </View>
            <View style={styles.cycleItem}>
              <Text style={styles.cycleNumber}>{numerologyProfile.personal_day}</Text>
              <Text style={styles.cycleLabel}>Personal Day</Text>
            </View>
          </View>
        </View>

        {/* Life Path */}
        <View style={styles.computedSection}>
          <Text style={styles.computedTitle}>YOUR NUMEROLOGY (COMPUTED)</Text>
          <View style={styles.computedRow}>
            <Text style={styles.computedLabel}>Life Path:</Text>
            <Text style={styles.computedValue}>{numerologyProfile.life_path} {numerologyProfile.life_path_name && `(${numerologyProfile.life_path_name})`}</Text>
          </View>
          <View style={styles.computedRow}>
            <Text style={styles.computedLabel}>Expression:</Text>
            <Text style={styles.computedValue}>{numerologyProfile.expression}</Text>
          </View>
          <Text style={styles.sourceText}>Source: computed_blueprint_v2.numerology</Text>
        </View>
      </>
    );
  };

  // Consciousness Profile
  const renderConsciousnessProfile = () => (
    <View style={styles.computedSection}>
      <Text style={styles.computedTitle}>AWARENESS PRACTICE</Text>
      <Text style={styles.consciousnessText}>
        Consciousness isn't computed — it's practiced.
        {'\n\n'}
        Use the frameworks in this app as mirrors,
        not as definitions of who you are.
        {'\n\n'}
        The goal is presence, not perfection.
      </Text>
    </View>
  );

  // Select which profile to render based on lens
  const renderProfile = () => {
    switch (lens) {
      case 'astrology':
        return renderAstrologyProfile();
      case 'human_design':
        return renderHumanDesignProfile();
      case 'numerology':
        return renderNumerologyProfile();
      case 'consciousness':
        return renderConsciousnessProfile();
      default:
        return null;
    }
  };

  // Chat placeholder text per lens
  const getChatPlaceholder = () => {
    switch (lens) {
      case 'astrology':
        return 'Ask about your sidereal profile...';
      case 'human_design':
        return 'Ask about your Human Design...';
      case 'numerology':
        return 'Ask about your cycles...';
      case 'consciousness':
        return 'Ask a question...';
      default:
        return 'Ask a question...';
    }
  };

  const renderChatInput = () => (
    <View style={styles.chatContainer}>
      <View style={styles.chatInputWrapper}>
        <TextInput
          style={styles.chatInput}
          placeholder={getChatPlaceholder()}
          placeholderTextColor={Colors.textTertiary}
          value={chatInput}
          onChangeText={setChatInput}
          multiline={false}
        />
        <TouchableOpacity 
          style={[styles.chatSendButton, !chatInput.trim() && styles.chatSendButtonDisabled]}
          disabled={!chatInput.trim() || isSending}
        >
          {isSending ? (
            <ActivityIndicator size="small" color={Colors.success} />
          ) : (
            <Ionicons name="send" size={20} color={chatInput.trim() ? Colors.success : Colors.textTertiary} />
          )}
        </TouchableOpacity>
      </View>
    </View>
  );

  // =========================================================================
  // MAIN RENDER
  // =========================================================================
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

      {/* Tabs */}
      {renderTabs()}

      <KeyboardAvoidingView 
        style={styles.flex1}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={0}
      >
        <ScrollView 
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Mode Label */}
          <Text style={styles.modeLabel}>
            {activeTab === 'summary' ? 'SUMMARY' : activeTab === 'snapshot' ? 'YOUR SNAPSHOT' : 'DEEP DIVE'}
          </Text>

          {/* Mirror Moment Card */}
          {renderMirrorMoment()}

          {/* Profile Data - show in snapshot and deep_dive modes */}
          {(activeTab === 'snapshot' || activeTab === 'deep_dive') && renderProfile()}
        </ScrollView>

        {/* Chat Input */}
        {renderChatInput()}
      </KeyboardAvoidingView>
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
    width: 32,
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
  // Tabs
  tabBar: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 8,
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
  // Scroll
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 20,
  },
  // Mode Label
  modeLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textSecondary,
    letterSpacing: 1.5,
    marginBottom: 12,
  },
  // Mirror Card
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
    fontWeight: '700',
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
  // Profile Cards
  profileCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  profileCardTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textSecondary,
    letterSpacing: 1.5,
    textAlign: 'center',
    marginBottom: 16,
  },
  profileGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  profileGridItem: {
    alignItems: 'center',
    flex: 1,
  },
  profileLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1,
    marginBottom: 4,
  },
  profileValue: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 2,
  },
  profileDegree: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
  // HD Profile Grid
  hdProfileGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  hdProfileItem: {
    width: '50%',
    alignItems: 'center',
    paddingVertical: 8,
  },
  hdProfileValue: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    textAlign: 'center',
  },
  // Cycles Grid (Numerology)
  cyclesGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  cycleItem: {
    alignItems: 'center',
  },
  cycleNumber: {
    fontSize: 32,
    fontWeight: '700',
    color: Colors.text,
  },
  cycleLabel: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginTop: 4,
  },
  // Computed Section
  computedSection: {
    paddingHorizontal: 4,
    marginBottom: 16,
  },
  computedTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.text,
    letterSpacing: 1,
    marginBottom: 12,
  },
  computedRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  computedLabel: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  computedValue: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
    textAlign: 'right',
    flex: 1,
    marginLeft: 16,
  },
  sourceText: {
    fontSize: 12,
    color: Colors.success,
    marginTop: 12,
  },
  // Empty Profile
  emptyProfileCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
  },
  emptyProfileText: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  // Consciousness
  consciousnessText: {
    fontSize: 15,
    color: Colors.text,
    lineHeight: 24,
  },
  // Chat
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
  chatSendButtonDisabled: {
    opacity: 0.5,
  },
});
