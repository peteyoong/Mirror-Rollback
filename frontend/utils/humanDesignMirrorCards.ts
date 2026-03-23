// ============================================
// HUMAN DESIGN MIRROR LANGUAGE CARDS
// ============================================
// Transforms HD content into recognition-first, tension-based, behaviorally grounded cards
// Following Mirror Language: direct, emotionally recognizable, psychologically engaging

export interface MirrorCard {
  title: string;
  subtitle: string;
  recognition: string;
  tension: string;
  realLifeMoments: string[];
  truthShift: string;
  tryThisInstead: string;
  crossLink?: string; // Cross-linking to related elements (single sentence, subtle)
}

// ============================================
// TYPE CARDS
// ============================================

export const TYPE_MIRROR_CARDS: { [key: string]: MirrorCard } = {
  'Generator': {
    title: 'Generator',
    subtitle: 'The responsive force',
    recognition: "You have sustainable energy for the things that light you up—but that energy disappears when you force yourself through what doesn't.",
    tension: "The world treats you like you should initiate. But when you push without a genuine pull, you end up drained and frustrated, wondering why you can't just make things happen like everyone else seems to.",
    realLifeMoments: [
      "You said yes to something out of obligation and now you're dragging yourself through it",
      "You feel guilty resting even when your body has clearly stopped responding",
      "You start strong on a project but lose all momentum when the excitement fades",
      "You notice your energy is different depending on whether you chose something or it was assigned"
    ],
    truthShift: "Your frustration isn't a flaw. It's feedback. It tells you when you've overridden your gut response and committed to the wrong thing.",
    tryThisInstead: "Before saying yes, pause long enough to feel if your body actually responds. A real yes feels like a pull forward. Silence or heaviness means wait."
  },
  
  'Manifesting Generator': {
    title: 'Manifesting Generator',
    subtitle: 'The multi-passionate force',
    recognition: "You move fast, you pivot often, and you have more energy than most people know what to do with—as long as you're following what actually excites you.",
    tension: "You've been told you're inconsistent, that you don't finish things, that you need to pick one lane. But forcing yourself down dead-end tracks is what actually drains you.",
    realLifeMoments: [
      "You start five things and only finish two, and the guilt is worse than the incomplete projects",
      "You know in your gut something is done before it looks done to others",
      "You skip steps that seem obvious to you but confuse everyone else",
      "You feel trapped when you have to follow a process that doesn't match your rhythm"
    ],
    truthShift: "Completion isn't about finishing everything. It's about extracting what was yours to take and moving on when the energy shifts.",
    tryThisInstead: "Notice when the fire goes out. If the energy is gone and won't come back, that's information—not failure. Trust the pivot."
  },
  
  'Projector': {
    title: 'Projector',
    subtitle: 'The recognized guide',
    recognition: "You see what others miss. You understand systems, people, dynamics—often better than they understand themselves. But that insight only lands when someone actually asks for it.",
    tension: "You give and give, hoping to be seen. But unsolicited guidance falls flat, and then comes the bitterness: why does no one appreciate what you offer?",
    realLifeMoments: [
      "You share a solution and watch it get ignored—then watch someone else say the same thing and get credit",
      "You feel exhausted from managing dynamics that aren't yours to manage",
      "You work twice as hard to prove your value because you don't feel naturally recognized",
      "You hold back what you see because you're tired of not being heard"
    ],
    truthShift: "Your value doesn't come from giving endlessly. It comes from being in the right rooms with people who genuinely see you.",
    tryThisInstead: "Before offering guidance, ask yourself: was I invited? If not, wait. Recognition will come, but only from the places that deserve your energy."
  },
  
  'Manifestor': {
    title: 'Manifestor',
    subtitle: 'The initiating force',
    recognition: "You have the power to start things that didn't exist before. Ideas become real when you move. But that power can feel isolating when others don't understand your speed.",
    tension: "You want to just act. But acting without warning creates friction—people feel blindsided, and then you feel controlled by their reactions.",
    realLifeMoments: [
      "You made a decision and everyone got upset, even though it was the right call",
      "You feel suffocated when you have to explain or justify your direction",
      "You withdraw because engaging feels like more resistance than it's worth",
      "You notice people either love your energy or actively push against it"
    ],
    truthShift: "Informing isn't asking permission. It's clearing the path so your power can move without unnecessary friction.",
    tryThisInstead: "Before you act, pause to let others know what's coming. Not because you need approval—but because informed people resist less."
  },
  
  'Reflector': {
    title: 'Reflector',
    subtitle: 'The environment reader',
    recognition: "You take in everything. You feel the room, the people, the energy—often more intensely than anyone else. That sensitivity is your intelligence, but it's also your vulnerability.",
    tension: "You absorb so much that you sometimes lose yourself. Whose feelings are these? Whose opinions? It takes time to know what's actually yours.",
    realLifeMoments: [
      "You feel completely different depending on who you're with",
      "You struggle to know if a decision is right because you keep seeing it from every angle",
      "You stayed too long in an environment that was slowly depleting you",
      "You make a fast decision and regret it within days"
    ],
    truthShift: "You're not designed for instant clarity. You're designed to gather perspectives over time. That's not indecision—it's thoroughness.",
    tryThisInstead: "Give yourself a full lunar cycle before major decisions. What's still true after 28 days is probably yours."
  }
};

// ============================================
// AUTHORITY CARDS
// ============================================

