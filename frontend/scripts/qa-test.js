/**
 * QA Test Script for Dominant Truth Engine - Direct Execution Version
 * Run with: node scripts/qa-test.js
 */

// Mock the interpreter functions inline for testing
// This allows us to test the logic without TypeScript compilation

const THEME_INDICATORS = {
  overcommitment: {
    houses: [6, 10, 1],
    planets: ['Saturn', 'Mars', 'Jupiter'],
    aspects: ['square', 'opposition'],
    chapters: ['saturn'],
    patterns: ['pressure_triangle', 'stellium']
  },
  avoidance: {
    houses: [12, 4, 8],
    planets: ['Neptune', 'Moon', 'Pluto'],
    aspects: ['square', 'opposition'],
    chapters: ['nodal', 'chiron'],
    patterns: ['opposition_axis']
  },
  premature_action: {
    houses: [1, 5, 9],
    planets: ['Mars', 'Jupiter', 'Uranus'],
    aspects: ['conjunction', 'square'],
    chapters: ['jupiter'],
    patterns: ['conjunction_chain']
  },
  delayed_decision: {
    houses: [7, 4, 12],
    planets: ['Saturn', 'Neptune', 'Moon'],
    aspects: ['opposition', 'square'],
    chapters: ['saturn', 'nodal'],
    patterns: ['opposition_axis', 'pressure_triangle']
  },
  emotional_suppression: {
    houses: [4, 8, 12],
    planets: ['Moon', 'Saturn', 'Pluto'],
    aspects: ['square', 'opposition', 'conjunction'],
    chapters: ['saturn', 'chiron'],
    patterns: ['pressure_triangle']
  },
  boundary_erosion: {
    houses: [7, 1, 12],
    planets: ['Neptune', 'Venus', 'Moon'],
    aspects: ['conjunction', 'opposition'],
    chapters: ['nodal', 'chiron'],
    patterns: ['conjunction_chain', 'flow_pattern']
  },
  communication_breakdown: {
    houses: [3, 7, 9],
    planets: ['Mercury', 'Saturn', 'Pluto'],
    aspects: ['square', 'opposition'],
    chapters: ['saturn'],
    patterns: ['pressure_triangle']
  },
  control_grip: {
    houses: [8, 10, 1],
    planets: ['Pluto', 'Saturn', 'Mars'],
    aspects: ['conjunction', 'square'],
    chapters: ['saturn'],
    patterns: ['conjunction_chain', 'pressure_triangle']
  },
  purpose_drift: {
    houses: [9, 10, 12],
    planets: ['Jupiter', 'Neptune', 'Saturn'],
    aspects: ['square', 'opposition'],
    chapters: ['nodal', 'jupiter'],
    patterns: ['opposition_axis']
  },
  overwhelm: {
    houses: [6, 12, 4],
    planets: ['Moon', 'Neptune', 'Saturn'],
    aspects: ['square', 'opposition', 'conjunction'],
    chapters: ['saturn', 'chiron'],
    patterns: ['stellium', 'pressure_triangle']
  }
};

const THEME_LIFE_AREAS = {
  overcommitment: "what you're carrying",
  avoidance: "what you're not looking at",
  premature_action: "where you're rushing",
  delayed_decision: "what you're putting off",
  emotional_suppression: "what you're holding in",
  boundary_erosion: "where you're giving yourself away",
  communication_breakdown: "what's not being said",
  control_grip: "what you're trying to control",
  purpose_drift: "your sense of direction",
  overwhelm: "how much you're holding"
};

