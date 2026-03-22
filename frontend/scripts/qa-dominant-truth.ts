/**
 * QA / Calibration Test Harness for Dominant Truth Engine
 * Master Astrologer v5 - Validation Pass
 * 
 * Run with: npx ts-node scripts/qa-dominant-truth.ts
 */

import {
  getDominantTruth,
  buildCollapsedInsights,
  buildLifeChapterAnalysis,
  buildAspectPatternAnalysis,
  getChartRuler,
  getDominantHouses,
} from '../services/astrology/astrologyInterpreter';

import {
  FullChartData,
  Timeframe,
  DominantTruth,
  CollapsedInsights,
} from '../services/astrology/astrologyTypes';

// Test chart data for peter@test.com (will be loaded from API)
let testChartData: FullChartData | null = null;

// ============================================
// TEST HARNESS
// ============================================

interface TestCase {
  timeframe: Timeframe;
  label: string;
}

interface TestResult {
  timeframe: Timeframe;
  label: string;
  dominantTruth: DominantTruth | null;
  collapsedInsights: CollapsedInsights;
  decisionTrace: DecisionTrace;
  benchmarkScores: BenchmarkScores;
  failureModes: FailureMode[];
}

interface DecisionTrace {
  dominantTheme: string | null;
  supportingThemes: string[];
  confidenceScore: number;
  lifeArea: string | null;
  pressureType: string | null;
  primaryTransitsUsed: string[];
  chapterInfluence: string | null;
  patternInfluence: string | null;
  houseRelevance: number[];
  chartRulerRelevance: string | null;
  sources: string[];
}

interface BenchmarkScores {
  whatIsHappening: number;  // 1-5
  whereInLife: number;      // 1-5
  whatGoingWrong: number;   // 1-5
  whyMattersToMe: number;   // 1-5
  usefulQuestion: number;   // 1-5
  notes: string[];
}

interface FailureMode {
  type: 'generic' | 'repetitive' | 'wrong_priority' | 'life_area_blur' | 'overweighting' | 'underweighting_recognition';
  description: string;
  severity: 'low' | 'medium' | 'high';
}

// ============================================
// RUN TESTS
// ============================================

function runTests(chartData: FullChartData): TestResult[] {
  const testCases: TestCase[] = [
    { timeframe: 'today', label: 'TODAY - Current' },
    { timeframe: 'week', label: 'THIS WEEK - Current' },
    { timeframe: 'month', label: 'THIS MONTH - Current' },
  ];
  
  const results: TestResult[] = [];
  
  // Pre-compute shared analysis
  const chapterAnalysis = buildLifeChapterAnalysis(chartData);
  const patternAnalysis = buildAspectPatternAnalysis(chartData);
  const chartRuler = getChartRuler(chartData);
  const dominantHouses = getDominantHouses(chartData);
  
  console.log('\n========================================');
  console.log('DOMINANT TRUTH QA TEST HARNESS');
  console.log('========================================\n');
  
  console.log('CHART CONTEXT:');
  console.log('- Chart Ruler:', chartRuler?.planet || 'None detected');
  console.log('- Dominant Houses:', dominantHouses.join(', ') || 'None detected');
  console.log('- Active Chapter:', chapterAnalysis.primaryChapter?.chapterType || 'None');
  console.log('- Chapter Strength:', chapterAnalysis.primaryChapter?.strengthScore || 0);
  console.log('- Dominant Pattern:', patternAnalysis.dominantPattern?.patternType || 'None');
  console.log('- Pattern Score:', patternAnalysis.dominantPattern?.priorityScore || 0);
  console.log('\n');
  
  for (const testCase of testCases) {
    const result = runSingleTest(chartData, testCase, chapterAnalysis, patternAnalysis, chartRuler, dominantHouses);
    results.push(result);
  }
  
  return results;
}

