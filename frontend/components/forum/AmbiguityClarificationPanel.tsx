/**
 * AmbiguityClarificationPanel — Slice C of the FCAC work.
 *
 * Renders when the backend resolver returns `AMBIGUOUS` (multiple
 * candidate names share a prefix or alias).  The panel lists the
 * candidates and lets the user pick one — the chosen candidate's
 * user_id is then used as `target_member_id` in a re-issued chat
 * request (handled by the parent).
 *
 * Strict rule (per user directive): never auto-pick.  Always ask.
 */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { ClarificationCandidate } from '../../services/api';
import { useTheme } from '../../contexts/ThemeContext';


interface Props {
  candidates: ClarificationCandidate[];
  originalMessage: string;
  onChoose: (cand: ClarificationCandidate) => void;
  onCancel: () => void;
}

export default function AmbiguityClarificationPanel({
  candidates, originalMessage, onChoose, onCancel,
}: Props) {
  const { theme } = useTheme();

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: theme.surface,
          borderColor:     theme.border,
        },
      ]}
    >
      <Text style={[styles.title, { color: theme.text }]}>
        I found multiple people. Which one did you mean?
      </Text>
      {originalMessage ? (
        <Text style={[styles.context, { color: theme.textTertiary }]} numberOfLines={2}>
          Your question: &ldquo;{originalMessage}&rdquo;
        </Text>
      ) : null}

      <ScrollView style={styles.list} keyboardShouldPersistTaps="handled">
        {candidates.map((c, idx) => (
          <TouchableOpacity
            key={`${c.user_id || 'noid'}-${idx}`}
            style={[styles.item, { borderBottomColor: theme.border }]}
            onPress={() => onChoose(c)}
            accessibilityRole="button"
            accessibilityLabel={`Pick ${c.name}`}
          >
            <View style={styles.itemRow}>
              <Text style={[styles.name, { color: theme.text }]} numberOfLines={1}>
                {c.name}
              </Text>
              {c.role ? (
                <Text style={[styles.role, { color: theme.textTertiary }]}>
                  {c.role.replace(/_/g, ' ')}
                </Text>
              ) : null}
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <TouchableOpacity
        style={[styles.cancel, { borderTopColor: theme.border }]}
        onPress={onCancel}
        accessibilityRole="button"
        accessibilityLabel="Cancel clarification"
      >
        <Text style={[styles.cancelText, { color: theme.textSecondary }]}>
          Never mind
        </Text>
      </TouchableOpacity>
    </View>
  );
}


const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginVertical:   12,
    borderRadius:     12,
    borderWidth:      StyleSheet.hairlineWidth,
    overflow:         'hidden',
  },
  title: {
    fontSize:    15,
    fontWeight:  '600',
    paddingHorizontal: 14,
    paddingTop:        14,
    paddingBottom:     2,
  },
  context: {
    fontSize:    12,
    fontStyle:   'italic',
    paddingHorizontal: 14,
    paddingBottom:     10,
  },
  list: {
    maxHeight: 280,
  },
  item: {
    paddingHorizontal: 14,
    paddingVertical:   12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  itemRow: {
    flexDirection:  'row',
    alignItems:     'center',
    justifyContent: 'space-between',
  },
  name: {
    fontSize:   15,
    fontWeight: '500',
    flexShrink: 1,
  },
  role: {
    fontSize:   12,
    marginLeft: 8,
  },
  cancel: {
    paddingVertical:   12,
    alignItems:        'center',
    borderTopWidth:    StyleSheet.hairlineWidth,
  },
  cancelText: {
    fontSize:   13,
    fontWeight: '500',
  },
});