// Mock chart data based on peter@test.com actual transits
const mockChartData = {
  transits: {
    strongest_hits: [
      { transit_point: 'Jupiter', natal_point: 'Saturn', aspect_type: 'square', orb: 0.3, natal_house: 3, applying: true },
      { transit_point: 'Pluto', natal_point: 'Mars', aspect_type: 'square', orb: 1.4, natal_house: 4, applying: false },
      { transit_point: 'Uranus', natal_point: 'Jupiter', aspect_type: 'square', orb: 1.0, natal_house: 8, applying: true },
      { transit_point: 'Neptune', natal_point: 'Chiron', aspect_type: 'conjunction', orb: 1.1, natal_house: 9, applying: true },
      { transit_point: 'Jupiter', natal_point: 'Sun', aspect_type: 'square', orb: 3.4, natal_house: 3, applying: false },
      { transit_point: 'Saturn', natal_point: 'Mercury', aspect_type: 'trine', orb: 2.1, natal_house: 3, applying: true },
      { transit_point: 'Pluto', natal_point: 'Venus', aspect_type: 'sextile', orb: 4.2, natal_house: 4, applying: false },
      { transit_point: 'Uranus', natal_point: 'Moon', aspect_type: 'opposition', orb: 3.8, natal_house: 2, applying: true },
      { transit_point: 'Neptune', natal_point: 'Mercury', aspect_type: 'square', orb: 4.5, natal_house: 3, applying: false },
      { transit_point: 'Saturn', natal_point: 'Sun', aspect_type: 'sextile', orb: 5.0, natal_house: 3, applying: true },
    ]
  },
  natal: {
    planets: {
      Sun: { sign: 'Sagittarius', house: 3 },
      Moon: { sign: 'Scorpio', house: 2 },
      Mercury: { sign: 'Sagittarius', house: 3 },
      Venus: { sign: 'Capricorn', house: 4 },
      Mars: { sign: 'Aquarius', house: 4 },
      Jupiter: { sign: 'Taurus', house: 8 },
      Saturn: { sign: 'Sagittarius', house: 3 },
    },
    angles: {
      asc: { sign: 'Virgo' }
    }
  }
};

// Simplified dominant truth detection
function getDominantTruth(chartData, chapter, pattern, timeframe) {
  const transits = chartData.transits.strongest_hits;
  const planets = chartData.natal.planets;
  
  // Score themes
  const themeScores = {};
  for (const category of Object.keys(THEME_INDICATORS)) {
    themeScores[category] = {
      category,
      score: 0,
      sources: [],
      houses: []
    };
  }
  
  // Score based on transits
  for (const hit of transits.slice(0, 10)) {
    const natalHouse = hit.natal_house || 0;
    const transitPlanet = hit.transit_point;
    const aspectType = hit.aspect_type;
    
    for (const [category, indicators] of Object.entries(THEME_INDICATORS)) {
      let hitScore = 0;
      
      if (indicators.houses.includes(natalHouse)) hitScore += 5;
      if (indicators.planets.includes(transitPlanet)) hitScore += 4;
      if (indicators.planets.includes(hit.natal_point)) hitScore += 4;
      if (indicators.aspects.includes(aspectType)) hitScore += 3;
      if (hit.orb <= 2) hitScore += 3;
      else if (hit.orb <= 5) hitScore += 1;
      
      if (hitScore > 0) {
        themeScores[category].score += hitScore;
        themeScores[category].sources.push(`${transitPlanet} ${aspectType} ${hit.natal_point}`);
        if (natalHouse && !themeScores[category].houses.includes(natalHouse)) {
          themeScores[category].houses.push(natalHouse);
        }
      }
    }
  }
  
  // Boost for chapter alignment
  if (chapter) {
    for (const [category, indicators] of Object.entries(THEME_INDICATORS)) {
      if (indicators.chapters.includes(chapter)) {
        themeScores[category].score += 10;
        themeScores[category].sources.push(`${chapter} chapter`);
      }
    }
  }
  
  // Boost for pattern alignment
  if (pattern) {
    for (const [category, indicators] of Object.entries(THEME_INDICATORS)) {
      if (indicators.patterns.includes(pattern)) {
        themeScores[category].score += 8;
        themeScores[category].sources.push(`${pattern} pattern`);
      }
    }
  }
  
  // Sort and select
  const sorted = Object.values(themeScores).sort((a, b) => b.score - a.score);
  const dominant = sorted[0];
  
  if (dominant.score < 15) return null;
  
  const confidence = Math.min(100, Math.round((dominant.score / 50) * 100));
  
  return {
    dominantTheme: dominant.category,
    supportingThemes: sorted.slice(1, 4).map(t => t.category),
    confidenceScore: confidence,
    lifeArea: THEME_LIFE_AREAS[dominant.category],
    houses: dominant.houses,
    sources: dominant.sources.slice(0, 5),
    score: dominant.score
  };
}

// Run tests
console.log('========================================');
console.log('DOMINANT TRUTH QA TEST - DECISION TRACE');
console.log('========================================\n');

const timeframes = ['today', 'week', 'month'];
const results = {};

// Simulate different chapter/pattern scenarios
const scenarios = [
  { chapter: null, pattern: null, label: 'No Chapter/Pattern' },
  { chapter: 'saturn', pattern: null, label: 'Saturn Chapter Active' },
  { chapter: 'jupiter', pattern: null, label: 'Jupiter Chapter Active' },
  { chapter: 'saturn', pattern: 'pressure_triangle', label: 'Saturn + Pressure Triangle' },
];