export const AUTHORITY_MIRROR_CARDS: { [key: string]: MirrorCard } = {
  'Emotional': {
    title: 'Emotional Authority',
    subtitle: 'Clarity through waves',
    recognition: "You don't get clarity in the moment. You feel your way into decisions, riding waves of emotion until something settles.",
    tension: "The world rewards fast decisions. But when you act from a peak or a valley, you commit to things that look different when the wave passes.",
    realLifeMoments: [
      "You said yes when you felt high and woke up wondering what you agreed to",
      "You said no in a low moment and later questioned if you pushed away something real",
      "You keep looping on a decision because nothing feels stable yet",
      "People pressure you for answers and you give them just to stop the pressure"
    ],
    truthShift: "Your clarity isn't in the high or the low. It's in the settling—that neutral place where the wave has passed and the truth remains.",
    tryThisInstead: "Sleep on it. Then sleep on it again. If it still feels right when you're calm, that's your answer."
  },
  
  'Sacral': {
    title: 'Sacral Authority',
    subtitle: 'Clarity through gut response',
    recognition: "Your body knows before your mind catches up. There's a pull toward or a pull away, and it happens in the moment—not through analysis.",
    tension: "You've learned to override your gut with logic. But every time you talk yourself into something your body said no to, you end up drained and stuck.",
    realLifeMoments: [
      "You feel an instant response but ignore it because you can't explain it",
      "You commit to something reasonable that your body never agreed to",
      "You say 'I don't know' when someone asks how you feel, because it's hard to translate gut knowing into words",
      "You notice frustration building and realize it started when you stopped listening"
    ],
    truthShift: "Your gut doesn't need reasons. It responds to life directly. Learning to trust it is learning to trust yourself.",
    tryThisInstead: "When asked something, notice your body's first reaction—before your mind explains it away. That first hit is usually right."
  },
  
  'Splenic': {
    title: 'Splenic Authority',
    subtitle: 'Clarity through intuition',
    recognition: "Your knowing arrives in a flash—subtle, quiet, once. It doesn't argue or repeat itself. If you miss it, it's gone.",
    tension: "You second-guess the hit because it doesn't come with proof. By the time you've reasoned through it, the moment has passed and the clarity with it.",
    realLifeMoments: [
      "You had a bad feeling about something but couldn't explain why, so you ignored it",
      "You made a snap decision that turned out to be exactly right",
      "You hesitated just long enough to lose access to what you knew",
      "You notice safety or danger in situations before others do"
    ],
    truthShift: "Your intuition doesn't wait for you to catch up. It speaks once, in the moment, and trusts you to listen.",
    tryThisInstead: "Practice catching the first quiet knowing before your mind starts analyzing. The more you notice it, the louder it seems."
  },
  
  'Ego': {
    title: 'Ego Authority',
    subtitle: 'Clarity through willpower',
    recognition: "You know what you want—and when you really want it, you can move mountains. But that willpower only sustains what your heart is genuinely in.",
    tension: "When you commit to things your heart doesn't actually want, your will runs dry. Then promises break, and you wonder why you can't follow through.",
    realLifeMoments: [
      "You made a commitment that seemed right but drained you completely",
      "You feel unstoppable when you're working toward something you truly want",
      "You've broken promises because the energy just wasn't there",
      "You notice the difference between 'I should want this' and 'I actually want this'"
    ],
    truthShift: "Your willpower isn't unlimited. It only refuels when it's pointed at something real. Check if you actually want it before you commit.",
    tryThisInstead: "Ask yourself honestly: Do I want this? If the answer isn't clear, don't promise. Your integrity depends on genuine desire."
  },
  
  'Self-Projected': {
    title: 'Self-Projected Authority',
    subtitle: 'Clarity through voice',
    recognition: "You find clarity by hearing yourself speak. Your truth emerges through expression, not isolated thought.",
    tension: "You think you should figure things out alone. But decisions made in your head often miss what becomes obvious the moment you say it out loud.",
    realLifeMoments: [
      "You started talking about a decision and suddenly knew the answer mid-sentence",
      "You feel stuck when you can't find someone to talk things through with",
      "You notice you're clearer after a conversation than before it",
      "You've said yes to something and immediately heard how wrong it sounded"
    ],
    truthShift: "You're not meant to figure everything out in silence. Your voice is part of your processing, not just the output.",
    tryThisInstead: "Find someone you trust and talk through the decision—not for their advice, but to hear yourself. The clarity is in your own voice."
  },
  
  'Mental': {
    title: 'Mental/Environmental Authority',
    subtitle: 'Clarity through perspective',
    recognition: "Your clarity doesn't come from inside. It comes from environment, conversation, and seeing the situation from multiple angles before deciding.",
    tension: "You feel pressure to just know. But your wisdom isn't about having answers—it's about gathering perspectives until the right path becomes obvious.",
    realLifeMoments: [
      "You feel clearer about decisions in certain places than others",
      "You've talked through the same thing with different people and kept changing your mind",
      "You notice your thinking shifts depending on who you're with",
      "You feel confused when asked to decide on the spot"
    ],
    truthShift: "You're designed to be influenced by your environment—not as weakness, but as intelligence. Different settings reveal different truths.",
    tryThisInstead: "Discuss important decisions in multiple settings with different people. Watch for where your clarity consistently appears."
  },
  
  'Lunar': {
    title: 'Lunar Authority',
    subtitle: 'Clarity through cycles',
    recognition: "Your clarity unfolds over time—about 28 days. You need to feel a decision across a full cycle before you really know.",
    tension: "The world wants answers now. But when you rush, you commit before you've seen all the angles, and regret follows.",
    realLifeMoments: [
      "You felt one way about something last week and completely different this week",
      "You've made fast decisions that felt wrong within days",
      "You notice patterns when you track how your feelings change over weeks",
      "You feel most clear about things you've been sitting with for a while"
    ],
    truthShift: "Waiting isn't indecision. It's how you access wisdom that others can't reach. What stays true across the whole cycle is yours to trust.",
    tryThisInstead: "For major decisions, wait a full lunar cycle. Track how you feel each week. The answer that persists is the real one."
  },
  
  'None': {
    title: 'No Inner Authority',
    subtitle: 'Clarity through environment',
    recognition: "You don't have a fixed internal compass—and that's by design. Your clarity comes from being in the right places with the right people.",
    tension: "You keep looking inside for answers that aren't there. The searching just creates more confusion.",
    realLifeMoments: [
      "You feel clear in some environments and completely lost in others",
      "You've made decisions based on where you were that you later questioned",
      "You notice you become different versions of yourself depending on context",
      "You feel pressure to have a consistent internal sense of direction"
    ],
    truthShift: "You're not broken. You're designed to be shaped by your surroundings. The question isn't 'what do I feel inside?' but 'where do I belong?'",
    tryThisInstead: "Pay attention to which environments bring you clarity. Choose those places. The answers follow the right setting."
  }
};

// ============================================
// PROFILE CARDS
// ============================================