function runSingleTest(
  chartData: FullChartData,
  testCase: TestCase,
  chapterAnalysis: any,
  patternAnalysis: any,
  chartRuler: any,
  dominantHouses: number[]
): TestResult {
  const { timeframe, label } = testCase;
  
  // Run the engine
  const dominantTruth = getDominantTruth(chartData, chapterAnalysis, patternAnalysis, timeframe);
  const collapsedInsights = buildCollapsedInsights(chartData, chapterAnalysis, patternAnalysis, timeframe);
  
  // Build decision trace
  const decisionTrace: DecisionTrace = {
    dominantTheme: dominantTruth?.dominantTheme || null,
    supportingThemes: dominantTruth?.supportingThemes || [],
    confidenceScore: dominantTruth?.confidenceScore || 0,
    lifeArea: dominantTruth?.lifeArea || null,
    pressureType: dominantTruth?.pressureType || null,
    primaryTransitsUsed: dominantTruth?.sources?.slice(0, 3) || [],
    chapterInfluence: dominantTruth?.chapterType || null,
    patternInfluence: dominantTruth?.patternType || null,
    houseRelevance: dominantTruth?.houses || [],
    chartRulerRelevance: chartRuler?.planet || null,
    sources: dominantTruth?.sources || [],
  };
  
  // Score against benchmarks
  const benchmarkScores = scoreBenchmarks(collapsedInsights, dominantTruth, timeframe);
  
  // Detect failure modes
  const failureModes = detectFailureModes(collapsedInsights, dominantTruth, timeframe);
  
  return {
    timeframe,
    label,
    dominantTruth,
    collapsedInsights,
    decisionTrace,
    benchmarkScores,
    failureModes,
  };
}

function scoreBenchmarks(
  insights: CollapsedInsights,
  truth: DominantTruth | null,
  timeframe: Timeframe
): BenchmarkScores {
  const notes: string[] = [];
  let scores: BenchmarkScores = {
    whatIsHappening: 0,
    whereInLife: 0,
    whatGoingWrong: 0,
    whyMattersToMe: 0,
    usefulQuestion: 0,
    notes: [],
  };
  
  if (!truth || !insights.narrative) {
    return { ...scores, notes: ['No dominant truth detected'] };
  }
  
  const narrative = insights.narrative;
  
  // 1. What is the one main thing happening?
  if (narrative.headline && narrative.headline.length > 20) {
    scores.whatIsHappening = narrative.headline.includes('you') || narrative.headline.includes('You') ? 4 : 3;
    if (narrative.coreTruth && narrative.coreTruth.length > 100) {
      scores.whatIsHappening = 5;
    }
  } else {
    scores.whatIsHappening = 2;
    notes.push('Headline too short or vague');
  }
  
  // 2. Where in life is it happening?
  if (narrative.whereThisShowsUp && narrative.whereThisShowsUp.length > 30) {
    scores.whereInLife = 4;
    if (truth.houses && truth.houses.length > 0) {
      scores.whereInLife = 5;
    }
  } else {
    scores.whereInLife = 2;
    notes.push('Life area specificity weak');
  }
  
  // 3. What am I likely doing wrong?
  if (narrative.whatGoesWrong && narrative.whatGoesWrong.length > 50) {
    scores.whatGoingWrong = narrative.whatGoesWrong.includes('you') ? 5 : 4;
  } else {
    scores.whatGoingWrong = 2;
    notes.push('What goes wrong section weak');
  }
  
  // 4. Why does this matter more for me?
  if (truth.chapterType || truth.patternType) {
    scores.whyMattersToMe = 4;
    if (truth.confidenceScore >= 70) {
      scores.whyMattersToMe = 5;
    }
  } else if (truth.confidenceScore >= 50) {
    scores.whyMattersToMe = 3;
  } else {
    scores.whyMattersToMe = 2;
    notes.push('Personal relevance weak - no chapter/pattern alignment');
  }
  
  // 5. What is the one useful question?
  if (narrative.question && narrative.question.includes('?')) {
    scores.usefulQuestion = narrative.question.length > 30 ? 5 : 4;
  } else {
    scores.usefulQuestion = 2;
    notes.push('Question missing or weak');
  }
  
  scores.notes = notes;
  return scores;
}