console.log('A. TEST CASES');
console.log('--------------------');
for (const tf of timeframes) {
  console.log(`- ${tf.toUpperCase()}`);
}
console.log('\nB. SCENARIOS TESTED');
console.log('--------------------');
for (const s of scenarios) {
  console.log(`- ${s.label}`);
}

console.log('\n========================================');
console.log('C. DECISION TRACES');
console.log('========================================\n');

for (const scenario of scenarios) {
  console.log(`\n--- SCENARIO: ${scenario.label} ---\n`);
  
  for (const timeframe of timeframes) {
    const truth = getDominantTruth(mockChartData, scenario.chapter, scenario.pattern, timeframe);
    
    console.log(`[${timeframe.toUpperCase()}]`);
    if (truth) {
      console.log(`  Dominant Theme: ${truth.dominantTheme}`);
      console.log(`  Raw Score: ${truth.score}`);
      console.log(`  Confidence: ${truth.confidenceScore}%`);
      console.log(`  Life Area: ${truth.lifeArea}`);
      console.log(`  Houses: ${truth.houses.join(', ') || 'None'}`);
      console.log(`  Supporting Themes: ${truth.supportingThemes.join(', ')}`);
      console.log(`  Sources: ${truth.sources.join('; ')}`);
    } else {
      console.log('  No dominant truth (score below threshold)');
    }
    console.log('');
  }
}

console.log('========================================');
console.log('D. FAILURE MODE ANALYSIS');
console.log('========================================\n');

// Check for repetitiveness
console.log('1. REPETITIVENESS CHECK');
console.log('-----------------------');
const baseResults = timeframes.map(tf => getDominantTruth(mockChartData, null, null, tf));
const themes = baseResults.filter(r => r).map(r => r.dominantTheme);
const unique = [...new Set(themes)];
console.log(`Themes across timeframes: ${themes.join(', ')}`);
console.log(`Unique: ${unique.length}/${themes.length}`);
if (unique.length === 1 && themes.length > 1) {
  console.log('⚠️ ISSUE: Same theme across all timeframes - may need timeframe-specific weighting');
} else {
  console.log('✓ OK: Theme varies or appropriate repetition');
}

// Check for generic issues
console.log('\n2. GENERICITY CHECK');
console.log('--------------------');
const baseResult = getDominantTruth(mockChartData, null, null, 'today');
if (baseResult) {
  const lifeArea = baseResult.lifeArea;
  if (lifeArea && lifeArea.includes("you're")) {
    console.log(`✓ Life area is specific: "${lifeArea}"`);
  } else {
    console.log(`⚠️ Life area may be vague: "${lifeArea}"`);
  }
  
  if (baseResult.houses.length > 0) {
    console.log(`✓ Houses identified: ${baseResult.houses.join(', ')}`);
  } else {
    console.log('⚠️ No specific houses - life area will be abstract');
  }
}

// Check for chapter overweighting
console.log('\n3. CHAPTER OVERWEIGHTING CHECK');
console.log('-------------------------------');
const noChapter = getDominantTruth(mockChartData, null, null, 'today');
const withChapter = getDominantTruth(mockChartData, 'saturn', null, 'today');

if (noChapter && withChapter) {
  console.log(`Without chapter: ${noChapter.dominantTheme} (score: ${noChapter.score})`);
  console.log(`With Saturn chapter: ${withChapter.dominantTheme} (score: ${withChapter.score})`);
  
  if (noChapter.dominantTheme !== withChapter.dominantTheme) {
    const scoreDiff = withChapter.score - noChapter.score;
    console.log(`Theme changed due to chapter (score boost: ${scoreDiff})`);
    if (scoreDiff > 15) {
      console.log('⚠️ Chapter may be overriding transit evidence');
    } else {
      console.log('✓ Chapter influence is balanced');
    }
  } else {
    console.log('✓ Theme unchanged - transits are strong enough');
  }
}

// Score distribution analysis
console.log('\n4. SCORE DISTRIBUTION');
console.log('---------------------');
const allThemeScores = {};
const transits = mockChartData.transits.strongest_hits;