export const PROFILE_MIRROR_CARDS: { [key: string]: MirrorCard } = {
  '1/3': {
    title: '1/3 Profile',
    subtitle: 'The Investigative Experimenter',
    recognition: "You need to understand things deeply before you can move forward—but you also can't help testing everything through direct experience.",
    tension: "You want certainty before acting, but certainty only comes after you've tried and failed a few times. The gap between needing to know and having to try creates constant friction.",
    realLifeMoments: [
      "You research something exhaustively but still feel unprepared when it's time to act",
      "You've learned more from what went wrong than from what went right",
      "You feel frustrated when people expect you to commit before you've tested it yourself",
      "You notice you're naturally skeptical until you've proven something in your own experience"
    ],
    truthShift: "Your path isn't study then success. It's study, try, adjust, try again. The foundation you're building comes from lived trial, not just theory.",
    tryThisInstead: "Accept that failure is part of your research process. What you discover through bumping into things is what becomes unshakeable."
  },
  
  '1/4': {
    title: '1/4 Profile',
    subtitle: 'The Investigative Networker',
    recognition: "You need deep foundations—solid understanding before you move. But your impact flows through relationships, not isolation.",
    tension: "You want to be thorough and prepared, but your influence depends on connection. Going too deep alone can disconnect you from the network that spreads your work.",
    realLifeMoments: [
      "You feel most confident sharing what you've studied thoroughly",
      "You influence others more than you realize through your close relationships",
      "You get frustrated when people oversimplify what you've taken time to understand",
      "You notice your opportunities come through people you know, not random chance"
    ],
    truthShift: "Your depth isn't meant to stay private. It's meant to be transmitted through the relationships you already have.",
    tryThisInstead: "Share what you're learning with your close network as you learn it. Your influence isn't about reaching strangers—it's about deepening what you already have."
  },
  
  '2/4': {
    title: '2/4 Profile',
    subtitle: 'The Natural Networker',
    recognition: "You have natural talents you don't fully see in yourself. Others notice your gifts before you do—and your influence flows through the relationships that call those gifts out.",
    tension: "You need alone time to develop your abilities, but your impact requires being seen. The dance between hermit mode and network mode can feel exhausting.",
    realLifeMoments: [
      "Someone asks you to do something you didn't know you were good at",
      "You feel drained when you've been 'on' for too long without retreat time",
      "You notice your opportunities come through friends and connections, not applications",
      "You resist being seen for something you haven't fully claimed in yourself"
    ],
    truthShift: "You don't need to build your gifts from scratch. You need to let others call them out of you while protecting time to integrate.",
    tryThisInstead: "Honor both modes. Time alone develops what's natural. Relationships create the invitations that activate it."
  },
  
  '2/5': {
    title: '2/5 Profile',
    subtitle: 'The Natural Problem-Solver',
    recognition: "You have abilities you take for granted—and people project onto you that you can solve problems you never claimed to handle.",
    tension: "You're called out of your hermit mode to help, but the projections can feel heavy. People expect you to be their answer, and when you're not, it can damage trust.",
    realLifeMoments: [
      "Strangers expect things from you that feel unearned",
      "You need significant alone time to stay grounded",
      "You've been blamed for not meeting expectations you never agreed to",
      "You notice you're good at things you never practiced—it just comes naturally"
    ],
    truthShift: "Your natural gifts will be seen whether you claim them or not. The projections aren't your responsibility, but how you manage them is.",
    tryThisInstead: "Be selective about which calls you answer. When you show up for the right situations, you deliver. When you show up for projections, everyone loses."
  },
  
  '3/5': {
    title: '3/5 Profile',
    subtitle: 'The Experimental Problem-Solver',
    recognition: "Your life is a laboratory. You learn by trying things that might not work—and others watch your experiments and expect you to have answers.",
    tension: "You carry both the weight of trial-and-error and the projections of being seen as a fixer. When your experiments fail, it can feel public and heavy.",
    realLifeMoments: [
      "You've had more false starts than most people you know",
      "You notice people look to you during crises, expecting practical wisdom",
      "You feel misunderstood when your process looks like chaos to others",
      "You've discovered solutions that only came through getting it wrong first"
    ],
    truthShift: "Your failures aren't shameful. They're research. And the practical wisdom people seek from you is built on those bumpy roads.",
    tryThisInstead: "Stop apologizing for the experiments that didn't work. They're the reason you have something real to offer."
  },
  
  '3/6': {
    title: '3/6 Profile',
    subtitle: 'The Experimental Role Model',
    recognition: "Your early life was chaotic—full of trial, error, and figuring things out the hard way. Now you're moving toward a role where others look to you for wisdom.",
    tension: "You carry the scars of a bumpy past while being expected to model something higher. The gap between where you've been and where you're heading can feel impossible.",
    realLifeMoments: [
      "You feel like you're still recovering from experiments that went sideways",
      "You notice a shift happening—less chaos, more perspective",
      "People look to you for guidance based on what you've survived",
      "You hesitate to lead because you remember how many times you got it wrong"
    ],
    truthShift: "Your messy past isn't a disqualification. It's your credential. Real wisdom comes from lived experience, not theory.",
    tryThisInstead: "Trust the shift that's happening. You don't have to be perfect to be someone worth watching. Your journey is the point."
  },
  
  '4/6': {
    title: '4/6 Profile',
    subtitle: 'The Networked Role Model',
    recognition: "Your influence flows through your relationships, and over time, you're becoming someone others observe and learn from—whether you intend to or not.",
    tension: "You rely on your network to create opportunity, but as you mature, you're being pushed toward a more visible role. Staying small feels safe but incomplete.",
    realLifeMoments: [
      "Your opportunities have always come through people you know",
      "You notice a pull toward stepping into something more public",
      "You feel protective of your close relationships but aware they're watching",
      "You've shifted from being in the mix to being slightly above it"
    ],
    truthShift: "Your influence isn't about performing leadership. It's about letting your network see how you live—and that naturally creates following.",
    tryThisInstead: "Keep your close relationships strong. Let them witness your evolution. Your role model energy is relational, not performative."
  },
  
  '4/1': {
    title: '4/1 Profile',
    subtitle: 'The Networked Investigator',
    recognition: "Your influence flows through relationships, but underneath that connection is a need for deep, secure foundations. You share only what you've fully understood.",
    tension: "Your network is your lifeline—but you also need solidity before you transmit. Sharing before you're ready destabilizes your base.",
    realLifeMoments: [
      "You feel most confident speaking about things you've thoroughly studied",
      "Your opportunities come through relationships, not luck or strangers",
      "You feel uncomfortable when pushed to act before you've anchored yourself",
      "You notice you influence the same group of people consistently, not crowds"
    ],
    truthShift: "Your network amplifies what you know deeply. The depth and the connection aren't separate—they serve each other.",
    tryThisInstead: "Don't rush to share. Build your foundation, then let it flow through the relationships you already have."
  },
  
  '5/1': {
    title: '5/1 Profile',
    subtitle: 'The Practical Investigator',
    recognition: "People expect you to have answers—especially practical ones. But you can only deliver when you've built a deep foundation underneath what you offer.",
    tension: "You attract projections from strangers: expectations that you'll fix things, solve problems, be the hero. When you're not grounded, those projections crush you.",
    realLifeMoments: [
      "You've been seen as a savior before you felt ready",
      "You feel exposed when someone expects expertise you haven't yet earned",
      "You notice you do your best work when you've studied something to the bone",
      "You've disappointed people who projected onto you more than you could hold"
    ],
    truthShift: "The expectations aren't going away. But you get to choose which ones you meet. Depth first, visibility second.",
    tryThisInstead: "Build your foundation before stepping into the projection field. When you're solid, the expectations become opportunities."
  },
  
  '5/2': {
    title: '5/2 Profile',
    subtitle: 'The Practical Natural',
    recognition: "You're seen as someone who can fix things—and you have natural talents that seem effortless. But you need space to develop those talents before being called on.",
    tension: "People project practical solutions onto you while you'd rather be left alone. The call out feels intrusive, but ignoring it entirely wastes your gifts.",
    realLifeMoments: [
      "Strangers expect things from you that feel unearned",
      "You have abilities that came naturally—you never had to struggle to learn them",
      "You need significant alone time or you start resenting the calls",
      "You've been blamed when someone's projection of you didn't match reality"
    ],
    truthShift: "Your natural gifts will be seen whether you want them to be or not. The question is which calls deserve your response.",
    tryThisInstead: "Protect your retreat time. Only answer the calls that match what you're actually here to offer."
  },
  
  '6/2': {
    title: '6/2 Profile',
    subtitle: 'The Role Model Natural',
    recognition: "You're moving toward being someone others look to—a role model. And underneath that, you have natural gifts that need space to develop without pressure.",
    tension: "You feel the pull to lead but also the need to retreat. The world calls you out while part of you wants to stay hidden until you're ready.",
    realLifeMoments: [
      "You sense a shift from being in the mess to being above it",
      "You need alone time that others don't always understand",
      "People have called you a natural at things you never practiced",
      "You're still integrating the chaos of your earlier years"
    ],
    truthShift: "You don't have to be finished to be worth following. Your natural evolution is the point. People learn by watching you become.",
    tryThisInstead: "Allow yourself to be seen in process. The role model energy isn't perfection—it's authentic integration."
  },
  
  '6/3': {
    title: '6/3 Profile',
    subtitle: 'The Role Model Experimenter',
    recognition: "Your path has been full of experiments—things that worked, things that didn't. Now you're shifting into something more visible: a life that others observe and learn from.",
    tension: "Your past feels messy compared to the role you're stepping into. How can you lead when you remember all the times you failed?",
    realLifeMoments: [
      "You've tried more things that didn't work than most people will ever attempt",
      "You notice a shift from being in the chaos to being slightly removed from it",
      "People look to you for wisdom even though you still feel like you're figuring it out",
      "You hesitate to step into leadership because your experiments are still fresh"
    ],
    truthShift: "The messy past is your qualification. You're not meant to be pristine—you're meant to show what it looks like to keep going.",
    tryThisInstead: "Trust the shift. Let people see how you've integrated the failures. That's what makes you worth watching."
  }
};

