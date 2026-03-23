// ============================================
// CROSS-LENS PATTERN MATCHER
// ============================================
// Lightweight theme detection across lenses
// Surfaces alignment without heavy NLP or backend logic

// Theme categories for pattern matching
const THEME_KEYWORDS: { [theme: string]: string[] } = {
  'action-impulse': [
    'initiate', 'impulse', 'act', 'move', 'start', 'begin', 'quick', 'fast',
    'urge', 'drive', 'push', 'force', 'momentum', 'action', 'react', 'trigger'
  ],
  'emotion-processing': [
    'emotion', 'feel', 'wave', 'clarity', 'process', 'sensitivity', 'mood',
    'emotional', 'feeling', 'heart', 'depth', 'intensity', 'calm', 'storm'
  ],
  'pressure-control': [
    'pressure', 'control', 'power', 'resist', 'limit', 'boundary', 'structure',
    'responsibility', 'weight', 'burden', 'contain', 'hold', 'grip', 'tension'
  ],
  'timing-patience': [
    'wait', 'patience', 'time', 'timing', 'slow', 'pause', 'delay', 'rush',
    'hurry', 'speed', 'pace', 'rhythm', 'cycle', 'season', 'ready'
  ],
  'trust-surrender': [
    'trust', 'surrender', 'let go', 'release', 'uncertainty', 'unknown',
    'faith', 'doubt', 'fear', 'safety', 'secure', 'risk', 'leap'
  ],
  'communication-expression': [
    'speak', 'voice', 'express', 'communicate', 'say', 'word', 'tell',
    'share', 'inform', 'silence', 'listen', 'hear', 'message', 'truth'
  ],
  'identity-self': [
    'identity', 'self', 'who', 'define', 'role', 'mask', 'authentic',
    'true', 'real', 'appear', 'image', 'perception', 'seen', 'visible'
  ],
  'relationship-connection': [
    'relationship', 'connect', 'close', 'intimacy', 'other', 'people',
    'partner', 'trust', 'bond', 'distance', 'attach', 'merge', 'separate'
  ],
  'growth-expansion': [
    'grow', 'expand', 'more', 'bigger', 'ambition', 'potential', 'develop',
    'evolve', 'learn', 'stretch', 'reach', 'aspire', 'goal', 'vision'
  ],
};

// Human-readable signal lines for each theme combination
const THEME_SIGNALS: { [combo: string]: string[] } = {
  // Single theme signals (when same theme appears in 2+ lenses)
  'action-impulse': [
    'Part of you moves quickly - sometimes before the rest has caught up.',
    'There is an urgency to act that does not always wait for full clarity.',
    'The impulse to begin often arrives before the plan is complete.',
  ],
  'emotion-processing': [
    'Emotional clarity takes longer than the mind wants to wait.',
    'What you feel is not always what you know - the gap matters.',
    'Waves move through you that need time to settle into truth.',
  ],
  'pressure-control': [
    'Something heavy is being carried - it may not all be yours.',
    'Control is being tested, or asked to soften.',
    'The weight of responsibility keeps finding you.',
  ],
  'timing-patience': [
    'Speed and slowness are in tension - both have something to teach.',
    'Waiting is not passive - it is where clarity grows.',
    'The right pace is not the fastest one.',
  ],
  'trust-surrender': [
    'Part of you knows what to do but does not fully trust it yet.',
    'Surrender and control are negotiating.',
    'What feels uncertain may be asking for faith, not answers.',
  ],
  'communication-expression': [
    'Something wants to be said - the timing matters as much as the words.',
    'Expression and silence are both speaking.',
    'What you share and what you hold back are both choices.',
  ],
  'identity-self': [
    'Who you are and who you appear to be are in conversation.',
    'The self you show is not always the self you feel.',
    'Identity is being questioned or refined.',
  ],
  'relationship-connection': [
    'Closeness and distance are both active right now.',
    'How you relate to others is under examination.',
    'Connection is asking for something real.',
  ],
  'growth-expansion': [
    'Growth is calling - but not without friction.',
    'Expansion meets limits, and both are teachers.',
    'The pull toward more is testing what can hold it.',
  ],
  
  // Combination signals (when multiple themes intersect)
  'action-impulse+emotion-processing': [
    'Acting before emotional clarity settles.',
    'The urge to move meets the need to feel.',
    'Impulse and emotion are in active dialogue.',
  ],
  'action-impulse+timing-patience': [
    'Speed and patience are pulling in different directions.',
    'Something wants to start before its time.',
    'The tension between now and not-yet.',
  ],
  'emotion-processing+timing-patience': [
    'Emotional truth unfolds slower than the mind wants.',
    'Clarity comes in waves, not on demand.',
    'Patience is being asked of the heart.',
  ],
  'pressure-control+timing-patience': [
    'Pressure around timing and response.',
    'Weight that wants release but is not ready.',
    'Control and timing are testing each other.',
  ],
  'action-impulse+pressure-control': [
    'The drive to act meets something that holds back.',
    'Force and resistance are both present.',
    'Power is being channeled - or blocked.',
  ],
  'trust-surrender+timing-patience': [
    'Trust is being asked before certainty arrives.',
    'Letting go before you are ready.',
    'Faith and timing are intertwined.',
  ],
  'communication-expression+timing-patience': [
    'Something wants to be said - but the right moment has not arrived.',
    'Words and timing need to align.',
    'Expression is waiting for its opening.',
  ],
  'identity-self+pressure-control': [
    'Who you are is under pressure.',
    'The self is being tested or refined.',
    'Identity and responsibility are tangled.',
  ],
  'growth-expansion+pressure-control': [
    'Growth is meeting real limits.',
    'Ambition and structure are negotiating.',
    'Expansion asks: what can actually hold this?',
  ],
};

