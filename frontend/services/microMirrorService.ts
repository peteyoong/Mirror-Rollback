/**
 * Micro-Mirror Response Generator
 * Generates short, contextual recognition + choice responses for journal entries
 */

// Pattern detection keywords for recognition
const PATTERNS = {
  slowingDown: ['slow', 'pause', 'breathe', 'rest', 'quiet', 'still', 'calm', 'peace'],
  overwhelm: ['overwhelm', 'too much', 'can\'t', 'exhausted', 'tired', 'drained', 'burned'],
  decision: ['decide', 'choice', 'option', 'should I', 'don\'t know if', 'torn', 'stuck'],
  relationship: ['they', 'he', 'she', 'partner', 'friend', 'family', 'mom', 'dad', 'relationship'],
  selfDoubt: ['doubt', 'wonder if', 'not sure', 'maybe I\'m', 'am I', 'enough', 'worth'],
  anger: ['angry', 'frustrated', 'annoyed', 'pissed', 'mad', 'furious', 'resentment'],
  sadness: ['sad', 'cry', 'miss', 'lost', 'grief', 'hurt', 'pain', 'empty'],
  anxiety: ['anxious', 'worried', 'nervous', 'fear', 'scared', 'panic', 'stress'],
  hope: ['hope', 'maybe', 'possible', 'want', 'wish', 'dream', 'excited'],
  change: ['change', 'different', 'new', 'start', 'begin', 'shift', 'move'],
  control: ['control', 'manage', 'handle', 'fix', 'solve', 'figure out'],
  letting_go: ['let go', 'release', 'accept', 'surrender', 'stop trying'],
  work: ['work', 'job', 'career', 'boss', 'project', 'deadline', 'meeting'],
  body: ['body', 'sleep', 'eat', 'health', 'sick', 'tired', 'energy'],
};

// Recognition templates by pattern
const RECOGNITIONS: { [key: string]: string[] } = {
  slowingDown: [
    'You slow down more here than you do anywhere else.',
    'Something in you needed to stop.',
    'You gave yourself permission to pause.',
  ],
  overwhelm: [
    'You\'re carrying more than you\'re letting on.',
    'There\'s a weight here you haven\'t put down.',
    'You\'ve been holding this longer than you realized.',
  ],
  decision: [
    'You already know which way you\'re leaning.',
    'The decision feels bigger than it probably is.',
    'You\'re looking for permission you don\'t actually need.',
  ],
  relationship: [
    'This is about them, but it\'s also about you.',
    'You\'re noticing something you\'ve been ignoring.',
    'There\'s a conversation you\'ve been avoiding.',
  ],
  selfDoubt: [
    'You\'re being harder on yourself than you\'d be on anyone else.',
    'The doubt is louder than the evidence.',
    'You already know you\'re capable of this.',
  ],
  anger: [
    'The anger is protecting something softer underneath.',
    'You\'re not as okay with this as you\'ve been pretending.',
    'Something crossed a line you didn\'t know you had.',
  ],
  sadness: [
    'You\'re letting yourself feel what you\'ve been holding.',
    'The sadness has been waiting for you to notice it.',
    'Something ended that you weren\'t ready to let go of.',
  ],
  anxiety: [
    'Your mind is running faster than the situation requires.',
    'You\'re preparing for something that might not happen.',
    'The worry is trying to protect you from uncertainty.',
  ],
  hope: [
    'You\'re letting yourself want something again.',
    'There\'s possibility here you haven\'t admitted out loud.',
    'Something is starting to shift.',
  ],
  change: [
    'You\'re in the middle of becoming something different.',
    'The old way isn\'t working anymore, and you know it.',
    'You\'re closer to the edge of change than you think.',
  ],
  control: [
    'You\'re trying to manage something that can\'t be managed.',
    'The grip is getting tighter, not looser.',
    'Control is the strategy, but it\'s not the solution.',
  ],
  letting_go: [
    'You\'re practicing something that doesn\'t come naturally.',
    'Letting go feels like losing, but it might be winning.',
    'You\'re learning the difference between giving up and releasing.',
  ],
  work: [
    'This is taking more from you than you\'re admitting.',
    'You\'re measuring yourself by the wrong metrics.',
    'The work matters, but so do you.',
  ],
  body: [
    'Your body has been trying to tell you something.',
    'You\'ve been overriding signals that deserve attention.',
    'The physical is connected to everything else.',
  ],
  default: [
    'Something about this mattered more than you expected.',
    'You needed to put this somewhere.',
    'There\'s more here than you\'ve said.',
  ],
};

// Choice templates by pattern
const CHOICES: { [key: string]: string[] } = {
  slowingDown: [
    'You can keep moving at your usual pace. Or you can notice what changes when you don\'t.',
  ],
  overwhelm: [
    'You can keep carrying it alone. Or you can set one thing down.',
  ],
  decision: [
    'You can keep weighing options. Or you can trust what you already know.',
  ],
  relationship: [
    'You can keep waiting for them to change. Or you can change what you accept.',
  ],
  selfDoubt: [
    'You can keep looking for proof you\'re enough. Or you can stop needing it.',
  ],
  anger: [
    'You can keep it contained. Or you can let it show you what matters.',
  ],
  sadness: [
    'You can push through it. Or you can let it move through you.',
  ],
  anxiety: [
    'You can keep bracing for impact. Or you can meet the moment when it arrives.',
  ],
  hope: [
    'You can protect yourself from disappointment. Or you can let yourself want this.',
  ],
  change: [
    'You can keep one foot in the old life. Or you can step all the way in.',
  ],
  control: [
    'You can tighten your grip. Or you can see what happens when you loosen it.',
  ],
  letting_go: [
    'You can hold on a little longer. Or you can find out what\'s on the other side.',
  ],
  work: [
    'You can keep proving yourself. Or you can trust that you already have.',
  ],
  body: [
    'You can override the signal again. Or you can listen this time.',
  ],
  default: [
    'You can let this pass. Or you can stay with it a little longer.',
  ],
};

/**
 * Detect the primary pattern in journal text
 */
const detectPattern = (text: string): string => {
  const lowerText = text.toLowerCase();
  let bestMatch = 'default';
  let highestScore = 0;

  for (const [pattern, keywords] of Object.entries(PATTERNS)) {
    let score = 0;
    for (const keyword of keywords) {
      if (lowerText.includes(keyword)) {
        score += 1;
      }
    }
    if (score > highestScore) {
      highestScore = score;
      bestMatch = pattern;
    }
  }

  return highestScore > 0 ? bestMatch : 'default';
};

/**
 * Get a deterministic but varied selection from array
 */
const selectFromArray = (arr: string[], seed: string): string => {
  // Use text length as simple seed for variety
  const index = seed.length % arr.length;
  return arr[index];
};

/**
 * Generate a Micro-Mirror response for journal text
 */
export const generateMicroMirrorResponse = (text: string): string => {
  // Skip generation for very short text
  if (!text || text.trim().length < 10) {
    return 'Something about this mattered more than you expected.';
  }

  const pattern = detectPattern(text);
  const recognitions = RECOGNITIONS[pattern] || RECOGNITIONS.default;
  const choices = CHOICES[pattern] || CHOICES.default;

  const recognition = selectFromArray(recognitions, text);
  
  // 70% chance to include choice line for longer entries
  const includeChoice = text.length > 50 && (text.length % 10) < 7;
  
  if (includeChoice) {
    const choice = selectFromArray(choices, text + 'choice');
    return `${recognition}\n${choice}`;
  }

  return recognition;
};

export default generateMicroMirrorResponse;