// ============================================
// CENTER CARDS
// ============================================

export const CENTER_MIRROR_CARDS: { [center: string]: { defined: MirrorCard; undefined: MirrorCard } } = {
  'head': {
    defined: {
      title: 'Defined Head Center',
      subtitle: 'Consistent mental pressure',
      recognition: "Certain questions keep returning to you—not because you're anxious, but because they're genuinely yours to sit with.",
      tension: "You might try to answer every mental pressure immediately, but not all questions need solving. Some are meant to be held.",
      realLifeMoments: [
        "You find yourself circling back to the same big questions",
        "You feel mentally busy but it's often productive, not chaotic",
        "You get frustrated when people ask you to stop thinking about something",
        "You notice you inspire others to think more deeply"
      ],
      truthShift: "Your mental pressure isn't a problem to fix. It's an engine. The questions that stay with you are meant to be worked, not escaped.",
      tryThisInstead: "Let questions live in you without forcing answers. The right ones will cook over time."
    },
    undefined: {
      title: 'Undefined Head Center',
      subtitle: 'Absorbing mental pressure',
      recognition: "You pick up mental pressure from everyone around you—questions that feel urgent but often aren't actually yours to answer.",
      tension: "You feel like you should solve everything. But half of what's spinning in your head came from somewhere else.",
      realLifeMoments: [
        "You get swept into other people's worries and start trying to solve them",
        "Your mind feels quieter when you're alone",
        "You've spent hours on questions that later seemed completely irrelevant",
        "You notice certain people make you more mentally anxious than others"
      ],
      truthShift: "Not every question deserves your attention. Learning to let the borrowed ones pass through saves enormous energy.",
      tryThisInstead: "When mental pressure spikes, ask: 'Is this question actually mine?' If not, let it go."
    }
  },
  
  'ajna': {
    defined: {
      title: 'Defined Ajna Center',
      subtitle: 'Consistent mental processing',
      recognition: "You have a fixed way of processing information. Your thinking is consistent, reliable—and sometimes difficult to shift once it's set.",
      tension: "Your certainty can become rigidity. What feels like clarity might actually be a blind spot.",
      realLifeMoments: [
        "You notice you analyze things the same way every time",
        "You feel frustrated when someone thinks completely differently than you",
        "You struggle to see perspectives that conflict with your mental framework",
        "Others either love your clarity or find you stubborn"
      ],
      truthShift: "Your consistent thinking is a strength, but it works best when you stay curious about what you might not be seeing.",
      tryThisInstead: "Notice when you're defending a position versus genuinely exploring. Flexibility doesn't threaten your clarity."
    },
    undefined: {
      title: 'Undefined Ajna Center',
      subtitle: 'Flexible mental processing',
      recognition: "You can see things from any angle. Your thinking shifts depending on who you're with—and that's actually an advantage.",
      tension: "You might feel like you should have more mental certainty. You envy people who seem so sure. But your flexibility is a gift, not a flaw.",
      realLifeMoments: [
        "You see multiple sides of an argument and genuinely understand each one",
        "You've changed your mind dramatically based on new information",
        "You feel confused when pressured to lock into one way of thinking",
        "You notice your thought patterns shift depending on who you're around"
      ],
      truthShift: "You're not meant to have fixed opinions. You're designed to understand how different minds work.",
      tryThisInstead: "Stop trying to be certain. Your wisdom is in seeing perspectives, not defending positions."
    }
  },
  
  'throat': {
    defined: {
      title: 'Defined Throat Center',
      subtitle: 'Consistent expression',
      recognition: "You have a reliable voice. When you speak, it carries. People feel it when you say something—whether you intend that or not.",
      tension: "Just because you can speak doesn't mean it's the right moment. Your voice has impact, but impact without timing can misfire.",
      realLifeMoments: [
        "You fill silence because the urge to express is strong",
        "You've said things that shifted the room more than you intended",
        "You notice people listen when you speak—even when you're not trying",
        "You sometimes speak before something is fully formed"
      ],
      truthShift: "Your voice is powerful. But power works best with precision. Timing matters as much as content.",
      tryThisInstead: "Let one beat of silence happen before you speak. If the impulse survives, it's probably real."
    },
    undefined: {
      title: 'Undefined Throat Center',
      subtitle: 'Variable expression',
      recognition: "Your voice is flexible—you can express in many ways depending on who you're with. But the inconsistency might make you try too hard to be heard.",
      tension: "You might talk to be noticed, or stay silent when you actually have something important to say. Neither extreme serves you.",
      realLifeMoments: [
        "You feel like you're always trying to get a word in",
        "Your voice sounds different depending on who you're around",
        "You've stayed quiet when you had something valuable to contribute",
        "You notice certain people make it easier to express yourself"
      ],
      truthShift: "You don't need to force your voice. When the right moment arrives, what comes through will surprise you.",
      tryThisInstead: "Trust the timing. Speak when something genuinely wants to come through, not when you're managing how you're perceived."
    }
  },
  
  'g': {
    defined: {
      title: 'Defined G Center',
      subtitle: 'Fixed sense of identity and direction',
      recognition: "You have a consistent sense of who you are and where you're going. Your direction feels internal and steady, even when external circumstances shift.",
      tension: "Your fixed identity might make it hard to hear feedback that challenges how you see yourself. Growth sometimes requires updating the self-concept.",
      realLifeMoments: [
        "You feel clear about your direction even when others don't understand",
        "You notice you're the same person in most environments",
        "You struggle when situations demand a version of you that doesn't match",
        "You feel grounded even when things around you are unstable"
      ],
      truthShift: "Your consistency is a gift. But growth sometimes asks you to expand who you think you are.",
      tryThisInstead: "Notice when your sense of self is serving you versus limiting you. Identity can be steady and still evolve."
    },
    undefined: {
      title: 'Undefined G Center',
      subtitle: 'Variable identity and direction',
      recognition: "Who you are shifts depending on where you are. You become different versions of yourself in different environments—and that's not confusion, that's sensitivity.",
      tension: "You might waste years trying to become consistent in a way you were never designed to be. The real question isn't 'who am I?' but 'where do I belong?'",
      realLifeMoments: [
        "You feel like a different person in different places",
        "You've questioned your identity more than most people",
        "Certain environments make you feel clear; others make you feel lost",
        "You've tried to lock down who you are, and it never quite stuck"
      ],
      truthShift: "Your identity isn't supposed to be fixed. You learn through contrast. The right environments reveal the real you.",
      tryThisInstead: "Stop asking 'who am I?' Start asking 'where do I feel most like myself?' Go there."
    }
  },
  
  'heart': {
    defined: {
      title: 'Defined Heart/Ego Center',
      subtitle: 'Consistent willpower',
      recognition: "You have access to steady willpower—when you commit, you can follow through. But that engine only works when your heart is genuinely in it.",
      tension: "You might make promises based on what you think you should want. When your heart isn't in it, the will runs out and the promise breaks.",
      realLifeMoments: [
        "You feel unstoppable when working on something you truly want",
        "You've broken commitments when the desire underneath disappeared",
        "You notice your energy is tied directly to genuine desire",
        "You feel drained when you commit to things you 'should' want but don't"
      ],
      truthShift: "Your willpower is real—but it only refuels when pointed at genuine desire. Check your heart before you promise.",
      tryThisInstead: "Before committing, ask: 'Do I actually want this?' If the answer isn't clear, don't promise. Your integrity depends on genuine desire."
    },
    undefined: {
      title: 'Undefined Heart/Ego Center',
      subtitle: 'Variable sense of worth',
      recognition: "Your sense of worth fluctuates—sometimes you feel confident, other times you feel like you have to prove yourself constantly.",
      tension: "You might overwork to prove your value, or collapse when you don't feel recognized. The race to prove worth never ends.",
      realLifeMoments: [
        "You've pushed yourself past healthy limits trying to earn respect",
        "You feel your value shift based on achievements",
        "You've made promises to prove yourself that you couldn't keep",
        "You notice some people make you feel valuable; others make you feel small"
      ],
      truthShift: "Your worth isn't earned through proving. It's not measured by output. When you stop racing, your real value becomes visible.",
      tryThisInstead: "Notice when you're working to prove versus working because it's yours to do. The difference changes everything."
    }
  },
  
  'spleen': {
    defined: {
      title: 'Defined Spleen Center',
      subtitle: 'Consistent intuition and survival awareness',
      recognition: "You have reliable instincts—a quiet knowing that speaks once, in the moment. When you trust it, you navigate with unusual precision.",
      tension: "The hit is so subtle you might override it with logic. But the first knowing doesn't repeat, and once you've reasoned past it, it's gone.",
      realLifeMoments: [
        "You've had gut feelings that turned out to be exactly right",
        "You notice danger or safety before anyone else in the room",
        "You've ignored your first hit and regretted it",
        "Your intuition speaks quietly—easy to miss if you're not listening"
      ],
      truthShift: "Your intuition isn't trying to convince you. It gives you one hit, trusts you to catch it, and moves on.",
      tryThisInstead: "Practice catching the first quiet signal before your mind starts explaining it away. That's where your precision lives."
    },
    undefined: {
      title: 'Undefined Spleen Center',
      subtitle: 'Amplified survival awareness',
      recognition: "You feel fear, health signals, and danger more intensely than others—sometimes because it's real, often because it's borrowed.",
      tension: "You hold onto things that feel threatening long after they're gone. Fears stay with you because you don't know which ones to release.",
      realLifeMoments: [
        "You've stayed in situations longer than healthy because leaving felt scarier",
        "You notice fears that don't seem to have a clear source",
        "Certain people make you more anxious without a clear reason",
        "You've been told to 'just relax' when your body is screaming something different"
      ],
      truthShift: "You feel everything intensely—but not all of it is yours. Learning to let borrowed fear pass through is a superpower.",
      tryThisInstead: "When fear arises, ask: 'Is this mine?' If you can't identify the source, it might be borrowed. Let it pass."
    }
  },
  
  'solar plexus': {
    defined: {
      title: 'Defined Solar Plexus',
      subtitle: 'Riding emotional waves',
      recognition: "You feel things in waves—highs, lows, and everything between. Your emotional life isn't flat, and it's not supposed to be.",
      tension: "You might make decisions in the peak or valley, thinking that intensity is clarity. It's not. Real knowing comes when the wave settles.",
      realLifeMoments: [
        "You've said yes in a high and wondered what you were thinking",
        "You've said no in a low and missed something real",
        "You notice your mood shifts without clear external triggers",
        "Others feel your emotional presence even when you're trying to hide it"
      ],
      truthShift: "Your emotions are information, not truth. The truth is what remains when the wave has passed.",
      tryThisInstead: "Wait until you're neutral before making big decisions. If it still feels right when you're calm, that's your answer."
    },
    undefined: {
      title: 'Undefined Solar Plexus',
      subtitle: 'Absorbing emotional waves',
      recognition: "You feel other people's emotions intensely—sometimes more than they feel them themselves. That sensitivity is a gift and a burden.",
      tension: "You might take on emotional storms that aren't yours and try to fix them. Or avoid emotional people entirely because it's overwhelming.",
      realLifeMoments: [
        "You walk into a room and immediately feel the emotional tone",
        "You've carried someone else's mood home without realizing it",
        "You feel relief when you're alone and can finally separate your feelings from theirs",
        "Intense people exhaust you"
      ],
      truthShift: "Not every emotion you feel is yours. Learning to let them pass through without attaching is freedom.",
      tryThisInstead: "Ask yourself: 'Is this mine?' When an emotion seems to come from nowhere, it probably came from someone."
    }
  },
  
  'sacral': {
    defined: {
      title: 'Defined Sacral Center',
      subtitle: 'Sustainable life force energy',
      recognition: "You have a motor that keeps going—real, sustainable energy for the things you respond to. It builds and builds when you're lit up.",
      tension: "You might override your gut with your mind, saying yes to things your body never agreed to. That's when the engine starts to stall.",
      realLifeMoments: [
        "You feel the difference between work that energizes and work that drains",
        "Your gut responds before your mind catches up",
        "You've pushed through frustration until you burned out",
        "You notice a physical pull toward some things and a deadness toward others"
      ],
      truthShift: "Your energy is not unlimited for everything—just for what you're genuinely responding to. That's the filter.",
      tryThisInstead: "Check in with your body before committing. A real yes feels like a pull forward. No response means wait."
    },
    undefined: {
      title: 'Undefined Sacral Center',
      subtitle: 'Variable life force energy',
      recognition: "You can amplify the energy of others—working intensely alongside people who are powered up. But that energy isn't sustainable on your own.",
      tension: "You might push yourself to match the pace of people with consistent energy, burning out because you're borrowing what you can't sustain.",
      realLifeMoments: [
        "You get swept up in other people's energy and crash later",
        "You've worked past the point of exhaustion trying to keep up",
        "You feel guilty for needing more rest than seems reasonable",
        "You notice your energy is completely different depending on who you're around"
      ],
      truthShift: "You're not designed for marathon energy. You're designed for efficiency. Knowing when to rest is your edge.",
      tryThisInstead: "Honor the rest you need. You don't have to prove you can keep up. Your value isn't in matching others' pace."
    }
  },
  
  'root': {
    defined: {
      title: 'Defined Root Center',
      subtitle: 'Consistent internal pressure',
      recognition: "You have a steady engine of pressure driving you forward. Urgency feels natural, and you're good at working under deadlines.",
      tension: "You might treat all pressure as urgent, exhausting yourself on manufactured emergencies. Not everything needs to happen now.",
      realLifeMoments: [
        "You thrive with deadlines that would stress others out",
        "You feel restless when there's nothing pressing to do",
        "You've created urgency just to have something to push against",
        "Your natural pace feels fast to people around you"
      ],
      truthShift: "Your drive is real. But it works best when pointed at things that actually matter. Manufactured urgency drains without producing.",
      tryThisInstead: "Before reacting to pressure, ask: 'Is this actually urgent?' Save your drive for what deserves it."
    },
    undefined: {
      title: 'Undefined Root Center',
      subtitle: 'Amplified stress and pressure',
      recognition: "You absorb pressure from your environment—deadlines, urgency, stress that isn't yours but feels like it is.",
      tension: "You rush to finish things just to relieve the pressure, even when rushing wasn't necessary. The relief is temporary; more pressure always comes.",
      realLifeMoments: [
        "You feel other people's deadlines as if they were your own",
        "You've rushed to complete something that didn't actually have urgency",
        "You feel calmer when you're alone than in fast-paced environments",
        "You've made hasty decisions just to stop the pressure"
      ],
      truthShift: "Not all urgency is real. Learning which pressure is yours and which is borrowed is the key to peace.",
      tryThisInstead: "When you feel rushed, pause and ask: 'Is this pressure mine?' Most of the time, it's not. Let it pass."
    }
  }
};