// Input types
export interface CrossLensInput {
  // From Human Design
  hdTypePattern?: string;
  hdAuthorityPattern?: string;
  
  // From Astrology
  astroAxisLines?: string[];
  astroMostImportantFactors?: string[];
  astroChartSpine?: string[];
  
  // From Pattern Engine (journal)
  compressedPatternLine?: string;
  selectedFacet?: string;
  facetLine?: string;
}

interface ThemeMatch {
  theme: string;
  sources: string[]; // Which lenses contributed
  strength: number;  // How many keyword matches
}

// Detect themes in a text
function detectThemes(text: string): { theme: string; count: number }[] {
  if (!text) return [];
  
  const lowerText = text.toLowerCase();
  const results: { theme: string; count: number }[] = [];
  
  for (const [theme, keywords] of Object.entries(THEME_KEYWORDS)) {
    let count = 0;
    for (const keyword of keywords) {
      if (lowerText.includes(keyword)) {
        count++;
      }
    }
    if (count > 0) {
      results.push({ theme, count });
    }
  }
  
  return results.sort((a, b) => b.count - a.count);
}

// Main matching function
export function getCrossLensSignals(input: CrossLensInput): string[] {
  const lensThemes: { lens: string; themes: { theme: string; count: number }[] }[] = [];
  
  // Process Human Design
  const hdTexts = [input.hdTypePattern, input.hdAuthorityPattern].filter(Boolean).join(' ');
  if (hdTexts) {
    const themes = detectThemes(hdTexts);
    if (themes.length > 0) {
      lensThemes.push({ lens: 'hd', themes });
    }
  }
  
  // Process Astrology
  const astroTexts = [
    ...(input.astroAxisLines || []),
    ...(input.astroMostImportantFactors || []),
    ...(input.astroChartSpine || []),
  ].filter(Boolean).join(' ');
  if (astroTexts) {
    const themes = detectThemes(astroTexts);
    if (themes.length > 0) {
      lensThemes.push({ lens: 'astro', themes });
    }
  }
  
  // Process Pattern Engine (Journal)
  const patternTexts = [
    input.compressedPatternLine,
    input.selectedFacet,
    input.facetLine,
  ].filter(Boolean).join(' ');
  if (patternTexts) {
    const themes = detectThemes(patternTexts);
    if (themes.length > 0) {
      lensThemes.push({ lens: 'pattern', themes });
    }
  }
  
  // Find themes that appear in 2+ lenses
  const themeToLenses: { [theme: string]: string[] } = {};
  
  for (const { lens, themes } of lensThemes) {
    for (const { theme, count } of themes) {
      if (count >= 1) { // At least one keyword match
        if (!themeToLenses[theme]) {
          themeToLenses[theme] = [];
        }
        if (!themeToLenses[theme].includes(lens)) {
          themeToLenses[theme].push(lens);
        }
      }
    }
  }
  
  // Filter to themes with 2+ lens matches
  const crossLensThemes = Object.entries(themeToLenses)
    .filter(([_, lenses]) => lenses.length >= 2)
    .sort((a, b) => b[1].length - a[1].length)
    .map(([theme]) => theme);
  
  if (crossLensThemes.length === 0) {
    return [];
  }
  
  // Generate signals
  const signals: string[] = [];
  const usedSignals = new Set<string>();
  
  // First, try combination signals for top 2 themes
  if (crossLensThemes.length >= 2) {
    const combo1 = `${crossLensThemes[0]}+${crossLensThemes[1]}`;
    const combo2 = `${crossLensThemes[1]}+${crossLensThemes[0]}`;
    const comboSignals = THEME_SIGNALS[combo1] || THEME_SIGNALS[combo2];
    
    if (comboSignals && comboSignals.length > 0) {
      const signal = comboSignals[0];
      if (!usedSignals.has(signal)) {
        signals.push(signal);
        usedSignals.add(signal);
      }
    }
  }
  
  // Then add single-theme signals
  for (const theme of crossLensThemes) {
    if (signals.length >= 3) break;
    
    const themeSignals = THEME_SIGNALS[theme];
    if (themeSignals) {
      for (const signal of themeSignals) {
        if (!usedSignals.has(signal) && signals.length < 3) {
          signals.push(signal);
          usedSignals.add(signal);
          break;
        }
      }
    }
  }
  
  return signals.slice(0, 3);
}

// Check if we should show the bridge at all
export function shouldShowCrossLensBridge(signals: string[]): boolean {
  return signals.length >= 1;
}
