"""Human Design Defined Gates Interpretation Service

Provides reflective, template-based interpretations for the 64 Human Design gates.
Uses the same Mirror tone as Centers and Gene Keys - practical, warm, non-deterministic.

This service returns ONLY the gates active in a user's chart, not all 64.
Each gate includes a Gene Keys bridge (shadow/gift/siddhi) for deeper exploration.
"""

from typing import List, Dict, Any, TypedDict, Optional
from services.human_design_centers import GATE_TO_CENTER

# =============================================================================
# GATE METADATA - Names, themes, and Gene Keys bridge
# =============================================================================

GATE_DATA = {
    1: {
        "name": "Self-Expression",
        "themes": ["creativity", "individuality", "authentic expression"],
        "shadow": "Entropy", "gift": "Freshness", "siddhi": "Beauty",
        "what_this_means": "Gate 1 is about expressing your unique creative identity. You carry an energy that wants to bring something genuinely new into the world—not by following trends, but by being authentically yourself.",
        "your_challenge": "The challenge is navigating the gap between your inner creative vision and whether the world receives it. You might feel misunderstood or ahead of your time. The pressure to express can also create anxiety when outlets aren't available.",
        "your_genius": "Your genius lies in bringing fresh perspectives simply by being yourself. You don't need to try to be original—you already are. Your presence naturally inspires others to find their own authentic voice.",
        "practical_experiments": [
            "Notice when you're creating for approval versus creating because it genuinely moves through you.",
            "Give yourself permission to express without needing immediate validation.",
            "Track when your creative energy is highest and protect that time."
        ],
        "remember": "Your creativity isn't about being different for its own sake. It's about being true to what naturally wants to come through you."
    },
    2: {
        "name": "Direction",
        "themes": ["receptivity", "natural direction", "higher knowing"],
        "shadow": "Dislocation", "gift": "Orientation", "siddhi": "Unity",
        "what_this_means": "Gate 2 carries a deep receptivity to direction and purpose. You have access to a kind of inner compass that knows where things need to go, even when you can't explain it logically.",
        "your_challenge": "The challenge is trusting this inner knowing when it doesn't make rational sense. You might second-guess your direction or get pulled off course by others' agendas. Feeling lost can be particularly disorienting for you.",
        "your_genius": "Your genius is in sensing the right direction—for yourself and sometimes for others. When you're aligned, you naturally guide situations toward their highest potential without forcing.",
        "practical_experiments": [
            "Practice listening to your first intuitive sense of direction before consulting logic.",
            "Notice the difference between being genuinely lost versus just being in the unknown.",
            "When others ask for direction, check if you're responding from true knowing or people-pleasing."
        ],
        "remember": "Your sense of direction isn't always about knowing the destination. Sometimes it's simply about knowing the next step."
    },
    3: {
        "name": "Ordering",
        "themes": ["mutation", "new beginnings", "innovation through chaos"],
        "shadow": "Chaos", "gift": "Innovation", "siddhi": "Innocence",
        "what_this_means": "Gate 3 is about bringing new order out of chaos. You carry the energy of mutation—the capacity to create new ways of doing things, often by working through difficulty and disorder.",
        "your_challenge": "The challenge is that new beginnings often feel chaotic before they settle into form. You might attract disruption or feel like you're constantly starting over. The mutation process can be uncomfortable.",
        "your_genius": "Your genius is in your capacity to innovate through difficulty. Where others see problems, you can find entirely new approaches. Your mutations, once integrated, often become the new standard.",
        "practical_experiments": [
            "Notice when chaos is productive (leading somewhere new) versus just disruptive.",
            "Give new beginnings time to find their form before judging them.",
            "Track patterns in what kinds of innovations naturally emerge through you."
        ],
        "remember": "The chaos isn't the destination—it's the birth canal. What emerges through difficulty often has staying power that easier creations lack."
    },
    4: {
        "name": "Mental Solutions",
        "themes": ["logic", "answers", "formulaic thinking"],
        "shadow": "Intolerance", "gift": "Understanding", "siddhi": "Forgiveness",
        "what_this_means": "Gate 4 is about finding mental solutions and answers. You have a mind that naturally works through problems logically, seeking formulas and patterns that can be applied consistently.",
        "your_challenge": "The challenge is that you might feel pressure to have answers when you don't, or become attached to solutions that worked before but don't fit new situations. Mental certainty can become rigidity.",
        "your_genius": "Your genius is in logical problem-solving. When you have the right data and the right timing, your mental formulas can genuinely help others navigate confusion. Your understanding runs deep.",
        "practical_experiments": [
            "Notice when you're offering solutions versus when you're just thinking out loud.",
            "Practice saying 'I don't have an answer yet' when you genuinely don't.",
            "Check if your mental formulas still fit, or if they need updating."
        ],
        "remember": "Not every problem needs a formula. Some situations need presence, not answers."
    },
    5: {
        "name": "Fixed Rhythms",
        "themes": ["timing", "patterns", "natural rhythms"],
        "shadow": "Impatience", "gift": "Patience", "siddhi": "Timelessness",
        "what_this_means": "Gate 5 is about attunement to fixed rhythms and natural timing. You carry an awareness of patterns and cycles, understanding that everything has its proper season.",
        "your_challenge": "The challenge is maintaining patience when rhythms feel slow or when others pressure you to move faster than natural timing allows. You might also become too rigid about routines.",
        "your_genius": "Your genius is in recognizing correct timing. You can sense when something is ready and when it isn't, which saves wasted effort and increases effectiveness.",
        "practical_experiments": [
            "Notice which rhythms in your life are genuinely yours versus adopted from others.",
            "Practice waiting when timing isn't right, even under pressure.",
            "Track how your energy flows through daily, weekly, and monthly cycles."
        ],
        "remember": "Patience isn't passive waiting. It's active attunement to what's actually ready to happen."
    },
    6: {
        "name": "Conflict Resolution",
        "themes": ["intimacy", "friction", "emotional depth"],
        "shadow": "Conflict", "gift": "Diplomacy", "siddhi": "Peace",
        "what_this_means": "Gate 6 carries the energy of emotional intimacy and the friction that comes with it. You have access to deep emotional connection, which sometimes means navigating conflict to get there.",
        "your_challenge": "The challenge is that intimacy often requires moving through discomfort. You might avoid conflict to keep peace, or create conflict without resolution. The emotional waves here can be intense.",
        "your_genius": "Your genius is in creating genuine emotional depth and connection. When you navigate friction skillfully, you can build intimacy that superficial harmony never achieves.",
        "practical_experiments": [
            "Notice when you're avoiding necessary friction versus when peace is genuine.",
            "Practice staying present through emotional discomfort without escalating or fleeing.",
            "Track which relationships deepen through conflict and which don't."
        ],
        "remember": "Not all conflict leads to intimacy, but genuine intimacy almost always requires moving through some friction."
    },
    7: {
        "name": "Self-Direction",
        "themes": ["leadership", "guidance", "role modeling"],
        "shadow": "Division", "gift": "Guidance", "siddhi": "Virtue",
        "what_this_means": "Gate 7 is about leading by example and providing direction. You carry a natural capacity to guide others, not through dominance but through demonstrating a way forward.",
        "your_challenge": "The challenge is leading without becoming authoritarian, and offering guidance without attachment to whether others follow. You might also struggle when you don't have clarity about your own direction.",
        "your_genius": "Your genius is in showing the way through your own life choices. When you're living your direction authentically, others naturally orient around you.",
        "practical_experiments": [
            "Notice when you're leading from genuine direction versus from desire for control.",
            "Practice offering guidance without attachment to outcomes.",
            "Check if your own life reflects what you're asking others to consider."
        ],
        "remember": "The most powerful leadership is demonstration, not instruction."
    },
    8: {
        "name": "Contribution",
        "themes": ["individual contribution", "making a mark", "unique style"],
        "shadow": "Mediocrity", "gift": "Style", "siddhi": "Exquisiteness",
        "what_this_means": "Gate 8 is about making your unique contribution and having impact through your individual style. You carry an energy that wants to contribute something that couldn't come from anyone else.",
        "your_challenge": "The challenge is that your contribution might not be immediately recognized or valued. You might also mistake being different for being valuable, rather than contributing what's genuinely useful.",
        "your_genius": "Your genius is in your distinctive approach. When you contribute from your authentic style, you fill a gap that no one else can fill in quite the same way.",
        "practical_experiments": [
            "Notice the difference between contributing for recognition versus genuine service.",
            "Identify what you naturally do differently from others and how that serves.",
            "Track which contributions land and which don't—what patterns emerge?"
        ],
        "remember": "Your style is valuable not because it's different, but because it's genuinely yours."
    },
    9: {
        "name": "Focus",
        "themes": ["concentration", "detail", "determination"],
        "shadow": "Inertia", "gift": "Determination", "siddhi": "Invincibility",
        "what_this_means": "Gate 9 is about the power of focus and attention to detail. You carry the capacity for sustained concentration that can accomplish things others give up on.",
        "your_challenge": "The challenge is that focus can become obsession, or inertia can make it hard to get started. You might get stuck in details while losing sight of the bigger picture.",
        "your_genius": "Your genius is in sustained attention. When you focus on what genuinely matters to you, your determination can move mountains slowly but surely.",
        "practical_experiments": [
            "Notice when your focus is productive versus when it's avoidance of bigger questions.",
            "Practice choosing what deserves your focused attention rather than defaulting to habit.",
            "Track how long your natural focus cycles last before needing breaks."
        ],
        "remember": "Focus is a finite resource. Spend it on what actually matters."
    },
    10: {
        "name": "Self-Love",
        "themes": ["behavior", "authenticity", "self-acceptance"],
        "shadow": "Self-Obsession", "gift": "Naturalness", "siddhi": "Being",
        "what_this_means": "Gate 10 is about loving yourself through authentic behavior. You carry an energy that naturally expresses who you are through how you act, not through what you say about yourself.",
        "your_challenge": "The challenge is that authentic behavior sometimes doesn't fit what's expected. You might contort yourself to be accepted, or become self-obsessed trying to figure out who you really are.",
        "your_genius": "Your genius is in natural self-expression. When you simply behave as yourself without performance, you model authentic living for others.",
        "practical_experiments": [
            "Notice when you're performing a version of yourself versus simply being.",
            "Practice small acts of authenticity in low-stakes situations.",
            "Track which environments let you be most naturally yourself."
        ],
        "remember": "Self-love isn't about feeling good about yourself. It's about being yourself even when it's uncomfortable."
    },
    11: {
        "name": "Ideas",
        "themes": ["conceptualization", "peace through ideas", "mental imagery"],
        "shadow": "Obscurity", "gift": "Idealism", "siddhi": "Light",
        "what_this_means": "Gate 11 is about the peace that comes from ideas and concepts. You have access to a rich inner world of mental imagery and possibilities that can illuminate understanding.",
        "your_challenge": "The challenge is that ideas alone don't change reality. You might get lost in conceptual worlds or struggle to ground your insights into practical application.",
        "your_genius": "Your genius is in seeing possibilities and patterns through the mind's eye. Your ideas, when shared at the right time, can shift how others see things.",
        "practical_experiments": [
            "Notice which ideas keep returning versus which pass through quickly.",
            "Practice discerning between ideas meant to be shared and those meant for your own contemplation.",
            "Track what happens when you try to force ideas versus when they emerge naturally."
        ],
        "remember": "Not every idea needs to be acted on. Some are meant simply to illuminate."
    },
    12: {
        "name": "Caution",
        "themes": ["articulation", "social caution", "emotional expression"],
        "shadow": "Vanity", "gift": "Discrimination", "siddhi": "Purity",
        "what_this_means": "Gate 12 is about careful articulation and knowing when to speak. You carry an awareness that words have power, and that timing matters in expression.",
        "your_challenge": "The challenge is finding the right moment to express. You might hold back too long, or speak at the wrong time. The emotional charge behind your words can also complicate delivery.",
        "your_genius": "Your genius is in discriminating when and how to express. When your timing is right, your words can land with particular impact.",
        "practical_experiments": [
            "Notice the emotional wave you're in before important conversations.",
            "Practice pausing before speaking to sense if timing is right.",
            "Track which expressions land well and what the conditions were."
        ],
        "remember": "The right words at the wrong time are still the wrong words."
    },
    13: {
        "name": "Listener",
        "themes": ["secrets", "listening", "collective memory"],
        "shadow": "Discord", "gift": "Discernment", "siddhi": "Empathy",
        "what_this_means": "Gate 13 is about deep listening and holding space for others' stories. You naturally draw out what people need to share, often hearing things others don't.",
        "your_challenge": "The challenge is that you may absorb others' experiences too deeply, or struggle with what to do with everything you've heard. The weight of others' secrets can be heavy.",
        "your_genius": "Your genius is in creating space where others feel truly heard. Your listening has healing power, even when you don't offer advice.",
        "practical_experiments": [
            "Notice when you're listening to help versus listening to absorb.",
            "Practice releasing what you've heard rather than carrying it indefinitely.",
            "Track your energy after different types of listening experiences."
        ],
        "remember": "Holding space doesn't mean holding onto everything you hear."
    },
    14: {
        "name": "Power Skills",
        "themes": ["resources", "empowerment", "material success"],
        "shadow": "Compromise", "gift": "Competence", "siddhi": "Bounteousness",
        "what_this_means": "Gate 14 is about managing resources and creating material success. You carry the power to generate and direct resources toward what matters.",
        "your_challenge": "The challenge is using your power without compromising your values, and not measuring your worth by material success alone. Resources can become traps as easily as freedoms.",
        "your_genius": "Your genius is in competent resource management. When aligned with purpose, your material power serves something larger than accumulation.",
        "practical_experiments": [
            "Notice where resources flow easily and where they feel stuck.",
            "Practice using material power for empowerment rather than control.",
            "Track the relationship between your values and your resource decisions."
        ],
        "remember": "Power skills are neutral. What matters is what you empower."
    },
    15: {
        "name": "Extremes",
        "themes": ["rhythm", "humanity", "flowing with life"],
        "shadow": "Dullness", "gift": "Magnetism", "siddhi": "Florescence",
        "what_this_means": "Gate 15 is about flowing with the extremes of human rhythm. You carry a magnetic quality that comes from accepting the full range of human experience.",
        "your_challenge": "The challenge is that extremes can be exhausting, and you might swing between too much and too little. Finding your own rhythm within the extremes takes time.",
        "your_genius": "Your genius is in your natural magnetism and acceptance of life's full spectrum. You help others feel normal in their own extremes.",
        "practical_experiments": [
            "Notice which rhythms genuinely serve you versus which you've adopted from others.",
            "Practice accepting your own extremes without trying to normalize them.",
            "Track the seasons of your natural rhythm—when do you expand and contract?"
        ],
        "remember": "The extremes aren't problems to solve. They're the full range of being human."
    },
    16: {
        "name": "Skills",
        "themes": ["enthusiasm", "talent identification", "mastery"],
        "shadow": "Indifference", "gift": "Versatility", "siddhi": "Mastery",
        "what_this_means": "Gate 16 is about identifying and developing skills. You have an enthusiasm for learning and a knack for recognizing talent—in yourself and others.",
        "your_challenge": "The challenge is staying with skills long enough to master them, and not spreading enthusiasm too thin. The excitement of new skills can overshadow depth.",
        "your_genius": "Your genius is in versatile skill development. You can become genuinely competent in multiple areas when your enthusiasm is sustained.",
        "practical_experiments": [
            "Notice which skills genuinely excite you versus which feel obligatory.",
            "Practice staying with a skill through the plateau phase.",
            "Track what skills you naturally identify in others—this reveals something about you."
        ],
        "remember": "Enthusiasm starts the journey. Discipline continues it. Mastery completes it."
    },
    17: {
        "name": "Opinions",
        "themes": ["following", "opinions", "organized thinking"],
        "shadow": "Opinion", "gift": "Far-sightedness", "siddhi": "Omniscience",
        "what_this_means": "Gate 17 is about organizing thoughts into coherent opinions. You have a mind that naturally structures understanding and can see patterns others miss.",
        "your_challenge": "The challenge is that opinions can become rigid positions, and the need to be right can override genuine understanding. Your mental organization might miss what can't be categorized.",
        "your_genius": "Your genius is in far-sighted thinking. When you share your organized perspective at the right time, you can help others see further than they could alone.",
        "practical_experiments": [
            "Notice when you're sharing insight versus defending a position.",
            "Practice holding opinions lightly enough to update them with new information.",
            "Track which of your opinions have stood the test of time."
        ],
        "remember": "Opinions are tools for understanding, not identities to defend."
    },
    18: {
        "name": "Correction",
        "themes": ["judgment", "improvement", "perfectionism"],
        "shadow": "Judgement", "gift": "Integrity", "siddhi": "Perfection",
        "what_this_means": "Gate 18 is about the drive to correct and improve. You naturally see what could be better and feel compelled to address it.",
        "your_challenge": "The challenge is that the corrective impulse can become harsh judgment of yourself or others. Not everything needs fixing, and timing matters for feedback.",
        "your_genius": "Your genius is in your capacity to improve things with integrity. When your corrections come from genuine care rather than criticism, they land differently.",
        "practical_experiments": [
            "Notice when correction serves improvement versus when it's just criticism.",
            "Practice asking if feedback is wanted before offering it.",
            "Track what happens when you apply your corrective eye to yourself with compassion."
        ],
        "remember": "The drive to correct is a gift when it serves growth, and a burden when it serves judgment."
    },
    19: {
        "name": "Wanting",
        "themes": ["sensitivity", "needs", "approaching others"],
        "shadow": "Co-dependence", "gift": "Sensitivity", "siddhi": "Sacrifice",
        "what_this_means": "Gate 19 is about sensitivity to needs—your own and others'. You naturally sense what's needed and have a strong drive to have those needs met.",
        "your_challenge": "The challenge is that sensitivity to needs can become neediness or over-giving. You might blur boundaries between your needs and others', or approach too intensely.",
        "your_genius": "Your genius is in your sensitivity. When balanced, you can sense and address needs that others miss, creating genuine support and connection.",
        "practical_experiments": [
            "Notice the difference between genuine needs and wants disguised as needs.",
            "Practice asking for what you need directly rather than hoping others will sense it.",
            "Track which needs are truly yours versus absorbed from your environment."
        ],
        "remember": "Sensitivity to needs is a gift. Codependence with needs is a trap."
    },
    20: {
        "name": "Now",
        "themes": ["presence", "metamorphosis", "present moment awareness"],
        "shadow": "Superficiality", "gift": "Self-Assurance", "siddhi": "Presence",
        "what_this_means": "Gate 20 is about the power of being fully present in the now. You have access to awareness that is entirely in this moment, without reference to past or future.",
        "your_challenge": "The challenge is that presence can appear superficial to those looking for depth in analysis. You might also struggle to plan or reflect when the now is all that feels real.",
        "your_genius": "Your genius is in present-moment awareness. Your capacity to be fully here makes you effective in situations that require immediate response.",
        "practical_experiments": [
            "Notice when presence feels powerful versus when it feels like avoidance.",
            "Practice distinguishing between genuine presence and distraction.",
            "Track what becomes possible when you're fully in the moment."
        ],
        "remember": "Presence isn't the absence of thought. It's the fullness of being here."
    },
    21: {
        "name": "Hunter",
        "themes": ["control", "material authority", "management"],
        "shadow": "Control", "gift": "Authority", "siddhi": "Valour",
        "what_this_means": "Gate 21 is about taking control of resources and situations. You carry a natural authority in managing what's under your domain.",
        "your_challenge": "The challenge is that control can become domination, and the hunter energy can become predatory rather than protective. Knowing when to control and when to release is key.",
        "your_genius": "Your genius is in effective resource management under your authority. When your control serves the whole rather than just yourself, your leadership is valued.",
        "practical_experiments": [
            "Notice when control serves the situation versus when it serves your ego.",
            "Practice releasing control in areas that aren't truly yours to manage.",
            "Track how others respond to your authority—what feedback emerges?"
        ],
        "remember": "Authority isn't about control. It's about being someone others can trust to manage things well."
    },
    22: {
        "name": "Grace",
        "themes": ["openness", "emotional charm", "social grace"],
        "shadow": "Dishonour", "gift": "Graciousness", "siddhi": "Grace",
        "what_this_means": "Gate 22 is about emotional openness and the capacity to charm. You carry a social grace that can open doors and create connections.",
        "your_challenge": "The challenge is that charm can become manipulation, and social grace can mask genuine feelings. The emotional waves of this gate can also create inconsistency.",
        "your_genius": "Your genius is in your graciousness. When you're genuinely open rather than performing, your natural charm creates authentic connection.",
        "practical_experiments": [
            "Notice when your grace is genuine versus when it's a social mask.",
            "Practice being socially open even when your emotional wave is low.",
            "Track which connections deepen through grace and which stay superficial."
        ],
        "remember": "True grace isn't about being charming. It's about being genuinely open."
    },
    23: {
        "name": "Assimilation",
        "themes": ["insight", "translation", "explaining complexity"],
        "shadow": "Complexity", "gift": "Simplicity", "siddhi": "Quintessence",
        "what_this_means": "Gate 23 is about translating complex insights into simple understanding. You have the capacity to assimilate and communicate ideas in accessible ways.",
        "your_challenge": "The challenge is that your insights might come before others are ready to hear them, or you might overcomplicate what could be simple. Timing is everything.",
        "your_genius": "Your genius is in simplification. When you share your insights at the right moment, you can make the complex understandable and actionable.",
        "practical_experiments": [
            "Notice when you're overcomplicating versus genuinely wrestling with complexity.",
            "Practice waiting until asked before sharing your simplified insights.",
            "Track which explanations land and what made them effective."
        ],
        "remember": "The best insights are simple, but getting to simplicity often requires moving through complexity."
    },
    24: {
        "name": "Rationalizing",
        "themes": ["returning thoughts", "mental breakthrough", "revisiting"],
        "shadow": "Addiction", "gift": "Invention", "siddhi": "Silence",
        "what_this_means": "Gate 24 is about the mind that returns and revisits. You naturally circle back to ideas, rationalizing and refining until breakthrough occurs.",
        "your_challenge": "The challenge is that returning can become rumination, and the quest for mental breakthrough can become addictive. Not every thought deserves repeated attention.",
        "your_genius": "Your genius is in mental persistence. Your capacity to revisit and refine can lead to genuine invention and understanding that single-pass thinking misses.",
        "practical_experiments": [
            "Notice which returning thoughts are productive and which are just loops.",
            "Practice releasing thoughts that have been processed enough.",
            "Track what conditions support genuine breakthrough versus spinning."
        ],
        "remember": "Returning is valuable when it refines. It's problematic when it just repeats."
    },
    25: {
        "name": "Innocence",
        "themes": ["spirit", "universal love", "unconditional acceptance"],
        "shadow": "Constriction", "gift": "Acceptance", "siddhi": "Universal Love",
        "what_this_means": "Gate 25 is about innocent acceptance and universal love. You carry a spirit that can love without conditions and accept without judgment.",
        "your_challenge": "The challenge is that unconditional acceptance can be naive, and the spirit of innocence can be wounded by a world that doesn't match it. Protecting your innocence while staying engaged is delicate.",
        "your_genius": "Your genius is in your capacity for acceptance. When you can hold universal love without losing discernment, you become a force for healing.",
        "practical_experiments": [
            "Notice when acceptance is genuine versus when it's avoidance of necessary boundaries.",
            "Practice maintaining innocence while still acknowledging reality.",
            "Track what happens to your spirit in different environments."
        ],
        "remember": "Innocence isn't naivety. It's the capacity to love without conditions even while seeing clearly."
    },
    26: {
        "name": "Taming",
        "themes": ["sales", "memory manipulation", "influence"],
        "shadow": "Pride", "gift": "Artfulness", "siddhi": "Invisibility",
        "what_this_means": "Gate 26 is about the art of influence and taming. You have a natural capacity to shape perception and memory, useful in sales, marketing, and persuasion.",
        "your_challenge": "The challenge is that influence can become manipulation, and pride in your ability can corrupt the gift. The line between artful persuasion and deception is thin.",
        "your_genius": "Your genius is in artful communication. When you use your influence in service of genuine value, you can move people toward what actually serves them.",
        "practical_experiments": [
            "Notice when your influence serves others versus when it serves your pride.",
            "Practice transparency about your persuasive abilities.",
            "Track the long-term effects of your influence—does it build trust?"
        ],
        "remember": "The greatest salespeople sell what genuinely helps. The rest just manipulate."
    },
    27: {
        "name": "Caring",
        "themes": ["nourishment", "caring for others", "nurturing"],
        "shadow": "Selfishness", "gift": "Altruism", "siddhi": "Selflessness",
        "what_this_means": "Gate 27 is about caring for and nourishing others. You carry a natural capacity to nurture and support, feeling fulfilled through genuine caregiving.",
        "your_challenge": "The challenge is that caring can become self-sacrifice, or you might care for others while neglecting yourself. The line between altruism and martyrdom matters.",
        "your_genius": "Your genius is in genuine nourishment. When your caring comes from fullness rather than depletion, you can sustainably support others.",
        "practical_experiments": [
            "Notice when caring depletes you versus when it fills you.",
            "Practice asking if care is wanted before providing it.",
            "Track the difference between caring from overflow versus from obligation."
        ],
        "remember": "You can't pour from an empty cup. Sustainable caring requires caring for yourself too."
    },
    28: {
        "name": "Struggle",
        "themes": ["risk-taking", "purpose through challenge", "game player"],
        "shadow": "Purposelessness", "gift": "Totality", "siddhi": "Immortality",
        "what_this_means": "Gate 28 is about finding purpose through struggle and risk. You're designed to engage fully with challenges, finding meaning in the game itself.",
        "your_challenge": "The challenge is that struggle can become the only mode of operation, or risks taken without purpose can be destructive. Not every fight is worth having.",
        "your_genius": "Your genius is in total engagement. When you choose your struggles wisely, your full commitment can achieve what half-hearted effort never could.",
        "practical_experiments": [
            "Notice which struggles give you energy and which deplete you.",
            "Practice discerning between meaningful risk and unnecessary danger.",
            "Track what happens when you commit totally versus when you hedge."
        ],
        "remember": "The struggle isn't the point—it's the crucible that reveals what matters."
    },
    29: {
        "name": "Saying Yes",
        "themes": ["commitment", "perseverance", "saying yes to life"],
        "shadow": "Half-heartedness", "gift": "Commitment", "siddhi": "Devotion",
        "what_this_means": "Gate 29 is about the power of saying yes and following through. You carry the energy of commitment—once you're in, you're in fully.",
        "your_challenge": "The challenge is saying yes too readily, or committing before you've checked if it's right for you. Half-hearted commitments drain everyone involved.",
        "your_genius": "Your genius is in wholehearted commitment. When you say yes to what's truly correct for you, your perseverance is remarkable.",
        "practical_experiments": [
            "Notice the difference between an authentic yes and a people-pleasing yes.",
            "Practice waiting before committing to check if it's genuinely right.",
            "Track which commitments energize you and which deplete you."
        ],
        "remember": "The power of yes requires the wisdom of no. Without discernment, commitment becomes obligation."
    },
    30: {
        "name": "Feelings",
        "themes": ["desire", "emotional depth", "feeling the extremes"],
        "shadow": "Desire", "gift": "Lightness", "siddhi": "Rapture",
        "what_this_means": "Gate 30 is about the full depth of emotional experience and desire. You feel things intensely and have access to emotional depths that others might avoid.",
        "your_challenge": "The challenge is that intense feelings can become overwhelming, or desire can become attachment. The emotional extremes of this gate require skillful navigation.",
        "your_genius": "Your genius is in emotional depth. Your capacity to feel fully, when channeled well, brings richness and meaning to experience.",
        "practical_experiments": [
            "Notice when desire is pointing toward something real versus just craving.",
            "Practice feeling fully without being controlled by feelings.",
            "Track your emotional rhythm—when do depths serve you and when do they swamp you?"
        ],
        "remember": "Depth of feeling is a gift, not a problem. The challenge is not to be ruled by it."
    },
    31: {
        "name": "Influence",
        "themes": ["leading", "verbal influence", "elected leadership"],
        "shadow": "Arrogance", "gift": "Leadership", "siddhi": "Humility",
        "what_this_means": "Gate 31 is about verbal influence and elected leadership. You have a natural capacity to lead through what you say, when others choose to follow.",
        "your_challenge": "The challenge is that leadership through influence requires being chosen—you can't force it. Arrogance about your leadership capacity undermines it.",
        "your_genius": "Your genius is in natural leadership. When you lead from genuine understanding rather than ego, others elect you to guide them.",
        "practical_experiments": [
            "Notice when you're leading because you're elected versus when you're forcing it.",
            "Practice speaking to influence without attachment to whether others follow.",
            "Track which contexts naturally elect your leadership."
        ],
        "remember": "True leadership is given, not taken. Your influence depends on others choosing to receive it."
    },
    32: {
        "name": "Continuity",
        "themes": ["duration", "transformation timing", "recognizing lasting value"],
        "shadow": "Failure", "gift": "Preservation", "siddhi": "Veneration",
        "what_this_means": "Gate 32 is about recognizing what has lasting value and ensuring continuity. You can sense what will endure and what won't, which is useful for investment of all kinds.",
        "your_challenge": "The challenge is fear of failure or change. You might cling to what's outlived its usefulness, or be too cautious about transformation.",
        "your_genius": "Your genius is in preservation instinct. You can sense what's worth keeping and what's ready to transform, which serves long-term success.",
        "practical_experiments": [
            "Notice what your instincts say about duration and transformation timing.",
            "Practice distinguishing between wise preservation and fear of change.",
            "Track which of your continuity assessments prove accurate over time."
        ],
        "remember": "Continuity isn't about avoiding change. It's about knowing what's worth preserving through change."
    },
    33: {
        "name": "Privacy",
        "themes": ["retreat", "reflection", "sharing in time"],
        "shadow": "Forgetting", "gift": "Mindfulness", "siddhi": "Revelation",
        "what_this_means": "Gate 33 is about the need for retreat and private reflection before sharing. You process experience deeply and need time before you're ready to communicate it.",
        "your_challenge": "The challenge is that retreat can become avoidance, or the processing period can extend indefinitely. Finding the right time to emerge and share matters.",
        "your_genius": "Your genius is in mindful reflection. What you share after deep processing often has more impact than immediate reaction.",
        "practical_experiments": [
            "Notice when retreat serves processing versus when it's avoidance.",
            "Practice honoring your need for privacy without isolation.",
            "Track how long your natural processing cycles last."
        ],
        "remember": "Privacy isn't hiding. It's preparing to share something worth sharing."
    },
    34: {
        "name": "Power",
        "themes": ["empowerment", "pure life force", "independent action"],
        "shadow": "Force", "gift": "Strength", "siddhi": "Majesty",
        "what_this_means": "Gate 34 is about raw power and life force energy. You have access to a pure energy that can accomplish things through sheer vitality.",
        "your_challenge": "The challenge is that power without direction can be destructive, or force can replace finesse. Your energy needs proper channeling.",
        "your_genius": "Your genius is in your life force. When your power serves something worth doing, you have remarkable capacity for sustained action.",
        "practical_experiments": [
            "Notice when your power is flowing freely versus when it's forced.",
            "Practice channeling your energy toward what genuinely matters.",
            "Track what conditions support healthy expression of your power."
        ],
        "remember": "Power is neutral. Its value depends entirely on what it serves."
    },
    35: {
        "name": "Change",
        "themes": ["experience", "adventure", "craving progress"],
        "shadow": "Hunger", "gift": "Adventure", "siddhi": "Boundlessness",
        "what_this_means": "Gate 35 is about the hunger for new experience and change. You crave progress and adventure, feeling most alive when exploring new territory.",
        "your_challenge": "The challenge is that hunger for the new can become endless seeking without satisfaction. Change for its own sake isn't necessarily progress.",
        "your_genius": "Your genius is in your appetite for adventure. Your willingness to seek new experience can lead to discoveries others wouldn't make.",
        "practical_experiments": [
            "Notice when the craving for change serves growth versus when it's just restlessness.",
            "Practice sitting with stability long enough to know if change is really needed.",
            "Track which adventures fulfill you and which leave you still hungry."
        ],
        "remember": "The hunger for change is a compass, not a destination. What you're seeking is sometimes already here."
    },
    36: {
        "name": "Crisis",
        "themes": ["emotional learning", "growth through difficulty", "darkening of the light"],
        "shadow": "Turbulence", "gift": "Humanity", "siddhi": "Compassion",
        "what_this_means": "Gate 36 is about growth through emotional difficulty and crisis. You're designed to move through darkness toward light, gaining wisdom along the way.",
        "your_challenge": "The challenge is that crisis can become a pattern rather than a portal. You might create turbulence or seek it out beyond what serves growth.",
        "your_genius": "Your genius is in the humanity you develop through difficulty. Your emotional experience, when processed, becomes wisdom you can offer others.",
        "practical_experiments": [
            "Notice when crisis is growth-producing versus when it's just drama.",
            "Practice moving through difficulty without identifying with it.",
            "Track what wisdom emerges from your emotional experiences."
        ],
        "remember": "Crisis is a teacher, not an identity. What matters is what you learn, not how much you suffer."
    },
    37: {
        "name": "Community",
        "themes": ["family", "bargains", "community building"],
        "shadow": "Weakness", "gift": "Equality", "siddhi": "Tenderness",
        "what_this_means": "Gate 37 is about creating and maintaining community through clear agreements. You have a natural sense for what makes groups function well.",
        "your_challenge": "The challenge is that community building requires negotiation, and agreements can become controlling. Maintaining boundaries while staying connected is delicate.",
        "your_genius": "Your genius is in creating equality within groups. When you establish fair agreements, you build communities that sustain.",
        "practical_experiments": [
            "Notice which community agreements serve everyone versus which serve only some.",
            "Practice renegotiating agreements when they no longer fit.",
            "Track what makes your communities thrive versus what makes them struggle."
        ],
        "remember": "Community isn't about agreement on everything. It's about agreements that allow difference to coexist."
    },
    38: {
        "name": "The Fighter",
        "themes": ["opposition", "finding purpose through struggle", "stubbornness"],
        "shadow": "Struggle", "gift": "Perseverance", "siddhi": "Honour",
        "what_this_means": "Gate 38 is about the fighter energy—finding purpose through opposition and struggle. You're designed to push against things that need pushing.",
        "your_challenge": "The challenge is that fighting can become the only mode of engagement, or stubbornness can replace discernment about what's worth fighting for.",
        "your_genius": "Your genius is in your perseverance. When you fight for what genuinely matters, your stubbornness becomes an asset.",
        "practical_experiments": [
            "Notice which fights give you purpose and which just drain you.",
            "Practice discerning between stubbornness and commitment.",
            "Track what happens when you choose your battles more selectively."
        ],
        "remember": "The fighter's gift isn't in fighting everything. It's in knowing what's worth the fight."
    },
    39: {
        "name": "Provocation",
        "themes": ["provoking spirit", "testing resolve", "emotional activation"],
        "shadow": "Provocation", "gift": "Dynamism", "siddhi": "Liberation",
        "what_this_means": "Gate 39 is about provocation as a way of testing and activating. You naturally stir things up to see what's real and what's pretense.",
        "your_challenge": "The challenge is that provocation can become destructive rather than revealing. Not everyone is ready to be tested, and timing matters.",
        "your_genius": "Your genius is in your dynamism. When you provoke skillfully, you reveal truth and activate potential that would otherwise stay dormant.",
        "practical_experiments": [
            "Notice when your provocation serves revelation versus when it just creates chaos.",
            "Practice asking if provocation is wanted or appropriate in different contexts.",
            "Track what emerges through your provocations—is it useful?"
        ],
        "remember": "Provocation is a tool for truth, not a personality to perform."
    },
    40: {
        "name": "Aloneness",
        "themes": ["delivery", "willpower for community", "solitude within connection"],
        "shadow": "Exhaustion", "gift": "Resolve", "siddhi": "Divine Will",
        "what_this_means": "Gate 40 is about finding aloneness within community—contributing from your own center. You have the willpower to deliver on commitments when they're right for you.",
        "your_challenge": "The challenge is exhaustion from over-giving, or withdrawing completely rather than finding balance. Your alone time is necessary, not negotiable.",
        "your_genius": "Your genius is in your resolve. When you contribute from genuine willingness rather than obligation, your delivery is powerful.",
        "practical_experiments": [
            "Notice when you're giving from resolve versus when you're giving from exhaustion.",
            "Practice protecting your alone time as essential, not optional.",
            "Track what happens to your delivery when you're properly recharged."
        ],
        "remember": "Aloneness isn't isolation. It's the center from which you can genuinely contribute."
    },
    41: {
        "name": "Fantasy",
        "themes": ["imagination", "new feelings", "possibility through dreaming"],
        "shadow": "Fantasy", "gift": "Anticipation", "siddhi": "Emanation",
        "what_this_means": "Gate 41 is about the power of imagination and anticipation. You have access to feelings about possibilities—dreams of what could be.",
        "your_challenge": "The challenge is that fantasy can substitute for reality, or anticipation can become more exciting than actual experience. Grounding dreams into action matters.",
        "your_genius": "Your genius is in your capacity to anticipate possibility. Your dreams, when acted upon, can become genuinely new creations.",
        "practical_experiments": [
            "Notice which fantasies point toward something real and which are just escape.",
            "Practice taking small actions toward your anticipated possibilities.",
            "Track which dreams survive contact with reality."
        ],
        "remember": "Fantasy is the seed of creation when it leads to action. It's escapism when it doesn't."
    },
    42: {
        "name": "Completion",
        "themes": ["growth", "finishing cycles", "maximizing experience"],
        "shadow": "Expectation", "gift": "Detachment", "siddhi": "Celebration",
        "what_this_means": "Gate 42 is about completing cycles and finishing what you start. You have a natural capacity to bring things to conclusion and harvest their lessons.",
        "your_challenge": "The challenge is expectations about how completion should look, or difficulty letting go when cycles truly end. Not everything finishes the way you expect.",
        "your_genius": "Your genius is in your capacity for completion. When you finish cycles cleanly, you free energy for what's next.",
        "practical_experiments": [
            "Notice which cycles are genuinely complete versus which you're abandoning.",
            "Practice releasing expectations about how endings should look.",
            "Track what becomes possible after clean completions."
        ],
        "remember": "Completion isn't just ending. It's harvesting the full value of what's been experienced."
    },
    43: {
        "name": "Insight",
        "themes": ["breakthrough", "unique perspective", "inner truth"],
        "shadow": "Deafness", "gift": "Insight", "siddhi": "Epiphany",
        "what_this_means": "Gate 43 is about breakthrough insights that come from within. You have access to a kind of knowing that doesn't follow logical steps—it simply arrives.",
        "your_challenge": "The challenge is that your insights might not be immediately understood by others, and the timing of sharing matters enormously. You might also become deaf to perspectives outside your insight.",
        "your_genius": "Your genius is in your unique knowing. When your insights are shared at the right moment, they can shift everything.",
        "practical_experiments": [
            "Notice when your insights are ready to be shared versus when they need more time.",
            "Practice listening to others' perspectives even when your insight feels complete.",
            "Track which insights stand the test of time."
        ],
        "remember": "Insight is a gift that depends on timing. The right truth at the wrong time is still ineffective."
    },
    44: {
        "name": "Alertness",
        "themes": ["patterns", "memory of success", "instinctive alertness"],
        "shadow": "Interference", "gift": "Teamwork", "siddhi": "Synarchy",
        "what_this_means": "Gate 44 is about instinctive alertness to patterns and what works. You carry memories of success that inform present awareness.",
        "your_challenge": "The challenge is that pattern recognition can become interference when you project the past onto the present inappropriately. Not every similar situation has the same solution.",
        "your_genius": "Your genius is in pattern awareness. Your instincts about what works can serve teams and collaborations when offered appropriately.",
        "practical_experiments": [
            "Notice when your pattern recognition serves versus when it interferes.",
            "Practice checking if the current situation actually matches past patterns.",
            "Track how often your instinctive alerts prove accurate."
        ],
        "remember": "Pattern recognition is useful when it informs. It's limiting when it predetermines."
    },
    45: {
        "name": "The King/Queen",
        "themes": ["gathering", "natural leadership", "material sovereignty"],
        "shadow": "Dominance", "gift": "Synergy", "siddhi": "Communion",
        "what_this_means": "Gate 45 is about natural material leadership and gathering resources. You have an energy that draws people and resources toward shared goals.",
        "your_challenge": "The challenge is that the gathering energy can become dominance, or you might identify too strongly with being the center. True sovereignty serves the whole.",
        "your_genius": "Your genius is in creating synergy. When you gather and lead from genuine service rather than ego, remarkable things become possible.",
        "practical_experiments": [
            "Notice when your gathering serves the whole versus when it serves your ego.",
            "Practice leading without needing to be the center of attention.",
            "Track what makes your gatherings succeed versus struggle."
        ],
        "remember": "The true ruler serves the kingdom. Dominance without service is just tyranny."
    },
    46: {
        "name": "Body",
        "themes": ["determination", "physical expression", "love of the body"],
        "shadow": "Seriousness", "gift": "Delight", "siddhi": "Ecstasy",
        "what_this_means": "Gate 46 is about loving and expressing through the body. You have a deep connection to physical experience and its capacity for joy.",
        "your_challenge": "The challenge is taking the body too seriously or not seriously enough. Physical expression needs both care and playfulness.",
        "your_genius": "Your genius is in physical delight. When you inhabit your body fully, you experience and transmit joy that mental life can't access.",
        "practical_experiments": [
            "Notice when you're fully in your body versus when you're dissociated from it.",
            "Practice physical activities that bring genuine delight, not just obligation.",
            "Track how your body awareness affects your overall wellbeing."
        ],
        "remember": "The body isn't just a vehicle for the mind. It's a source of wisdom and joy in its own right."
    },
    47: {
        "name": "Realization",
        "themes": ["understanding", "mental clarity through time", "sense-making"],
        "shadow": "Oppression", "gift": "Transmutation", "siddhi": "Transfiguration",
        "what_this_means": "Gate 47 is about realizing understanding over time. You have the capacity to transmute confusion into clarity, though it often takes longer than you'd like.",
        "your_challenge": "The challenge is the oppression of not understanding when you want to. The pressure to make sense of things before they're ready to be understood.",
        "your_genius": "Your genius is in eventual realization. When you trust the process, understanding arrives in its own time—often more complete than forced conclusions.",
        "practical_experiments": [
            "Notice when you're forcing understanding versus when you're allowing it.",
            "Practice sitting with confusion as part of the realization process.",
            "Track how long different types of understanding take to arrive."
        ],
        "remember": "Realization can't be rushed. The understanding that arrives in its own time is usually more complete."
    },
    48: {
        "name": "Depth",
        "themes": ["skill", "depth of mastery", "fear of inadequacy"],
        "shadow": "Inadequacy", "gift": "Resourcefulness", "siddhi": "Wisdom",
        "what_this_means": "Gate 48 is about deep skill and the fear of being inadequate. You have potential for profound mastery, but also sensitivity to whether you know enough.",
        "your_challenge": "The challenge is that fear of inadequacy can prevent you from sharing what you actually know. You might wait forever to feel 'ready.'",
        "your_genius": "Your genius is in your depth. When you share from your genuine knowledge without waiting for perfection, your resourcefulness serves others.",
        "practical_experiments": [
            "Notice when fear of inadequacy is protecting you versus holding you back.",
            "Practice sharing what you know without claiming to know everything.",
            "Track where your genuine depth lies—what do you actually know well?"
        ],
        "remember": "Adequacy isn't about knowing everything. It's about offering what you genuinely have."
    },
    49: {
        "name": "Revolution",
        "themes": ["principles", "rejection and acceptance", "social change"],
        "shadow": "Reaction", "gift": "Revolution", "siddhi": "Rebirth",
        "what_this_means": "Gate 49 is about revolutionary change based on principles. You have a strong sense of what's acceptable and what needs to change.",
        "your_challenge": "The challenge is that reaction can substitute for genuine revolution, or you might reject things prematurely. Knowing when change is necessary requires discernment.",
        "your_genius": "Your genius is in principled transformation. When you act from genuine values rather than reaction, your revolutionary energy creates lasting change.",
        "practical_experiments": [
            "Notice when you're reacting versus when you're responding to genuine principle.",
            "Practice discerning between necessary revolution and unnecessary disruption.",
            "Track what changes you create that actually last."
        ],
        "remember": "Revolution without principle is just chaos. Principle without action is just opinion."
    },
    50: {
        "name": "Values",
        "themes": ["responsibility", "nurturing values", "guardianship"],
        "shadow": "Corruption", "gift": "Equilibrium", "siddhi": "Harmony",
        "what_this_means": "Gate 50 is about taking responsibility for values and their preservation. You have a natural sense of what needs to be protected and maintained.",
        "your_challenge": "The challenge is that responsibility can become burden, or values can become rigid rules. Finding equilibrium between protection and flexibility matters.",
        "your_genius": "Your genius is in values guardianship. When you hold values with both firmness and adaptability, you create conditions for harmony.",
        "practical_experiments": [
            "Notice which values you're genuinely responsible for versus which you've adopted.",
            "Practice holding values firmly without rigidity.",
            "Track what happens when your values create equilibrium versus tension."
        ],
        "remember": "Values worth protecting are also worth questioning. Guardianship includes knowing when to adapt."
    },
    51: {
        "name": "Shock",
        "themes": ["initiative", "competitive spirit", "being first"],
        "shadow": "Agitation", "gift": "Initiative", "siddhi": "Awakening",
        "what_this_means": "Gate 51 is about the willingness to initiate and shock. You carry competitive energy that wants to go first and wake things up.",
        "your_challenge": "The challenge is that initiative can become agitation, or the need to be first can override wisdom about timing. Shocking for shock's sake serves no one.",
        "your_genius": "Your genius is in your initiative. When your competitive energy serves awakening rather than ego, you can catalyze genuine breakthroughs.",
        "practical_experiments": [
            "Notice when your initiative serves awakening versus when it just causes disruption.",
            "Practice discerning between competition that elevates and competition that diminishes.",
            "Track what happens when you channel your shock energy purposefully."
        ],
        "remember": "The power to shock is neutral. Its value depends entirely on what it awakens."
    },
    52: {
        "name": "Stillness",
        "themes": ["concentration", "mountain energy", "inaction as action"],
        "shadow": "Stress", "gift": "Restraint", "siddhi": "Stillness",
        "what_this_means": "Gate 52 is about the power of stillness and concentrated inaction. You have access to a groundedness that doesn't need to move to be powerful.",
        "your_challenge": "The challenge is that stillness can become stagnation, or the pressure of stress can make stillness feel impossible. Knowing when to be still takes wisdom.",
        "your_genius": "Your genius is in restraint. When you choose stillness from strength rather than avoidance, your concentrated presence has power.",
        "practical_experiments": [
            "Notice when stillness is powerful versus when it's avoidance.",
            "Practice being still even under pressure, when appropriate.",
            "Track what becomes possible through concentrated stillness."
        ],
        "remember": "Stillness isn't inactivity. It's concentrated presence that doesn't waste energy on unnecessary movement."
    },
    53: {
        "name": "Starting",
        "themes": ["beginnings", "cycles", "pressure to start"],
        "shadow": "Immaturity", "gift": "Expansion", "siddhi": "Superabundance",
        "what_this_means": "Gate 53 is about the pressure and excitement of new beginnings. You carry the energy that starts cycles, feeling the pull toward what's next.",
        "your_challenge": "The challenge is that starting can become a pattern that avoids completion, or immaturity can rush into beginnings without preparation.",
        "your_genius": "Your genius is in expansion through beginnings. When you start things that are genuinely ready to begin, you open possibilities others wouldn't.",
        "practical_experiments": [
            "Notice when the urge to start comes from genuine readiness versus avoidance of current cycles.",
            "Practice completing current cycles before beginning new ones.",
            "Track which of your beginnings lead to expansion versus fragmentation."
        ],
        "remember": "The power of starting depends on what you start and when. Not every impulse to begin should be followed."
    },
    54: {
        "name": "Ambition",
        "themes": ["drive", "rising up", "transforming circumstances"],
        "shadow": "Greed", "gift": "Aspiration", "siddhi": "Ascension",
        "what_this_means": "Gate 54 is about the drive to rise and transform your circumstances. You carry an ambition that wants to elevate—yourself and potentially others.",
        "your_challenge": "The challenge is that ambition can become greed, or the drive to rise can lose connection with purpose. Elevation without service is hollow.",
        "your_genius": "Your genius is in aspiration. When your ambition serves something larger than personal gain, your drive to rise lifts others too.",
        "practical_experiments": [
            "Notice when ambition serves growth versus when it serves greed.",
            "Practice aspiring toward things that would benefit more than just yourself.",
            "Track what happens when you align ambition with purpose."
        ],
        "remember": "Ambition is fuel. What matters is where you direct it."
    },
    55: {
        "name": "Spirit",
        "themes": ["emotional range", "spirit in emotion", "abundance and melancholy"],
        "shadow": "Victimization", "gift": "Freedom", "siddhi": "Freedom",
        "what_this_means": "Gate 55 is about experiencing spirit through the full range of emotion. You feel deeply—both abundance and melancholy—as expressions of being alive.",
        "your_challenge": "The challenge is that emotional intensity can feel like victimization, or you might try to escape the low tides. The full range is the gift.",
        "your_genius": "Your genius is in emotional freedom. When you embrace the full spectrum without being imprisoned by any state, you access genuine spirit.",
        "practical_experiments": [
            "Notice when you're feeling your emotions versus when you're identified with them.",
            "Practice allowing all emotional states without trying to fix or escape them.",
            "Track how your emotional range connects to your sense of spirit and aliveness."
        ],
        "remember": "The spirit isn't found by escaping emotion. It's found by experiencing emotion fully without losing yourself in it."
    },
    56: {
        "name": "Stimulation",
        "themes": ["storytelling", "stimulating others", "belief transmission"],
        "shadow": "Distraction", "gift": "Enrichment", "siddhi": "Intoxication",
        "what_this_means": "Gate 56 is about the power of storytelling and stimulating experience. You can weave narratives and beliefs that capture attention and create meaning.",
        "your_challenge": "The challenge is that storytelling can become distraction, or stimulation can substitute for substance. Not every engaging story is true.",
        "your_genius": "Your genius is in enrichment through narrative. When your stories serve truth rather than just entertainment, they can genuinely transform understanding.",
        "practical_experiments": [
            "Notice when your storytelling enriches versus when it just distracts.",
            "Practice discerning between stories worth telling and stories that just fill space.",
            "Track what happens when you use your narrative gifts in service of truth."
        ],
        "remember": "The power to captivate through story is a responsibility. Enrichment matters more than entertainment."
    },
    57: {
        "name": "Intuition",
        "themes": ["clarity", "gentle penetration", "intuitive knowing"],
        "shadow": "Unease", "gift": "Intuition", "siddhi": "Clarity",
        "what_this_means": "Gate 57 is about intuitive knowing that comes gently but clearly. You have access to a kind of awareness that penetrates situations softly.",
        "your_challenge": "The challenge is that intuition speaks quietly and doesn't repeat itself. You might miss it or second-guess it into silence.",
        "your_genius": "Your genius is in your intuitive clarity. When you learn to hear and trust its gentle voice, you navigate with remarkable precision.",
        "practical_experiments": [
            "Notice how your intuition communicates—what does its voice sound like?",
            "Practice trusting intuitive knowing before logic has time to override it.",
            "Track how accurate your intuitive hits are over time."
        ],
        "remember": "Intuition is a whisper, not a shout. Learning to hear it requires slowing down enough to listen."
    },
    58: {
        "name": "Joy",
        "themes": ["vitality", "aliveness", "correcting for joy"],
        "shadow": "Dissatisfaction", "gift": "Vitality", "siddhi": "Bliss",
        "what_this_means": "Gate 58 is about the drive toward joy and vitality. You have energy that naturally seeks what feels alive and corrects what doesn't.",
        "your_challenge": "The challenge is that the seeking can become chronic dissatisfaction, or the corrective impulse can become criticism. Joy requires acceptance alongside improvement.",
        "your_genius": "Your genius is in your vitality. When you follow what genuinely brings life rather than just critiquing what doesn't, you become a source of aliveness.",
        "practical_experiments": [
            "Notice when correction serves joy versus when it just feeds dissatisfaction.",
            "Practice appreciating what's already alive alongside what could be improved.",
            "Track what actually brings you vitality versus what you think should."
        ],
        "remember": "Joy isn't found by fixing everything. It's found by fully receiving what's already alive."
    },
    59: {
        "name": "Intimacy",
        "themes": ["sexuality", "breaking barriers", "genetic strategy"],
        "shadow": "Dishonesty", "gift": "Intimacy", "siddhi": "Transparency",
        "what_this_means": "Gate 59 is about the drive toward intimacy and breaking through barriers between people. You have energy that dissolves separation and creates connection.",
        "your_challenge": "The challenge is that intimacy requires honesty, and the barrier-breaking energy can override appropriate boundaries. Not every wall should come down.",
        "your_genius": "Your genius is in creating genuine intimacy. When your openness is balanced with discernment, you can build connections of remarkable depth.",
        "practical_experiments": [
            "Notice when your intimacy-seeking serves connection versus when it overrides boundaries.",
            "Practice honesty as the foundation of genuine intimacy.",
            "Track which barriers are meant to dissolve and which are protective."
        ],
        "remember": "True intimacy requires transparency. But transparency without discernment is just exposure."
    },
    60: {
        "name": "Acceptance",
        "themes": ["limitation", "accepting what is", "mutation through acceptance"],
        "shadow": "Limitation", "gift": "Realism", "siddhi": "Justice",
        "what_this_means": "Gate 60 is about accepting limitations as the ground from which change becomes possible. You understand that mutation requires first accepting what is.",
        "your_challenge": "The challenge is that acceptance can become resignation, or you might fight limitations that are actually useful. Not all constraints are problems.",
        "your_genius": "Your genius is in realistic assessment. When you accept genuine limitations without being defeated by them, you find freedom within form.",
        "practical_experiments": [
            "Notice which limitations are genuine constraints versus which are self-imposed.",
            "Practice accepting what can't be changed while changing what can.",
            "Track what becomes possible through acceptance rather than resistance."
        ],
        "remember": "Acceptance isn't giving up. It's starting from reality rather than fantasy."
    },
    61: {
        "name": "Mystery",
        "themes": ["inner truth", "pressure to know", "mystery contemplation"],
        "shadow": "Psychosis", "gift": "Inspiration", "siddhi": "Sanctity",
        "what_this_means": "Gate 61 is about the drive to know the unknowable—to contemplate mystery. You feel pressure to understand deep truths that may not have simple answers.",
        "your_challenge": "The challenge is that the pressure to know can become obsessive, or you might confuse your mental constructs with actual truth. Mystery doesn't always resolve.",
        "your_genius": "Your genius is in inspired contemplation. When you hold questions without forcing answers, insight arrives in its own time.",
        "practical_experiments": [
            "Notice when the pressure to know serves understanding versus when it creates anxiety.",
            "Practice holding questions without demanding immediate answers.",
            "Track what inspires you to contemplate—what mysteries keep calling?"
        ],
        "remember": "Some truths are meant to be contemplated, not concluded. The mystery itself is sometimes the point."
    },
    62: {
        "name": "Details",
        "themes": ["precision", "naming things", "expressing facts"],
        "shadow": "Intellect", "gift": "Precision", "siddhi": "Impeccability",
        "what_this_means": "Gate 62 is about precision in naming and expressing details. You have a capacity for articulating facts and information with accuracy.",
        "your_challenge": "The challenge is that precision can become pedantry, or intellectual accuracy can override emotional truth. Not everything important can be named exactly.",
        "your_genius": "Your genius is in precise expression. When you name things accurately without losing the forest for the trees, your clarity serves understanding.",
        "practical_experiments": [
            "Notice when precision serves communication versus when it just shows off.",
            "Practice discerning which details matter and which can be released.",
            "Track when your precise expression lands and when it creates distance."
        ],
        "remember": "Precision is valuable in service of understanding. It's pedantry when it substitutes for connection."
    },
    63: {
        "name": "Doubt",
        "themes": ["questioning", "logical pressure", "after completion"],
        "shadow": "Doubt", "gift": "Inquiry", "siddhi": "Truth",
        "what_this_means": "Gate 63 is about the logical mind that questions and doubts. You carry pressure to make sure things make sense, which can serve truth or create paralysis.",
        "your_challenge": "The challenge is that doubt can become chronic, preventing action even when enough information exists. The logical mind is never fully satisfied.",
        "your_genius": "Your genius is in genuine inquiry. When your questioning serves understanding rather than avoidance, you can find truths others miss.",
        "practical_experiments": [
            "Notice when doubt serves verification versus when it prevents action.",
            "Practice recognizing 'enough' certainty without waiting for absolute proof.",
            "Track which doubts prove useful and which just create delay."
        ],
        "remember": "Doubt is a tool for truth-finding. It becomes a trap when it's used to avoid commitment."
    },
    64: {
        "name": "Confusion",
        "themes": ["mental pressure", "before completion", "transition contemplation"],
        "shadow": "Confusion", "gift": "Imagination", "siddhi": "Illumination",
        "what_this_means": "Gate 64 is about the mental pressure that comes before understanding—the confusion that precedes clarity. You contemplate transitions and endings.",
        "your_challenge": "The challenge is that confusion can feel overwhelming, or you might try to force clarity before it's ready. The pressure to understand is intense here.",
        "your_genius": "Your genius is in your imagination. When you allow confusion to transform rather than fighting it, illumination can arrive.",
        "practical_experiments": [
            "Notice when confusion is productive processing versus just spinning.",
            "Practice sitting with not-knowing without forcing premature conclusions.",
            "Track how long your confusion cycles last before clarity emerges."
        ],
        "remember": "Confusion often precedes insight. The darkness before dawn is real, but so is the dawn."
    }
}


