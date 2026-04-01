"""Lens Diagnosis Engine V3.2 - Mirror-Level Diagnosis Quality

CORE PRINCIPLE: Name the pattern being lived, not explain it.
User should feel: "This is exactly what I'm doing right now"

V3.2 RULES:
1. Name internal conflict directly - "part of you wants X, another part knows Y"
2. No teaching tone, no "this may feel like"
3. Use contradiction/tension as the driver
4. Ground in real behavior (decisions, reactions, conversations, timing)
5. Gene Key Shadow/Gift tension drives the HD narrative
6. Better Move shows consequences, not commands
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# GENE KEY DATA
# =============================================================================

try:
    from data.gene_keys_data import GENE_KEYS
except ImportError:
    GENE_KEYS = {}


def get_gene_key_for_gate(gate_number: int) -> Dict[str, Any]:
    """Get Gene Key data for a gate number (1:1 mapping)."""
    return GENE_KEYS.get(gate_number, {
        "gene_key": gate_number,
        "shadow": "Unknown",
        "gift": "Unknown",
        "siddhi": "Unknown",
    })


# =============================================================================
# V3.2: GENE KEY TENSION NARRATIVES - Shadow vs Gift as real-world conflict
# =============================================================================

GENE_KEY_TENSION_NARRATIVES = {
    # Gate 1: Self-Expression
    1: {
        "shadow": "Entropy",
        "gift": "Freshness", 
        "tension": "Part of you wants to create something new—but another part keeps pulling back into what's familiar. The stale path feels safer. It isn't.",
        "misstep": "recycling old approaches because new ones feel risky",
        "wise": "The fresh move is sitting right there. You keep looking past it because it doesn't come with guarantees.",
    },
    # Gate 2: Direction
    2: {
        "shadow": "Dislocation",
        "gift": "Orientation",
        "tension": "You know something about where this needs to go—but you can't explain it yet. The pressure to justify your sense of direction is distorting it.",
        "misstep": "explaining yourself before you're ready, diluting what you actually know",
        "wise": "Your sense of direction doesn't need defending. It needs following.",
    },
    # Gate 3: Ordering
    3: {
        "shadow": "Chaos",
        "gift": "Innovation",
        "tension": "Everything feels disordered—and part of you wants to force structure onto it. But this chaos isn't a problem to fix. It's something trying to emerge.",
        "misstep": "imposing order too early, killing what's trying to form",
        "wise": "Stay in the mess a little longer. The new pattern will show itself when you stop forcing the old one.",
    },
    # Gate 4: Formulization
    4: {
        "shadow": "Intolerance",
        "gift": "Understanding",
        "tension": "You're certain you're right—and frustrated that others don't see it. But certainty isn't the same as truth. The gap between them is costing you.",
        "misstep": "dismissing perspectives that don't match your mental model",
        "wise": "Being right matters less than being understood. And understanding requires listening first.",
    },
    # Gate 5: Fixed Rhythms
    5: {
        "shadow": "Impatience",
        "gift": "Patience",
        "tension": "You want it to happen now—but the timing isn't yours to control. The impatience is real, but acting on it won't speed anything up.",
        "misstep": "forcing the timeline because waiting feels unbearable",
        "wise": "This has its own rhythm. Fighting it creates friction. Matching it creates flow.",
    },
    # Gate 6: Friction
    6: {
        "shadow": "Conflict",
        "gift": "Diplomacy",
        "tension": "There's friction building—and part of you wants to force it open. But pushing into conflict before it's ready creates more damage than clarity.",
        "misstep": "starting the hard conversation when you're reactive, not ready",
        "wise": "The confrontation might be necessary. The timing might not be now.",
    },
    # Gate 7: The Role of the Self
    7: {
        "shadow": "Division",
        "gift": "Guidance",
        "tension": "You see what needs to happen—but no one asked. The urge to lead is real, but leading without invitation creates resistance instead of movement.",
        "misstep": "taking charge when you haven't been chosen",
        "wise": "When they're ready to be led, they'll turn to you. Until then, your job is to stay ready.",
    },
    # Gate 8: Contribution
    8: {
        "shadow": "Mediocrity",
        "gift": "Style",
        "tension": "Part of you wants to play it safe—fit in, don't stand out. But playing small isn't protecting you. It's costing you.",
        "misstep": "dimming yourself to avoid judgment",
        "wise": "Your difference is your contribution. Hiding it helps no one.",
    },
    # Gate 9: Focus
    9: {
        "shadow": "Inertia",
        "gift": "Determination",
        "tension": "You know what needs attention—but the pull toward distraction is strong. The resistance isn't about the task. It's about what the task represents.",
        "misstep": "scattering energy to avoid the one thing that actually matters",
        "wise": "Pick the one thing. Stay on it. Watch what shifts.",
    },
    # Gate 10: Self-Love
    10: {
        "shadow": "Self-Obsession",
        "gift": "Naturalness",
        "tension": "You're watching yourself too closely—adjusting, performing, managing perception. But the constant self-monitoring is exhausting everyone, including you.",
        "misstep": "overthinking how you're coming across instead of just being",
        "wise": "Stop editing yourself mid-sentence. The unfiltered version is more trustworthy.",
    },
    # Gate 11: Ideas
    11: {
        "shadow": "Obscurity",
        "gift": "Idealism",
        "tension": "Ideas are flooding in—but none of them feel solid enough to act on. The temptation is to chase all of them. The trap is chasing any of them too soon.",
        "misstep": "treating every idea like it needs immediate action",
        "wise": "Not every idea is meant to be acted on. Some are just meant to pass through.",
    },
    # Gate 12: Caution
    12: {
        "shadow": "Vanity",
        "gift": "Discrimination",
        "tension": "You want to be heard—but the timing isn't right. Speaking now might feel urgent, but it won't land. And what doesn't land gets wasted.",
        "misstep": "pushing your voice out when no one is ready to receive it",
        "wise": "Wait for the moment when what you say will actually be heard. It's coming.",
    },
    # Gate 13: The Listener
    13: {
        "shadow": "Discord",
        "gift": "Discernment",
        "tension": "You're holding things that aren't yours—other people's stories, secrets, weight. The burden is real. So is the question of what's yours to carry.",
        "misstep": "absorbing everything without filtering what actually belongs to you",
        "wise": "Not every story needs your attention. Some just need your witness—and then release.",
    },
    # Gate 14: Power Skills
    14: {
        "shadow": "Compromise",
        "gift": "Competence",
        "tension": "You have the power to make this work—but you're underselling it. The compromise isn't about humility. It's about fear of being seen at full capacity.",
        "misstep": "accepting less than you're capable of delivering",
        "wise": "Stop negotiating down. What you can do is what you can do.",
    },
    # Gate 15: Extremes
    15: {
        "shadow": "Dullness",
        "gift": "Magnetism",
        "tension": "You're averaging yourself out—flattening the highs, hiding the lows. But the middle ground isn't where your power lives.",
        "misstep": "smoothing over the extremes to fit in",
        "wise": "Your range is the point. Stop shrinking it.",
    },
    # Gate 16: Skills
    16: {
        "shadow": "Indifference",
        "gift": "Versatility",
        "tension": "Nothing feels interesting enough to commit to. But the boredom isn't about the options—it's about avoiding the depth that commitment requires.",
        "misstep": "staying shallow to avoid the risk of mastery",
        "wise": "Pick something and go deep. The interest follows the investment.",
    },
    # Gate 17: Opinions
    17: {
        "shadow": "Opinion",
        "gift": "Far-sightedness",
        "tension": "You see what's coming—but no one asked for your opinion. The urge to correct is strong. The cost of unsolicited advice is higher.",
        "misstep": "offering your take when it wasn't requested",
        "wise": "Hold the insight until someone reaches for it. Then it lands differently.",
    },
    # Gate 18: Correction
    18: {
        "shadow": "Judgment",
        "gift": "Integrity",
        "tension": "You see what's broken—and the urge to fix it is relentless. But not everything that's wrong is yours to correct. And not everyone wants to be improved.",
        "misstep": "correcting things that aren't yours to fix",
        "wise": "The clearest judgment is knowing when to act on it—and when to let it be.",
    },
    # Gate 19: Wanting
    19: {
        "shadow": "Co-dependence",
        "gift": "Sensitivity",
        "tension": "You can feel what everyone needs—and part of you wants to meet all of it. But the needs are endless, and you're not.",
        "misstep": "overextending to meet needs that aren't yours to fill",
        "wise": "Your sensitivity is a gift. But boundaries are what let you keep it.",
    },
    # Gate 20: The Now
    20: {
        "shadow": "Superficiality",
        "gift": "Self-Assurance",
        "tension": "You're reacting faster than you're thinking—moving on impulse, skipping depth. The speed feels like decisiveness. It's not.",
        "misstep": "acting before the moment is actually ready",
        "wise": "Slow the response by half a beat. That's where the real clarity lives.",
    },
    # Gate 21: Control
    21: {
        "shadow": "Control",
        "gift": "Authority",
        "tension": "You're gripping tighter because things feel uncertain. But control born from fear creates resistance, not results.",
        "misstep": "micromanaging what you can't actually control",
        "wise": "Real authority comes from knowing when to hold—and when to let go.",
    },
    # Gate 22: Grace
    22: {
        "shadow": "Dishonor",
        "gift": "Graciousness",
        "tension": "The emotional wave is cresting—and part of you wants to ride it into confrontation. But acting from the peak distorts everything.",
        "misstep": "saying what you feel before the wave passes",
        "wise": "Wait until the charge fades. Then say what's true.",
    },
    # Gate 23: Assimilation
    23: {
        "shadow": "Complexity",
        "gift": "Simplicity",
        "tension": "You're overcomplicating something that's actually simple. The complexity isn't in the thing—it's in your resistance to seeing it clearly.",
        "misstep": "adding layers to avoid the obvious answer",
        "wise": "The simple version is usually the true one. Say less.",
    },
    # Gate 24: Returning
    24: {
        "shadow": "Addiction",
        "gift": "Invention",
        "tension": "Your mind keeps circling back to the same thought—not because it's unfinished, but because you're avoiding what comes next.",
        "misstep": "ruminating instead of deciding",
        "wise": "The loop breaks when you stop waiting for certainty and start moving.",
    },
    # Gate 25: Spirit of the Self
    25: {
        "shadow": "Constriction",
        "gift": "Acceptance",
        "tension": "You're bracing for something that might not even happen. The constriction is a defense against pain—but it's blocking more than protection.",
        "misstep": "closing off to avoid potential hurt",
        "wise": "Stay open. Even if it costs something.",
    },
    # Gate 26: The Trickster
    26: {
        "shadow": "Pride",
        "gift": "Artfulness",
        "tension": "You're selling something—maybe yourself, maybe an idea. But the pitch is running ahead of the truth. And overselling creates a debt you'll have to pay later.",
        "misstep": "promising more than you can deliver to close the deal now",
        "wise": "Say only what you know is true. Let that be enough.",
    },
    # Gate 27: Nourishment
    27: {
        "shadow": "Selfishness",
        "gift": "Altruism",
        "tension": "You're giving more than you have—depleting yourself to care for others. But empty caregivers don't help anyone.",
        "misstep": "nurturing others while starving yourself",
        "wise": "Fill your own cup first. Then the giving becomes sustainable.",
    },
    # Gate 28: The Game Player
    28: {
        "shadow": "Purposelessness",
        "gift": "Totality",
        "tension": "Nothing feels worth the effort—and the question 'what's the point?' keeps surfacing. But the meaninglessness isn't in the things. It's in the disconnection.",
        "misstep": "withdrawing because nothing seems to matter",
        "wise": "Pick one thing and give it everything. The meaning follows the commitment.",
    },
    # Gate 29: Perseverance
    29: {
        "shadow": "Half-heartedness",
        "gift": "Commitment",
        "tension": "You said yes—but part of you is still holding back. The half-commitment is worse than no commitment. It drains without delivering.",
        "misstep": "staying in situations you're not fully committed to",
        "wise": "Either go all in or step all the way out. The middle is where energy dies.",
    },
    # Gate 30: Desire
    30: {
        "shadow": "Desire",
        "gift": "Lightness",
        "tension": "The wanting is intense—almost consuming. But chasing desire without discernment leads to exhaustion, not satisfaction.",
        "misstep": "pursuing intensity for its own sake",
        "wise": "Not everything that pulls you is meant to be caught. Some things are just meant to be felt.",
    },
    # Gate 31: Influence
    31: {
        "shadow": "Arrogance",
        "gift": "Leadership",
        "tension": "You have something to say—and the certainty that people should listen. But influence that demands attention rarely gets it.",
        "misstep": "expecting to be followed before being invited to lead",
        "wise": "Real influence comes from being chosen, not from insisting.",
    },
    # Gate 32: Continuity
    32: {
        "shadow": "Failure",
        "gift": "Preservation",
        "tension": "You can feel what's not going to work—and the fear of getting it wrong is paralyzing. But avoiding risk doesn't protect you. It just keeps you stuck.",
        "misstep": "refusing to act because you might fail",
        "wise": "The instinct is useful. But fear of failure isn't the same as wisdom.",
    },
    # Gate 33: Privacy
    33: {
        "shadow": "Forgetting",
        "gift": "Mindfulness",
        "tension": "You're retreating—pulling back from what feels like too much. The withdrawal makes sense. But isolation is a refuge, not a solution.",
        "misstep": "hiding to avoid being overwhelmed",
        "wise": "Retreat when you need to. But don't disappear. The world still needs what you carry.",
    },
    # Gate 34: Power
    34: {
        "shadow": "Force",
        "gift": "Strength",
        "tension": "The energy to act is surging—but energy without direction becomes force. And force creates resistance, not results.",
        "misstep": "pushing through when the situation calls for precision",
        "wise": "Channel the power, don't spray it. Strength is force with aim.",
    },
    # Gate 35: Change
    35: {
        "shadow": "Hunger",
        "gift": "Adventure",
        "tension": "The hunger for something new is relentless—but hunger moves fast and burns out. Adventure only opens when you move at the right moment.",
        "misstep": "chasing novelty because stillness feels unbearable",
        "wise": "The next experience isn't going anywhere. Wait for the one that's actually calling you.",
    },
    # Gate 36: Crisis
    36: {
        "shadow": "Turbulence",
        "gift": "Humanity",
        "tension": "Everything feels heightened—emotional, raw, unstable. But the turbulence isn't random. Something is trying to break through.",
        "misstep": "reacting to the wave instead of riding it",
        "wise": "Don't fight the intensity. Move with it. What's on the other side is worth reaching.",
    },
    # Gate 37: Family
    37: {
        "shadow": "Weakness",
        "gift": "Equality",
        "tension": "You're giving more than you're receiving—and the imbalance is starting to show. The loyalty is real, but so is the drain.",
        "misstep": "sacrificing yourself to maintain harmony",
        "wise": "Equality means giving and receiving. One without the other isn't balance—it's depletion.",
    },
    # Gate 38: Opposition
    38: {
        "shadow": "Struggle",
        "gift": "Perseverance",
        "tension": "You're fighting—maybe with the situation, maybe with yourself. The struggle feels necessary. But not all battles are yours.",
        "misstep": "fighting to prove you can, not because you should",
        "wise": "Save the fight for what actually matters. Everything else is just noise.",
    },
    # Gate 39: Provocation
    39: {
        "shadow": "Provocation",
        "gift": "Dynamism",
        "tension": "You're poking at something—testing it, provoking a reaction. The push might wake something up. It might also break something that wasn't ready.",
        "misstep": "provoking to create movement when patience would serve better",
        "wise": "Not everything responds well to pressure. Some things open on their own.",
    },
    # Gate 40: Aloneness
    40: {
        "shadow": "Exhaustion",
        "gift": "Resolve",
        "tension": "You've been giving more than you realized—and the exhaustion is catching up. The urge to push through is strong. But depletion isn't strength.",
        "misstep": "ignoring the need for rest because there's still more to do",
        "wise": "You can't pour from empty. And you're closer to empty than you're admitting.",
    },
    # Gate 41: Contraction
    41: {
        "shadow": "Fantasy",
        "gift": "Anticipation",
        "tension": "You're imagining how it could go—running scenarios, building futures in your mind. But fantasy is a placeholder, not a plan.",
        "misstep": "living in the possibility instead of taking the first step",
        "wise": "The future you're imagining requires a present action. Start there.",
    },
    # Gate 42: Growth
    42: {
        "shadow": "Expectation",
        "gift": "Detachment",
        "tension": "You're holding on to how things were supposed to go—and the gap between expectation and reality is exhausting you.",
        "misstep": "clinging to an outcome that's no longer available",
        "wise": "Let the old version of this die. Something else is trying to grow.",
    },
    # Gate 43: Insight
    43: {
        "shadow": "Deafness",
        "gift": "Insight",
        "tension": "You know something—but no one wants to hear it. The clarity is real. The timing isn't.",
        "misstep": "insisting on your insight when no one is ready to receive it",
        "wise": "Hold the knowing. When the moment comes, you'll be heard.",
    },
    # Gate 44: Coming to Meet
    44: {
        "shadow": "Interference",
        "gift": "Teamwork",
        "tension": "You can see what needs to happen—and you're tempted to make it happen yourself. But inserting yourself too early creates friction, not flow.",
        "misstep": "stepping in before you're truly needed",
        "wise": "Wait to be called. Your timing will be better.",
    },
    # Gate 45: Gathering Together
    45: {
        "shadow": "Dominance",
        "gift": "Synergy",
        "tension": "You're taking charge—but not everyone wants to be led. The confidence is real. The resistance it's creating is also real.",
        "misstep": "assuming control when partnership would work better",
        "wise": "Lead when invited. Collaborate when not.",
    },
    # Gate 46: Determination
    46: {
        "shadow": "Seriousness",
        "gift": "Delight",
        "tension": "You're working hard—but the joy is missing. The grind is real, but so is the question: is this still worth the weight?",
        "misstep": "grinding through without checking if you still care",
        "wise": "If the body doesn't want it, no amount of discipline will make it right.",
    },
    # Gate 47: Realization
    47: {
        "shadow": "Oppression",
        "gift": "Transmutation",
        "tension": "Something feels stuck—trapped, heavy, impossible to shift. But the pressure isn't random. It's building toward breakthrough.",
        "misstep": "giving up right before the shift",
        "wise": "Stay with it. The oppression is the last stage before transformation.",
    },
    # Gate 48: Depth
    48: {
        "shadow": "Inadequacy",
        "gift": "Resourcefulness",
        "tension": "You feel like you don't know enough—like you're not ready. But the inadequacy is a story, not a truth. You know more than you're letting yourself use.",
        "misstep": "waiting to feel ready instead of starting with what you have",
        "wise": "Start before you feel qualified. Mastery comes from practice, not preparation.",
    },
    # Gate 49: Revolution
    49: {
        "shadow": "Reaction",
        "gift": "Revolution",
        "tension": "Something needs to change—and the urge to burn it down is strong. But reaction isn't revolution. One is impulsive. The other is intentional.",
        "misstep": "destroying before you know what you're building",
        "wise": "Change what needs changing. But do it with aim, not anger.",
    },
    # Gate 50: Values
    50: {
        "shadow": "Corruption",
        "gift": "Equilibrium",
        "tension": "Your values are being tested—compromised, pressured, bent. The discomfort is the signal. Something isn't aligned.",
        "misstep": "bending values to keep the peace",
        "wise": "Hold the line. Even when it costs something.",
    },
    # Gate 51: Shock
    51: {
        "shadow": "Agitation",
        "gift": "Initiative",
        "tension": "Something jolted you—unexpected, disorienting, uncomfortable. The shock is a doorway, not a trap. But only if you move through it.",
        "misstep": "retreating into safety instead of letting the shock wake you up",
        "wise": "Don't recover too fast. The disruption is showing you something.",
    },
    # Gate 52: Stillness
    52: {
        "shadow": "Stress",
        "gift": "Restraint",
        "tension": "Everything in you wants to move—but the moment is calling for stillness. The stress comes from fighting what's actually needed.",
        "misstep": "forcing movement when the situation calls for pause",
        "wise": "Stillness isn't stagnation. It's gathering power.",
    },
    # Gate 53: Development
    53: {
        "shadow": "Immaturity",
        "gift": "Expansion",
        "tension": "Something new is starting—but you're rushing it. The beginning isn't ready to become the middle yet.",
        "misstep": "trying to accelerate a process that has its own pace",
        "wise": "Let beginnings be beginnings. The rest will follow.",
    },
    # Gate 54: Ambition
    54: {
        "shadow": "Greed",
        "gift": "Aspiration",
        "tension": "The drive to rise is intense—but the hunger is outpacing the work. Ambition without patience becomes greed.",
        "misstep": "grabbing for position before earning trust",
        "wise": "Climb steadily. The shortcuts cost more than they save.",
    },
    # Gate 55: Spirit
    55: {
        "shadow": "Victimization",
        "gift": "Freedom",
        "tension": "You're feeling the weight of what's happened—maybe stuck in the story of how you got here. But the past is an anchor, not a destination.",
        "misstep": "staying in the pain because leaving it feels like betrayal",
        "wise": "You can honor what happened without living there.",
    },
    # Gate 56: Stimulation
    56: {
        "shadow": "Distraction",
        "gift": "Enrichment",
        "tension": "Everything is interesting—but nothing is landing. The stimulation is endless, and you're skimming instead of sinking in.",
        "misstep": "chasing more input when depth would serve better",
        "wise": "Pick one thing and let it teach you. Surface is exhausting.",
    },
    # Gate 57: Intuition
    57: {
        "shadow": "Unease",
        "gift": "Intuition",
        "tension": "Something feels off—but you can't name it. The unease is real. Don't explain it away.",
        "misstep": "rationalizing away the instinct because it's inconvenient",
        "wise": "Trust the hit. Even when you can't justify it.",
    },
    # Gate 58: Joy
    58: {
        "shadow": "Dissatisfaction",
        "gift": "Vitality",
        "tension": "Nothing feels quite right—close, but not there. The dissatisfaction is pointing at something. But fixing it externally won't reach it.",
        "misstep": "changing circumstances to fix an internal gap",
        "wise": "The aliveness you want isn't in the next thing. It's in how you meet this one.",
    },
    # Gate 59: Sexuality
    59: {
        "shadow": "Dishonesty",
        "gift": "Intimacy",
        "tension": "There's something you're not saying—to yourself or someone else. The barrier to intimacy isn't them. It's what you're hiding.",
        "misstep": "protecting yourself at the cost of connection",
        "wise": "Say the thing. The real thing. See what opens.",
    },
    # Gate 60: Limitation
    60: {
        "shadow": "Limitation",
        "gift": "Realism",
        "tension": "The constraints feel suffocating—but they're not arbitrary. There's something in the structure trying to teach you.",
        "misstep": "fighting the limits instead of working within them",
        "wise": "The constraint isn't blocking you. It's shaping you.",
    },
    # Gate 61: Inner Truth
    61: {
        "shadow": "Psychosis",
        "gift": "Inspiration",
        "tension": "The mind is reaching for something it can't quite grasp—and the not-knowing is unbearable. But some things can only be felt, not thought.",
        "misstep": "thinking harder when the answer lives elsewhere",
        "wise": "Let the question sit unanswered. Inspiration comes from stillness, not strain.",
    },
    # Gate 62: Details
    62: {
        "shadow": "Intellect",
        "gift": "Precision",
        "tension": "You're gathering more facts—but the clarity isn't coming. At some point, more data becomes avoidance.",
        "misstep": "researching instead of deciding",
        "wise": "You have enough. Use what you know.",
    },
    # Gate 63: Doubt
    63: {
        "shadow": "Doubt",
        "gift": "Inquiry",
        "tension": "The doubt keeps surfacing—picking apart what feels true, questioning everything. But doubt without direction becomes paralysis.",
        "misstep": "doubting to avoid committing",
        "wise": "Ask the real question. Then act on whatever answer comes.",
    },
    # Gate 64: Confusion
    64: {
        "shadow": "Confusion",
        "gift": "Imagination",
        "tension": "Nothing is clear—and the harder you look, the murkier it gets. The confusion isn't a problem to solve. It's a transition to sit with.",
        "misstep": "forcing clarity before it's ready",
        "wise": "The picture will form. Let it be blurry for now.",
    },
}


# =============================================================================
# V3.2: TYPE/AUTHORITY TENSION NARRATIVES - Real-world behavioral conflicts
# =============================================================================

HD_TYPE_TENSIONS_V32 = {
    "Generator": {
        "core_tension": "responding vs initiating",
        "behavioral_pattern": "You want to make things happen—but your power comes from responding, not starting. The urge to initiate is the trap.",
        "misstep": "starting things before the gut says yes",
        "wise": "The right things will come to you. Your job is to be available for them—not to go hunting.",
    },
    "Manifesting Generator": {
        "core_tension": "speed vs alignment",
        "behavioral_pattern": "You can move fast—but fast isn't always right. The temptation is to skip the response check because you already know what you want.",
        "misstep": "moving before confirming with the gut, then having to backtrack",
        "wise": "You can go fast. But check first. The extra beat saves you from reversals.",
    },
    "Projector": {
        "core_tension": "seeing vs being invited to see",
        "behavioral_pattern": "You can see what others miss—but offering that vision uninvited creates resistance. The clarity is real. The timing is the variable.",
        "misstep": "sharing your read before anyone asked for it",
        "wise": "The invitation is coming. Don't exhaust yourself waiting—but don't skip the wait either.",
    },
    "Manifestor": {
        "core_tension": "impact vs friction",
        "behavioral_pattern": "You can move things—but moving without warning creates resistance. The power is real. So is the wake you leave behind.",
        "misstep": "acting without letting people know what's coming",
        "wise": "Informing isn't asking permission. It's reducing the friction that slows you down.",
    },
    "Reflector": {
        "core_tension": "sampling vs committing",
        "behavioral_pattern": "You're absorbing everything—and nothing feels solid enough to commit to. But the instability isn't a flaw. It's how you see clearly.",
        "misstep": "deciding before the full picture forms",
        "wise": "Give it a full cycle. What feels true after 28 days is actually true.",
    },
}

HD_AUTHORITY_TENSIONS_V32 = {
    "Emotional": {
        "pattern": "You feel strongly right now—but strong isn't clear. Clarity comes after the wave passes, not at its peak.",
        "misstep": "deciding when the feeling is loudest",
        "wise": "Wait for emotional neutrality. That's where truth lives.",
    },
    "Sacral": {
        "pattern": "Your gut already knows. The question is whether you're listening or overriding it with logic.",
        "misstep": "thinking yourself out of what the body already said",
        "wise": "Trust the initial response. Everything after is doubt.",
    },
    "Splenic": {
        "pattern": "You knew in the first second. The instinct came and went—and everything since has been second-guessing.",
        "misstep": "waiting for confirmation that already came",
        "wise": "The first hit was right. Stop looking for reasons.",
    },
    "Ego": {
        "pattern": "If your heart isn't in it, you can't sustain it. The will to commit has to be real.",
        "misstep": "promising what you don't actually want to deliver",
        "wise": "Only commit what your heart will back. Everything else will collapse.",
    },
    "Self-Projected": {
        "pattern": "You won't know until you hear yourself say it. The clarity comes through speaking, not thinking.",
        "misstep": "deciding in your head without talking it through",
        "wise": "Say it out loud. The truth reveals itself in your own voice.",
    },
    "Mental": {
        "pattern": "You need a sounding board—not for their opinion, but for your own clarity. Talking reveals what thinking hides.",
        "misstep": "deciding alone when you need external reflection",
        "wise": "Find someone to talk to. Not for answers—for mirrors.",
    },
    "Lunar": {
        "pattern": "This needs more time than it feels like. Big decisions require a full cycle to reveal themselves.",
        "misstep": "rushing to certainty because the pressure is high",
        "wise": "28 days. That's not arbitrary—that's how you see clearly.",
    },
}


# =============================================================================
# V3.2: ASTROLOGY TRANSIT TENSIONS - Real-world behavioral conflicts
# =============================================================================

ASTRO_TRANSIT_TENSIONS_V32 = {
    "Sun": {
        "theme": "identity",
        "tension": "You're being asked who you really are—not who you perform as, not who you've been. And the gap between those is uncomfortable.",
        "misstep": "performing a version of yourself that no longer fits",
        "wise": "The authentic move feels risky because it is. Do it anyway.",
    },
    "Moon": {
        "theme": "emotional needs",
        "tension": "Something needs attending to—an emotional truth you've been sidestepping. The mood is the message.",
        "misstep": "dismissing the feeling because it's inconvenient",
        "wise": "Follow the emotion to its source. That's where the real work is.",
    },
    "Mercury": {
        "theme": "perception",
        "tension": "Your mind is active—too active. The loop between thinking and clarity isn't closing. Thinking more won't help.",
        "misstep": "analyzing past the point of usefulness",
        "wise": "Say it or write it. Get it out of your head and into form.",
    },
    "Venus": {
        "theme": "desire",
        "tension": "What you want is clear—but something is blocking the direct path. The compromise feels reasonable. It isn't.",
        "misstep": "settling for a version of what you want instead of the real thing",
        "wise": "Be honest about what you actually desire. Then negotiate from there.",
    },
    "Mars": {
        "theme": "action",
        "tension": "The drive to move is strong—maybe too strong. There's power available, but power without aim creates damage.",
        "misstep": "acting because the energy is there, not because the timing is right",
        "wise": "Channel the energy into something specific. Unfocused fire burns everything.",
    },
    "Jupiter": {
        "theme": "expansion",
        "tension": "Something wants to grow—but growth without boundaries becomes bloat. The opportunity is real. So is the risk of overreach.",
        "misstep": "expanding into areas you can't actually sustain",
        "wise": "Grow where you're rooted. The rest is just stretching.",
    },
    "Saturn": {
        "theme": "structure",
        "tension": "Something is pressing down—demanding accountability, structure, consequence. The weight is real, but so is what it's building.",
        "misstep": "resisting the discipline because it feels heavy",
        "wise": "The constraint isn't punishment. It's the shape of what you're becoming.",
    },
    "Uranus": {
        "theme": "disruption",
        "tension": "Something wants to break—routines, assumptions, patterns that no longer fit. The instability is the invitation.",
        "misstep": "clinging to stability when the situation demands change",
        "wise": "Let it shake. What survives is what matters.",
    },
    "Neptune": {
        "theme": "dissolution",
        "tension": "The edges are blurring—what was certain is becoming less so. The confusion isn't failure. It's transition.",
        "misstep": "forcing clarity when the moment calls for unknowing",
        "wise": "Float. The ground will form when it's ready.",
    },
    "Pluto": {
        "theme": "transformation",
        "tension": "Something is dying—and you're holding on. The resistance isn't protecting you. It's just prolonging the process.",
        "misstep": "fighting the ending instead of allowing it",
        "wise": "Let go. What's on the other side requires empty hands.",
    },
}

ASTRO_HOUSE_TENSIONS_V32 = {
    1: {"area": "self-presentation", "surface": "how you show up, how you're seen, the face you lead with"},
    2: {"area": "resources", "surface": "money, possessions, what you depend on, self-worth"},
    3: {"area": "communication", "surface": "how you think, speak, learn—daily exchanges"},
    4: {"area": "foundation", "surface": "home, family, roots—where you come from and where you feel safe"},
    5: {"area": "creation", "surface": "what you create, how you play, what brings joy—including love"},
    6: {"area": "service", "surface": "daily work, health, routines—how you maintain yourself"},
    7: {"area": "partnership", "surface": "one-on-one relationships—intimate, professional, adversarial"},
    8: {"area": "depth", "surface": "shared resources, intimacy, death, transformation—what's hidden"},
    9: {"area": "expansion", "surface": "beliefs, travel, meaning—how you make sense of life"},
    10: {"area": "vocation", "surface": "career, reputation, legacy—what you're known for"},
    11: {"area": "collective", "surface": "community, friendships, hopes—where you belong"},
    12: {"area": "dissolution", "surface": "endings, solitude, the unconscious—what's beneath"},
}


# =============================================================================
# V3.2: MAIN HD DIAGNOSIS GENERATOR
# =============================================================================

def get_center_for_gate(gate: int) -> str:
    """Map gate number to its center."""
    if gate in [64, 61, 63]:
        return "Head"
    if gate in [47, 24, 4, 17, 43, 11]:
        return "Ajna"
    if gate in [62, 23, 56, 35, 12, 45, 33, 8, 31, 20, 16]:
        return "Throat"
    if gate in [7, 1, 13, 25, 46, 2, 15, 10]:
        return "G/Identity"
    if gate in [21, 40, 26, 51]:
        return "Heart/Ego"
    if gate in [5, 14, 29, 59, 9, 3, 42, 27, 34]:
        return "Sacral"
    if gate in [6, 37, 22, 36, 30, 55, 49]:
        return "Solar Plexus"
    if gate in [48, 57, 44, 50, 32, 28, 18]:
        return "Spleen"
    if gate in [58, 38, 54, 53, 60, 52, 19, 39, 41]:
        return "Root"
    return "Sacral"


async def generate_hd_today_diagnosis(
    db,
    user_id: str,
    hd_data: Dict[str, Any],
    active_gates: List[int],
    transit_gates: List[int],
    defined_centers: List[str],
    undefined_centers: List[str]
) -> Dict[str, Any]:
    """
    V3.2: Generate Human Design Today diagnosis with Mirror-level quality.
    Gene Key Shadow/Gift tension drives the narrative.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    hd_type = hd_data.get("type", "Generator")
    authority = hd_data.get("authority", "Sacral")
    
    # Normalize authority
    authority_key = "Sacral"
    auth_lower = authority.lower() if authority else ""
    if "emotional" in auth_lower:
        authority_key = "Emotional"
    elif "sacral" in auth_lower:
        authority_key = "Sacral"
    elif "splenic" in auth_lower:
        authority_key = "Splenic"
    elif "ego" in auth_lower or "heart" in auth_lower:
        authority_key = "Ego"
    elif "self" in auth_lower:
        authority_key = "Self-Projected"
    elif "mental" in auth_lower or "environment" in auth_lower:
        authority_key = "Mental"
    elif "lunar" in auth_lower or "moon" in auth_lower:
        authority_key = "Lunar"
    
    # Get type and authority tensions
    type_tension = HD_TYPE_TENSIONS_V32.get(hd_type, HD_TYPE_TENSIONS_V32["Generator"])
    auth_tension = HD_AUTHORITY_TENSIONS_V32.get(authority_key, HD_AUTHORITY_TENSIONS_V32["Sacral"])
    
    # Find dominant gate and its Gene Key narrative
    dominant_gate = active_gates[0] if active_gates else 35
    gene_key = get_gene_key_for_gate(dominant_gate)
    gene_key_narrative = GENE_KEY_TENSION_NARRATIVES.get(dominant_gate, {})
    
    shadow = gene_key_narrative.get("shadow", gene_key.get("shadow", "Unknown"))
    gift = gene_key_narrative.get("gift", gene_key.get("gift", "Unknown"))
    
    # Build V3.2 diagnosis using Gene Key tension as the core
    if gene_key_narrative:
        title = f"The Pull Between {shadow} and {gift}"
        body = gene_key_narrative.get("tension", f"Part of you is caught in {shadow.lower()}—another part knows {gift.lower()} is possible. The gap between them is where you're living today.")
        
        # Add authority layer to body
        body += f" {auth_tension['pattern']}"
        
        bridge = f"This isn't broken—it's your design under pressure. The {shadow.lower()} is showing you where the {gift.lower()} wants to emerge."
        
        # V3.2: Consequence-based misstep and wise move
        misstep = gene_key_narrative.get("misstep", type_tension["misstep"])
        wise = gene_key_narrative.get("wise", type_tension["wise"])
    else:
        # Fallback using type tension
        title = type_tension["core_tension"].replace(" vs ", " and ").title()
        body = f"{type_tension['behavioral_pattern']} {auth_tension['pattern']}"
        bridge = "This is your design working as designed. The tension is the path, not the problem."
        misstep = type_tension["misstep"]
        wise = type_tension["wise"]
    
    # Build signals
    gate_signals = []
    for g in active_gates[:5]:
        gk = get_gene_key_for_gate(g)
        gk_narrative = GENE_KEY_TENSION_NARRATIVES.get(g, {})
        gate_signals.append({
            "gate": g,
            "shadow": gk_narrative.get("shadow", gk.get("shadow", "Unknown")),
            "gift": gk_narrative.get("gift", gk.get("gift", "Unknown")),
            "center": get_center_for_gate(g),
            "activation": "transit" if g in transit_gates else "natal",
        })
    
    return {
        "success": True,
        "lens": "human_design",
        "date": today,
        "title": title,
        "body": body,
        "bridge": bridge,
        "misstep": misstep,
        "better_move": wise,
        "signals": {
            "active_gates": gate_signals,
            "defined_centers": defined_centers,
            "undefined_centers": undefined_centers,
            "type": hd_type,
            "authority": authority,
        },
        "debug": {
            "dominant_gate": dominant_gate,
            "shadow": shadow,
            "gift": gift,
            "type": hd_type,
            "authority_key": authority_key,
            "version": "v3.2",
        }
    }


