/**
 * Ophiuchus Metadata — single frontend source of truth.
 * ----------------------------------------------------------------------
 * Build marker: ophiuchus-first-class-content-v1
 *
 * Mirrors backend/services/ophiuchus_metadata.py. Imported by every UI
 * surface that needs Ophiuchus element / modality / narrative blocks so
 * Ophiuchus charts never render "unknown" element or empty narrative.
 *
 * Voice — integration under pressure, contact with complexity, repair at
 * the threshold between Scorpio depth and Sagittarius meaning. Never
 * "chosen one", "13th sign mystery", "healer savior", or "more evolved".
 */

export const OPHIUCHUS_SIGN_NAME = 'Ophiuchus';

export const OPHIUCHUS_ELEMENT   = 'Ether';      // 5th transcendent element
export const OPHIUCHUS_MODALITY  = 'Mutable';
export const OPHIUCHUS_POLARITY  = 'Neutral';
export const OPHIUCHUS_RULER     = 'Chiron';
export const OPHIUCHUS_CO_RULER  = 'Pluto';
export const OPHIUCHUS_GLYPH     = '⛎';
export const OPHIUCHUS_ARCHETYPE = 'shaman / wound-keeper / threshold';
export const OPHIUCHUS_KEYWORD   = 'threshold';

// Trait words used by the deep-dive panels when displaying sign qualities.
export const OPHIUCHUS_QUALITIES: string[] = [
  'integrating', 'threshold-crossing', 'pattern-recognising', 'restorative', 'embodied',
];

// Sun
export const OPHIUCHUS_SUN_TENSION =
  'Can stay too long inside the analysis of a wound; can mistake processing depth for moving through it.';
export const OPHIUCHUS_SUN_GIFT =
  'Steady contact with complexity; the ability to metabolise hard material and turn it into something usable.';

// Moon
export const OPHIUCHUS_MOON_TENSION =
  'Emotional patterns ask to be enacted, not just felt; sitting with the feeling can become a way of avoiding the integration.';
export const OPHIUCHUS_MOON_GIFT =
  'Emotional stamina at the threshold; can stay with another\'s hard material without merging or fleeing.';
export const OPHIUCHUS_MOON_NEED =
  'integration, repair, and small repeatable crossings — not just consolation';

// Ascendant
export const OPHIUCHUS_ASC_TENSION =
  'Can come across as heavier or more weighted than the moment requires; people may project crisis where there is only depth.';
export const OPHIUCHUS_ASC_GIFT =
  'A grounded presence at thresholds — the kind of person hard conversations land safely around.';

// Mercury
export const OPHIUCHUS_MERCURY_STYLE =
  'pattern recognition over surface fact — tracks how things land, repeat, and integrate';
export const OPHIUCHUS_MERCURY_TENSION =
  'Can keep re-examining the pattern instead of acting on it; talking about it can become the deferral.';
export const OPHIUCHUS_MERCURY_GIFT =
  'Communication that finishes things — names the pattern, names the next move, ends the loop.';

// Cross-context narrative lines for lens / reflection surfaces.
export const OPHIUCHUS_GENERAL_BEHAVIOUR =
  'You may notice depth asking to translate into action today — less interest in re-examining the pattern, more in walking through it.';
export const OPHIUCHUS_GENERAL_DAY_NOTE =
  'Old patterns sit close to the surface; the body registers what hasn\'t been moved yet.';
export const OPHIUCHUS_REFLECTION_PROMPT =
  'What pattern have you understood long enough that it\'s asking now to be enacted, not explained?';
export const OPHIUCHUS_REFLECTION_THEME =
  'Depth alone isn\'t the work anymore — integration is.';

// Timeline year-arc — mirrors backend SIGN_PATTERNS["Ophiuchus"].
export const OPHIUCHUS_TIMELINE = {
  tension:         'going through it vs. going around it',
  year_theme:      'This year keeps putting you at thresholds you\'ve avoided crossing—places where the depth of what you\'ve felt has to translate into something you actually do with it.',
  arc_description: 'Across the year, you\'ll notice the same pattern: a hard thing surfaces, you sit inside it longer than most people would, and then it asks to be metabolised — not just understood. The year isn\'t asking you to perform recovery. It\'s asking what changes when you stop circling the wound and start walking through it.',
  cost_of_action:  'the integration is exhausting and slow—but the pattern you\'ve been carrying actually shifts',
  cost_of_waiting: 'you stay with the depth, but the depth alone isn\'t doing the work anymore',
};

export const OPHIUCHUS_META = {
  sign:      OPHIUCHUS_SIGN_NAME,
  element:   OPHIUCHUS_ELEMENT,
  modality:  OPHIUCHUS_MODALITY,
  polarity:  OPHIUCHUS_POLARITY,
  ruler:     OPHIUCHUS_RULER,
  co_ruler:  OPHIUCHUS_CO_RULER,
  glyph:     OPHIUCHUS_GLYPH,
  archetype: OPHIUCHUS_ARCHETYPE,
  keyword:   OPHIUCHUS_KEYWORD,
};
