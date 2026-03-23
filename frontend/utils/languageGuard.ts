/**
 * Language Quality Guard Layer
 * 
 * Post-processing utility that ensures all user-facing text is:
 * - Grammatically correct
 * - Natural and fluent
 * - Consistent in tone (observational, not declarative)
 * 
 * Apply to ALL generated text before rendering in UI.
 */

// ============================================
// 1. ARTICLE CORRECTION (a/an)
// ============================================

// Words that start with vowel sounds (use "an")
const VOWEL_SOUND_WORDS = [
  'initiating', 'emotional', 'honest', 'hour', 'honor', 'heir',
  'opening', 'underlying', 'unusual', 'urgent', 'ultimate',
  'inner', 'outer', 'earlier', 'older', 'evolving', 'emerging',
  'intuitive', 'instinctive', 'impulse', 'impact', 'important',
  'identity', 'issue', 'insight', 'intensity', 'intention',
  'absence', 'abundance', 'acceptance', 'accident', 'achievement',
  'action', 'active', 'actual', 'acute', 'addition', 'adjustment',
  'adult', 'advance', 'advantage', 'adventure', 'aesthetic',
  'affection', 'afraid', 'afternoon', 'age', 'agency', 'agent',
  'agreement', 'air', 'alarm', 'alert', 'alien', 'alive',
  'allegiance', 'alliance', 'allowance', 'almost', 'alone',
  'alternative', 'altogether', 'amateur', 'ambition', 'ambitious',
  'amendment', 'amount', 'analysis', 'ancestor', 'ancient',
  'anger', 'angle', 'angry', 'animal', 'anniversary', 'announcement',
  'annual', 'answer', 'anticipation', 'anxiety', 'anxious',
  'apartment', 'apology', 'apparent', 'appeal', 'appearance',
  'appetite', 'apple', 'application', 'appointment', 'appreciation',
  'approach', 'appropriate', 'approval', 'april', 'architect',
  'architecture', 'area', 'argument', 'arm', 'army', 'arrangement',
  'array', 'arrival', 'arrow', 'art', 'article', 'artificial',
  'artist', 'artistic', 'aspect', 'aspiration', 'assault',
  'assembly', 'assertion', 'assessment', 'asset', 'assignment',
  'assistance', 'assistant', 'association', 'assumption', 'assurance',
  'atmosphere', 'atom', 'attachment', 'attack', 'attempt', 'attention',
  'attitude', 'attorney', 'attraction', 'attribute', 'auction',
  'audience', 'august', 'aunt', 'author', 'authority', 'autumn',
  'availability', 'average', 'award', 'awareness', 'awful',
  'edge', 'effect', 'effective', 'efficiency', 'efficient', 'effort',
  'egg', 'ego', 'eight', 'either', 'elaborate', 'elder', 'elderly',
  'election', 'electric', 'electrical', 'electricity', 'electron',
  'electronic', 'element', 'elementary', 'elephant', 'elevation',
  'elite', 'else', 'elsewhere', 'email', 'embarrassment', 'embassy',
  'embrace', 'emergence', 'emergency', 'emission', 'emotion',
  'emperor', 'emphasis', 'empire', 'employee', 'employer', 'employment',
  'empty', 'encounter', 'encouragement', 'end', 'ending', 'endless',
  'endorsement', 'enemy', 'energy', 'enforcement', 'engagement',
  'engine', 'engineer', 'engineering', 'enjoyment', 'enormous',
  'enough', 'enterprise', 'entertainment', 'enthusiasm', 'entire',
  'entirely', 'entity', 'entrance', 'entrepreneur', 'entry',
  'envelope', 'environment', 'environmental', 'episode', 'equal',
  'equality', 'equally', 'equation', 'equipment', 'equivalent',
  'era', 'error', 'escape', 'essay', 'essence', 'essential',
  'essentially', 'establishment', 'estate', 'estimate', 'eternal',
  'ethics', 'ethnic', 'european', 'evaluation', 'eve', 'even',
  'evening', 'event', 'eventually', 'every', 'everybody', 'everyday',
  'everyone', 'everything', 'everywhere', 'evidence', 'evil',
  'evolution', 'exact', 'exactly', 'exam', 'examination', 'example',
  'excellence', 'excellent', 'exception', 'excess', 'excessive',
  'exchange', 'excitement', 'exciting', 'excuse', 'executive',
  'exercise', 'exhibit', 'exhibition', 'exile', 'existence',
  'existing', 'exit', 'expansion', 'expectation', 'expedition',
  'expense', 'expensive', 'experience', 'experiment', 'experimental',
  'expert', 'expertise', 'explanation', 'exploration', 'explosion',
  'export', 'exposure', 'expression', 'extension', 'extensive',
  'extent', 'external', 'extra', 'extraordinary', 'extreme', 'extremely',
  'eye',
  'icon', 'idea', 'ideal', 'identical', 'identification', 'ideology',
  'ignorance', 'ill', 'illegal', 'illness', 'illusion', 'illustration',
  'image', 'imagination', 'imagine', 'immediate', 'immediately',
  'immigrant', 'immigration', 'immune', 'implementation', 'implication',
  'implicit', 'impression', 'impressive', 'improvement', 'incentive',
  'inch', 'incident', 'inclination', 'inclusion', 'income',
  'incomplete', 'increase', 'increasingly', 'incredible', 'incredibly',
  'independence', 'independent', 'index', 'indication', 'indicator',
  'individual', 'industrial', 'industry', 'inevitable', 'infant',
  'infection', 'infinite', 'inflation', 'influence', 'informal',
  'information', 'infrastructure', 'ingredient', 'inhabitant',
  'initial', 'initially', 'initiative', 'injection', 'injury',
  'injustice', 'ink', 'inn', 'innocence', 'innocent', 'innovation',
  'innovative', 'input', 'inquiry', 'insect', 'insertion', 'inside',
  'inspection', 'inspector', 'inspiration', 'installation', 'instance',
  'instant', 'instead', 'institute', 'institution', 'institutional',
  'instruction', 'instructor', 'instrument', 'insurance', 'intake',
  'integration', 'integrity', 'intellectual', 'intelligence',
  'intelligent', 'intense', 'intensity', 'intent', 'interaction',
  'interest', 'interested', 'interesting', 'interface', 'interference',
  'interior', 'internal', 'international', 'internet', 'interpretation',
  'intervention', 'interview', 'intimate', 'introduction', 'invasion',
  'invention', 'inventory', 'investigation', 'investigator',
  'investment', 'investor', 'invitation', 'involvement', 'iron',
  'irony', 'island', 'isolation', 'israeli', 'item',
  'object', 'objection', 'objective', 'obligation', 'observation',
  'observer', 'obstacle', 'occasion', 'occasional', 'occasionally',
  'occupation', 'ocean', 'october', 'odd', 'odds', 'offense',
  'offensive', 'offer', 'offering', 'office', 'officer', 'official',
  'offspring', 'oil', 'okay', 'old', 'olive', 'olympic', 'omission',
  'once', 'ongoing', 'onion', 'online', 'only', 'onset', 'opening',
  'opera', 'operation', 'operational', 'operator', 'opinion',
  'opponent', 'opportunity', 'opposite', 'opposition', 'option',
  'oral', 'orange', 'orbit', 'orchestra', 'order', 'ordinary',
  'organ', 'organic', 'organisation', 'organization', 'organizational',
  'orientation', 'origin', 'original', 'originally', 'other',
  'otherwise', 'ought', 'ounce', 'ourselves', 'outcome', 'outdoor',
  'outer', 'outfit', 'outlet', 'outline', 'outlook', 'output',
  'outrage', 'outside', 'outsider', 'outstanding', 'oven', 'overall',
  'overcome', 'overlook', 'overnight', 'overseas', 'overwhelming',
  'owner', 'ownership', 'oxygen',
  'ugly', 'ultimate', 'ultimately', 'umbrella', 'unable', 'uncertainty',
  'uncle', 'uncomfortable', 'unconscious', 'under', 'underlying',
  'understanding', 'undertaking', 'unemployment', 'unexpected',
  'unfair', 'unfortunately', 'unhappy', 'uniform', 'union', 'unique',
  'unit', 'united', 'unity', 'universal', 'universe', 'university',
  'unknown', 'unlikely', 'unnecessary', 'unpleasant', 'unusual',
  'unwilling', 'update', 'upgrade', 'upon', 'upper', 'upset',
  'upstairs', 'upward', 'urban', 'urge', 'urgency', 'urgent', 'usage',
  'use', 'used', 'useful', 'user', 'usual', 'usually', 'utility',
  'utilization',
];

