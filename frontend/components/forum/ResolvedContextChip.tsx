/**
 * ResolvedContextChip — Slice C of the Forum Chat Auto Context (FCAC) work.
 *
 * Renders the resolver-decided frame as a small, glanceable chip ABOVE the
 * chat answer.  Strictly USER-FACING language — internal taxonomy strings
 * (MEMBER / PAIRWISE / MULTI_PERSON / etc.) never appear in the rendered
 * text.  Mirror voice only.
 *
 * Examples:
 *     👤 Mel · Spouse
 *     👤 Thaddeus · Child
 *     👥 Mel ↔ Thaddeus
 *     🌐 Forum
 *     👨‍👩‍👧‍👦 My children
 *     🪞 Self
 *
 * The component is purely presentational — it takes a `ResolvedContextBlock`
 * (from `services/api`) and renders it.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ResolvedContextBlock } from '../../services/api';
import { useTheme } from '../../contexts/ThemeContext';


// ─────────────────────────────────────────────────────────────────
// Role → user-facing label table.  Internal role tokens
// (spouse / child / parent / …) are mapped to capitalised English.
// Unknown roles fall through to a generic "Member" label.
// ─────────────────────────────────────────────────────────────────
const ROLE_LABELS: Record<string, string> = {
  spouse:           'Spouse',
  partner:          'Partner',
  ex_partner:       'Former partner',
  former_partner:   'Former partner',
  child:            'Child',
  parent:           'Parent',
  sibling:          'Sibling',
  close_friend:     'Close friend',
  friend:           'Friend',
  mentor:           'Mentor',
  mentee:           'Mentee',
  coach:            'Coach',
  coachee:          'Coachee',
  colleague:        'Colleague',
  cofounder:        'Co-founder',
  business_partner: 'Business partner',
  forum_member:     'Forum member',
  forum_mate:       'Forum member',
};


// ─────────────────────────────────────────────────────────────────
// scope_class → label  (MULTI_PERSON branch)
// ─────────────────────────────────────────────────────────────────
const SCOPE_LABELS: Record<string, { emoji: string; label: string }> = {
  my_children: { emoji: '👨‍👩‍👧‍👦', label: 'My children' },
  my_siblings: { emoji: '👫',         label: 'My siblings' },
  my_parents:  { emoji: '👪',         label: 'My parents' },
  my_circle:   { emoji: '🌐',         label: 'My circle' },
};


interface Props {
  ctx: ResolvedContextBlock;
}

export default function ResolvedContextChip({ ctx }: Props) {
  const { theme } = useTheme();

  // Compute a single { emoji, label } pair per frame.  Never expose the
  // internal frame token to the user.
  let emoji = '🪞';
  let label = 'Self';

  switch (ctx.frame) {
    case 'SELF':
      emoji = '🪞';
      label = 'Self';
      break;

    case 'MEMBER': {
      emoji = '👤';
      const name = ctx.target_name?.trim() || 'Member';
      const roleLabel = ctx.target_role
        ? ROLE_LABELS[ctx.target_role] ?? null
        : null;
      label = roleLabel ? `${name} · ${roleLabel}` : name;
      break;
    }

    case 'PAIRWISE': {
      emoji = '👥';
      const a = ctx.target_name?.trim()   || 'Member A';
      const b = ctx.target_name_b?.trim() || 'Member B';
      label = `${a} ↔ ${b}`;
      break;
    }

    case 'MULTI_PERSON': {
      const scope = (ctx.scope_class && SCOPE_LABELS[ctx.scope_class]) || null;
      emoji = scope?.emoji ?? '🌐';
      label = scope?.label ?? 'A group';
      break;
    }

    case 'FORUM':
      emoji = '🌐';
      label = 'Forum';
      break;

    case 'AMBIGUOUS':
      emoji = '❓';
      label = 'Multiple matches';
      break;

    default:
      emoji = '🪞';
      label = 'Self';
  }

  return (
    <View
      style={[
        styles.chip,
        {
          backgroundColor: theme.accent + '15',
          borderColor:     theme.accent + '40',
        },
      ]}
      accessibilityLabel={`Resolved context: ${label}`}
    >
      <Text style={styles.emoji}>{emoji}</Text>
      <Text
        style={[styles.label, { color: theme.text }]}
        numberOfLines={1}
      >
        {label}
      </Text>
    </View>
  );
}


const styles = StyleSheet.create({
  chip: {
    flexDirection:  'row',
    alignItems:     'center',
    alignSelf:      'flex-start',
    paddingHorizontal: 10,
    paddingVertical:    6,
    borderRadius:      14,
    borderWidth:        StyleSheet.hairlineWidth,
    marginBottom:       6,
  },
  emoji: {
    fontSize: 14,
    marginRight: 6,
  },
  label: {
    fontSize:   13,
    fontWeight: '500',
  },
});