function detectFailureModes(
  insights: CollapsedInsights,
  truth: DominantTruth | null,
  timeframe: Timeframe
): FailureMode[] {
  const modes: FailureMode[] = [];
  
  if (!truth || !insights.narrative) {
    modes.push({
      type: 'generic',
      description: 'No dominant truth detected - confidence below threshold',
      severity: 'high'
    });
    return modes;
  }
  
  const narrative = insights.narrative;
  
  // A. GENERIC TRUTH
  const genericPhrases = ['something', 'things', 'stuff', 'various', 'some'];
  if (genericPhrases.some(p => narrative.headline.toLowerCase().includes(p))) {
    modes.push({
      type: 'generic',
      description: `Headline contains generic phrase: "${narrative.headline}"`,
      severity: 'medium'
    });
  }
  
  // B. LIFE-AREA BLUR
  if (!truth.houses || truth.houses.length === 0) {
    modes.push({
      type: 'life_area_blur',
      description: 'No specific houses identified - life area is abstract',
      severity: 'medium'
    });
  }
  
  // C. OVERWEIGHTING
  if (truth.sources && truth.sources.length > 0) {
    const chapterCount = truth.sources.filter(s => s.includes('chapter')).length;
    const patternCount = truth.sources.filter(s => s.includes('pattern')).length;
    const transitCount = truth.sources.filter(s => !s.includes('chapter') && !s.includes('pattern')).length;
    
    if (chapterCount > transitCount && chapterCount > 1) {
      modes.push({
        type: 'overweighting',
        description: `Chapter logic may be overriding transits (chapter: ${chapterCount}, transit: ${transitCount})`,
        severity: 'low'
      });
    }
  }
  
  // D. UNDERWEIGHTING RECOGNITION
  if (truth.confidenceScore >= 70 && !narrative.recognitionLine) {
    modes.push({
      type: 'underweighting_recognition',
      description: `High confidence (${truth.confidenceScore}) but no recognition line`,
      severity: 'low'
    });
  }
  
  // E. Wrong timeframe tone
  if (timeframe === 'today' && narrative.coreTruth.includes('phase') && !narrative.coreTruth.includes('today')) {
    modes.push({
      type: 'wrong_priority',
      description: 'TODAY should feel immediate, but copy uses "phase" language',
      severity: 'low'
    });
  }
  
  if (timeframe === 'month' && narrative.timeframeContext.includes('today')) {
    modes.push({
      type: 'wrong_priority',
      description: 'MONTH should feel developmental, but context mentions "today"',
      severity: 'low'
    });
  }
  
  return modes;
}

// ============================================
// OUTPUT RESULTS
// ============================================

