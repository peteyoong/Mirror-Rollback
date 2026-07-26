import React from 'react';
import { ScrollView, TouchableOpacity, Text, View, StyleSheet } from 'react-native';

export interface LensTabDef {
  key: string;
  label: string;
}

/**
 * LensTabBar — shared horizontal pill tab bar for all lens views.
 *
 * Replaces the old `flex: 1` tab rows that clipped/overlapped labels on
 * narrow viewports (<360px). Pills never wrap; the row scrolls
 * horizontally when tabs exceed the viewport width.
 */
export default function LensTabBar({
  tabs,
  activeKey,
  onChange,
  theme,
}: {
  tabs: LensTabDef[];
  activeKey: string;
  onChange: (key: string) => void;
  theme: any;
}) {
  return (
    <View style={[styles.wrap, { borderBottomColor: theme.border }]}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.row}
      >
        {tabs.map((t) => {
          const active = t.key === activeKey;
          return (
            <TouchableOpacity
              key={t.key}
              onPress={() => onChange(t.key)}
              style={[styles.pill, active && styles.pillActive]}
              accessibilityRole="button"
              accessibilityState={{ selected: active }}
              activeOpacity={0.7}
            >
              <Text
                numberOfLines={1}
                style={[
                  styles.pillText,
                  { color: active ? theme.accent : theme.textTertiary },
                ]}
              >
                {t.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    gap: 8,
  },
  pill: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: 'transparent',
    minHeight: 36,
    justifyContent: 'center',
  },
  pillActive: {
    backgroundColor: 'rgba(198, 168, 124, 0.12)',
    borderColor: 'rgba(198, 168, 124, 0.38)',
  },
  pillText: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.2,
  },
});
