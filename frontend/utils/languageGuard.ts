/**
 * Language Quality Guard Layer
 * 
 * Post-processing utility that ensures all user-facing text is:
 * - Grammatically correct (a/an, punctuation)
 * - Natural and fluent (phrasing)
 * - Consistent in tone (observational, not declarative)
 * 
 * Apply to ALL generated text before rendering in UI.
 * 
 * IMPORTANT:
 * - Do not change meaning
 * - Do not rewrite content deeply
 * - Only polish language, fix grammar, improve readability
 * - Safe for undefined/null
 * - Idempotent: calling twice should not keep changing text
 */

// ============================================
// STEP 1: NORMALIZE APOSTROPHES/QUOTES/SPACING
// ============================================

function normalizeQuotesAndSpacing(text: string): string {
  let result = text;
  
  // Normalize smart quotes to straight quotes
  result = result.replace(/[\u2018\u2019]/g, "'"); // ' '
  result = result.replace(/[\u201C\u201D]/g, '"'); // " "
  
  // Normalize various dashes to em-dash
  result = result.replace(/\s*[–—]\s*/g, '—'); // en-dash and em-dash
  result = result.replace(/\s+-\s+/g, '—'); // spaced hyphen to em-dash
  
  // Collapse multiple spaces
  result = result.replace(/\s{2,}/g, ' ');
  
  return result;
}

// ============================================
// STEP 2: FIX ARTICLE MISTAKES (a/an)
// ============================================

// Specific patterns where "a" should be "an" (vowel sounds)
const A_TO_AN_PATTERNS = [
  // Explicitly listed in requirements
  /\ba\s+(initiating)\b/gi,
  /\ba\s+(emotional)\b/gi,
  /\ba\s+(honest)\b/gi,
  /\ba\s+(intuitive)\b/gi,
  /\ba\s+(expansive)\b/gi,
  /\ba\s+(imaginative)\b/gi,
  // Common astrology/mirror terms
  /\ba\s+(inner)\b/gi,
  /\ba\s+(outer)\b/gi,
  /\ba\s+(underlying)\b/gi,
  /\ba\s+(urgent)\b/gi,
  /\ba\s+(emerging)\b/gi,
  /\ba\s+(evolving)\b/gi,
  /\ba\s+(instinctive)\b/gi,
  /\ba\s+(unconscious)\b/gi,
  /\ba\s+(identity)\b/gi,
  /\ba\s+(impulse)\b/gi,
  /\ba\s+(intensity)\b/gi,
  /\ba\s+(opening)\b/gi,
  /\ba\s+(older)\b/gi,
  /\ba\s+(earlier)\b/gi,
  /\ba\s+(unusual)\b/gi,
  /\ba\s+(ultimate)\b/gi,
  /\ba\s+(hour)\b/gi,
  /\ba\s+(honor)\b/gi,
  /\ba\s+(heir)\b/gi,
  /\ba\s+(active)\b/gi,
  /\ba\s+(aesthetic)\b/gi,
  /\ba\s+(emotional)\b/gi,
  /\ba\s+(energetic)\b/gi,
  /\ba\s+(electric)\b/gi,
];

// Specific patterns where "an" should be "a" (consonant sounds despite vowel spelling)
const AN_TO_A_PATTERNS = [
  /\ban\s+(unique)\b/gi,
  /\ban\s+(useful)\b/gi,
  /\ban\s+(united)\b/gi,
  /\ban\s+(universal)\b/gi,
  /\ban\s+(uniform)\b/gi,
  /\ban\s+(union)\b/gi,
  /\ban\s+(unit)\b/gi,
  /\ban\s+(used)\b/gi,
  /\ban\s+(usual)\b/gi,
  /\ban\s+(European)\b/gi,
  /\ban\s+(euphoric)\b/gi,
  /\ban\s+(one)\b/gi,
  /\ban\s+(once)\b/gi,
];

function fixArticles(text: string): string {
  let result = text;
  
  // Fix "a" → "an" before vowel sounds
  for (const pattern of A_TO_AN_PATTERNS) {
    result = result.replace(pattern, (match, word) => {
      const article = match.charAt(0) === 'A' ? 'An' : 'an';
      return `${article} ${word}`;
    });
  }
  
  // Fix "an" → "a" before consonant sounds
  for (const pattern of AN_TO_A_PATTERNS) {
    result = result.replace(pattern, (match, word) => {
      const article = match.charAt(0) === 'A' ? 'A' : 'a';
      return `${article} ${word}`;
    });
  }
  
  return result;
}

// ============================================
// STEP 3: FIX COMMON PHRASING
// ============================================