function outputResults(results: TestResult[]): void {
  console.log('\n========================================');
  console.log('A. TEST CASES RUN');
  console.log('========================================');
  results.forEach(r => console.log(`- ${r.label}`));
  
  console.log('\n========================================');
  console.log('B. DOMINANT TRUTH OUTPUTS');
  console.log('========================================');
  
  for (const result of results) {
    console.log(`\n--- ${result.label} ---`);
    if (result.collapsedInsights.narrative) {
      const n = result.collapsedInsights.narrative;
      console.log(`HEADLINE: ${n.headline}`);
      console.log(`CORE TRUTH: ${n.coreTruth.substring(0, 200)}...`);
      console.log(`WHERE THIS SHOWS UP: ${n.whereThisShowsUp}`);
      console.log(`WHAT GOES WRONG: ${n.whatGoesWrong.substring(0, 150)}...`);
      console.log(`QUESTION: ${n.question}`);
      console.log(`RECOGNITION LINE: ${n.recognitionLine || 'None'}`);
      console.log(`TIMEFRAME CONTEXT: ${n.timeframeContext}`);
    } else {
      console.log('No dominant truth detected');
    }
  }
  
  console.log('\n========================================');
  console.log('C. DECISION TRACES');
  console.log('========================================');
  
  for (const result of results) {
    console.log(`\n--- ${result.label} ---`);
    const d = result.decisionTrace;
    console.log(`Dominant Theme: ${d.dominantTheme || 'None'}`);
    console.log(`Supporting Themes: ${d.supportingThemes.join(', ') || 'None'}`);
    console.log(`Confidence Score: ${d.confidenceScore}`);
    console.log(`Life Area: ${d.lifeArea || 'None'}`);
    console.log(`Pressure Type: ${d.pressureType || 'None'}`);
    console.log(`Houses: ${d.houseRelevance.join(', ') || 'None'}`);
    console.log(`Primary Signals: ${d.primaryTransitsUsed.join(', ') || 'None'}`);
    console.log(`Chapter Influence: ${d.chapterInfluence || 'None'}`);
    console.log(`Pattern Influence: ${d.patternInfluence || 'None'}`);
    console.log(`Chart Ruler: ${d.chartRulerRelevance || 'None'}`);
    console.log(`All Sources: ${d.sources.join(', ') || 'None'}`);
  }
  
  console.log('\n========================================');
  console.log('D. BENCHMARK SCORES');
  console.log('========================================');
  
  for (const result of results) {
    console.log(`\n--- ${result.label} ---`);
    const b = result.benchmarkScores;
    console.log(`1. What is happening: ${b.whatIsHappening}/5`);
    console.log(`2. Where in life: ${b.whereInLife}/5`);
    console.log(`3. What going wrong: ${b.whatGoingWrong}/5`);
    console.log(`4. Why matters to me: ${b.whyMattersToMe}/5`);
    console.log(`5. Useful question: ${b.usefulQuestion}/5`);
    console.log(`TOTAL: ${b.whatIsHappening + b.whereInLife + b.whatGoingWrong + b.whyMattersToMe + b.usefulQuestion}/25`);
    if (b.notes.length > 0) {
      console.log(`Notes: ${b.notes.join('; ')}`);
    }
  }
  
  console.log('\n========================================');
  console.log('E. FAILURE MODES FOUND');
  console.log('========================================');
  
  const allModes: { result: string; mode: FailureMode }[] = [];
  for (const result of results) {
    for (const mode of result.failureModes) {
      allModes.push({ result: result.label, mode });
    }
  }
  
  if (allModes.length === 0) {
    console.log('No failure modes detected!');
  } else {
    for (const { result, mode } of allModes) {
      console.log(`\n[${mode.severity.toUpperCase()}] ${mode.type}`);
      console.log(`  Context: ${result}`);
      console.log(`  Description: ${mode.description}`);
    }
  }
  
  console.log('\n========================================');
  console.log('F. REPETITIVENESS CHECK');
  console.log('========================================');
  
  const themes = results.map(r => r.decisionTrace.dominantTheme).filter(Boolean);
  const uniqueThemes = [...new Set(themes)];
  console.log(`Themes across timeframes: ${themes.join(', ')}`);
  console.log(`Unique themes: ${uniqueThemes.length}/${themes.length}`);
  
  if (uniqueThemes.length === 1 && themes.length > 1) {
    console.log('⚠️ WARNING: Same theme repeated across all timeframes');
    console.log('   This may be appropriate if transits strongly converge, but check if framing differs.');
  } else if (uniqueThemes.length === themes.length) {
    console.log('✓ All timeframes show different dominant themes');
  }
  
  // Check if headlines differ
  const headlines = results.map(r => r.collapsedInsights.narrative?.headline).filter(Boolean);
  const uniqueHeadlines = [...new Set(headlines)];
  console.log(`\nHeadlines across timeframes: ${uniqueHeadlines.length} unique / ${headlines.length} total`);
  
  console.log('\n========================================');
  console.log('G. TIMEFRAME TONE VALIDATION');
  console.log('========================================');
  
  for (const result of results) {
    const n = result.collapsedInsights.narrative;
    if (!n) continue;
    
    console.log(`\n--- ${result.label} ---`);
    
    if (result.timeframe === 'today') {
      const isImmediate = n.timeframeContext.includes('today') || n.timeframeContext.includes('active');
      console.log(`Expected: immediate, behavioral`);
      console.log(`Context: "${n.timeframeContext}"`);
      console.log(`Assessment: ${isImmediate ? '✓ Feels immediate' : '⚠️ May not feel immediate enough'}`);
    }
    
    if (result.timeframe === 'week') {
      const isRecurring = n.timeframeContext.includes('keeps') || n.timeframeContext.includes('recurring') || n.timeframeContext.includes('thread');
      console.log(`Expected: recurring, pattern-based`);
      console.log(`Context: "${n.timeframeContext}"`);
      console.log(`Assessment: ${isRecurring ? '✓ Feels recurring' : '⚠️ May not emphasize pattern enough'}`);
    }
    
    if (result.timeframe === 'month') {
      const isDevelopmental = n.timeframeContext.includes('theme') || n.timeframeContext.includes('period') || n.timeframeContext.includes('shaping');
      console.log(`Expected: developmental, bigger arc`);
      console.log(`Context: "${n.timeframeContext}"`);
      console.log(`Assessment: ${isDevelopmental ? '✓ Feels developmental' : '⚠️ May not emphasize bigger arc'}`);
    }
  }
  
  console.log('\n========================================');
  console.log('H. FINAL SUMMARY');
  console.log('========================================');
  
  const totalBenchmark = results.reduce((sum, r) => 
    sum + r.benchmarkScores.whatIsHappening + r.benchmarkScores.whereInLife + 
    r.benchmarkScores.whatGoingWrong + r.benchmarkScores.whyMattersToMe + 
    r.benchmarkScores.usefulQuestion, 0
  );
  const maxBenchmark = results.length * 25;
  const percentage = Math.round((totalBenchmark / maxBenchmark) * 100);
  
  console.log(`Overall Benchmark Score: ${totalBenchmark}/${maxBenchmark} (${percentage}%)`);
  
  const highSeverityCount = allModes.filter(m => m.mode.severity === 'high').length;
  const mediumSeverityCount = allModes.filter(m => m.mode.severity === 'medium').length;
  const lowSeverityCount = allModes.filter(m => m.mode.severity === 'low').length;
  
  console.log(`Failure Modes: ${highSeverityCount} high, ${mediumSeverityCount} medium, ${lowSeverityCount} low`);
  
  if (percentage >= 80 && highSeverityCount === 0) {
    console.log('\n✓ RECOMMENDATION: Dominant Truth engine is working well');
  } else if (percentage >= 60 && highSeverityCount <= 1) {
    console.log('\n⚠️ RECOMMENDATION: Dominant Truth engine needs minor calibration');
  } else {
    console.log('\n✗ RECOMMENDATION: Dominant Truth engine needs significant calibration');
  }
}

