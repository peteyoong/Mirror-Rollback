"""
Mirror Content System V1
========================

Unified content structure for all lenses (Human Design, Gene Keys, Astrology, BaZi, etc.)

STRUCTURE:
- Recognition (top, always visible)
- WHAT THIS IS (2-3 lines)
- WHEN IT TRIPS YOU UP (2-3 lines)  
- WHEN IT WORKS (2-3 lines)
- AT YOUR HIGHEST (1-2 lines)
- WHERE YOU'LL NOTICE THIS TODAY (3 bullets)
- TRY THIS (3 bullets)
- WHY THIS IS HAPPENING (collapsible)

LANGUAGE RULES:
- Start with "You…" or "You tend to…"
- No system-first phrasing
- No "energy", "alignment", "consistent energy"
- No abstract terms without behavior
- Every section must map to real-life situations

GENE KEYS INTEGRATION:
- Shadow → WHEN IT TRIPS YOU UP
- Gift → WHEN IT WORKS
- Siddhi → AT YOUR HIGHEST

SUCCESS CRITERIA:
- User immediately recognizes themselves
- User can apply within same day
- User does not need system knowledge
- Content feels precise, not generic
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class MirrorContent:
    """Standard content structure for all Mirror outputs."""
    
    # Recognition line (top, always visible)
    recognition: str
    
    # Core sections
    what_this_is: str  # 2-3 lines
    when_it_trips_you_up: str  # 2-3 lines (Shadow behavior)
    when_it_works: str  # 2-3 lines (Gift behavior)
    at_your_highest: str  # 1-2 lines (Siddhi/potential)
    
    # Practical sections
    where_youll_notice_today: List[str]  # 3 bullets
    try_this: List[str]  # 3 bullets
    
    # Collapsible explanation
    why_this_is_happening: str  # Technical/system explanation
    
    # Metadata (shown last, secondary)
    system_label: str  # e.g., "Ajna · defined" or "Gate 1 · Creativity"


def create_mirror_content(
    recognition: str,
    what_this_is: str,
    when_it_trips_you_up: str,
    when_it_works: str,
    at_your_highest: str,
    where_youll_notice_today: List[str],
    try_this: List[str],
    why_this_is_happening: str,
    system_label: str,
) -> Dict[str, Any]:
    """Create a standardized Mirror content block."""
    return {
        "recognition": recognition,
        "what_this_is": what_this_is,
        "when_it_trips_you_up": when_it_trips_you_up,
        "when_it_works": when_it_works,
        "at_your_highest": at_your_highest,
        "where_youll_notice_today": where_youll_notice_today,
        "try_this": try_this,
        "why_this_is_happening": why_this_is_happening,
        "system_label": system_label,
    }


# =============================================================================
# HUMAN DESIGN CENTER CONTENT
# =============================================================================

HD_CENTER_CONTENT = {
    "Head": {
        "defined": {
            "recognition": "You get caught by questions that won't let go.",
            "what_this_is": "You tend to have a mind that generates its own questions and inspirations. Ideas arrive uninvited and stay until you've turned them over enough times. This mental activity comes from within you.",
            "when_it_trips_you_up": "You chase every interesting question as if they're all urgent. You feel pressure to figure things out before moving on. You mistake mental noise for important insights.",
            "when_it_works": "You follow questions that keep returning over time. You write down inspirations without immediately acting. You recognize which ideas are genuinely yours to pursue.",
            "at_your_highest": "You become a source of inspiration for others—your questions open doors that wouldn't exist otherwise.",
            "where_youll_notice_today": [
                "A question or idea keeps circling back even when you're busy",
                "You feel a subtle pressure to figure something out",
                "You find yourself researching something you didn't plan to"
            ],
            "try_this": [
                "Write the question down. If it's still important in 3 days, pursue it.",
                "When mental pressure hits, ask: 'Is this mine to solve?'",
                "Notice which questions disappear when you leave certain people."
            ],
            "why_this_is_happening": "Your Head center generates consistent mental pressure and inspiration. This creates a reliable source of questions and ideas, but can also create overwhelm if you treat every thought as urgent.",
            "system_label": "Head center · defined"
        },
        "undefined": {
            "recognition": "You take in other people's mental pressure as your own.",
            "what_this_is": "You tend to absorb questions and mental intensity from the environment. Ideas arrive from outside you, and sometimes you mistake them for your own thoughts. Your mental activity changes based on who you're around.",
            "when_it_trips_you_up": "You chase ideas that disappear when you're alone. You feel overwhelmed in mentally active environments. You can't tell which questions are actually yours to answer.",
            "when_it_works": "You recognize when inspiration comes from outside. You let go of questions that don't stay with you. You choose your mental environments carefully.",
            "at_your_highest": "You become wise about inspiration itself—seeing which questions truly matter versus which are just mental noise.",
            "where_youll_notice_today": [
                "Your thinking changes intensity based on who you're around",
                "You feel pressure to answer questions that aren't really yours",
                "An idea feels urgent now but might fade by tonight"
            ],
            "try_this": [
                "Before acting on an inspiration, wait until you're alone. Does it stay?",
                "Notice how your mental activity changes in different rooms.",
                "Ask: 'Would I care about this if no one else did?'"
            ],
            "why_this_is_happening": "Your Head center is open, meaning you absorb and amplify mental pressure from others. This gives you wisdom about how minds work, but can overwhelm you if you don't recognize what's not yours.",
            "system_label": "Head center · open"
        }
    },
    "Ajna": {
        "defined": {
            "recognition": "You lock into a way of seeing things—and once it makes sense, you stick with it.",
            "what_this_is": "You tend to process information in consistent patterns. Your opinions form through your own internal logic, and changing your mind requires real evidence, not just someone else's pressure.",
            "when_it_trips_you_up": "You become rigid and defensive about your views. You stop considering new information. You feel pressure to have opinions about everything, even when you don't need one.",
            "when_it_works": "You offer reliable perspectives that don't shift with every conversation. You think clearly under pressure. You know when you haven't formed a view yet.",
            "at_your_highest": "You become a source of clarity for others—your consistent thinking helps people see what they couldn't see alone.",
            "where_youll_notice_today": [
                "You hold a clear opinion and find yourself defending it",
                "You process new information through your existing framework first",
                "Someone disagrees and you feel certain before hearing them out"
            ],
            "try_this": [
                "When someone disagrees, ask yourself: 'What would change my mind?'",
                "Practice saying 'I haven't formed a view on that yet.'",
                "Map someone's logic before deciding they're wrong."
            ],
            "why_this_is_happening": "Your Ajna center processes information in fixed patterns. This creates mental reliability but can become rigidity if you stop questioning your own conclusions.",
            "system_label": "Ajna · defined"
        },
        "undefined": {
            "recognition": "You think differently depending on who you're around.",
            "what_this_is": "You tend to see multiple perspectives easily. Your mind is flexible—you can argue any side of a debate. What you think shifts based on context, and that's a feature, not a flaw.",
            "when_it_trips_you_up": "You pretend to have certainty you don't have. You adopt others' opinions without realizing it. You feel pressure to pick a side when you genuinely see both.",
            "when_it_works": "You embrace not knowing. You recognize when opinions belong to others. You use your flexibility to understand perspectives others can't.",
            "at_your_highest": "You become wise about certainty itself—seeing that most opinions are contextual, not absolute.",
            "where_youll_notice_today": [
                "Your opinion shifts based on who you're talking to",
                "You can argue either side of something convincingly",
                "You feel uncertain about what you 'really' think"
            ],
            "try_this": [
                "Say 'I see it differently in different contexts' and notice how it feels.",
                "After leaving a strong personality, check: which thoughts were theirs?",
                "Practice being comfortable without a fixed opinion."
            ],
            "why_this_is_happening": "Your Ajna center takes in others' thought processes. This makes you mentally flexible but can create confusion about what you actually believe.",
            "system_label": "Ajna · open"
        }
    },
    "Throat": {
        "defined": {
            "recognition": "You speak and act in recognizable patterns—your voice has a consistent style.",
            "what_this_is": "You tend to communicate in ways others recognize. When something needs to be said, it often comes out. Words, actions, or creative output flow from you in consistent ways.",
            "when_it_trips_you_up": "You speak just to be heard, not because you have something to say. You fill silences that don't need filling. You talk over others or dominate conversations.",
            "when_it_works": "You speak at the right moment, not just because you can. You know when silence is more powerful. Your words land because of timing, not volume.",
            "at_your_highest": "You become a voice that moves things forward—your expression creates change that wouldn't happen otherwise.",
            "where_youll_notice_today": [
                "You naturally take the lead in conversations",
                "Others wait for you to speak first",
                "You feel a pull to fill silence or move things forward"
            ],
            "try_this": [
                "Before speaking in a meeting, count to three. Does the moment need you?",
                "Practice letting silence exist without filling it.",
                "Notice when you speak from habit versus genuine need."
            ],
            "why_this_is_happening": "Your Throat center has consistent access to expression and manifestation. This makes you a natural communicator but can lead to over-speaking if timing isn't considered.",
            "system_label": "Throat · defined"
        },
        "undefined": {
            "recognition": "You communicate differently depending on the situation—your voice adapts.",
            "what_this_is": "You tend to express yourself in ways that match the context. Sometimes words come easily; other times they don't. Your communication style shifts based on who you're with.",
            "when_it_trips_you_up": "You force yourself to speak when you have nothing to say. You feel invisible or struggle to be heard. You overcompensate by talking too much or staying silent too long.",
            "when_it_works": "You wait to be asked before offering perspective. You recognize when timing matters more than content. You adapt your voice to serve the moment.",
            "at_your_highest": "You become wise about communication itself—knowing when words matter and when silence is the message.",
            "where_youll_notice_today": [
                "Speaking feels easier in some settings than others",
                "You might feel pressure to fill silence or go very quiet",
                "Your communication style shifts based on the room"
            ],
            "try_this": [
                "Wait to be invited before sharing your perspective.",
                "Notice when you're forcing expression versus when it flows.",
                "Ask: 'Does this moment actually need my voice?'"
            ],
            "why_this_is_happening": "Your Throat center adapts to the environment. This gives you flexibility in expression but can create uncertainty about when and how to speak.",
            "system_label": "Throat · open"
        }
    },
    "G Center": {
        "defined": {
            "recognition": "You have a steady sense of who you are and where you're going.",
            "what_this_is": "You tend to know your direction, even when external circumstances are uncertain. Something in you holds identity and path. Others may look to you for steadiness.",
            "when_it_trips_you_up": "You stay on a path just because it's familiar. You become rigid about identity or direction. You can't understand people who feel less certain about who they are.",
            "when_it_works": "You trust your sense of direction without forcing it. You know the difference between genuine knowing and habit. You let your path evolve while staying rooted.",
            "at_your_highest": "You become a guide for others—your steady direction helps people find their own way.",
            "where_youll_notice_today": [
                "You know what you want, even if you can't explain why",
                "People ask for your guidance or follow your lead",
                "You feel pulled toward certain places, people, or paths"
            ],
            "try_this": [
                "Ask: 'Is this direction still true, or am I just used to it?'",
                "Notice if your steadiness is serving you or keeping you stuck.",
                "When feeling lost, wait before forcing a direction."
            ],
            "why_this_is_happening": "Your G Center provides consistent identity and direction. This creates inner stability but can become rigidity if you stop questioning whether your path still fits.",
            "system_label": "G Center · defined"
        },
        "undefined": {
            "recognition": "You feel different in different places and with different people.",
            "what_this_is": "You tend to pick up a sense of identity and direction from your environment. Who you are shifts based on context. This isn't instability—it's openness to discovering yourself through experience.",
            "when_it_trips_you_up": "You attach to someone else's direction as if it's yours. You feel lost or uncertain about who you are. You become chameleon-like in ways that feel inauthentic.",
            "when_it_works": "You choose environments that bring out your best self. You recognize that identity is discovered, not fixed. You find yourself through exploration, not definition.",
            "at_your_highest": "You become wise about identity itself—seeing that who we are is always contextual and evolving.",
            "where_youll_notice_today": [
                "You're not sure 'who you are' or where you're headed",
                "Certain places or people make you feel more like yourself",
                "You feel lost, then suddenly clear, depending on context"
            ],
            "try_this": [
                "Notice which places make you feel most yourself. Go there.",
                "Ask: 'Is this my direction, or am I following someone else's?'",
                "Instead of 'Who am I?', ask 'Who am I right now, in this context?'"
            ],
            "why_this_is_happening": "Your G Center is open to identity and direction from the environment. This makes your sense of self fluid but requires careful choice of where and with whom you spend time.",
            "system_label": "G Center · open"
        }
    },
    "Ego": {
        "defined": {
            "recognition": "You can push through when you've committed to something.",
            "what_this_is": "You tend to have willpower available when you decide to use it. When you say you'll do something, you usually can. Commitment and follow-through are accessible to you.",
            "when_it_trips_you_up": "You prove yourself when no proof is required. You make promises you shouldn't just because you technically can. You push when rest would serve better.",
            "when_it_works": "You commit only to what genuinely matters. You use willpower strategically, not compulsively. You rest without feeling like you're failing.",
            "at_your_highest": "You become a force for what truly matters—your will serves purposes larger than proving yourself.",
            "where_youll_notice_today": [
                "You feel capable of making promises and keeping them",
                "You may push through resistance when something matters",
                "You have opinions about what's worth effort"
            ],
            "try_this": [
                "Before committing, ask: 'Is this mine to do, or am I proving I can?'",
                "Practice resting even when you could keep going.",
                "Notice when willpower is serving you versus depleting you."
            ],
            "why_this_is_happening": "Your Ego center provides consistent access to will and determination. This makes commitment reliable but can lead to overwork if every situation becomes a test.",
            "system_label": "Heart/Ego · defined"
        },
        "undefined": {
            "recognition": "You have variable willpower—sometimes you can push through, other times you can't.",
            "what_this_is": "You tend to have an inconsistent relationship with effort and will. Some days commitment is easy; other days it's impossible. This isn't weakness—it's a different design.",
            "when_it_trips_you_up": "You over-promise to prove your worth, then burn out. You compare yourself to people who push harder. You feel like failure when willpower isn't available.",
            "when_it_works": "You stop trying to prove yourself. You commit only to what you can actually sustain. You recognize that worth isn't measured by willpower.",
            "at_your_highest": "You become wise about will itself—seeing when effort is needed and when it's just ego.",
            "where_youll_notice_today": [
                "Effort feels available in some moments and impossible in others",
                "You might over-promise, then struggle to follow through",
                "You compare yourself to people who seem more driven"
            ],
            "try_this": [
                "Ask: 'Am I saying yes because I can, or to prove something?'",
                "Practice saying 'I'm not sure I can commit to that.'",
                "Notice when you're amplifying someone else's drive as your own."
            ],
            "why_this_is_happening": "Your Ego center is open to willpower from others. This means your relationship with effort varies—and your wisdom lies in knowing when not to push.",
            "system_label": "Heart/Ego · open"
        }
    },
    "Solar Plexus": {
        "defined": {
            "recognition": "You feel things in waves—your emotions rise and fall in patterns.",
            "what_this_is": "You tend to experience emotional highs and lows that belong to you. Clarity about decisions comes after time, not in the first moment. You bring an emotional atmosphere into spaces you enter.",
            "when_it_trips_you_up": "You make commitments at emotional peaks or lows. You expect feelings to be constant. You force decisions before the wave has passed.",
            "when_it_works": "You ride the wave without acting on extremes. You wait for clarity instead of forcing it. You trust that mood shifts are normal, not problems.",
            "at_your_highest": "You become emotionally wise—your depth brings richness and connection that pure logic could never access.",
            "where_youll_notice_today": [
                "Your mood shifts without clear external cause",
                "You feel certain in one moment, less certain hours later",
                "Big decisions feel better when you've slept on them"
            ],
            "try_this": [
                "For any decision that matters, wait at least one full day.",
                "When you feel certain at an emotional peak, write it down and revisit later.",
                "Practice saying 'I'm not sure yet' when asked during a wave."
            ],
            "why_this_is_happening": "Your Solar Plexus generates emotional waves. This creates depth and richness but means clarity comes over time, not instantly.",
            "system_label": "Solar Plexus · defined"
        },
        "undefined": {
            "recognition": "You absorb emotions from others—feeling what they feel, sometimes more intensely.",
            "what_this_is": "You tend to take in the emotional atmosphere around you. Your own baseline is more neutral, but you amplify whatever feelings are in the room. Conflict nearby becomes your conflict.",
            "when_it_trips_you_up": "You mistake someone else's emotion for your own. You avoid emotional situations entirely. You take responsibility for feelings that aren't yours to fix.",
            "when_it_works": "You recognize when emotions arrive from outside. You feel without absorbing. You use your sensitivity to read rooms accurately.",
            "at_your_highest": "You become wise about emotions themselves—seeing the waves without drowning in them.",
            "where_youll_notice_today": [
                "You pick up tension in a room before others notice",
                "Your mood shifts based on who you're around",
                "Conflict nearby feels like your own conflict"
            ],
            "try_this": [
                "After leaving an emotional situation, ask: 'Is this feeling mine?'",
                "Notice your baseline when completely alone.",
                "Practice being in emotional spaces without trying to fix anything."
            ],
            "why_this_is_happening": "Your Solar Plexus amplifies emotions from the environment. This makes you emotionally perceptive but requires learning to release what isn't yours.",
            "system_label": "Solar Plexus · open"
        }
    },
    "Sacral": {
        "defined": {
            "recognition": "You have consistent energy for work that engages you.",
            "what_this_is": "You tend to have sustainable power for effort—when something is right, you can go and go. Your gut responds to opportunities with a felt sense of yes or no.",
            "when_it_trips_you_up": "You override your gut response with logic. You stay in draining work because you technically can. You don't notice exhaustion until you've gone too far.",
            "when_it_works": "You trust your gut's first response. You stop before exhaustion hits. You engage only with work that genuinely lights you up.",
            "at_your_highest": "You become a sustainable force—your effort builds things that last because it comes from genuine engagement.",
            "where_youll_notice_today": [
                "You feel energy rising for certain tasks and dropping for others",
                "Your gut responds quickly: a subtle yes or no before you think",
                "You can keep working long after others would stop, if engaged"
            ],
            "try_this": [
                "When asked to do something, notice your body's first response.",
                "Practice stopping before you're exhausted.",
                "Honor that 'ugh' feeling—it's data, not laziness."
            ],
            "why_this_is_happening": "Your Sacral center provides sustainable life force for correct engagement. This creates work capacity but requires listening to gut signals about what's truly right.",
            "system_label": "Sacral · defined"
        },
        "undefined": {
            "recognition": "You don't have consistent work energy—you need to know when enough is enough.",
            "what_this_is": "You tend to have variable capacity for sustained effort. You can borrow work energy from others, but it's not sustainably yours. Learning your actual limits prevents burnout.",
            "when_it_trips_you_up": "You push based on borrowed energy. You compare yourself to people with consistent drive. You don't stop until you're completely depleted.",
            "when_it_works": "You stop before you're exhausted. You work in bursts rather than marathons. You know your actual sustainable pace.",
            "at_your_highest": "You become wise about effort itself—knowing when enough is enough, not just for you but in general.",
            "where_youll_notice_today": [
                "Your energy doesn't match what's expected of you",
                "You might be running on fumes without realizing it",
                "You need to rest before you feel tired"
            ],
            "try_this": [
                "Stop working before you're exhausted.",
                "Notice how your energy changes around different people.",
                "Ask: 'Is this my energy, or am I borrowing someone else's?'"
            ],
            "why_this_is_happening": "Your Sacral center is open to life force from others. This means your work capacity varies—your wisdom is knowing when to stop, not matching others' endurance.",
            "system_label": "Sacral · open"
        }
    },
    "Spleen": {
        "defined": {
            "recognition": "You get quiet, instant signals about what's safe or healthy.",
            "what_this_is": "You tend to receive subtle knowing in the moment—a hit about what's right or wrong that doesn't repeat. Your body gives you data about safety, timing, and health before your mind catches up.",
            "when_it_trips_you_up": "You override the signal with logic or politeness. You second-guess the first hit. You assume others have the same instinct and project safety onto them.",
            "when_it_works": "You honor the first hit, even without a reason. You trust your body's data. You act on instinct before the mind talks you out of it.",
            "at_your_highest": "You navigate life with real-time knowing—your instinct becomes a reliable compass in any situation.",
            "where_youll_notice_today": [
                "You get a 'hit' about something you can't explain",
                "Your body reacts to people or places before your mind catches up",
                "You know something is 'off' without knowing why"
            ],
            "try_this": [
                "When you get a quiet 'no,' honor it before finding a reason.",
                "Practice noticing your first response before analysis kicks in.",
                "Pay attention to what your body does around different people."
            ],
            "why_this_is_happening": "Your Spleen provides consistent access to instinct and survival awareness. This creates real-time knowing but requires learning to hear its quiet voice before the mind overrides it.",
            "system_label": "Spleen · defined"
        },
        "undefined": {
            "recognition": "You hold onto things longer than you should—jobs, relationships, habits.",
            "what_this_is": "You tend to struggle with letting go. Security feels uncertain, so you grip what you have even when it no longer serves. Fear may feel more amplified for you.",
            "when_it_trips_you_up": "You stay in something past its expiration because change feels unsafe. You ignore health signals. You let fear make decisions for you.",
            "when_it_works": "You recognize when the grip is keeping you stuck. You face fear without letting it decide. You release what's ready to go.",
            "at_your_highest": "You become wise about fear itself—knowing what's truly dangerous versus what just feels scary.",
            "where_youll_notice_today": [
                "You're staying in something past its time because change feels risky",
                "Fear feels more intense than others seem to experience",
                "You might dismiss intuitive hits or health signals"
            ],
            "try_this": [
                "Name one thing you're holding onto that might be ready to release.",
                "Ask: 'Am I holding on for safety, or because it still serves?'",
                "When fear arises, check: is this real or amplified?"
            ],
            "why_this_is_happening": "Your Spleen is open to survival awareness from others. This can amplify fear and make letting go difficult—your wisdom comes from learning what's truly unsafe versus what just feels that way.",
            "system_label": "Spleen · open"
        }
    },
    "Root": {
        "defined": {
            "recognition": "You handle pressure without being destabilized by it.",
            "what_this_is": "You tend to manage stress in your own rhythm. Urgency arrives but doesn't overwhelm you. You may even work better under pressure or deadline.",
            "when_it_trips_you_up": "You create unnecessary urgency. You become addicted to pressure. You can't relax even when nothing is urgent.",
            "when_it_works": "You use pressure strategically, not compulsively. You can complete things without deadline pressure. You rest genuinely.",
            "at_your_highest": "You become a grounding force for others—your steadiness under pressure creates space for everyone to breathe.",
            "where_youll_notice_today": [
                "You feel steady even when a lot is happening",
                "You might create deadlines to get yourself moving",
                "Stress doesn't seem to affect you as much as others"
            ],
            "try_this": [
                "Try finishing something without creating a deadline.",
                "Notice when you're manufacturing urgency that isn't real.",
                "Practice genuine rest, not 'productive rest.'"
            ],
            "why_this_is_happening": "Your Root center provides consistent access to pressure and drive. This creates resilience under stress but can become addiction to urgency if you're not careful.",
            "system_label": "Root · defined"
        },
        "undefined": {
            "recognition": "You absorb pressure from outside—other people's urgency becomes yours.",
            "what_this_is": "You tend to feel other people's stress as your own. Deadlines that aren't yours become urgent. You may rush to finish things just to get them off your plate.",
            "when_it_trips_you_up": "You rush even when there's no actual rush. You feel chronically stressed in fast environments. You can't tell the difference between your urgency and someone else's.",
            "when_it_works": "You recognize when pressure is borrowed. You choose calm environments. You complete things at your own pace without absorbing external stress.",
            "at_your_highest": "You become wise about urgency itself—seeing when pressure is real and when it's manufactured.",
            "where_youll_notice_today": [
                "You feel stressed by other people's deadlines",
                "Calm environments feel like relief; busy ones overwhelm you",
                "You rush even when nothing is actually urgent"
            ],
            "try_this": [
                "When pressure hits, ask: 'Is this deadline real, or absorbed?'",
                "Practice doing something at your natural pace.",
                "Notice how urgency changes in different environments."
            ],
            "why_this_is_happening": "Your Root center amplifies pressure from the environment. This can create chronic stress—your wisdom lies in recognizing what urgency is actually yours.",
            "system_label": "Root · open"
        }
    }
}


# =============================================================================
# GENE KEYS CONTENT TRANSFORMATION
# =============================================================================

def transform_gene_key_to_mirror_content(
    gate_number: int,
    shadow: str,
    gift: str,
    siddhi: str,
    shadow_description: str,
    gift_description: str,
    siddhi_description: str,
    programming_partner: int = None,
) -> Dict[str, Any]:
    """
    Transform Gene Keys content into Mirror Content System format.
    
    Shadow → WHEN IT TRIPS YOU UP
    Gift → WHEN IT WORKS
    Siddhi → AT YOUR HIGHEST
    """
    
    # Build recognition from the shadow/gift dynamic
    recognition = f"You carry a tension between {shadow.lower()} and {gift.lower()}—and it shapes how you show up."
    
    # Transform shadow into behavioral language
    when_it_trips_you_up = _behavior_first_transform(shadow_description, "shadow")
    
    # Transform gift into behavioral language
    when_it_works = _behavior_first_transform(gift_description, "gift")
    
    # Transform siddhi into highest potential
    at_your_highest = _behavior_first_transform(siddhi_description, "siddhi")
    
    # Generate practical sections
    where_youll_notice_today = _generate_daily_situations(shadow, gift, gate_number)
    try_this = _generate_try_this(shadow, gift, gate_number)
    
    # Technical explanation
    why_this_is_happening = f"Gate {gate_number} represents the journey from {shadow} through {gift} to {siddhi}. This isn't a problem to fix—it's a spectrum of expression. The shadow shows where you get caught; the gift shows your natural capacity; the siddhi shows what becomes possible with integration."
    
    return create_mirror_content(
        recognition=recognition,
        what_this_is=f"You tend to experience life through the lens of {gift.lower()}—but when pressure hits, {shadow.lower()} can take over. This is a core theme in how you operate.",
        when_it_trips_you_up=when_it_trips_you_up,
        when_it_works=when_it_works,
        at_your_highest=at_your_highest,
        where_youll_notice_today=where_youll_notice_today,
        try_this=try_this,
        why_this_is_happening=why_this_is_happening,
        system_label=f"Gate {gate_number} · {gift}"
    )


def _behavior_first_transform(description: str, mode: str) -> str:
    """Transform a description to start with 'You' and be behavior-focused."""
    # Simple transformation - can be enhanced with more sophisticated NLP
    if description.startswith("You"):
        return description
    
    prefixes = {
        "shadow": "You fall into",
        "gift": "You naturally access",
        "siddhi": "You embody"
    }
    
    prefix = prefixes.get(mode, "You experience")
    
    # Clean up the description
    desc = description.strip()
    if desc[0].isupper():
        desc = desc[0].lower() + desc[1:]
    
    return f"{prefix} {desc}"


def _generate_daily_situations(shadow: str, gift: str, gate_number: int) -> List[str]:
    """Generate WHERE YOU'LL NOTICE THIS TODAY bullets."""
    # This would be enhanced with gate-specific content
    return [
        f"A moment where {shadow.lower()} starts creeping in",
        f"An opportunity to express {gift.lower()} naturally",
        "A choice between the reactive and the responsive"
    ]