// ============================================
// INCARNATION CROSS CARDS
// ============================================

export const CROSS_MIRROR_CARDS: { [key: string]: MirrorCard } = {
  'Right Angle': {
    title: 'Right Angle Cross',
    subtitle: 'Personal destiny',
    recognition: "Your journey is about you. Not in a selfish way—but in the sense that your path unfolds through your own experience, not service to others' agendas.",
    tension: "You might feel guilty for focusing on your own development. But your personal growth IS your contribution. Self-focus isn't selfishness here—it's purpose.",
    realLifeMoments: [
      "You feel pulled toward your own growth more than external causes",
      "Others' expectations don't override your internal direction",
      "You've felt guilty for prioritizing your path over helping others",
      "Your biggest lessons came from personal experience, not observation"
    ],
    truthShift: "Your journey serves others by being fully lived—not by being abandoned for someone else's mission.",
    tryThisInstead: "Stop apologizing for focusing on your path. Your contribution comes through becoming yourself, not disappearing into service."
  },
  
  'Left Angle': {
    title: 'Left Angle Cross',
    subtitle: 'Transpersonal karma',
    recognition: "Your journey is bound up with others. You're here to meet, influence, and be transformed by the people your path crosses.",
    tension: "You might feel frustrated that your direction seems dependent on other people. But the connections aren't obstacles—they're the point.",
    realLifeMoments: [
      "Key relationships have dramatically redirected your path",
      "You've been transformed by people you didn't expect",
      "Your purpose feels tied to specific connections",
      "You notice your trajectory shifts when significant people enter or exit"
    ],
    truthShift: "Your destiny isn't solo. It's collaborative. The people who cross your path are part of the design, not distractions from it.",
    tryThisInstead: "Pay attention to who shows up. The significant connections aren't accidents—they're invitations."
  },
  
  'Juxtaposition': {
    title: 'Juxtaposition Cross',
    subtitle: 'Fixed fate',
    recognition: "Your path is unusually focused—a specific geometry that doesn't bend easily. You're here to do something particular, and the directness of that can feel isolating.",
    tension: "You might feel misunderstood or stuck on a track that others don't see. The narrowness isn't limitation—it's precision.",
    realLifeMoments: [
      "You've felt like you're on a path others can't fully understand",
      "Your life seems to follow a specific thread, even when you try to diverge",
      "Major changes have felt forced rather than chosen",
      "You notice your focus naturally narrows rather than expands"
    ],
    truthShift: "Your path isn't narrow because you're limited. It's focused because that focus is how you create impact.",
    tryThisInstead: "Trust the specificity. Your track may be narrow, but what you contribute by staying on it matters."
  }
};