// Words that start with consonant sounds despite vowel spelling (use "a")
const CONSONANT_SOUND_WORDS = [
  'unique', 'united', 'universal', 'universe', 'university', 'uniform',
  'union', 'unit', 'unity', 'uranium', 'urban', 'urge', 'urgent',
  'usage', 'use', 'used', 'useful', 'user', 'usual', 'usually',
  'utility', 'utmost', 'utopia', 'european', 'euphoria', 'eulogy',
  'eucalyptus', 'euphemism', 'one', 'once',
];

function fixArticles(text: string): string {
  // Fix "a" before vowel sounds → "an"
  let result = text;
  
  // Pattern: "a " followed by word starting with vowel
  result = result.replace(/\b[Aa]\s+([aeiouAEIOU]\w*)/g, (match, word) => {
    const lowerWord = word.toLowerCase();
    // Check if it's a consonant-sound exception
    if (CONSONANT_SOUND_WORDS.some(w => lowerWord.startsWith(w.toLowerCase()))) {
      return match; // Keep "a"
    }
    // It's a vowel sound, use "an"
    const article = match.charAt(0) === 'A' ? 'An' : 'an';
    return `${article} ${word}`;
  });
  
  // Fix "an" before consonant sounds → "a"
  result = result.replace(/\b[Aa]n\s+([bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]\w*)/g, (match, word) => {
    const lowerWord = word.toLowerCase();
    // Check if it's a vowel-sound exception (like "hour", "honest")
    const vowelSoundConsonants = ['hour', 'honest', 'honor', 'honour', 'heir', 'herb'];
    if (vowelSoundConsonants.some(w => lowerWord.startsWith(w))) {
      return match; // Keep "an"
    }
    // It's a consonant sound, use "a"
    const article = match.charAt(0) === 'A' ? 'A' : 'a';
    return `${article} ${word}`;
  });
  
  return result;
}

