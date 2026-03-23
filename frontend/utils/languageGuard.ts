/**
 * Language Quality Guard Layer
 * 
 * Post-processing utility that ensures all user-facing text is:
 * - Grammatically correct (a/an, verb conjugation)
 * - Natural and fluent (phrasing)
 * - Consistent in tone (observational, not declarative)
 * 
 * Apply to ALL generated text before rendering in UI.
 */

// ============================================
// STEP 1: NORMALIZE QUOTES/SPACING
// ============================================

function normalizeQuotesAndSpacing(text: string): string {
  let result = text;
  
  // Normalize smart quotes
  result = result.replace(/[\u2018\u2019]/g, "'");
  result = result.replace(/[\u201C\u201D]/g, '"');
  
  // Normalize dashes
  result = result.replace(/\s*[–—]\s*/g, '—');
  result = result.replace(/\s+-\s+/g, '—');
  
  // Collapse multiple spaces
  result = result.replace(/\s{2,}/g, ' ');
  
  return result;
}

// ============================================
// STEP 2: FIX ARTICLE MISTAKES (a/an)
// ============================================

// Words that require "an" (vowel sounds)
const VOWEL_SOUND_WORDS = [
  'initiating', 'emotional', 'honest', 'intuitive', 'expansive', 'imaginative',
  'inner', 'outer', 'underlying', 'urgent', 'emerging', 'evolving',
  'instinctive', 'unconscious', 'identity', 'impulse', 'intensity',
  'opening', 'older', 'earlier', 'unusual', 'ultimate', 'hour', 'honor',
  'heir', 'active', 'aesthetic', 'energetic', 'electric', 'emotional',
  'important', 'interesting', 'intense', 'intimate', 'internal', 'external',
  'early', 'easy', 'eager', 'earnest', 'earthly', 'obvious', 'occasional',
  'odd', 'official', 'only', 'open', 'opposite', 'ordinary', 'original',
  'other', 'overall', 'ongoing', 'uncertain', 'underlying', 'unexpected',
  'unfamiliar', 'unhealthy', 'unknown', 'unlikely', 'unspoken', 'unusual',
  'upward', 'urgent', 'absolute', 'abstract', 'abundant', 'academic',
  'acceptable', 'accessible', 'accidental', 'accurate', 'active',
  'actual', 'additional', 'adequate', 'administrative', 'adult',
  'advanced', 'aesthetic', 'afraid', 'aggressive', 'alert', 'alien',
  'alive', 'alleged', 'alternative', 'amazing', 'ambitious', 'ancient',
  'angry', 'annual', 'anxious', 'apparent', 'appropriate', 'arbitrary',
  'artistic', 'ashamed', 'athletic', 'attractive', 'automatic', 'available',
  'average', 'aware', 'awful', 'awkward'
];

// Words that require "a" despite starting with vowel (consonant sounds)
const CONSONANT_SOUND_WORDS = [
  'unique', 'useful', 'united', 'universal', 'uniform', 'union', 'unit',
  'used', 'usual', 'european', 'euphoric', 'one', 'once'
];

function fixArticles(text: string): string {
  let result = text;
  
  // Fix "a" → "an" before vowel sounds
  // Match "a " followed by any word starting with vowel
  result = result.replace(/\ba\s+([aeiouAEIOU]\w*)/g, (match, word) => {
    const lowerWord = word.toLowerCase();
    // Check if it's a consonant-sound exception (unique, useful, etc.)
    if (CONSONANT_SOUND_WORDS.some(w => lowerWord === w || lowerWord.startsWith(w))) {
      return match; // Keep "a"
    }
    // Check if it's in our vowel sound list OR starts with vowel
    const article = match.charAt(0) === 'A' ? 'An' : 'an';
    return `${article} ${word}`;
  });
  
  // Fix "an" → "a" before consonant sounds (unique, useful, etc.)
  for (const word of CONSONANT_SOUND_WORDS) {
    const regex = new RegExp(`\\ban\\s+(${word})`, 'gi');
    result = result.replace(regex, (match, w) => {
      const article = match.charAt(0) === 'A' ? 'A' : 'a';
      return `${article} ${w}`;
    });
  }
  
  return result;
}