// Helper function to get mirror card content
export function getTypeMirrorCard(type: string): MirrorCard | null {
  return TYPE_MIRROR_CARDS[type] || null;
}

export function getAuthorityMirrorCard(authority: string): MirrorCard | null {
  return AUTHORITY_MIRROR_CARDS[authority] || null;
}

export function getProfileMirrorCard(profile: string): MirrorCard | null {
  return PROFILE_MIRROR_CARDS[profile] || null;
}

export function getCenterMirrorCard(center: string, isDefined: boolean): MirrorCard | null {
  const normalizedCenter = center.toLowerCase().replace('ego', 'heart').replace(' center', '').replace('centre', '').trim();
  const centerData = CENTER_MIRROR_CARDS[normalizedCenter];
  if (!centerData) return null;
  return isDefined ? centerData.defined : centerData.undefined;
}

export function getCrossMirrorCard(crossType: string): MirrorCard | null {
  // Extract the cross type (Right Angle, Left Angle, Juxtaposition)
  if (crossType.toLowerCase().includes('right angle')) {
    return CROSS_MIRROR_CARDS['Right Angle'];
  }
  if (crossType.toLowerCase().includes('left angle')) {
    return CROSS_MIRROR_CARDS['Left Angle'];
  }
  if (crossType.toLowerCase().includes('juxtaposition')) {
    return CROSS_MIRROR_CARDS['Juxtaposition'];
  }
  return null;
}

