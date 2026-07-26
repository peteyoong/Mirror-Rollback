/**
 * HomeTextureCheckIn — daily texture chip (micro-reflection-v3-home-texture)
 * ========================================================================
 *
 * A soft, dismissible Home-tab card that asks
 *   "How are you holding right now?"
 *
 * 8 texture chips (tense / distant / open / pressured / stuck / clear /
 * conflicted / softer).  Tap one → POSTs to
 *   /api/micro-reflection/home-texture
 * then optionally offers a second step:
 *   "What does this connect to?"  → work / relationships / self /
 *                                   family / forum / not sure
 *
 * Rules:
 *   - One tap is enough.  No streaks.  No scores.  No charts.
 *   - Tap saves SILENTLY (tiny ack).
 *   - Dismissible per session (returns next day).
 *   - Once logged today, collapses to a quiet "Held for today" line.
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  LayoutAnimation,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  UIManager,
  View,
} from 'react-native';

import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

type Texture =
  | 'tense'
  | 'distant'
  | 'open'
  | 'pressured'
  | 'stuck'
  | 'clear'
  | 'conflicted'
  | 'softer';

type Domain =
  | 'work'
  | 'relationships'
  | 'self'
  | 'family'
  | 'forum'
  | 'not_sure';

const TEXTURES: Texture[] = [
  'tense', 'distant', 'open', 'pressured',
  'stuck', 'clear', 'conflicted', 'softer',
];

const TEXTURE_LABEL: Record<Texture, string> = {
  tense: 'tense',
  distant: 'distant',
  open: 'open',
  pressured: 'pressured',
  stuck: 'stuck',
  clear: 'clear',
  conflicted: 'conflicted',
  softer: 'softer',
};

const DOMAINS: Domain[] = ['work', 'relationships', 'self', 'family', 'forum', 'not_sure'];

const DOMAIN_LABEL: Record<Domain, string> = {
  work: 'work',
  relationships: 'relationships',
  self: 'self',
  family: 'family',
  forum: 'forum',
  not_sure: 'not sure',
};

const ACKS = [
  'Held.',
  'Noted.',
  "I'll hold that.",
];

interface Props {
  userId: string;
}

export default function HomeTextureCheckIn({ userId }: Props) {
  const { theme } = useTheme();
  const [loaded, setLoaded] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [loggedToday, setLoggedToday] = useState<{
    texture: Texture | null;
    domain: Domain | null;
  } | null>(null);
  const [tappedTexture, setTappedTexture] = useState<Texture | null>(null);
  const [tappedDomain, setTappedDomain] = useState<Domain | null>(null);
  const [posting, setPosting] = useState(false);

  const ack = React.useMemo(
    () => ACKS[Math.floor(Math.random() * ACKS.length)],
    [],
  );

  // Check "logged today" state on mount.
  useEffect(() => {
    let cancelled = false;
    const fetchToday = async () => {
      try {
        const resp = await api.get(
          `/micro-reflection/${userId}/home-texture/today`,
        );
        if (cancelled) return;
        if (resp?.data?.logged_today && resp.data.last) {
          setLoggedToday({
            texture: (resp.data.last.texture as Texture) || null,
            domain: (resp.data.last.domain as Domain) || null,
          });
        }
      } catch {
        // Silent — never disturb home.
      } finally {
        if (!cancelled) setLoaded(true);
      }
    };
    if (userId) void fetchToday();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const postTap = useCallback(
    async (texture: Texture, domain?: Domain) => {
      if (!userId) return;
      setPosting(true);
      try {
        await api.post('/micro-reflection/home-texture', {
          user_id: userId,
          texture,
          domain: domain ?? null,
        });
      } catch {
        // Silent.
      } finally {
        setPosting(false);
      }
    },
    [userId],
  );

  const onTapTexture = (t: Texture) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setTappedTexture(t);
    void postTap(t);
  };

  const onTapDomain = (d: Domain) => {
    if (!tappedTexture) return;
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setTappedDomain(d);
    void postTap(tappedTexture, d);
    setLoggedToday({ texture: tappedTexture, domain: d });
  };

  const onSkipDomain = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setLoggedToday({ texture: tappedTexture, domain: null });
  };

  const onDismiss = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setDismissed(true);
  };

  if (!loaded || dismissed) return null;

  // ── Already logged today — quiet "held" line ─────────────────────────
  if (loggedToday) {
    return (
      <View
        style={[
          styles.cardQuiet,
          { backgroundColor: theme.surface, borderColor: theme.border },
        ]}
      >
        <Text style={[styles.kicker, { color: theme.textTertiary }]}>
          How you're holding
        </Text>
        <Text style={[styles.heldLine, { color: theme.textSecondary }]}>
          Held for today
          {loggedToday.texture ? ` · ${TEXTURE_LABEL[loggedToday.texture]}` : ''}
          {loggedToday.domain && loggedToday.domain !== 'not_sure'
            ? ` · ${DOMAIN_LABEL[loggedToday.domain]}`
            : ''}
          .
        </Text>
      </View>
    );
  }

  // ── Stage 1: texture chips ───────────────────────────────────────────
  if (!tappedTexture) {
    return (
      <View
        style={[
          styles.card,
          { backgroundColor: theme.surface, borderColor: theme.border },
        ]}
      >
        <View style={styles.headerRow}>
          <View style={{ flex: 1 }}>
            <Text style={[styles.kicker, { color: theme.textTertiary }]}>
              A check-in
            </Text>
            <Text style={[styles.prompt, { color: theme.text }]}>
              How are you holding right now?
            </Text>
          </View>
          <TouchableOpacity
            onPress={onDismiss}
            hitSlop={10}
            accessibilityRole="button"
            accessibilityLabel="Dismiss"
            style={styles.dismissBtn}
          >
            <Text style={[styles.dismissText, { color: theme.textTertiary }]}>×</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.chipRow}>
          {TEXTURES.map((t) => (
            <TouchableOpacity
              key={t}
              activeOpacity={0.7}
              disabled={posting}
              onPress={() => onTapTexture(t)}
              accessibilityRole="button"
              accessibilityLabel={`Texture: ${TEXTURE_LABEL[t]}`}
              style={[
                styles.chip,
                { borderColor: theme.border, backgroundColor: 'transparent' },
              ]}
            >
              <Text style={[styles.chipText, { color: theme.textSecondary }]}>
                {TEXTURE_LABEL[t]}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    );
  }

  // ── Stage 2: optional domain follow-up ───────────────────────────────
  if (!tappedDomain) {
    return (
      <View
        style={[
          styles.card,
          { backgroundColor: theme.surface, borderColor: theme.border },
        ]}
      >
        <Text style={[styles.kicker, { color: theme.textTertiary }]}>
          {ack}
        </Text>
        <Text style={[styles.prompt, { color: theme.text }]}>
          What does this connect to?
        </Text>
        <Text style={[styles.subPrompt, { color: theme.textTertiary }]}>
          Optional.
        </Text>
        <View style={styles.chipRow}>
          {DOMAINS.map((d) => (
            <TouchableOpacity
              key={d}
              activeOpacity={0.7}
              disabled={posting}
              onPress={() => onTapDomain(d)}
              accessibilityRole="button"
              accessibilityLabel={`Domain: ${DOMAIN_LABEL[d]}`}
              style={[
                styles.chip,
                { borderColor: theme.border, backgroundColor: 'transparent' },
              ]}
            >
              <Text style={[styles.chipText, { color: theme.textSecondary }]}>
                {DOMAIN_LABEL[d]}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        <TouchableOpacity
          onPress={onSkipDomain}
          hitSlop={6}
          accessibilityRole="button"
          accessibilityLabel="Skip"
          style={styles.skipBtn}
        >
          <Text style={[styles.skipText, { color: theme.textTertiary }]}>
            Skip
          </Text>
        </TouchableOpacity>
      </View>
    );
  }

  // unreachable — loggedToday set above will catch this state
  return null;
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 20,
    marginBottom: 16,
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    gap: 10,
  },
  cardQuiet: {
    marginHorizontal: 20,
    marginBottom: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    gap: 2,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  dismissBtn: {
    width: 28,
    height: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dismissText: {
    fontSize: 20,
    fontWeight: '300',
    lineHeight: 22,
  },
  kicker: {
    fontSize: 10.5,
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    fontWeight: '500',
  },
  prompt: {
    fontSize: 16,
    lineHeight: 22,
    fontWeight: '500',
    marginTop: 2,
  },
  subPrompt: {
    fontSize: 12,
    fontStyle: 'italic',
  },
  heldLine: {
    fontSize: 13,
    lineHeight: 19,
    marginTop: 2,
    fontStyle: 'italic',
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 4,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
  },
  chipText: {
    fontSize: 12.5,
    letterSpacing: 0.2,
  },
  skipBtn: {
    alignSelf: 'flex-start',
    marginTop: 4,
    paddingVertical: 4,
  },
  skipText: {
    fontSize: 11.5,
    fontStyle: 'italic',
    letterSpacing: 0.2,
  },
});