// ============================================
// STEP 3: FIX VERB CONJUGATION AFTER "to"
// ============================================

function fixVerbConjugation(text: string): string {
  let result = text;
  
  // Fix "You tend to Xs" → "You tend to X"
  // After "to", verb must be base form (no trailing 's')
  result = result.replace(/\b(tend to|have to|need to|want to|try to|like to|seem to|appear to|continue to|begin to|start to|choose to|prefer to|love to|hate to|learn to|decide to|hope to|expect to|plan to|manage to|fail to|refuse to)\s+(\w+?)(es|s)\b/gi, 
    (match, infinitivePhrase, verbBase, ending) => {
      // Don't remove 's' from words that naturally end in 's' (like "process" base form)
      // Check if removing the ending creates a valid base form
      const baseForm = verbBase;
      
      // Common verbs where we need to fix
      const verbFixes: Record<string, string> = {
        'process': 'process',
        'processe': 'process',
        'react': 'react',
        'move': 'move',
        'feel': 'feel',
        'think': 'think',
        'see': 'see',
        'create': 'create',
        'make': 'make',
        'take': 'take',
        'give': 'give',
        'show': 'show',
        'hold': 'hold',
        'keep': 'keep',
        'hide': 'hide',
        'push': 'push',
        'pull': 'pull',
        'build': 'build',
        'seek': 'seek',
        'find': 'find',
        'protect': 'protect',
        'avoid': 'avoid',
        'manage': 'manage',
        'express': 'express',
        'expresse': 'express',
        'suppress': 'suppress',
        'suppresse': 'suppress',
        'release': 'release',
        'releas': 'release',
        'focus': 'focus',
        'focuse': 'focus',
      };
      
      const fullVerb = verbBase + ending;
      const lowerVerb = fullVerb.toLowerCase();
      
      // Check if it's a verb that needs fixing
      if (verbFixes[verbBase.toLowerCase()]) {
        return `${infinitivePhrase} ${verbFixes[verbBase.toLowerCase()]}`;
      }
      
      // For verbs ending in -es, remove -es (processes → process)
      if (ending.toLowerCase() === 'es') {
        return `${infinitivePhrase} ${verbBase}`;
      }
      
      // For verbs ending in -s, remove -s (reacts → react)
      if (ending.toLowerCase() === 's') {
        return `${infinitivePhrase} ${verbBase}`;
      }
      
      return match;
    }
  );
  
  // Specific fixes for common mistakes
  result = result.replace(/\btend to processes\b/gi, 'tend to process');
  result = result.replace(/\btend to reacts\b/gi, 'tend to react');
  result = result.replace(/\btend to moves\b/gi, 'tend to move');
  result = result.replace(/\btend to feels\b/gi, 'tend to feel');
  result = result.replace(/\btend to thinks\b/gi, 'tend to think');
  result = result.replace(/\btend to sees\b/gi, 'tend to see');
  result = result.replace(/\btend to creates\b/gi, 'tend to create');
  result = result.replace(/\btend to makes\b/gi, 'tend to make');
  result = result.replace(/\btend to takes\b/gi, 'tend to take');
  result = result.replace(/\btend to gives\b/gi, 'tend to give');
  result = result.replace(/\btend to shows\b/gi, 'tend to show');
  result = result.replace(/\btend to holds\b/gi, 'tend to hold');
  result = result.replace(/\btend to keeps\b/gi, 'tend to keep');
  result = result.replace(/\btend to hides\b/gi, 'tend to hide');
  result = result.replace(/\btend to pushes\b/gi, 'tend to push');
  result = result.replace(/\btend to pulls\b/gi, 'tend to pull');
  result = result.replace(/\btend to builds\b/gi, 'tend to build');
  result = result.replace(/\btend to seeks\b/gi, 'tend to seek');
  result = result.replace(/\btend to finds\b/gi, 'tend to find');
  result = result.replace(/\btend to protects\b/gi, 'tend to protect');
  result = result.replace(/\btend to avoids\b/gi, 'tend to avoid');
  result = result.replace(/\btend to manages\b/gi, 'tend to manage');
  result = result.replace(/\btend to expresses\b/gi, 'tend to express');
  result = result.replace(/\btend to suppresses\b/gi, 'tend to suppress');
  result = result.replace(/\btend to releases\b/gi, 'tend to release');
  result = result.replace(/\btend to focuses\b/gi, 'tend to focus');
  
  return result;
}

