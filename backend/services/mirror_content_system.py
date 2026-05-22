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
            "system_label": "Head center · defined",
            "v2": {
                "recognition": (
                    "You get caught by questions that won't let go. A line "
                    "of inquiry can stay with you for weeks — not because "
                    "you're forcing it, but because the mind keeps "
                    "returning to it on its own."
                ),
                "how_it_shows_up": [
                    "Ideas and questions arrive uninvited and stay until you've turned them over enough times.",
                    "People experience your curiosity as steady; you don't drop a line of thought easily.",
                    "You can sit inside a question longer than most people can tolerate.",
                ],
                "the_distortion": [
                    "The pressure to answer can feel constant, even when no answer is required.",
                    "You can mistake mental persistence for importance, and chase a question that isn't actually yours to solve.",
                    "Inspiration becomes background noise that crowds out rest.",
                ],
                "the_gift": [
                    "You see the shape of a problem long after others have moved on — sometimes that's exactly when it matters most.",
                    "You generate the questions other people don't think to ask.",
                ],
                "the_siddhi": {
                    "shadow": "Chasing every interesting question.",
                    "gift": "Following the inquiry that won't let go.",
                    "siddhi": "Knowing which questions are worth carrying — and which can be set down.",
                    "resonance_line": "Not every question is yours to answer.",
                },
                "why_this_exists": (
                    "This comes from a defined Head center — Human "
                    "Design's source of mental inspiration and the steady "
                    "pressure to wonder."
                ),
            }
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
            "system_label": "Head center · open",
            "v2": {
                "recognition": (
                    "Your mind catches whatever inspiration is in the room. "
                    "A question that means nothing to you alone can suddenly "
                    "feel urgent in someone else's presence — that's not "
                    "confusion, that's a wider channel for what's worth "
                    "thinking about."
                ),
                "how_it_shows_up": [
                    "The questions you find yourself chasing shift depending on who you're around.",
                    "You light up around mentally alive people and quiet down in mentally flat rooms.",
                    "An idea that felt urgent yesterday can have completely lost its grip by today.",
                ],
                "the_distortion": [
                    "You take someone else's burning question and carry it as if it were yours.",
                    "The pressure to figure something out feels borrowed but still loud.",
                    "You end up researching things you didn't actually need to know.",
                ],
                "the_gift": [
                    "You read which questions are mentally alive in a room — and which ones are stale.",
                    "Over time, you become unusually good at telling what's worth thinking about from what isn't.",
                ],
                "the_siddhi": {
                    "shadow": "Carrying questions that were never yours.",
                    "gift": "Sensing which questions are actually worth pursuing.",
                    "siddhi": "Wisdom about inspiration itself — the difference between a real question and a mental rumour.",
                    "resonance_line": "Not every pressure to know belongs to you.",
                },
                "why_this_exists": (
                    "This comes from an undefined Head center — open to "
                    "absorbing and amplifying mental pressure rather than "
                    "generating it."
                ),
            }
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
            "system_label": "Ajna · defined",
            # ──────────────────────────────────────────────────────────
            # V2 — Recognition-First Rewrite (HD Deep Dive V2)
            # Centers = the stable psychological weather system
            # underneath the person. Atmospheric, identity-level.
            # Framework explanation moves LAST and stays short.
            # ──────────────────────────────────────────────────────────
            "v2": {
                "recognition": (
                    "You settle into a way of understanding things and stay "
                    "with it longer than most people do. Others experience "
                    "your thinking as consistent — sometimes stabilizing, "
                    "sometimes difficult to move."
                ),
                "how_it_shows_up": [
                    "You don't easily abandon a perspective once it clicks internally.",
                    "People look to you for certainty or interpretation.",
                    "Mental consistency becomes part of how others recognize you.",
                ],
                "the_distortion": [
                    "Certainty can quietly become rigidity.",
                    "You defend conclusions long after curiosity should have reopened.",
                    "The pressure to already know closes off the room you'd actually think best inside.",
                ],
                "the_gift": [
                    "Your steadiness helps others orient themselves.",
                    "You can hold a line of thought through chaos without collapsing into confusion.",
                ],
                "the_siddhi": {
                    "shadow": "Defending what you already concluded.",
                    "gift": "Steadying others through complexity.",
                    "siddhi": "Holding clarity loosely enough that it can move.",
                    "resonance_line": "Not every certainty needs to be guarded.",
                },
                "why_this_exists": (
                    "This comes from a defined Ajna center — the area "
                    "Human Design associates with how you interpret and "
                    "stabilize thought."
                ),
            },
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
            "system_label": "Ajna · open",
            # ──────────────────────────────────────────────────────────
            # V2 — open centers must NOT be pathologized.
            # Read as: permeability, amplification, sensitivity,
            # wisdom-through-exposure. NOT: lack, inconsistency.
            # ──────────────────────────────────────────────────────────
            "v2": {
                "recognition": (
                    "Your thinking borrows shape from whatever room you're "
                    "in. Around clear thinkers you sound clear; around "
                    "confusion you sound less sure — what looks like "
                    "inconsistency is actually a much wider mental aperture."
                ),
                "how_it_shows_up": [
                    "You read other people's thinking quickly — sometimes before they finish a sentence.",
                    "Your view on the same question can land differently in different conversations.",
                    "You catch the logic gap in someone else's argument faster than they do.",
                ],
                "the_distortion": [
                    "You defend a position you don't actually hold, just because you were the one who said it.",
                    "The need to have an answer closes a mind built for holding many at once.",
                    "Borrowed certainty starts to feel like your own — and you carry it past where it served you.",
                ],
                "the_gift": [
                    "You can hold contradictory ideas without collapsing them too early.",
                    "You see the shape of someone else's thinking, which is what makes you a useful interpreter and editor.",
                    "Time and contrast reveal what is actually yours to think — and over the years that becomes a kind of accuracy.",
                ],
                "the_siddhi": {
                    "shadow": "Performing certainty you haven't actually arrived at.",
                    "gift": "Reading the field of thought without flattening it.",
                    "siddhi": "Knowing the wisest move is often to stay in the question.",
                    "resonance_line": "Not knowing is its own form of accuracy.",
                },
                "why_this_exists": (
                    "This comes from an undefined Ajna center — in Human "
                    "Design, an open Ajna is built to absorb and reflect "
                    "many forms of thinking rather than lock into one."
                ),
            },
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
            "system_label": "Throat · defined",
            "v2": {
                "recognition": (
                    "When you have something to say, it tends to come out "
                    "the way you meant it. Your voice has a recognisable "
                    "shape — people learn what to expect when you speak, "
                    "and they tend to listen."
                ),
                "how_it_shows_up": [
                    "You know when you're ready to say a thing — and when you're not yet.",
                    "Your voice carries a consistent signature; people often quote you accurately.",
                    "Turning an idea into words happens reliably when the moment is right.",
                ],
                "the_distortion": [
                    "You can speak before being asked, or push expression when timing isn't yet ripe.",
                    "Consistency in voice can harden into a script — the same phrasings, the same defaults.",
                    "You may keep talking past the point others were ready to hear.",
                ],
                "the_gift": [
                    "You give shape to what others couldn't quite name.",
                    "When you commit to saying a thing, it tends to land.",
                ],
                "the_siddhi": {
                    "shadow": "Speaking before the moment asks you to.",
                    "gift": "Giving language to what mattered.",
                    "siddhi": "Knowing that what's worth saying tends to land on its own.",
                    "resonance_line": "The right words wait for the right moment.",
                },
                "why_this_exists": (
                    "This comes from a defined Throat center — Human "
                    "Design's seat of expression and the reliable mechanics "
                    "of speech."
                ),
            }
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
            "system_label": "Throat · open",
            "v2": {
                "recognition": (
                    "Your voice takes on the colour of whatever room you're "
                    "in. With one person you're succinct; with another you "
                    "can't get a word in — and over time, you've gotten "
                    "unusually good at reading when speaking actually "
                    "serves something."
                ),
                "how_it_shows_up": [
                    "The way you talk shifts depending on who you're with.",
                    "You feel pressure to fill silences that no one else seems to feel.",
                    "You sometimes say something just to find out whether it's actually true.",
                ],
                "the_distortion": [
                    "You speak to be seen rather than because the moment was ready for what you have.",
                    "Pressure to have a voice overrides the more accurate move of waiting.",
                    "You exhaust yourself trying to keep up in conversations that aren't actually expecting much from you.",
                ],
                "the_gift": [
                    "You read whose voice a room is actually waiting for — and it isn't always yours.",
                    "When you do speak, it has unusual weight because it wasn't background noise.",
                ],
                "the_siddhi": {
                    "shadow": "Talking to prove you're here.",
                    "gift": "Speaking when the moment actually asks for it.",
                    "siddhi": "The voice that arrives only when it's needed becomes the one most worth hearing.",
                    "resonance_line": "Silence is its own kind of presence.",
                },
                "why_this_exists": (
                    "This comes from an undefined Throat center — built "
                    "for variability and reading the field, not for a "
                    "fixed manifesting rhythm."
                ),
            }
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
            "system_label": "G Center · defined",
            "v2": {
                "recognition": (
                    "You carry a sense of who you are that doesn't easily "
                    "shift. People recognise you across years and contexts "
                    "— there's something stable underneath whatever else is "
                    "happening on the surface."
                ),
                "how_it_shows_up": [
                    "Your sense of direction, identity, and what you love stays largely consistent.",
                    "Others orient themselves to you — sometimes without realising they're doing it.",
                    "You can stand still in your own identity while everything around you is moving.",
                ],
                "the_distortion": [
                    "Stability can become inflexibility — refusing a shift that would actually be true.",
                    "Others' need to know you can pressure you to over-define who you are.",
                    "You mistake the sameness of identity for the only valid version of you.",
                ],
                "the_gift": [
                    "You give others a point to navigate from.",
                    "You hold a steady line of self that lets the people around you find theirs.",
                ],
                "the_siddhi": {
                    "shadow": "Defending the version of you that no longer fits.",
                    "gift": "Being a steady reference point for those still finding theirs.",
                    "siddhi": "Holding identity loosely enough that it can refine without breaking.",
                    "resonance_line": "Who you are can quietly grow without needing to be announced.",
                },
                "why_this_exists": (
                    "This comes from a defined G center — Human Design's "
                    "seat of identity, love, and direction."
                ),
            }
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
            "system_label": "G Center · open",
            "v2": {
                # CRITICAL — open G is one of the most easily pathologized.
                # Frame as wider relational aperture / adaptive intelligence,
                # never as identity confusion or brokenness.
                "recognition": (
                    "Your sense of who you are and where you're going moves "
                    "with the environment more than most people's does. "
                    "What looks from outside like searching is, on the "
                    "inside, a much wider capacity to recognise where you "
                    "actually belong."
                ),
                "how_it_shows_up": [
                    "Who you are can feel different in different rooms — and both versions can be true.",
                    "The right place, the right people, the right work change everything about how you experience yourself.",
                    "You read whether a setting is actually yours before you can rationalise why.",
                ],
                "the_distortion": [
                    "You force a fixed identity because the world expects one of you.",
                    "You commit to a direction because someone else seemed certain about it.",
                    "You measure yourself against people whose stability you weren't built to copy.",
                ],
                "the_gift": [
                    "You navigate by environment with unusual accuracy — over time, you learn the geography of where you flourish.",
                    "You can hold many versions of yourself without collapsing them, which makes you adaptive in a way fixed identities aren't.",
                ],
                "the_siddhi": {
                    "shadow": "Pretending to a fixed self you haven't actually found.",
                    "gift": "Letting place and people shape who you can be.",
                    "siddhi": "Belonging is something you recognise, not something you manufacture.",
                    "resonance_line": "Where you stand changes who you can be.",
                },
                "why_this_exists": (
                    "This comes from an undefined G center — designed to "
                    "recognise belonging by exposure, not to manufacture "
                    "identity from inside."
                ),
            }
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
            "system_label": "Heart/Ego · defined",
            "v2": {
                "recognition": (
                    "When you commit to something, you can stay with it "
                    "longer than most. You know what you're willing to do — "
                    "and what you're not — and that holds even when others "
                    "would have moved on."
                ),
                "how_it_shows_up": [
                    "You feel a steady internal sense of what you'd put yourself behind.",
                    "You don't easily promise; once you do, you tend to deliver.",
                    "Your sense of worth doesn't depend on the room you're in.",
                ],
                "the_distortion": [
                    "Willpower can harden into proving — repeating a commitment you've outgrown.",
                    "You may overpromise to yourself and then refuse to renegotiate.",
                    "The stakes you set can outpace the rest of you that has to carry them.",
                ],
                "the_gift": [
                    "You can hold a promise across time, which makes you trustworthy in ways most people aren't.",
                    "You teach others, quietly, that follow-through is possible.",
                ],
                "the_siddhi": {
                    "shadow": "Proving worth through what you can carry.",
                    "gift": "Committing to what's actually yours to commit to.",
                    "siddhi": "Willpower used in service of what you love rather than to prove anything.",
                    "resonance_line": "What you keep your word on becomes who you are.",
                },
                "why_this_exists": (
                    "This comes from a defined Heart/Ego center — Human "
                    "Design's seat of willpower, commitment, and self-worth."
                ),
            }
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
            "system_label": "Heart/Ego · open",
            "v2": {
                # CRITICAL — open Ego is one of the most easily pathologized.
                # Frame as wave-based wisdom, not "lacks willpower".
                "recognition": (
                    "You're not built to grind. Your willpower runs in "
                    "waves, not in straight lines, and the most accurate "
                    "move with you isn't pushing harder — it's reading "
                    "when the actual yes is there."
                ),
                "how_it_shows_up": [
                    "Some days you can move mountains; other days the same thing feels heavier than it should.",
                    "You're sensitive to environments that demand constant proving, and you wilt under them.",
                    "You quietly know your worth is not the same thing as your output.",
                ],
                "the_distortion": [
                    "You try to manufacture willpower you don't have, and end up exhausted.",
                    "You overpromise to keep up with people built differently — and resent yourself when you can't deliver.",
                    "The world's just-push-through rhetoric makes you feel deficient instead of simply differently designed.",
                ],
                "the_gift": [
                    "You see when willpower is being misused as a substitute for genuine alignment.",
                    "You can teach others that worth doesn't need to be earned through constant output.",
                ],
                "the_siddhi": {
                    "shadow": "Forcing a commitment your body isn't behind.",
                    "gift": "Honouring the waves rather than fighting them.",
                    "siddhi": "Worth that doesn't depend on proving anything.",
                    "resonance_line": "You don't need to push through to deserve being here.",
                },
                "why_this_exists": (
                    "This comes from an undefined Heart/Ego center — built "
                    "for wave-based, context-dependent commitment rather "
                    "than constant grind."
                ),
            }
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
            "system_label": "Solar Plexus · defined",
            "v2": {
                "recognition": (
                    "You move through emotional waves. Clarity doesn't "
                    "arrive in flat moments — it arrives once the wave has "
                    "moved through you. Your patience with that process is "
                    "one of your most useful instincts."
                ),
                "how_it_shows_up": [
                    "Your mood has a recognisable rhythm — people learn to wait for the right moment to bring something to you.",
                    "Decisions feel different on the bottom of a wave than they do on the top, and you've learnt to factor that in.",
                    "You can hold a strong feeling without acting on it immediately.",
                ],
                "the_distortion": [
                    "You decide on the peak of the wave — and regret it on the bottom.",
                    "You drop into now-truth and treat it as permanent.",
                    "You let intensity be a substitute for clarity.",
                ],
                "the_gift": [
                    "You bring emotional weight to whatever you commit to.",
                    "When you do speak from clarity, it has a depth that flat-state thinking can't reach.",
                ],
                "the_siddhi": {
                    "shadow": "Acting on the peak of the wave.",
                    "gift": "Letting the wave finish before deciding.",
                    "siddhi": "Emotional accuracy that arrives only with time.",
                    "resonance_line": "Wait for the next morning.",
                },
                "why_this_exists": (
                    "This comes from a defined Solar Plexus — the "
                    "emotional wave is your authority, not your enemy."
                ),
            }
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
            "system_label": "Solar Plexus · open",
            "v2": {
                # CRITICAL — open Solar Plexus is easy to pathologize as
                # "too sensitive". Frame as high-resolution empathic read.
                "recognition": (
                    "You feel the emotional weather of whoever is near you "
                    "more sharply than they do. What you've sometimes been "
                    "told is too sensitive is actually a very "
                    "high-resolution read of the room."
                ),
                "how_it_shows_up": [
                    "You walk into a room and can tell what was happening there before you arrived.",
                    "Conflict nearby becomes your conflict — even when it isn't.",
                    "You amplify whatever emotional state the strongest person near you is carrying.",
                ],
                "the_distortion": [
                    "You confuse someone else's tension for your own and act on it as if it were.",
                    "You avoid conflict for everyone, including conflict that wasn't yours to manage.",
                    "You go quiet around big feelings in others, then resent the silence.",
                ],
                "the_gift": [
                    "You read what others can't read in themselves yet, and over time that becomes a kind of accuracy you can trust.",
                    "You make the people around you feel felt without doing anything obvious.",
                ],
                "the_siddhi": {
                    "shadow": "Carrying everyone else's weather as if it were yours.",
                    "gift": "Knowing the difference between what you walked in with and what walked in with the room.",
                    "siddhi": "Empathy that doesn't lose track of where you end.",
                    "resonance_line": "What you feel here is not always yours to keep.",
                },
                "why_this_exists": (
                    "This comes from an undefined Solar Plexus — built to "
                    "amplify and read emotional fields, not to generate a "
                    "steady internal weather."
                ),
            }
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
            "system_label": "Sacral · defined",
            "v2": {
                "recognition": (
                    "You have a steady supply of work-and-life energy when "
                    "it's pointed at the right things. Your body knows "
                    "what's a real yes and what isn't — the trick has "
                    "always been listening to it."
                ),
                "how_it_shows_up": [
                    "You can keep going on what's genuinely yours; you stall on what isn't.",
                    "Your gut has a faster, more reliable read on a decision than your head does.",
                    "People feel your aliveness when you're working in a yes direction.",
                ],
                "the_distortion": [
                    "You push past the no your body is already giving you.",
                    "You confuse I could do this with I should do this.",
                    "You burn out on the wrong yes long after the body stopped agreeing.",
                ],
                "the_gift": [
                    "When you're on a true yes, you become unreasonably productive without strain.",
                    "You teach others, by example, that energy follows alignment.",
                ],
                "the_siddhi": {
                    "shadow": "Forcing yourself through every no.",
                    "gift": "Trusting the body's yes.",
                    "siddhi": "Generative energy that follows truth, not effort.",
                    "resonance_line": "If your body is saying no, the answer is no.",
                },
                "why_this_exists": (
                    "This comes from a defined Sacral — Human Design's "
                    "generator of life-force energy and gut response."
                ),
            }
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
            "system_label": "Sacral · open",
            "v2": {
                # Non-Generators — protect against "low energy" framing.
                "recognition": (
                    "Your energy isn't built to run flat. It comes in "
                    "surges and ebbs, and the people around you can "
                    "amplify or drain it without realising. The accurate "
                    "move with you isn't constant output — it's "
                    "protecting where the surges go."
                ),
                "how_it_shows_up": [
                    "You can match other people's energy temporarily and then crash later.",
                    "Pushing through tiredness costs you more than it costs people built differently.",
                    "You're at your sharpest on a small number of right things, not a long list of shoulds.",
                ],
                "the_distortion": [
                    "You measure yourself against constant-energy people and feel broken.",
                    "You burn yourself out trying to keep up with a rhythm you weren't built for.",
                    "You take on workloads as if your energy were a renewable resource on demand.",
                ],
                "the_gift": [
                    "When you do show up, you bring concentration most generators can't sustain.",
                    "You see clearly that more output isn't always the right answer — and the people around you eventually learn from that.",
                ],
                "the_siddhi": {
                    "shadow": "Performing energy you don't actually have.",
                    "gift": "Working in surges, resting in ebbs.",
                    "siddhi": "A life paced by what's actually alive rather than what's expected.",
                    "resonance_line": "Rest is a strategy, not a weakness.",
                },
                "why_this_exists": (
                    "This comes from an undefined Sacral — designed for "
                    "burst-and-recover, not constant production."
                ),
            }
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
            "system_label": "Spleen · defined",
            "v2": {
                "recognition": (
                    "Your body knows things before your mind does. A "
                    "faint sense of off arrives a second before the "
                    "situation reveals it — and over time, you've learnt "
                    "that the faint sense was almost always right."
                ),
                "how_it_shows_up": [
                    "You catch a wrong note in a person, a place, or a plan before you can explain it.",
                    "You feel safer in some rooms than in others, and that feeling is usually accurate.",
                    "Your timing instinct is reliable when you don't overthink it.",
                ],
                "the_distortion": [
                    "You override the quiet signal in favour of the louder argument.",
                    "You wait for proof of what you already knew.",
                    "You explain the hunch into uncertainty and miss the window it opened.",
                ],
                "the_gift": [
                    "You sense health, safety, and timing with a fidelity most people don't have.",
                    "You give those near you the benefit of an early-warning system without ever announcing it.",
                ],
                "the_siddhi": {
                    "shadow": "Talking yourself out of what your body already knew.",
                    "gift": "Listening to the first signal.",
                    "siddhi": "Instinct trusted exactly because it doesn't repeat itself.",
                    "resonance_line": "The first whisper is usually the truth.",
                },
                "why_this_exists": (
                    "This comes from a defined Spleen — Human Design's "
                    "seat of instinct, immune awareness, and "
                    "present-moment knowing."
                ),
            }
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
            "system_label": "Spleen · open",
            "v2": {
                "recognition": (
                    "Without a steady internal alarm system, you've learnt "
                    "to read safety, timing, and wellbeing through "
                    "everything around you. Other people's instincts pass "
                    "through you, and you've gotten unusually good at "
                    "telling which ones to trust."
                ),
                "how_it_shows_up": [
                    "You can hold on to relationships, habits, or environments that aren't actually well for you, because the no-signal isn't loud.",
                    "You amplify the calm or the alarm of whoever you're with.",
                    "Decisions about timing — when to leave, when to act — can feel harder for you than for others.",
                ],
                "the_distortion": [
                    "You override your tiredness or unease because no internal alarm is firing.",
                    "You stay too long in the wrong thing because there was no clear signal to leave.",
                    "You confuse familiarity with safety.",
                ],
                "the_gift": [
                    "You read other people's instinct unusually accurately, which makes you good at advising on situations you yourself aren't inside.",
                    "You develop, over time, an inherited library of others' wisdom about safety, health, and timing.",
                ],
                "the_siddhi": {
                    "shadow": "Treating familiarity as safety.",
                    "gift": "Borrowing well from the instincts you trust.",
                    "siddhi": "Wisdom about timing that compounds over years.",
                    "resonance_line": "What's familiar isn't automatically what's safe.",
                },
                "why_this_exists": (
                    "This comes from an undefined Spleen — built to read "
                    "instinct in others and over time, not to generate a "
                    "constant internal alarm."
                ),
            }
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
            "system_label": "Root · defined",
            "v2": {
                "recognition": (
                    "You carry your own pressure. Some part of you is "
                    "always running a clock, with or without an external "
                    "deadline — and most of the time that internal "
                    "pressure is what gets the thing done."
                ),
                "how_it_shows_up": [
                    "You have an internal drive to move that doesn't need outside coaching.",
                    "You hit deadlines because the pressure was already alive inside you, not because someone else applied it.",
                    "Stillness can feel uncomfortable in a way other people don't experience.",
                ],
                "the_distortion": [
                    "You drive yourself past where the body can keep up.",
                    "You confuse stress with productivity and add pressure that wasn't needed.",
                    "Rest can feel like an emergency rather than a strategy.",
                ],
                "the_gift": [
                    "You set the pace others can move at, without becoming controlling about it.",
                    "You translate restlessness into reliable forward motion.",
                ],
                "the_siddhi": {
                    "shadow": "Generating pressure for its own sake.",
                    "gift": "Using internal pressure as a clean engine.",
                    "siddhi": "Stillness as the rarest kind of work.",
                    "resonance_line": "Not all motion is progress.",
                },
                "why_this_exists": (
                    "This comes from a defined Root — Human Design's "
                    "source of adrenaline, drive, and life-pressure."
                ),
            }
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
            "system_label": "Root · open",
            "v2": {
                "recognition": (
                    "Other people's deadlines and urgency become yours "
                    "faster than they should. What looks like "
                    "procrastination is often the body refusing to make "
                    "someone else's pressure feel like your own."
                ),
                "how_it_shows_up": [
                    "You feel jittery in rushed environments even when nothing is actually on fire for you.",
                    "A friend's stress can land in your body within minutes.",
                    "You speed up to discharge pressure that isn't actually about you.",
                ],
                "the_distortion": [
                    "You make decisions in a hurry to make the feeling go away.",
                    "You measure productivity by how much pressure you're under rather than what's actually getting done.",
                    "You stay in environments whose tempo is wearing you down.",
                ],
                "the_gift": [
                    "You can hold steady when others can't, once you've learnt the pressure isn't yours.",
                    "You read the actual urgency of a situation without being dragged by its theatrics.",
                ],
                "the_siddhi": {
                    "shadow": "Hurrying to escape borrowed pressure.",
                    "gift": "Distinguishing real urgency from imported urgency.",
                    "siddhi": "A pace that's actually yours.",
                    "resonance_line": "You don't have to hurry just because someone else is.",
                },
                "why_this_exists": (
                    "This comes from an undefined Root — designed to "
                    "absorb and read pressure rather than continually "
                    "generate it."
                ),
            }
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
