// ============================================
// PROGRAMMING PARTNERS - GATE POLARITY SYSTEM
// ============================================
// Silent layer that creates deeper tension
// Never exposed in UI - only used to sharpen synthesis
// Reveals the tension underneath the tension

export interface PolarityTension {
  gates: [number, number];
  theme: string;
  // Lived behavioral patterns
  swing: string;           // The back-and-forth the user actually lives
  relationship: string;    // How this shows up with others
  blindSpot: string;       // The overcorrection or compensation
  integration: string;     // What maturity/alignment looks like
  // Shorter punch versions
  tensionPunch: string;    // One-line tension hit
  blindSpotPunch: string;  // One-line blind spot hit
}

// ============================================
// COMPLETE PROGRAMMING PARTNER MAP (1-64)
// Each gate has exactly one partner across the wheel
// ============================================

export const PROGRAMMING_PARTNERS: { [gate: number]: number } = {
  1: 2,   2: 1,
  3: 50,  50: 3,
  4: 49,  49: 4,
  5: 35,  35: 5,
  6: 36,  36: 6,
  7: 13,  13: 7,
  8: 14,  14: 8,
  9: 16,  16: 9,
  10: 15, 15: 10,
  11: 12, 12: 11,
  17: 18, 18: 17,
  19: 33, 33: 19,
  20: 34, 34: 20,
  21: 48, 48: 21,
  22: 47, 47: 22,
  23: 43, 43: 23,
  24: 44, 44: 24,
  25: 46, 46: 25,
  26: 45, 45: 26,
  27: 28, 28: 27,
  29: 30, 30: 29,
  31: 41, 41: 31,
  32: 42, 42: 32,
  37: 40, 40: 37,
  38: 39, 39: 38,
  51: 57, 57: 51,
  52: 58, 58: 52,
  53: 54, 54: 53,
  55: 59, 59: 55,
  56: 60, 60: 56,
  61: 62, 62: 61,
  63: 64, 64: 63,
};

// ============================================
// POLARITY TENSION TRANSLATIONS
// Lived behavior, not theory
// ============================================