class GateInterpretation(TypedDict):
    """Full interpretation for a single defined gate."""
    gate_number: int
    line_numbers_present: List[int]
    center_name: str
    gate_name: str
    themes: List[str]
    shadow: str
    gift: str
    siddhi: str
    what_this_means: str
    your_challenge: str
    your_genius: str
    practical_experiments: List[str]
    remember: str


def get_gate_interpretation(
    gate_number: int,
    line_numbers: List[int]
) -> GateInterpretation:
    """Get interpretation for a single gate.
    
    Args:
        gate_number: The gate number (1-64)
        line_numbers: List of line numbers present for this gate
    
    Returns:
        GateInterpretation with all fields populated
    """
    gate_data = GATE_DATA.get(gate_number)
    center_name = GATE_TO_CENTER.get(gate_number, "Unknown")
    
    if not gate_data:
        # Fallback for any missing gates
        return {
            "gate_number": gate_number,
            "line_numbers_present": line_numbers,
            "center_name": center_name,
            "gate_name": f"Gate {gate_number}",
            "themes": ["exploration", "discovery"],
            "shadow": "Unknown",
            "gift": "Unknown", 
            "siddhi": "Unknown",
            "what_this_means": f"Gate {gate_number} carries unique energy that expresses through the {center_name}.",
            "your_challenge": "Understanding this gate takes experimentation and observation.",
            "your_genius": "Every gate carries gifts waiting to be discovered.",
            "practical_experiments": [
                "Notice how this energy shows up in your life.",
                "Observe when this gate feels active or dormant.",
                "Track patterns in how this energy expresses."
            ],
            "remember": "Your gates are doorways to understanding yourself more deeply."
        }
    
    return {
        "gate_number": gate_number,
        "line_numbers_present": line_numbers,
        "center_name": center_name,
        "gate_name": gate_data["name"],
        "themes": gate_data["themes"],
        "shadow": gate_data["shadow"],
        "gift": gate_data["gift"],
        "siddhi": gate_data["siddhi"],
        "what_this_means": gate_data["what_this_means"],
        "your_challenge": gate_data["your_challenge"],
        "your_genius": gate_data["your_genius"],
        "practical_experiments": gate_data["practical_experiments"],
        "remember": gate_data["remember"]
    }