const PHRASING_FIXES: [RegExp, string][] = [
  // Explicitly listed in requirements
  [/quality to your/gi, 'quality in your'],
  [/quality to the/gi, 'quality in the'],
  [/show the world/gi, 'show to the world'],
  [/plays out most intensely in home and emotional foundation/gi, 'shows up most strongly in your home and emotional foundation'],
  [/what you need to feel safe—not what you show the world/gi, 'what you need to feel safe—not what you show to the world'],
  
  // Additional natural phrasing fixes
  [/plays out most intensely in/gi, 'shows up most strongly in'],
  [/plays out most/gi, 'shows up most'],
  [/plays out in/gi, 'shows up in'],
  [/plays out/gi, 'shows up'],
  
  // Missing "your" before life areas
  [/in home and emotional/gi, 'in your home and emotional'],
  [/in home and family/gi, 'in your home and family'],
  [/in career and public/gi, 'in your career and public'],
  [/in relationships and/gi, 'in your relationships and'],
  
  // Redundancy cleanup
  [/very unique/gi, 'unique'],
  [/most unique/gi, 'unique'],
  [/reason is because/gi, 'reason is that'],
];

function fixPhrasing(text: string): string {
  let result = text;
  for (const [pattern, replacement] of PHRASING_FIXES) {
    result = result.replace(pattern, replacement);
  }
  return result;
}

// ============================================
// STEP 4: TONE NORMALIZATION (Observational)
// ============================================

const TONE_FIXES: [RegExp, string][] = [
  // "You are someone who" → "You tend to"
  [/You are someone who\s+/gi, 'You tend to '],
  [/You're someone who\s+/gi, 'You tend to '],
  
  // "You are a person who" → "You tend to"
  [/You are a person who\s+/gi, 'You tend to '],
  [/You're a person who\s+/gi, 'You tend to '],
  
  // "This means you are" → softer
  [/This means you are\s+/gi, 'This suggests you may be '],
  [/This means that you are\s+/gi, 'This suggests you may be '],
  
  // Soften absolute statements
  [/You will always/gi, 'You may often'],
  [/You will never/gi, 'You may rarely'],
  [/always feel/gi, 'often feel'],
  [/never feel/gi, 'rarely feel'],
  
  // "You are" at start of sentence only when followed by identity statement
  // Be careful - don't change "You are trying" or "You are noticing"
  [/^You are defined by/gim, 'You tend to be defined by'],
  [/^You are someone defined/gim, 'You tend to be someone defined'],
];

function normalizeTone(text: string): string {
  let result = text;
  for (const [pattern, replacement] of TONE_FIXES) {
    result = result.replace(pattern, replacement);
  }
  return result;
}

// ============================================
// STEP 5: PUNCTUATION CLEANUP
// ============================================

function cleanPunctuation(text: string): string {
  let result = text;
  
  // Collapse double spaces (again after other fixes)
  result = result.replace(/\s{2,}/g, ' ');
  
  // Trim stray spaces before punctuation
  result = result.replace(/\s+([.,;:!?])/g, '$1');
  
  // Add space after punctuation if missing (but not for abbreviations)
  result = result.replace(/([.,;:!?])([A-Za-z])/g, '$1 $2');
  
  // Normalize repeated punctuation
  result = result.replace(/\.{2,}/g, '.');
  result = result.replace(/,{2,}/g, ',');
  result = result.replace(/!{2,}/g, '!');
  result = result.replace(/\?{2,}/g, '?');
  result = result.replace(/—{2,}/g, '—');
  
  return result;
}

// ============================================
// STEP 6: CONTEXT-SPECIFIC FIXES
// ============================================

function contextFixes(text: string): string {
  let result = text;
  
  // Fix duplicate words
  result = result.replace(/\byour your\b/gi, 'your');
  result = result.replace(/\bthe the\b/gi, 'the');
  result = result.replace(/\ba a\b/gi, 'a');
  result = result.replace(/\ban an\b/gi, 'an');
  result = result.replace(/\bto to\b/gi, 'to');
  result = result.replace(/\bin in\b/gi, 'in');
  
  // Fix broken possessives
  result = result.replace(/your's/gi, 'yours');
  result = result.replace(/it's own/gi, 'its own');
  
  return result;
}

// ============================================
// MAIN EXPORT: cleanText()
// ============================================

/**
 * Main text cleaning function.
 * Apply this to ALL user-facing generated text before rendering.
 * 
 * Pipeline:
 * 1. Normalize apostrophes/quotes/spacing
 * 2. Fix article mistakes (a/an)
 * 3. Fix common phrasing
 * 4. Tone normalization
 * 5. Punctuation cleanup
 * 6. Context-specific fixes
 * 7. Final trim
 * 
 * @param text - Raw generated text (can be undefined/null)
 * @returns Cleaned, polished text (empty string if input was falsy)
 */
export function cleanText(text?: string | null): string {
  // Safe for undefined/null
  if (!text || typeof text !== 'string') {
    return '';
  }
  
  let result = text;
  
  // Pipeline
  result = normalizeQuotesAndSpacing(result);
  result = fixArticles(result);
  result = fixPhrasing(result);
  result = normalizeTone(result);
  result = cleanPunctuation(result);
  result = contextFixes(result);
  
  // Final trim
  result = result.trim();
  
  // Ensure sentence starts with capital letter
  if (result.length > 0) {
    result = result.charAt(0).toUpperCase() + result.slice(1);
  }
  
  return result;
}

/**
 * Clean an array of text items.
 * Useful for cleaning lists of patterns, themes, etc.
 */
export function cleanTextArray(texts?: string[] | null): string[] {
  if (!texts || !Array.isArray(texts)) return [];
  return texts.map(t => cleanText(t));
}

export default cleanText;