export const POLARITY_TENSIONS: { [key: string]: PolarityTension } = {
  // GATE 1 ↔ 2: Self-expression ↔ Receptive direction
  '1-2': {
    gates: [1, 2],
    theme: 'creative expression ↔ waiting for direction',
    swing: "You want to express something unique—but you're also waiting for the right direction to emerge. You swing between pushing your vision and surrendering to what wants to come through.",
    relationship: "You can be magnetically creative, but sometimes you hold back waiting for a sign that may not come the way you expect.",
    blindSpot: "You think you need to know your direction before you create. Sometimes creation IS the direction.",
    integration: "Express without needing to know where it leads. The direction reveals itself through the expression.",
    tensionPunch: "You want to create something—but keep waiting for permission that was never required.",
    blindSpotPunch: "You hold back your expression waiting for direction. The expression IS the direction."
  },
  
  // GATE 3 ↔ 50: Innovation/ordering ↔ Values/responsibility
  '3-50': {
    gates: [3, 50],
    theme: 'new beginnings ↔ established values',
    swing: "Part of you wants to start fresh, innovate, break the mold. Another part feels the weight of responsibility and what should be preserved.",
    relationship: "You can feel torn between disrupting what exists and protecting what matters.",
    blindSpot: "You think innovation and responsibility are opposites. They're not—responsible innovation is your actual path.",
    integration: "Start new things that honor what genuinely matters. Not all that's old deserves keeping; not all that's new deserves starting.",
    tensionPunch: "You want to start something new—but feel the weight of what you'd be disrupting.",
    blindSpotPunch: "You think you have to choose between innovation and responsibility. You don't."
  },
  
  // GATE 4 ↔ 49: Mental solutions ↔ Revolution/rejection
  '4-49': {
    gates: [4, 49],
    theme: 'logical answers ↔ emotional revolution',
    swing: "You want clean mental answers—but life keeps forcing decisions that aren't just logical. They're personal. Sometimes something in you has already said no before your mind caught up.",
    relationship: "You can analyze endlessly while your body has already rejected the situation.",
    blindSpot: "You think more analysis will solve it. Sometimes the real issue is that something in you has already said no.",
    integration: "Let your mind inform, not overrule. When your body rejects something, honor that—even if you can't explain why yet.",
    tensionPunch: "You keep analyzing what your gut already rejected.",
    blindSpotPunch: "More thinking won't solve what your body has already decided."
  },
  
  // GATE 5 ↔ 35: Fixed rhythms ↔ Change/experience
  '5-35': {
    gates: [5, 35],
    theme: 'patience/timing ↔ hunger for experience',
    swing: "You want movement, new experience, momentum. But life keeps teaching you that not everything should happen on your timeline. There's a rhythm you keep fighting.",
    relationship: "You can push for change when patience would serve better, or wait too long when it's time to move.",
    blindSpot: "You think waiting is passive. Real patience is active attunement to what's actually ready.",
    integration: "Move when the rhythm supports it. Not every experience is yours to have right now.",
    tensionPunch: "You want change now. Life keeps showing you there's a rhythm.",
    blindSpotPunch: "You mistake restlessness for readiness."
  },
  
  // GATE 6 ↔ 36: Intimacy/conflict ↔ Crisis/emotional experience
  '6-36': {
    gates: [6, 36],
    theme: 'emotional intimacy ↔ emotional crisis',
    swing: "You're drawn to emotional depth—but depth means navigating crisis, not avoiding it. You swing between craving connection and fearing the mess it creates.",
    relationship: "Intimacy requires moving through discomfort. You sometimes avoid the friction that would actually deepen the bond.",
    blindSpot: "You want closeness without crisis. That's not how emotional depth works.",
    integration: "Real intimacy includes the mess. The friction is part of the deepening.",
    tensionPunch: "You want depth—but keep avoiding the friction that creates it.",
    blindSpotPunch: "You can't get to intimacy by avoiding emotional crisis."
  },
  
  // GATE 7 ↔ 13: Leadership/direction ↔ Listening/secrets
  '7-13': {
    gates: [7, 13],
    theme: 'leading ↔ listening',
    swing: "Part of you wants to lead, to point the direction. Another part needs to listen first, to hold what others share before knowing where to point.",
    relationship: "You may lead before you've truly heard, or listen so long you never step into direction.",
    blindSpot: "You think leading means knowing. Sometimes leading means listening until direction emerges.",
    integration: "Listen until you know. Then lead without hesitation.",
    tensionPunch: "You want to lead—but haven't finished listening.",
    blindSpotPunch: "You direct before you've truly heard."
  },
  
  // GATE 8 ↔ 14: Contribution ↔ Power/resources
  '8-14': {
    gates: [8, 14],
    theme: 'making a contribution ↔ having resources to empower',
    swing: "You want to contribute something meaningful—but you also hold resources that respond to direction. The tension is between expressing yourself and empowering what genuinely calls you.",
    relationship: "You can give yourself away in contribution, or hoard resources that were meant to flow.",
    blindSpot: "You think contribution and power are separate. Your contribution IS your power when directed correctly.",
    integration: "Contribute what you have to what genuinely moves you. That's both expression and power.",
    tensionPunch: "You want to contribute—but hold back the resources that would make it real.",
    blindSpotPunch: "Your contribution requires your resources. They're not separate."
  },
  
  // GATE 9 ↔ 16: Focus/detail ↔ Enthusiasm/skills
  '9-16': {
    gates: [9, 16],
    theme: 'focused detail ↔ enthusiastic expression',
    swing: "Part of you wants to focus, perfect the detail. Another part wants to express, share the skill, channel enthusiasm. You swing between over-focusing and over-expressing.",
    relationship: "You may get lost in details others don't care about, or express before you've mastered the depth.",
    blindSpot: "You think focus and expression are sequential. They feed each other simultaneously.",
    integration: "Focus sharpens expression. Expression reveals what needs more focus.",
    tensionPunch: "You perfect endlessly or express prematurely.",
    blindSpotPunch: "Focus without expression becomes obsession. Expression without focus becomes noise."
  },
  
  // GATE 10 ↔ 15: Self-behavior ↔ Extremes/humanity
  '10-15': {
    gates: [10, 15],
    theme: 'being yourself ↔ accepting all of humanity',
    swing: "You want to be authentically yourself—but you also sense the full range of human behavior, including what you'd rather not accept. You swing between self-love and self-judgment.",
    relationship: "You may judge in others what you haven't accepted in yourself.",
    blindSpot: "You think being yourself means being consistent. Your humanity includes the extremes.",
    integration: "Accept your full range. Authenticity includes the parts you'd rather hide.",
    tensionPunch: "You want to be yourself—but reject the parts that don't fit your image.",
    blindSpotPunch: "You can't be authentic while hiding your extremes."
  },
  
  // GATE 11 ↔ 12: Ideas/stimulation ↔ Caution/expression
  '11-12': {
    gates: [11, 12],
    theme: 'endless ideas ↔ cautious expression',
    swing: "You have a lot to say—but not every thought is ready to be spoken. Part of you is full of ideas. Another part refuses to speak until the mood is right.",
    relationship: "You can overwhelm others with unfiltered ideas, or hold back so much nothing lands.",
    blindSpot: "You think all ideas deserve voice. Some need to mature in silence first.",
    integration: "Let ideas flow internally. Express only what's ready to land.",
    tensionPunch: "Your mind is full. Your voice is selective.",
    blindSpotPunch: "Not every idea deserves expression. Some need to ripen."
  },
  
  // GATE 17 ↔ 18: Opinions ↔ Correction
  '17-18': {
    gates: [17, 18],
    theme: 'having opinions vs seeing what is wrong',
    swing: "You form views and see flaws. The tension is between organizing understanding and dismantling what does not work. You swing between explaining and critiquing.",
    relationship: "You may come across as opinionated when you are actually trying to help, or critical when you are actually seeking clarity.",
    blindSpot: "You think your opinions help when sometimes they lecture. You think your corrections improve when sometimes they wound.",
    integration: "Offer views when asked. Correct what invites correction. Not everything needs your opinion or your fix.",
    tensionPunch: "You see what is wrong and have views about everything.",
    blindSpotPunch: "Not everything needs your opinion. Not everything needs your correction."
  },
  
  // GATE 19 ↔ 33: Wanting/needing ↔ Privacy/retreat
  '19-33': {
    gates: [19, 33],
    theme: 'reaching for connection ↔ withdrawing to process',
    swing: "You reach toward others, wanting connection, needing to be met. But you also need to retreat, to process alone, to have privacy. You swing between reaching and withdrawing.",
    relationship: "You may overwhelm others with your needs, or disappear when they need you.",
    blindSpot: "You think reaching is connecting. Sometimes retreat is what creates the space for real connection.",
    integration: "Reach when it's real. Retreat when you need to. Both serve connection.",
    tensionPunch: "You want closeness—then need to disappear.",
    blindSpotPunch: "Your reaching can push away. Your retreat can be the gift."
  },
  
  // GATE 20 ↔ 34: Present/now ↔ Power/response
  '20-34': {
    gates: [20, 34],
    theme: 'being present ↔ having power to respond',
    swing: "You can be completely present, articulating what's happening now. But presence without power is observation. Power without presence is force. You swing between watching and acting.",
    relationship: "You may observe when action is needed, or act when presence would serve.",
    blindSpot: "You think being present is enough. Sometimes presence requires power to manifest.",
    integration: "Be present AND powerful. Observe AND respond. They're not opposites.",
    tensionPunch: "You're present—but sometimes too present to act.",
    blindSpotPunch: "Observation without response is just watching."
  },
  
  // GATE 21 ↔ 48: Control ↔ Depth
  '21-48': {
    gates: [21, 48],
    theme: 'willful control ↔ patient depth',
    swing: "You want to control, to direct, to manage resources. But real mastery requires depth that can't be forced. You swing between controlling the surface and developing the depth.",
    relationship: "You may control what you haven't mastered, or avoid control because you don't feel deep enough.",
    blindSpot: "You think control is power. Sometimes depth is power, and control is just noise.",
    integration: "Develop depth first. Control follows naturally from genuine mastery.",
    tensionPunch: "You control what you haven't mastered.",
    blindSpotPunch: "Real authority comes from depth, not grip."
  },
  
  // GATE 22 ↔ 47: Emotional expression ↔ Mental realization
  '22-47': {
    gates: [22, 47],
    theme: 'emotional openness ↔ mental processing',
    swing: "You feel things deeply and can express with grace—when the mood is right. But you also process constantly, making sense of experiences that may never fully resolve. You swing between feeling and figuring out.",
    relationship: "You may express before you've understood, or think until you've lost the feeling.",
    blindSpot: "You think understanding will complete the feeling. Some things are felt, not figured out.",
    integration: "Feel what needs feeling. Understand what can be understood. Don't confuse them.",
    tensionPunch: "You process what needs to be felt. You express what needs to be understood.",
    blindSpotPunch: "Not everything resolves in the mind. Some experiences are lived, not solved."
  },
  
  // GATE 23 ↔ 43: Assimilation/speaking ↔ Inner knowing
  '23-43': {
    gates: [23, 43],
    theme: 'translating insight ↔ having insight',
    swing: "You know things uniquely—but translation is the work. You swing between holding insight that can't be shared and sharing before it's ready to land.",
    relationship: "You may seem strange when you share, or silent when you have something others need.",
    blindSpot: "You think the insight is clear because you see it. Translation is half the work.",
    integration: "Know first. Translate carefully. The right ears will hear.",
    tensionPunch: "You know things others don't see—but can't always make them see it.",
    blindSpotPunch: "Your insight needs translation. Not everyone speaks your frequency."
  },
  
  // GATE 24 ↔ 44: Rationalization ↔ Pattern recognition
  '24-44': {
    gates: [24, 44],
    theme: 'making sense of inspiration ↔ recognizing patterns',
    swing: "Inspiration comes, and you try to make it make sense. But you also see patterns from the past that inform what you're trying to understand. You swing between new understanding and familiar patterns.",
    relationship: "You may force new insight into old patterns, or miss the pattern behind the inspiration.",
    blindSpot: "You think new inspiration is brand new. Often it's an old pattern trying to upgrade.",
    integration: "Let inspiration inform the pattern. Let the pattern ground the inspiration.",
    tensionPunch: "You keep trying to understand what your body already recognizes.",
    blindSpotPunch: "The 'new insight' is often an old pattern in new clothes."
  },
  
  // GATE 25 ↔ 46: Innocence/spirit ↔ Body/serendipity
  '25-46': {
    gates: [25, 46],
    theme: 'universal love ↔ embodied experience',
    swing: "You carry a kind of spiritual innocence—but you also live in a body that demands presence. You swing between transcending experience and being fully in it.",
    relationship: "You may seem spiritually aloof, or so embodied you miss the larger pattern.",
    blindSpot: "You think spirit and body are separate. The body IS how spirit moves through the world.",
    integration: "Be in your body. That's how innocence becomes real, not abstract.",
    tensionPunch: "You reach for transcendence—but your path is through the body.",
    blindSpotPunch: "Spirit without body is concept. Body without spirit is survival."
  },
  
  // GATE 26 ↔ 45: Taming/selling ↔ Gathering/ruling
  '26-45': {
    gates: [26, 45],
    theme: 'convincing ↔ commanding',
    swing: "Part of you sells, convinces, influences through story. Another part commands, gathers, expects loyalty. You swing between persuading and demanding.",
    relationship: "You may oversell when your presence alone would command, or demand when persuasion would work.",
    blindSpot: "You think you need to convince when sometimes you just need to show up and lead.",
    integration: "Know when to sell, when to lead. Both have their place.",
    tensionPunch: "You convince when you could command. You demand when you could persuade.",
    blindSpotPunch: "Sometimes your presence is more convincing than your pitch."
  },
  
  // GATE 27 ↔ 28: Caring/nurturing ↔ Struggling for meaning
  '27-28': {
    gates: [27, 28],
    theme: 'nurturing others ↔ finding meaning through struggle',
    swing: "You care, nurture, feed what needs nourishment. But you also need struggle that matters—not just caretaking. You swing between giving care and needing purpose.",
    relationship: "You may nurture others while starving your own meaning, or fight for purpose while neglecting who needs you.",
    blindSpot: "You think caring is your purpose. Sometimes caring avoids the harder struggle you actually need.",
    integration: "Care for what matters. Struggle for what's worth it. Don't confuse comfort with purpose.",
    tensionPunch: "You care for others while avoiding your own meaningful struggle.",
    blindSpotPunch: "Nurturing can be an escape from the fight you're meant to have."
  },
  
  // GATE 29 ↔ 30: Saying yes ↔ Recognizing feelings
  '29-30': {
    gates: [29, 30],
    theme: 'commitment ↔ desire/passion',
    swing: "You commit. You say yes. But desire is fickle—what you commit to and what you feel passion for don't always align. You swing between over-committing and under-feeling.",
    relationship: "You may commit to things you don't actually feel, or feel deeply for things you won't commit to.",
    blindSpot: "You think commitment should follow desire. Sometimes commitment creates the feeling.",
    integration: "Commit to what you can feel through. Feel what deserves your commitment.",
    tensionPunch: "You commit to things you don't feel—or feel things you won't commit to.",
    blindSpotPunch: "Desire without commitment is fantasy. Commitment without feeling is endurance."
  },
  
  // GATE 31 ↔ 41: Influence/leadership ↔ Fantasy/contraction
  '31-41': {
    gates: [31, 41],
    theme: 'leading through influence ↔ imagining possibilities',
    swing: "You can influence, lead, set direction. But you also dream, imagine, feel the pull of possibility that hasn't materialized. You swing between leading what is and imagining what could be.",
    relationship: "You may lead toward fantasies that aren't grounded, or stay so practical you never inspire.",
    blindSpot: "You think leading and dreaming are separate. Vision without leadership is fantasy. Leadership without vision is management.",
    integration: "Dream AND lead. Let imagination inform direction. Let direction ground imagination.",
    tensionPunch: "You influence toward futures you haven't fully imagined—or imagine futures you never lead toward.",
    blindSpotPunch: "Vision without action is fantasy. Action without vision is just moving."
  },
  
  // GATE 32 ↔ 42: Continuity/instinct ↔ Growth/finishing
  '32-42': {
    gates: [32, 42],
    theme: 'preserving what works ↔ completing cycles',
    swing: "You sense what will endure, what's worth continuing. But you also need to complete cycles—let things end so new growth can begin. You swing between preserving and finishing.",
    relationship: "You may hold onto what's outlived its purpose, or end cycles before they've fully matured.",
    blindSpot: "You think preservation is safety. Sometimes the safe move is to let something complete.",
    integration: "Preserve what's truly alive. Complete what's truly done. Don't confuse continuity with fear of endings.",
    tensionPunch: "You hold on past completion—or end before maturity.",
    blindSpotPunch: "Not everything that could continue should continue."
  },
  
  // GATE 37 ↔ 40: Friendship/bargain ↔ Aloneness/boundaries
  '37-40': {
    gates: [37, 40],
    theme: 'loyalty/belonging ↔ independence/solitude',
    swing: "You want loyalty and closeness—but the second it feels one-sided, something in you pulls back hard. You swing between all-in belonging and complete withdrawal.",
    relationship: "You may overgive until resentment forces a boundary, then swing into isolation before finding balance.",
    blindSpot: "You call it commitment—but sometimes it's overgiving until you have no choice but to shut the door.",
    integration: "Give when there's mutual flow. Withdraw before resentment builds, not after.",
    tensionPunch: "You want closeness—then need space before you've said why.",
    blindSpotPunch: "Your resentment builds in silence. By the time you speak, you're already gone."
  },
  
  // GATE 38 ↔ 39: Fighting/stubbornness ↔ Provocation
  '38-39': {
    gates: [38, 39],
    theme: 'fighting for meaning ↔ provoking spirit',
    swing: "You fight for what matters—stubbornly, persistently. But you also provoke, test, push until something responds. You swing between stubborn resistance and deliberate provocation.",
    relationship: "You may fight battles that don't need fighting, or provoke reactions you're not prepared to handle.",
    blindSpot: "You think fighting proves it matters. Sometimes the fight IS the avoidance.",
    integration: "Fight for what's genuinely worth it. Provoke what's ready to awaken. Not everything deserves your stubbornness.",
    tensionPunch: "You fight for everything—or provoke to see what fights back.",
    blindSpotPunch: "Not every battle proves meaning. Some just prove stubbornness."
  },
  
  // GATE 51 ↔ 57: Shock/initiation ↔ Intuition/instinct
  '51-57': {
    gates: [51, 57],
    theme: 'shocking/initiating ↔ intuitive knowing',
    swing: "You can shock, initiate, wake people up. But you also know intuitively, in the moment, without drama. You swing between disruptive awakening and quiet knowing.",
    relationship: "You may shock when intuition would serve, or stay quiet when initiation is needed.",
    blindSpot: "You think shock creates awakening. Sometimes quiet knowing is the deeper initiation.",
    integration: "Shock when genuinely needed. Trust intuition when it's clear. Don't confuse drama with transformation.",
    tensionPunch: "You shock when you could simply know—or know without acting.",
    blindSpotPunch: "Not every awakening requires disruption. Some truth is quiet."
  },
  
  // GATE 52 ↔ 58: Stillness/concentration ↔ Vitality/joy
  '52-58': {
    gates: [52, 58],
    theme: 'stillness ↔ aliveness',
    swing: "Part of you wants to be still, concentrated, mountain-like. Another part pulses with vitality, joy, life force that wants to move. You swing between stillness and aliveness.",
    relationship: "You may seem too still when others need your energy, or too alive when stillness would serve.",
    blindSpot: "You think stillness is suppression. Real stillness is concentrated aliveness, not absence of life.",
    integration: "Be still AND alive. The mountain is not dead—it's concentrated.",
    tensionPunch: "You oscillate between frozen still and bursting alive.",
    blindSpotPunch: "Stillness isn't deadness. You can be concentrated AND vital."
  },
  
  // GATE 53 ↔ 54: Starting ↔ Ambition/rising
  '53-54': {
    gates: [53, 54],
    theme: 'beginning cycles ↔ climbing/ambition',
    swing: "You start things—new cycles, new beginnings. But you also want to rise, to ascend, to transform position. You swing between starting fresh and climbing higher.",
    relationship: "You may start things you never climb, or climb in cycles you never properly began.",
    blindSpot: "You think starting is enough. Some beginnings require the full climb to mean anything.",
    integration: "Start what you're willing to climb. Climb what you properly started.",
    tensionPunch: "You start what you don't finish climbing—or climb what you never properly started.",
    blindSpotPunch: "A beginning without ambition is just a false start."
  },
  
  // GATE 55 ↔ 59: Spirit/abundance ↔ Intimacy/breaking barriers
  '55-59': {
    gates: [55, 59],
    theme: 'emotional spirit ↔ breaking intimacy barriers',
    swing: "You carry emotional spirit, a sense of abundance or melancholy. But you also break barriers, push into intimacy, dissolve what separates. You swing between emotional depth and intimate penetration.",
    relationship: "You may dissolve barriers when containment would serve, or contain when breaking through is needed.",
    blindSpot: "You think your mood IS you. It's weather, not identity. Breaking barriers requires knowing the difference.",
    integration: "Feel your spirit. Break through when it's right. Your mood informs but doesn't decide.",
    tensionPunch: "Your emotional waves meet your drive to break through—not always at the right time.",
    blindSpotPunch: "You push for intimacy in waves. Others don't always know which wave they're getting."
  },
  
  // GATE 56 ↔ 60: Stimulation/storytelling ↔ Limitation/acceptance
  '56-60': {
    gates: [56, 60],
    theme: 'stimulation/ideas ↔ accepting limitations',
    swing: "You stimulate, tell stories, share ideas that spark. But you also know limitation, the creative power of constraint. You swing between infinite possibility and necessary limits.",
    relationship: "You may over-stimulate when limits would focus, or accept limits before exploring possibility.",
    blindSpot: "You think stimulation is creativity. Sometimes the limit IS the creative force.",
    integration: "Stimulate within limits. The constraint creates the shape.",
    tensionPunch: "You spark endlessly—or accept limits too soon.",
    blindSpotPunch: "Unlimited stimulation is noise. Creativity needs constraint."
  },
  
  // GATE 61 ↔ 62: Mystery/inner truth ↔ Details/expression
  '61-62': {
    gates: [61, 62],
    theme: 'inner knowing ↔ precise expression',
    swing: "You know things mysteriously, from within. But you also need precision, details, exact expression. You swing between inner mystery and outer articulation.",
    relationship: "You may stay in mystery when precision is needed, or over-detail when the knowing speaks for itself.",
    blindSpot: "You think mystery is vague. Real mystery is precise—it just can't be proven.",
    integration: "Know mysteriously. Express precisely. Both can be true.",
    tensionPunch: "You know without words—then struggle to find the exact ones.",
    blindSpotPunch: "Mystery isn't vagueness. The deepest knowing can be the most precise."
  },
  
  // GATE 63 ↔ 64: Doubt/logic ↔ Confusion/before completion
  '63-64': {
    gates: [63, 64],
    theme: 'logical doubt ↔ mental pressure/confusion',
    swing: "You doubt logically, questioning what doesn't add up. But you also carry mental pressure, confusion, images that haven't resolved. You swing between structured doubt and unstructured confusion.",
    relationship: "You may doubt what's actually clear, or confuse what could be clarified.",
    blindSpot: "You think doubt creates clarity. Sometimes doubt maintains confusion.",
    integration: "Doubt what deserves questioning. Let confusion resolve in its time. Not everything needs your skepticism.",
    tensionPunch: "You question everything—including what's already clear.",
    blindSpotPunch: "Your doubt doesn't always serve clarity. Sometimes it extends confusion."
  },
};