def build_defined_gates(
    active_gates: List[int],
    personality_gates: List[dict] = None,
    design_gates: List[dict] = None
) -> List[GateInterpretation]:
    """Build interpretations for all defined gates.
    
    Args:
        active_gates: List of all active gate numbers
        personality_gates: List of personality gate data (optional, for line info)
        design_gates: List of design gate data (optional, for line info)
    
    Returns:
        List of GateInterpretation for all active gates
    """
    # Build line mapping from personality and design gates
    gate_lines: Dict[int, List[int]] = {}
    
    # Process personality gates
    if personality_gates:
        for pg in personality_gates:
            gate_num = pg.get('gate') if isinstance(pg, dict) else pg
            if isinstance(pg, dict):
                gate_info = pg.get('gate', {})
                if isinstance(gate_info, dict):
                    gate_num = gate_info.get('gate', gate_num)
                    line = gate_info.get('line', 1)
                else:
                    gate_num = gate_info
                    line = pg.get('line', 1)
            else:
                line = 1
            
            if gate_num:
                if gate_num not in gate_lines:
                    gate_lines[gate_num] = []
                if line and line not in gate_lines[gate_num]:
                    gate_lines[gate_num].append(line)
    
    # Process design gates
    if design_gates:
        for dg in design_gates:
            gate_num = dg.get('gate') if isinstance(dg, dict) else dg
            if isinstance(dg, dict):
                gate_info = dg.get('gate', {})
                if isinstance(gate_info, dict):
                    gate_num = gate_info.get('gate', gate_num)
                    line = gate_info.get('line', 1)
                else:
                    gate_num = gate_info
                    line = dg.get('line', 1)
            else:
                line = 1
            
            if gate_num:
                if gate_num not in gate_lines:
                    gate_lines[gate_num] = []
                if line and line not in gate_lines[gate_num]:
                    gate_lines[gate_num].append(line)
    
    # Build interpretations for each active gate
    gates = []
    for gate_num in sorted(set(active_gates)):
        lines = gate_lines.get(gate_num, [1])  # Default to line 1 if no line info
        interpretation = get_gate_interpretation(gate_num, lines)
        gates.append(interpretation)
    
    return gates