def _generate_try_this(shadow: str, gift: str, gate_number: int) -> List[str]:
    """Generate TRY THIS bullets."""
    return [
        f"When you notice {shadow.lower()} arising, pause before reacting.",
        f"Look for one situation where you can express {gift.lower()} today.",
        f"Ask: 'What would the {gift.lower()} version of me do here?'"
    ]


# =============================================================================
# CONTENT HELPERS
# =============================================================================

def get_hd_center_content(center_name: str, is_defined: bool) -> Dict[str, Any]:
    """Get Mirror Content for a Human Design center."""
    state = "defined" if is_defined else "undefined"
    center_content = HD_CENTER_CONTENT.get(center_name, {}).get(state)
    
    if not center_content:
        # Fallback
        return create_mirror_content(
            recognition=f"You experience {center_name.lower()} in your own way.",
            what_this_is=f"Your {center_name.lower()} expresses {'consistently' if is_defined else 'variably'}.",
            when_it_trips_you_up="When you're not aware, patterns can run you.",
            when_it_works="When you're present, you can choose your response.",
            at_your_highest="You integrate this aspect fully into who you are.",
            where_youll_notice_today=[
                "In how you show up in conversations",
                "In your energy throughout the day",
                "In decisions you need to make"
            ],
            try_this=[
                "Notice how this shows up without judgment.",
                "Experiment with a different response than usual.",
                "Ask: 'Is this serving me right now?'"
            ],
            why_this_is_happening=f"This reflects your {center_name} configuration.",
            system_label=f"{center_name} · {'defined' if is_defined else 'open'}"
        )
    
    return center_content


def format_mirror_content_for_display(content: Dict[str, Any]) -> Dict[str, Any]:
    """Format Mirror Content for frontend display."""
    return {
        # Top section (always visible)
        "recognition": content["recognition"],
        
        # Core expandable sections
        "sections": [
            {
                "title": "What This Is",
                "content": content["what_this_is"],
                "expanded_by_default": True
            },
            {
                "title": "When It Trips You Up",
                "content": content["when_it_trips_you_up"],
                "expanded_by_default": True
            },
            {
                "title": "When It Works",
                "content": content["when_it_works"],
                "expanded_by_default": True
            },
            {
                "title": "At Your Highest",
                "content": content["at_your_highest"],
                "expanded_by_default": True
            },
        ],
        
        # Practical sections
        "where_today": {
            "title": "Where You'll Notice This Today",
            "items": content["where_youll_notice_today"]
        },
        "try_this": {
            "title": "Try This",
            "items": content["try_this"]
        },
        
        # Collapsible explanation
        "why": {
            "title": "Why This Is Happening",
            "content": content["why_this_is_happening"],
            "collapsed_by_default": True
        },
        
        # Metadata (bottom)
        "system_label": content["system_label"]
    }