// ============================================
// GET POLARITY TENSION FOR A GATE
// ============================================

export function getPolarityTension(gate: number): PolarityTension | null {
  const partner = PROGRAMMING_PARTNERS[gate];
  if (!partner) return null;
  
  // Create sorted key (smaller gate first)
  const key = gate < partner ? `${gate}-${partner}` : `${partner}-${gate}`;
  return POLARITY_TENSIONS[key] || null;
}

// ============================================
// GET DOMINANT POLARITY FROM CHART DATA
// Prioritizes: Sun/Earth > Channels > Other activations
// ============================================

export interface PolarityInput {
  personalitySun?: number | { gate: number; line: number };
  personalityEarth?: number | { gate: number; line: number };
  designSun?: number | { gate: number; line: number };
  designEarth?: number | { gate: number; line: number };
  consciousGates?: number[];
  unconsciousGates?: number[];
  channels?: Array<{ gates?: string; centers?: string[] }>;
}

export interface RankedPolarity {
  tension: PolarityTension;
  priority: number;
  source: string;
  gateNumber: number;
}

export function getDominantPolarities(input: PolarityInput, maxResults: number = 2): RankedPolarity[] {
  const polarities: RankedPolarity[] = [];
  
  // Helper to extract gate number
  const getGate = (val: number | { gate: number; line: number } | undefined): number | null => {
    if (!val) return null;
    if (typeof val === 'number') return val;
    return val.gate;
  };
  
  // Priority 1: Personality Sun (highest - conscious identity)
  const pSun = getGate(input.personalitySun);
  if (pSun) {
    const tension = getPolarityTension(pSun);
    if (tension) {
      polarities.push({ tension, priority: 10, source: 'personality_sun', gateNumber: pSun });
    }
  }
  
  // Priority 2: Design Sun (body/unconscious driver)
  const dSun = getGate(input.designSun);
  if (dSun && dSun !== pSun) {
    const tension = getPolarityTension(dSun);
    if (tension) {
      polarities.push({ tension, priority: 9, source: 'design_sun', gateNumber: dSun });
    }
  }
  
  // Priority 3: Personality Earth (conscious grounding)
  const pEarth = getGate(input.personalityEarth);
  if (pEarth && pEarth !== pSun && pEarth !== dSun) {
    const tension = getPolarityTension(pEarth);
    if (tension) {
      polarities.push({ tension, priority: 8, source: 'personality_earth', gateNumber: pEarth });
    }
  }
  
  // Priority 4: Design Earth
  const dEarth = getGate(input.designEarth);
  if (dEarth && dEarth !== pSun && dEarth !== dSun && dEarth !== pEarth) {
    const tension = getPolarityTension(dEarth);
    if (tension) {
      polarities.push({ tension, priority: 7, source: 'design_earth', gateNumber: dEarth });
    }
  }
  
  // Priority 5: Gates in channels
  if (input.channels && input.channels.length > 0) {
    for (const channel of input.channels) {
      const gates = channel.gates?.match(/\d+/g)?.map(Number) || [];
      for (const gate of gates) {
        if (!polarities.find(p => p.gateNumber === gate)) {
          const tension = getPolarityTension(gate);
          if (tension) {
            polarities.push({ tension, priority: 6, source: 'channel', gateNumber: gate });
          }
        }
      }
    }
  }
  
  // Sort by priority and return top results
  polarities.sort((a, b) => b.priority - a.priority);
  
  // Deduplicate by tension (same gate pair can appear from different sources)
  const seen = new Set<string>();
  const unique: RankedPolarity[] = [];
  
  for (const p of polarities) {
    const key = `${Math.min(...p.tension.gates)}-${Math.max(...p.tension.gates)}`;
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(p);
    }
    if (unique.length >= maxResults) break;
  }
  
  return unique;
}