// ============================================
// CROSS-LINK GENERATION
// ============================================
// Creates subtle, single-sentence connections between HD elements
// Max 1 cross-link per card

export interface CrossLinkContext {
  type?: string;
  authority?: string;
  profile?: string;
  definedCenters?: string[];
  undefinedCenters?: string[];
  channels?: { gates?: string; name?: string }[];
  personalitySun?: number | { gate: number };
  designSun?: number | { gate: number };
  consciousGates?: number[];
  unconsciousGates?: number[];
}

// Generate cross-link for a gate based on context
export function getGateCrossLink(gateNum: number, context: CrossLinkContext): string | null {
  // Check if gate has a programming partner in their chart
  const partnerGate = getProgrammingPartner(gateNum);
  const hasPartner = partnerGate && (
    context.consciousGates?.includes(partnerGate) ||
    context.unconsciousGates?.includes(partnerGate)
  );
  
  // Check if gate is part of a channel
  const channelPartner = getChannelPartner(gateNum, context.channels || []);
  
  // Prioritize programming partner tension
  if (hasPartner) {
    return getProgrammingPartnerCrossLink(gateNum, partnerGate!);
  }
  
  // Then channel connection
  if (channelPartner) {
    return getChannelCrossLink(gateNum, channelPartner);
  }
  
  // Then authority tension
  if (context.authority) {
    return getGateAuthorityCrossLink(gateNum, context.authority);
  }
  
  return null;
}

// Generate cross-link for a center based on context
export function getCenterCrossLink(center: string, isDefined: boolean, context: CrossLinkContext): string | null {
  const normalizedCenter = center.toLowerCase().replace(' center', '').replace('centre', '').trim();
  
  // Undefined centers → sensitivity to external influence
  if (!isDefined) {
    return getUndefinedCenterCrossLink(normalizedCenter, context.type || '');
  }
  
  // Defined centers → consistent energy output
  return getDefinedCenterCrossLink(normalizedCenter, context.authority || '');
}

// Generate cross-link for Type based on Authority
export function getTypeCrossLink(type: string, authority: string): string | null {
  const key = `${type}_${authority}`;
  
  const crossLinks: { [key: string]: string } = {
    'Generator_Emotional': "Part of you responds instantly—but another part needs time. That tension is built in.",
    'Generator_Sacral': "Your body knows before your mind. Learning to trust that is the work.",
    'Manifesting Generator_Emotional': "You move fast, but your clarity unfolds slow. The mismatch is designed.",
    'Manifesting Generator_Sacral': "Your energy shifts quickly—and that's correct, not inconsistent.",
    'Projector_Emotional': "You see things clearly, but when to share isn't instant. The timing matters.",
    'Projector_Splenic': "You sense the truth instantly—but speaking it uninvited still lands wrong.",
    'Manifestor_Emotional': "You want to act now, but your wave isn't done. That friction shapes everything.",
    'Manifestor_Splenic': "The knowing comes once. Catching it before doubt kicks in—that's the edge.",
    'Reflector_Lunar': "You absorb everything. What's actually yours takes time to sort out."
  };
  
  return crossLinks[key] || null;
}

// Generate cross-link for Authority based on Type
export function getAuthorityCrossLink(authority: string, type: string): string | null {
  const key = `${authority}_${type}`;
  
  const crossLinks: { [key: string]: string } = {
    'Emotional_Projector': "Your clarity comes in waves—and trying to guide from peaks or valleys creates mismatch.",
    'Emotional_Generator': "Your gut responds fast, but acting on the initial hit often misses what the wave reveals.",
    'Emotional_Manifestor': "The urge to initiate comes before clarity settles. That gap is where friction lives.",
    'Sacral_Generator': "Your response is the truth. The mind questioning it is the noise.",
    'Sacral_Manifesting Generator': "Energy shifting isn't failure—it's the signal that something else is alive.",
    'Splenic_Projector': "You know instantly, but speaking without invitation wastes the knowing.",
    'Splenic_Manifestor': "The hit comes once. Missing it means reasoning your way to something that already passed."
  };
  
  return crossLinks[key] || null;
}