// ============================================
// STEP 4: FIX COMMON PHRASING
// ============================================

function fixPhrasing(text: string): string {
  let result = text;
  
  // Fix phrasing
  result = result.replace(/quality to your/gi, 'quality in your');
  result = result.replace(/quality to the/gi, 'quality in the');
  result = result.replace(/show the world/gi, 'show to the world');
  result = result.replace(/plays out most intensely in home and emotional foundation/gi, 
    'shows up most strongly in your home and emotional foundation');
  result = result.replace(/plays out most intensely in/gi, 'shows up most strongly in');
  result = result.replace(/plays out most/gi, 'shows up most');
  result = result.replace(/plays out in/gi, 'shows up in');
  result = result.replace(/plays out/gi, 'shows up');
  
  // Missing "your" before life areas
  result = result.replace(/in home and emotional/gi, 'in your home and emotional');
  result = result.replace(/in home and family/gi, 'in your home and family');
  result = result.replace(/in career and public/gi, 'in your career and public');
  
  return result;
}

// ============================================
// STEP 5: TONE NORMALIZATION
// ============================================

function normalizeTone(text: string): string {
  let result = text;
  
  // Only replace specific patterns - be careful not to over-replace
  // "You are someone who X" → "You tend to X"
  result = result.replace(/You are someone who\s+/gi, 'You tend to ');
  result = result.replace(/You're someone who\s+/gi, 'You tend to ');
  result = result.replace(/You are a person who\s+/gi, 'You tend to ');
  result = result.replace(/You're a person who\s+/gi, 'You tend to ');
  
  // DO NOT replace "You are feeling", "You are noticing", etc.
  // Only replace "You are" when followed by noun/adjective identity statements
  // "You are defined by" → "You tend to be defined by"
  result = result.replace(/^You are defined by/gim, 'You tend to be defined by');
  
  return result;
}

// ============================================
// STEP 6: VOICE CONSISTENCY (MIRROR VOICE)
// ============================================
// Ensures all text feels like ONE consistent voice:
// - Observational, not authoritative
// - Grounded, not abstract
// - Personal, but not intrusive
// - Clear, not poetic for the sake of it

function normalizeVoice(text: string): string {
  let result = text;
  
  // ============================================
  // FORBIDDEN PATTERNS → MIRROR VOICE
  // ============================================
  
  // "This reveals that you are..." → "You may notice..."
  result = result.replace(/This reveals that you are\s+/gi, 'You may notice ');
  result = result.replace(/This reveals that you\s+/gi, 'You may notice that you ');
  result = result.replace(/This reveals\s+/gi, 'You may notice ');
  
  // "This means you are..." → "This tends to show up as..."
  result = result.replace(/This means you are\s+/gi, 'This tends to show up as ');
  result = result.replace(/This means that you are\s+/gi, 'This tends to show up as ');
  result = result.replace(/This means you\s+/gi, 'This suggests you ');
  result = result.replace(/This means that you\s+/gi, 'This suggests you ');
  
  // "This indicates that..." → "This can feel like..."
  result = result.replace(/This indicates that you\s+/gi, 'You may find that you ');
  result = result.replace(/This indicates that\s+/gi, 'This can feel like ');
  result = result.replace(/This indicates\s+/gi, 'This can show up as ');
  
  // "This shows that you are..." → "You may notice..."
  result = result.replace(/This shows that you are\s+/gi, 'You may notice ');
  result = result.replace(/This shows that you\s+/gi, 'You may notice that you ');
  result = result.replace(/This shows that\s+/gi, 'This tends to show up when ');
  
  // "This suggests you are..." → "Part of you..."
  result = result.replace(/This suggests you are\s+/gi, 'Part of you may be ');
  result = result.replace(/This suggests that you are\s+/gi, 'Part of you may be ');
  
  // "You are inherently..." → "There can be..."
  result = result.replace(/You are inherently\s+/gi, 'There can be ');
  result = result.replace(/You're inherently\s+/gi, 'There can be ');
  
  // "You are naturally..." → "You may naturally..."
  result = result.replace(/You are naturally\s+/gi, 'You may naturally ');
  result = result.replace(/You're naturally\s+/gi, 'You may naturally ');
  
  // "You are fundamentally..." → "At your core, you tend to be..."
  result = result.replace(/You are fundamentally\s+/gi, 'At your core, you tend to be ');
  result = result.replace(/You're fundamentally\s+/gi, 'At your core, you tend to be ');
  
  // ============================================
  // CLINICAL/FORMAL → GROUNDED
  // ============================================
  
  // "It is important to note that..." → (remove)
  result = result.replace(/It is important to note that\s+/gi, '');
  result = result.replace(/It's important to note that\s+/gi, '');
  
  // "It should be noted that..." → (remove)
  result = result.replace(/It should be noted that\s+/gi, '');
  
  // "It can be observed that..." → (remove)
  result = result.replace(/It can be observed that\s+/gi, '');
  
  // "One might say that..." → (remove or simplify)
  result = result.replace(/One might say that\s+/gi, '');
  
  // "In essence," → (remove)
  result = result.replace(/In essence,\s+/gi, '');
  
  // "Essentially," → (remove)
  result = result.replace(/Essentially,\s+/gi, '');
  
  // ============================================
  // DRAMATIC/SPIRITUAL → OBSERVATIONAL
  // ============================================
  
  // "Your soul craves..." → "Part of you may crave..."
  result = result.replace(/Your soul craves\s+/gi, 'Part of you may crave ');
  result = result.replace(/Your soul needs\s+/gi, 'Part of you may need ');
  result = result.replace(/Your soul wants\s+/gi, 'Part of you may want ');
  
  // "You are destined to..." → "You may find yourself drawn to..."
  result = result.replace(/You are destined to\s+/gi, 'You may find yourself drawn to ');
  result = result.replace(/You're destined to\s+/gi, 'You may find yourself drawn to ');
  
  // "The universe is telling you..." → "There may be..."
  result = result.replace(/The universe is telling you\s+/gi, 'There may be ');
  result = result.replace(/The cosmos is\s+/gi, 'There may be ');
  
  // "Your higher self..." → "Part of you..."
  result = result.replace(/Your higher self\s+/gi, 'Part of you ');
  
  // ============================================
  // AUTHORITATIVE → OBSERVATIONAL
  // ============================================
  
  // "You must..." → "You may find it helpful to..."
  result = result.replace(/You must\s+/gi, 'You may find it helpful to ');
  
  // "You need to..." → "You may benefit from..."
  result = result.replace(/You need to understand\s+/gi, 'It can help to notice ');
  result = result.replace(/You need to realize\s+/gi, 'You may notice ');
  result = result.replace(/You need to accept\s+/gi, 'There may be value in accepting ');
  result = result.replace(/You need to\s+/gi, 'You may benefit from ');
  
  // "You should..." → "You might consider..."
  result = result.replace(/You should always\s+/gi, 'You might consider ');
  result = result.replace(/You should never\s+/gi, 'You may want to avoid ');
  result = result.replace(/You should\s+/gi, 'You might ');
  
  // "You will always..." → "You may often..."
  result = result.replace(/You will always\s+/gi, 'You may often ');
  
  // "You will never..." → "You may rarely..."
  result = result.replace(/You will never\s+/gi, 'You may rarely ');
  
  // ============================================
  // SMOOTH MIRROR VOICE PATTERNS
  // ============================================
  
  // "Your X reveals..." → "You may notice..." (handles multi-word like "Moon in Aries")
  result = result.replace(/Your [A-Z][a-zA-Z\s]+ reveals that\s+/gi, 'You may notice that ');
  result = result.replace(/Your [A-Z][a-zA-Z\s]+ reveals\s+/gi, 'You may notice ');
  
  // "Your X indicates..." → "This can show up as..."
  result = result.replace(/Your [A-Z][a-zA-Z\s]+ indicates that\s+/gi, 'This can feel like ');
  result = result.replace(/Your [A-Z][a-zA-Z\s]+ indicates\s+/gi, 'This can show up as ');
  
  // "Your X shows..." → "You may notice..."
  result = result.replace(/Your [A-Z][a-zA-Z\s]+ shows that\s+/gi, 'You may notice that ');
  result = result.replace(/Your [A-Z][a-zA-Z\s]+ shows\s+/gi, 'You may notice ');
  
  // "Your X means..." → "This tends to..."
  result = result.replace(/Your [A-Z][a-zA-Z\s]+ means that\s+/gi, 'This tends to show up as ');
  result = result.replace(/Your [A-Z][a-zA-Z\s]+ means\s+/gi, 'This tends to ');
  
  // ============================================
  // ENSURE CONSISTENT TRANSITIONS
  // ============================================
  
  // Clean up double "You may" at start
  result = result.replace(/^You may You may/gim, 'You may');
  result = result.replace(/You may notice You may/gi, 'You may');
  
  // Fix capitalization after removals
  result = result.replace(/\.\s+([a-z])/g, (match, char) => '. ' + char.toUpperCase());
  
  return result;
}

// ============================================
// STEP 7: PUNCTUATION CLEANUP
// ============================================

function cleanPunctuation(text: string): string {
  let result = text;
  
  // Collapse double spaces
  result = result.replace(/\s{2,}/g, ' ');
  
  // Trim spaces before punctuation
  result = result.replace(/\s+([.,;:!?])/g, '$1');
  
  // Add space after punctuation if missing
  result = result.replace(/([.,;:!?])([A-Za-z])/g, '$1 $2');
  
  // Normalize repeated punctuation
  result = result.replace(/\.{2,}/g, '.');
  result = result.replace(/,{2,}/g, ',');
  result = result.replace(/—{2,}/g, '—');
  
  return result;
}

// ============================================
// STEP 7: CONTEXT FIXES
// ============================================

function contextFixes(text: string): string {
  let result = text;
  
  // Fix duplicate words
  result = result.replace(/\byour your\b/gi, 'your');
  result = result.replace(/\bthe the\b/gi, 'the');
  result = result.replace(/\ba a\b/gi, 'a');
  result = result.replace(/\ban an\b/gi, 'an');
  result = result.replace(/\bto to\b/gi, 'to');
  
  // Fix possessives
  result = result.replace(/your's/gi, 'yours');
  result = result.replace(/it's own/gi, 'its own');
  
  return result;
}

// ============================================
// MAIN EXPORT: cleanText()
// ============================================

/**
 * Main text cleaning function.
 * Apply to ALL user-facing generated text before rendering.
 * 
 * Pipeline:
 * 1. Normalize quotes/spacing
 * 2. Fix articles (a/an)
 * 3. Tone normalization (identity → observational)
 * 4. Fix verb conjugation
 * 5. Fix phrasing
 * 6. VOICE CONSISTENCY (Mirror Voice)
 * 7. Clean punctuation
 * 8. Context fixes
 */
export function cleanText(text?: string | null): string {
  if (!text || typeof text !== 'string') {
    return '';
  }
  
  let result = text;
  
  // Pipeline - ORDER MATTERS!
  // 1. Normalize quotes/spacing first
  result = normalizeQuotesAndSpacing(result);
  
  // 2. Fix articles (a/an) 
  result = fixArticles(result);
  
  // 3. Tone normalization BEFORE verb fix
  //    "You are someone who processes" → "You tend to processes"
  result = normalizeTone(result);
  
  // 4. Fix verb conjugation AFTER tone
  //    "You tend to processes" → "You tend to process"
  result = fixVerbConjugation(result);
  
  // 5. Fix phrasing
  result = fixPhrasing(result);
  
  // 6. VOICE CONSISTENCY (Mirror Voice)
  //    Converts authoritative/clinical/dramatic → observational/grounded
  result = normalizeVoice(result);
  
  // 7. Clean punctuation
  result = cleanPunctuation(result);
  
  // 8. Context fixes
  result = contextFixes(result);
  
  // Final trim
  result = result.trim();
  
  return result;
}

/**
 * Clean array of strings
 */
export function cleanTextArray(texts?: string[] | null): string[] {
  if (!texts || !Array.isArray(texts)) return [];
  return texts.map(t => cleanText(t));
}

export default cleanText;