// ============================================
// MOCK DATA FOR TESTING
// ============================================

// Since we can't fetch from API in this context, use mock data based on peter@test.com
const mockChartData: FullChartData = {
  success: true,
  natal: {
    planets: {
      Sun: { sign: 'Sagittarius', house: 3, degree: 15.5 },
      Moon: { sign: 'Scorpio', house: 2, degree: 8.3 },
      Mercury: { sign: 'Sagittarius', house: 3, degree: 22.1 },
      Venus: { sign: 'Capricorn', house: 4, degree: 5.7 },
      Mars: { sign: 'Aquarius', house: 4, degree: 18.2 },
      Jupiter: { sign: 'Taurus', house: 8, degree: 12.4 },
      Saturn: { sign: 'Sagittarius', house: 3, degree: 28.9 },
      Uranus: { sign: 'Sagittarius', house: 3, degree: 20.1 },
      Neptune: { sign: 'Capricorn', house: 4, degree: 4.8 },
      Pluto: { sign: 'Scorpio', house: 2, degree: 7.2 },
      'North Node': { sign: 'Aries', house: 7, degree: 15.0 },
      Chiron: { sign: 'Gemini', house: 9, degree: 10.5 },
      'South Node': { sign: 'Libra', house: 1, degree: 15.0 },
    },
    angles: {
      asc: { sign: 'Virgo', degree: 5.0 },
      mc: { sign: 'Gemini', degree: 2.0 },
    },
    aspects: [
      { point_a: 'Sun', point_b: 'Saturn', aspect_type: 'conjunction', orb: 2.5 },
      { point_a: 'Moon', point_b: 'Pluto', aspect_type: 'conjunction', orb: 1.1 },
      { point_a: 'Mercury', point_b: 'Uranus', aspect_type: 'conjunction', orb: 2.0 },
      { point_a: 'Venus', point_b: 'Neptune', aspect_type: 'conjunction', orb: 0.9 },
      { point_a: 'Mars', point_b: 'Saturn', aspect_type: 'square', orb: 3.2 },
      { point_a: 'Sun', point_b: 'Moon', aspect_type: 'sextile', orb: 4.1 },
      { point_a: 'Jupiter', point_b: 'Pluto', aspect_type: 'opposition', orb: 5.2 },
    ],
  },
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
    ],
    total_active_aspects: 10,
    moon_phase: 'waxing_gibbous',
  },
};

// ============================================
// MAIN
// ============================================

console.log('Loading chart data for peter@test.com...');
const results = runTests(mockChartData);
outputResults(results);