# =============================================================================
# V3.2: ASTROLOGY DIAGNOSIS GENERATOR
# =============================================================================

async def generate_astro_today_diagnosis(
    db,
    user_id: str,
    chart_data: Dict[str, Any],
    transits: List[Dict[str, Any]],
    active_houses: List[int]
) -> Dict[str, Any]:
    """
    V3.2: Generate Astrology Today diagnosis with Mirror-level quality.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Find dominant transit
    dominant_transit = None
    dominant_planet = "Moon"
    
    for transit in transits[:5]:
        planet = transit.get("planet", "")
        if planet in ASTRO_TRANSIT_TENSIONS_V32:
            dominant_transit = transit
            dominant_planet = planet
            break
    
    if not dominant_transit and transits:
        dominant_transit = transits[0]
        dominant_planet = dominant_transit.get("planet", "Moon")
    
    planet_tension = ASTRO_TRANSIT_TENSIONS_V32.get(dominant_planet, ASTRO_TRANSIT_TENSIONS_V32["Moon"])
    
    # Get primary house
    primary_house = active_houses[0] if active_houses else 1
    house_info = ASTRO_HOUSE_TENSIONS_V32.get(primary_house, ASTRO_HOUSE_TENSIONS_V32[1])
    
    # V3.2 diagnosis
    title = f"{planet_tension['theme'].title()} Under Pressure"
    
    body = f"{planet_tension['tension']} This is landing in your {house_info['area']}—{house_info['surface']}."
    
    bridge = "This transit is moving through. It's not permanent—but what it reveals is worth sitting with."
    
    misstep = planet_tension["misstep"]
    wise = planet_tension["wise"]
    
    # Build signals
    transit_signals = []
    for t in transits[:5]:
        transit_signals.append({
            "planet": t.get("planet"),
            "aspect": t.get("aspect"),
            "natal_planet": t.get("natal_planet"),
            "house": t.get("house"),
        })
    
    house_signals = []
    for h in active_houses[:3]:
        h_info = ASTRO_HOUSE_TENSIONS_V32.get(h, {})
        house_signals.append({
            "house": h,
            "area": h_info.get("area", ""),
            "surface": h_info.get("surface", ""),
        })
    
    return {
        "success": True,
        "lens": "astrology",
        "date": today,
        "title": title,
        "body": body,
        "bridge": bridge,
        "misstep": misstep,
        "better_move": wise,
        "signals": {
            "transits": transit_signals,
            "active_houses": active_houses[:3],
            "house_meanings": house_signals,
        },
        "debug": {
            "dominant_planet": dominant_planet,
            "primary_house": primary_house,
            "transit_count": len(transits),
            "version": "v3.2",
        }
    }