// ============================================
// INJECT POLARITY INTO SYNTHESIS SECTIONS
// Returns enhanced text with polarity punch
// ============================================

export function enhanceTensionWithPolarity(baseTension: string, polarities: RankedPolarity[]): string {
  if (polarities.length === 0) return baseTension;
  
  // Use the top polarity's tension punch
  const topPolarity = polarities[0];
  const punch = topPolarity.tension.tensionPunch;
  
  // Combine without bloating
  return `${baseTension} ${punch}`;
}

export function enhanceBlindSpotWithPolarity(baseBlindSpot: string, polarities: RankedPolarity[]): string {
  if (polarities.length === 0) return baseBlindSpot;
  
  const topPolarity = polarities[0];
  const punch = topPolarity.tension.blindSpotPunch;
  
  return `${baseBlindSpot} ${punch}`;
}

export function enhanceEdgeWithPolarity(baseEdge: string, polarities: RankedPolarity[]): string {
  if (polarities.length === 0) return baseEdge;
  
  const topPolarity = polarities[0];
  const integration = topPolarity.tension.integration;
  
  // Only add if it's short enough
  if (integration.length < 80) {
    return `${baseEdge} ${integration}`;
  }
  return baseEdge;
}

export function getPolarityBehavioralBullet(polarities: RankedPolarity[]): string | null {
  if (polarities.length === 0) return null;
  
  const topPolarity = polarities[0];
  return topPolarity.tension.swing.split('.')[0] + '.';
}

export function getPolarityRelationshipBullet(polarities: RankedPolarity[]): string | null {
  if (polarities.length === 0) return null;
  
  // Use second polarity if available for variety
  const polarity = polarities.length > 1 ? polarities[1] : polarities[0];
  return polarity.tension.relationship.split('.')[0] + '.';
}