// ============================================
// 2. AWKWARD PHRASING REPLACEMENTS
// ============================================

const PHRASING_REPLACEMENTS: [RegExp, string][] = [
  // Preposition fixes
  [/quality to your/gi, 'quality in your'],
  [/quality to the/gi, 'quality in the'],
  [/show the world/gi, 'show to the world'],
  [/plays out most intensely in/gi, 'shows up most strongly in'],
  [/plays out in/gi, 'shows up in'],
  [/plays out most/gi, 'shows up most'],
  [/plays out/gi, 'shows up'],
  
  // Flow improvements
  [/in home and emotional/gi, 'in your home and emotional'],
  [/in home and family/gi, 'in your home and family'],
  [/in career and public/gi, 'in your career and public'],
  [/in relationships and/gi, 'in your relationships and'],
  
  // Redundancy
  [/very unique/gi, 'unique'],
  [/most unique/gi, 'unique'],
  [/completely unique/gi, 'unique'],
  [/very essential/gi, 'essential'],
  [/absolutely essential/gi, 'essential'],
  [/past history/gi, 'history'],
  [/future plans/gi, 'plans'],
  [/end result/gi, 'result'],
  [/free gift/gi, 'gift'],
  [/true fact/gi, 'fact'],
  [/reason is because/gi, 'reason is that'],
  [/reason why is/gi, 'reason is'],
  
  // Smoothing
  [/there is a tendency for you to/gi, 'you tend to'],
  [/you have a tendency to/gi, 'you tend to'],
  [/it is possible that you/gi, 'you may'],
  [/it seems like you/gi, 'you may'],
  [/it appears that you/gi, 'you may'],
];

function fixPhrasing(text: string): string {
  let result = text;
  for (const [pattern, replacement] of PHRASING_REPLACEMENTS) {
    result = result.replace(pattern, replacement);
  }
  return result;
}

// ============================================
// 3. TONE NORMALIZATION (Observational)
// ============================================