// Helper: Get programming partner gate
function getProgrammingPartner(gate: number): number | null {
  const partners: { [key: number]: number } = {
    1: 2, 2: 1, 3: 4, 4: 3, 5: 6, 6: 5, 7: 8, 8: 7,
    9: 10, 10: 9, 11: 12, 12: 11, 13: 14, 14: 13,
    15: 16, 16: 15, 17: 18, 18: 17, 19: 20, 20: 19,
    21: 22, 22: 21, 23: 24, 24: 23, 25: 26, 26: 25,
    27: 28, 28: 27, 29: 30, 30: 29, 31: 32, 32: 31,
    33: 34, 34: 33, 35: 36, 36: 35, 37: 38, 38: 37,
    39: 40, 40: 39, 41: 42, 42: 41, 43: 44, 44: 43,
    45: 46, 46: 45, 47: 48, 48: 47, 49: 50, 50: 49,
    51: 52, 52: 51, 53: 54, 54: 53, 55: 56, 56: 55,
    57: 58, 58: 57, 59: 60, 60: 59, 61: 62, 62: 61,
    63: 64, 64: 63
  };
  return partners[gate] || null;
}

// Helper: Get channel partner gate
function getChannelPartner(gate: number, channels: { gates?: string; name?: string }[]): number | null {
  for (const channel of channels) {
    if (!channel.gates) continue;
    const gatesInChannel = channel.gates.split('-').map(g => parseInt(g.trim()));
    if (gatesInChannel.includes(gate)) {
      const partner = gatesInChannel.find(g => g !== gate);
      return partner || null;
    }
  }
  return null;
}

// Programming partner cross-links (polarity tension)
function getProgrammingPartnerCrossLink(gate: number, partnerGate: number): string {
  const polarities: { [key: string]: string } = {
    '1_2': "Part of you wants creative direction—another part needs receptivity. They pull against each other.",
    '2_1': "You have receptive wisdom, but something in you keeps pushing for creative assertion.",
    '3_4': "You experiment to learn, but there's pressure to have logical answers before you've tried.",
    '4_3': "You want formulaic certainty, but growth comes from trial and error you can't skip.",
    '5_6': "You sense timing, but emotional depth keeps complicating what feels 'right'.",
    '6_5': "Emotional waves are teaching you, but part of you just wants fixed rhythms.",
    '7_8': "You guide direction, but another energy wants unique individual expression.",
    '8_7': "Your contribution is individual, but there's pull toward leading others.",
    '9_10': "Focus and detail conflict with your need for authentic self-expression.",
    '10_9': "Being yourself clashes with pressure to focus narrowly.",
    '11_12': "Ideas flood in, but expressing them requires a different kind of stillness.",
    '12_11': "Cautious expression battles with the overflow of mental stimulation.",
    '17_18': "Opinions form easily, but correcting what's flawed takes different energy.",
    '18_17': "You see what needs fixing, but that clashes with confident knowing.",
    '21_22': "Control and emotional openness pull in opposite directions.",
    '22_21': "Grace in emotion conflicts with will to control.",
    '27_28': "Caring and meaning-seeking create different priorities.",
    '28_27': "Struggling for purpose battles with nurturing instincts.",
    '29_30': "Commitment conflicts with emotional hunger for experience.",
    '30_29': "Desire for feeling burns against the pull of saying yes.",
    '35_36': "Experience seeking clashes with emotional crisis navigation.",
    '36_35': "Crisis moves you, but adventure calls differently.",
    '39_40': "Provocation and rest don't naturally coexist.",
    '40_39': "Your need for alone time conflicts with instinct to provoke.",
    '47_48': "Realization and depth operate on different timescales.",
    '48_47': "You go deep, but meaning hits in flashes you can't force.",
    '57_58': "Intuition and joyful aliveness compete for attention.",
    '58_57': "Vitality clashes with the quiet of intuitive knowing.",
    '63_64': "Doubt and confusion overlap—one questions, one imagines."
  };
  
  const key = `${gate}_${partnerGate}`;
  const reverseKey = `${partnerGate}_${gate}`;
  
  return polarities[key] || polarities[reverseKey] || 
    "There's built-in tension between different parts of how you're wired.";
}

// Channel cross-links (completed energy)
function getChannelCrossLink(gate: number, partnerGate: number): string {
  return `This connects to another active energy in you—together they form a consistent way you process life.`;
}

// Gate + Authority tension
function getGateAuthorityCrossLink(gate: number, authority: string): string | null {
  // Gates that specifically conflict with emotional authority (waiting)
  const impulsiveGates = [3, 35, 36, 41, 51, 53];
  if (authority === 'Emotional' && impulsiveGates.includes(gate)) {
    return "This energy wants to move now—but your clarity takes time. That tension is real.";
  }
  
  // Gates that want certainty (conflict with splenic authority's one-time knowing)
  const certaintyGates = [4, 17, 48, 63];
  if (authority === 'Splenic' && certaintyGates.includes(gate)) {
    return "This wants logical certainty, but your knowing comes once and doesn't explain itself.";
  }
  
  return null;
}

// Undefined center cross-links
function getUndefinedCenterCrossLink(center: string, type: string): string | null {
  const crossLinks: { [key: string]: string } = {
    'g': "This is why your direction shifts depending on environment—it's sensitivity, not confusion.",
    'heart': "This is why proving yourself feels urgent but draining—the pressure isn't naturally yours.",
    'sacral': "Without consistent energy access, rest isn't laziness—it's necessary.",
    'spleen': "Safety feels uncertain because you're amplifying others' fear, not your own.",
    'root': "Urgency hits you from outside. The pressure you feel often isn't yours.",
    'ajna': "Your mind picks up others' certainty. What you think can depend on who's around.",
    'head': "Questions and inspiration flood in from everywhere. Not all of them are yours to solve.",
    'throat': "Expression depends on who's in the room. Silence isn't failure—it's sensitivity.",
    'solar plexus': "You feel others' emotions intensely. Distinguishing theirs from yours is the work."
  };
  
  return crossLinks[center] || null;
}

// Defined center cross-links  
function getDefinedCenterCrossLink(center: string, authority: string): string | null {
  const crossLinks: { [key: string]: string } = {
    'sacral': "This energy is consistent—but how you direct it still depends on response, not will.",
    'heart': "Willpower is reliable here, but it only sustains what your heart actually wants.",
    'g': "Direction is steady—but the right invitations still matter for where you go.",
    'spleen': "Safety instincts are consistent—the knowing just comes once and doesn't repeat.",
    'solar plexus': "Emotions are yours, and they wave. Clarity lives in the settling, not the peaks."
  };
  
  return crossLinks[center] || null;
}
