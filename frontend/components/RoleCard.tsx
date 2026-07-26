import React from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { fontFamily } from '../theme/tokens';
import { LifeRoleCard } from '../services/api';

interface Props {
  data: LifeRoleCard | null;
  loading?: boolean;
}

/**
 * RoleCard — the anchor of the Life tab.
 *
 * Sits ABOVE the sub-tabs. Designed to feel like an anchor, NOT another
 * accordion block:
 *  - prominent header line ("The Role You're In")
 *  - role statement in larger type
 *  - tension / distortion / orientation as small labelled rows
 *  - not_for shown as a subtle footer line in the accent tint
 *
 * Uses no framework names. All copy comes from the backend synthesis engine.
 */
export default function RoleCard({ data, loading }: Props) {
  const { theme, isDark } = useTheme();

  const headerColor = theme.accent;
  const borderTint = isDark ? theme.accent + '30' : theme.accent + '40';
  const bgTint = isDark ? theme.accent + '10' : theme.accent + '08';

  if (loading && !data) {
    return (
      <View style={[styles.card, { backgroundColor: bgTint, borderColor: borderTint }]}>
        <View style={styles.eyebrowRow}>
          <Ionicons name="compass" size={14} color={headerColor} />
          <Text style={[styles.eyebrow, { color: headerColor }]}>THE ROLE YOU&apos;RE IN</Text>
        </View>
        <ActivityIndicator size="small" color={headerColor} style={{ marginTop: 12 }} />
      </View>
    );
  }

  if (!data || !data.role) {
    return null;
  }

  const Row = ({ label, value }: { label: string; value: string | null | undefined }) => {
    if (!value) return null;
    return (
      <View style={styles.subRow}>
        <Text style={[styles.subLabel, { color: theme.textTertiary }]}>{label}</Text>
        <Text style={[styles.subValue, { color: theme.text }]}>{value}</Text>
      </View>
    );
  };

  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: bgTint,
          borderColor: borderTint,
        },
      ]}
    >
      {/* Eyebrow — announces the anchor */}
      <View style={styles.eyebrowRow}>
        <Ionicons name="compass" size={14} color={headerColor} />
        <Text style={[styles.eyebrow, { color: headerColor }]}>THE ROLE YOU&apos;RE IN</Text>
      </View>

      {/* Role headline (larger type, prominent) */}
      <Text style={[styles.role, { color: theme.text }]}>{data.role}</Text>

      {/* Labelled rows: tension → distortion → orientation */}
      <View style={styles.subStack}>
        <Row label="Tension" value={data.tension} />
        <Row label="Distortion" value={data.distortion} />
        <Row label="Orientation" value={data.orientation} />
      </View>

      {/* Not for — subtle footer */}
      {data.not_for ? (
        <View style={[styles.notForRow, { borderTopColor: borderTint }]}>
          <Text style={[styles.notForLabel, { color: headerColor }]}>Not for</Text>
          <Text style={[styles.notForValue, { color: theme.text }]}>{data.not_for}</Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 16,
    marginTop: 4,
    marginBottom: 16,
    padding: 18,
    borderRadius: 16,
    borderWidth: 1,
  },
  eyebrowRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 10,
  },
  eyebrow: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 1.2,
  },
  role: {
    fontFamily: fontFamily.display,
    fontSize: 17,
    lineHeight: 24,
    fontWeight: '400',
    letterSpacing: 0.2,
    marginBottom: 14,
  },
  subStack: {
    gap: 10,
  },
  subRow: {
    gap: 2,
  },
  subLabel: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  subValue: {
    fontSize: 14,
    lineHeight: 21,
  },
  notForRow: {
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: 2,
  },
  notForLabel: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  notForValue: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
});