const TONE_REPLACEMENTS: [RegExp, string][] = [
  // "You are someone who" → "You tend to"
  [/You are someone who\s+/gi, 'You tend to '],
  [/You're someone who\s+/gi, 'You tend to '],
  
  // "You are a person who" → "You tend to"
  [/You are a person who\s+/gi, 'You tend to '],
  [/You're a person who\s+/gi, 'You tend to '],
  
  // "This means you are" → "This suggests you may be"
  [/This means you are\s+/gi, 'This suggests you may be '],
  [/This means that you are\s+/gi, 'This suggests you may be '],
  
  // "You are" at sentence start → soften
  [/^You are\s+(?!trying|noticing|aware|feeling|processing)/gim, 'You tend to be '],
  
  // "You will" → "You may"
  [/You will always/gi, 'You may often'],
  [/You will never/gi, 'You may rarely'],
  [/You will\s+/gi, 'You may '],
  
  // "You must" → "You may find yourself"
  [/You must\s+/gi, 'You may find yourself needing to '],
  
  // "You need to" → soften
  [/You need to\s+/gi, 'You may benefit from '],
  
  // "You should" → soften  
  [/You should\s+/gi, 'You might consider '],
  
  // "This is because" → soften
  [/This is because you are/gi, 'This may be because you tend to be'],
  [/This is because you/gi, 'This may be because you'],
  
  // Absolute statements → probabilistic
  [/always feel/gi, 'often feel'],
  [/never feel/gi, 'rarely feel'],
  [/always need/gi, 'often need'],
  [/never need/gi, 'rarely need'],
];

function normalizeTone(text: string): string {
  let result = text;
  for (const [pattern, replacement] of TONE_REPLACEMENTS) {
    result = result.replace(pattern, replacement);
  }
  return result;
}

// ============================================
// 4. MICRO FIXES
// ============================================

function microFixes(text: string): string {
  let result = text;
  
  // Fix double spaces
  result = result.replace(/\s{2,}/g, ' ');
  
  // Fix space before punctuation
  result = result.replace(/\s+([.,;:!?])/g, '$1');
  
  // Fix missing space after punctuation
  result = result.replace(/([.,;:!?])([A-Za-z])/g, '$1 $2');
  
  // Fix multiple punctuation
  result = result.replace(/\.{2,}/g, '.');
  result = result.replace(/,{2,}/g, ',');
  result = result.replace(/!{2,}/g, '!');
  result = result.replace(/\?{2,}/g, '?');
  
  // Fix spaces around em-dashes
  result = result.replace(/\s*—\s*/g, '—');
  result = result.replace(/\s*–\s*/g, '—'); // Convert en-dash to em-dash
  result = result.replace(/\s+-\s+/g, '—'); // Convert spaced hyphen to em-dash
  
  // Trim whitespace
  result = result.trim();
  
  // Ensure sentence starts with capital letter
  result = result.replace(/^([a-z])/, (match) => match.toUpperCase());
  
  // Fix common typos
  result = result.replace(/\bteh\b/gi, 'the');
  result = result.replace(/\byou'r\b/gi, "you're");
  result = result.replace(/\bits'\b/g, "it's");
  result = result.replace(/\bthier\b/gi, 'their');
  
  return result;
}

// ============================================
// 5. CONTEXT-SPECIFIC FIXES
// ============================================

function contextFixes(text: string): string {
  let result = text;
  
  // Fix "in your your" double possessive
  result = result.replace(/in your your/gi, 'in your');
  result = result.replace(/to your your/gi, 'to your');
  result = result.replace(/of your your/gi, 'of your');
  
  // Fix "the the" 
  result = result.replace(/\bthe the\b/gi, 'the');
  
  // Fix "a a" or "an an"
  result = result.replace(/\ba a\b/gi, 'a');
  result = result.replace(/\ban an\b/gi, 'an');
  
  // Fix broken possessives
  result = result.replace(/your's/gi, 'yours');
  result = result.replace(/it's own/gi, 'its own');
  
  // Fix "feelings feelings" type duplicates
  result = result.replace(/\b(\w+)\s+\1\b/gi, '$1');
  
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
 * 1. Article correction (a/an)
 * 2. Phrasing replacements
 * 3. Tone normalization
 * 4. Context-specific fixes
 * 5. Micro fixes (whitespace, punctuation)
 * 
 * @param text - Raw generated text
 * @returns Cleaned, polished text
 */
export function cleanText(text: string | null | undefined): string {
  if (!text) return '';
  
  let result = text;
  
  // Pipeline
  result = fixArticles(result);
  result = fixPhrasing(result);
  result = normalizeTone(result);
  result = contextFixes(result);
  result = microFixes(result);
  
  return result;
}

/**
 * Clean an array of text items.
 * Useful for cleaning lists of patterns, themes, etc.
 */
export function cleanTextArray(texts: string[] | null | undefined): string[] {
  if (!texts || !Array.isArray(texts)) return [];
  return texts.map(t => cleanText(t));
}

/**
 * Clean text in an object's string values.
 * Useful for cleaning API response objects.
 */
export function cleanTextObject<T extends Record<string, unknown>>(obj: T | null | undefined): T {
  if (!obj || typeof obj !== 'object') return obj as T;
  
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === 'string') {
      result[key] = cleanText(value);
    } else if (Array.isArray(value)) {
      result[key] = value.map(v => typeof v === 'string' ? cleanText(v) : v);
    } else {
      result[key] = value;
    }
  }
  return result as T;
}

export default cleanText;