for (const category of Object.keys(THEME_INDICATORS)) {
  allThemeScores[category] = 0;
  const indicators = THEME_INDICATORS[category];
  
  for (const hit of transits.slice(0, 10)) {
    const natalHouse = hit.natal_house || 0;
    if (indicators.houses.includes(natalHouse)) allThemeScores[category] += 5;
    if (indicators.planets.includes(hit.transit_point)) allThemeScores[category] += 4;
    if (indicators.planets.includes(hit.natal_point)) allThemeScores[category] += 4;
    if (indicators.aspects.includes(hit.aspect_type)) allThemeScores[category] += 3;
    if (hit.orb <= 2) allThemeScores[category] += 3;
    else if (hit.orb <= 5) allThemeScores[category] += 1;
  }
}

const sortedScores = Object.entries(allThemeScores)
  .sort(([,a], [,b]) => b - a)
  .slice(0, 5);

console.log('Top 5 themes by transit evidence:');
for (const [theme, score] of sortedScores) {
  console.log(`  ${theme}: ${score}`);
}

const topScore = sortedScores[0][1];
const secondScore = sortedScores[1][1];
const gap = topScore - secondScore;
console.log(`\nGap between #1 and #2: ${gap}`);
if (gap < 5) {
  console.log('⚠️ Close competition - dominant truth may be unstable');
} else {
  console.log('✓ Clear dominant theme');
}

console.log('\n========================================');
console.log('E. CALIBRATION RECOMMENDATIONS');
console.log('========================================\n');

// Based on analysis
const recommendations = [];

// Check threshold
if (baseResult && baseResult.score < 20) {
  recommendations.push({
    type: 'threshold',
    issue: 'Threshold may be too low',
    current: 15,
    recommended: 18,
    reason: 'Dominant truth at score 15 may include weak signals'
  });
}

// Check chapter weighting
if (withChapter && noChapter && withChapter.dominantTheme !== noChapter.dominantTheme) {
  const chapterBoost = withChapter.score - noChapter.score;
  if (chapterBoost > 12) {
    recommendations.push({
      type: 'weighting',
      issue: 'Chapter influence too strong',
      current: '+10 for chapter alignment',
      recommended: '+7 for chapter alignment',
      reason: 'Chapter is overriding transit evidence'
    });
  }
}

// Check house specificity
if (baseResult && baseResult.houses.length === 0) {
  recommendations.push({
    type: 'scoring',
    issue: 'House capture weak',
    current: 'Only capture houses with +5 score',
    recommended: 'Capture all houses from matched transits',
    reason: 'Life area statements need house context'
  });
}

// Check recognition line threshold
console.log('Recognition Line Analysis:');
console.log(`Current threshold: 70% confidence`);
console.log(`Test result confidence: ${baseResult?.confidenceScore || 0}%`);
if (baseResult?.confidenceScore >= 70) {
  console.log('✓ Recognition line would show');
} else if (baseResult?.confidenceScore >= 50) {
  recommendations.push({
    type: 'threshold',
    issue: 'Recognition line threshold may be too high',
    current: 70,
    recommended: 60,
    reason: 'Moderate confidence still deserves recognition'
  });
}

console.log('\nRecommendations:');
if (recommendations.length === 0) {
  console.log('✓ No critical calibration issues found');
} else {
  for (const r of recommendations) {
    console.log(`\n[${r.type.toUpperCase()}] ${r.issue}`);
    console.log(`  Current: ${r.current}`);
    console.log(`  Recommended: ${r.recommended}`);
    console.log(`  Reason: ${r.reason}`);
  }
}

console.log('\n========================================');
console.log('F. FINAL RECOMMENDATION');
console.log('========================================\n');

const issueCount = recommendations.length;
const hasHighSeverity = recommendations.some(r => r.type === 'threshold' || r.type === 'weighting');

if (issueCount === 0) {
  console.log('✓ RECOMMENDATION: Dominant Truth engine is working well');
  console.log('  The engine correctly identifies the strongest theme based on transit evidence.');
} else if (issueCount <= 2 && !hasHighSeverity) {
  console.log('⚠️ RECOMMENDATION: Minor calibration needed');
  console.log('  The engine is functional but could be tuned for better specificity.');
} else {
  console.log('✗ RECOMMENDATION: Calibration needed before deployment');
  console.log('  Address the issues above to improve accuracy.');
}

console.log('\nSINGLE BIGGEST ISSUE:');
if (recommendations.length > 0) {
  const biggest = recommendations[0];
  console.log(`${biggest.issue} - ${biggest.reason}`);
} else {
  console.log('None - engine is performing as expected');
}
