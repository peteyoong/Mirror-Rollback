"""Horizon Interpretation Layer V1.0 - Timeframe-Specific Astrology

CORE RULE: Today / Week / Month MUST produce DISTINCT interpretations.
The same event may be relevant across all 3, but the framing MUST change.

THREE INTERPRETATION MODES:

A. TODAY MODE
   Question: "What is peaking or loud right now?"
   Focus: Immediate lived texture, body, emotions, reactions, tension
   Language: Present tense, immediate, urgent

B. WEEK MODE  
   Question: "What keeps surfacing across these days?"
   Focus: Recurring themes, buildup + peak + aftermath
   Language: Repetition, revisiting, resurfacing

C. MONTH MODE
   Question: "What larger arc is this part of?"
   Focus: Broader storyline, phase, cycle, transformation
   Language: Phase, reorientation, longer lesson

GUARDRAILS:
- Themes MUST be distinct across horizons
- whats_happening blocks MUST differ
- Same event, different framing
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =============================================================================
# HORIZON-SPECIFIC FULL MOON CONTENT
# =============================================================================

FULL_MOON_HORIZONS = {
    "Aries": {
        "today": {
            "headline": "Full Moon in Aries — Peak Urgency",
            "theme": "The impulse to act is peaking right now",
            "what_it_means": "Everything feels urgent TODAY. The body wants to move, decide, push forward — even without full clarity.",
            "felt_texture": [
                "Restlessness that won't settle until something moves",
                "Irritability with anyone who slows you down",
                "Physical tension demanding release",
            ],
            "action": "Move ONE thing forward today — but don't burn bridges in the heat",
            "question": "What are you ready to push through right now, even if it's uncomfortable?",
        },
        "week": {
            "headline": "Full Moon Week — Urgency Keeps Returning",
            "theme": "The same impatience keeps surfacing this week",
            "what_it_means": "This week, you may notice the same urgency returning in different situations. The buildup → peak → aftermath of this Full Moon is asking: what are you avoiding by staying busy?",
            "felt_texture": [
                "The same restlessness showing up in different contexts",
                "Repeated moments of wanting to force progress",
                "Irritability that keeps finding new targets",
            ],
            "action": "Notice where the urgency repeats — that's where the real tension lives",
            "question": "What keeps triggering the same impatient response this week?",
        },
        "month": {
            "headline": "This Month's Arc — Learning to Act Without Forcing",
            "theme": "A month of confronting your relationship with urgency",
            "what_it_means": "This Full Moon is one peak inside a larger monthly lesson about action vs. reaction. The month is teaching you when to push and when to wait.",
            "felt_texture": [
                "Phases of high drive followed by necessary rest",
                "Learning the difference between impulse and intuition",
                "Old patterns of forcing outcomes being challenged",
            ],
            "action": "Track your impulses this month — notice which ones are wise and which are just impatience",
            "question": "What is this month teaching you about the right way to move forward?",
        },
    },
    "Taurus": {
        "today": {
            "headline": "Full Moon in Taurus — Peak Stubbornness",
            "theme": "Something feels non-negotiable right now",
            "what_it_means": "You're digging in TODAY. Something you're holding onto feels essential, even if others don't understand why.",
            "felt_texture": [
                "Physical tension when asked to compromise",
                "Needing comfort that no one else can provide right now",
                "The body refusing to budge",
            ],
            "action": "Notice what you're gripping — is it security or fear of change?",
            "question": "What are you refusing to let go of today, and why?",
        },
        "week": {
            "headline": "Full Moon Week — The Same Resistance Returning",
            "theme": "The same stubbornness keeps surfacing this week",
            "what_it_means": "This week, you may find yourself repeatedly drawn back to the same position — the same thing you won't budge on. The repetition is trying to show you something.",
            "felt_texture": [
                "The same boundary being tested from different angles",
                "Repeated moments of digging in",
                "Comfort-seeking that keeps returning",
            ],
            "action": "Notice which resistance is wisdom and which is just fear of change",
            "question": "What keeps bringing you back to the same immovable position this week?",
        },
        "month": {
            "headline": "This Month's Arc — Redefining What You Need",
            "theme": "A month of confronting what you truly value vs. what you're just clinging to",
            "what_it_means": "This Full Moon highlights one moment in a larger monthly process of sorting real needs from outdated attachments. The month is teaching you what's worth holding onto.",
            "felt_texture": [
                "Gradual loosening of things you thought were essential",
                "New clarity about actual vs. imagined security",
                "The body slowly releasing old tension patterns",
            ],
            "action": "By month's end, identify one thing you've been holding that's ready to be released",
            "question": "What is this month teaching you about the difference between need and habit?",
        },
    },
    "Gemini": {
        "today": {
            "headline": "Full Moon in Gemini — Peak Mental Noise",
            "theme": "The mind is LOUD right now",
            "what_it_means": "Too many options, not enough clarity TODAY. The mental chatter is peaking — trying to think your way through won't work.",
            "felt_texture": [
                "Overthinking every possible scenario",
                "Starting conversations you can't finish",
                "Scattered energy pulling in multiple directions",
            ],
            "action": "Write it down — get it out of your head and onto paper",
            "question": "What are you overthinking right now that doesn't actually need a decision today?",
        },
        "week": {
            "headline": "Full Moon Week — The Same Thoughts Keep Circling",
            "theme": "The same mental loops keep returning this week",
            "what_it_means": "This week, notice how the same thoughts, conversations, or options keep circling back. The repetition is pointing at something you haven't fully processed yet.",
            "felt_texture": [
                "The same question returning in different forms",
                "Repeated conversations about the same topic",
                "Mental noise that quiets then returns",
            ],
            "action": "Track which thoughts keep returning — they're showing you what actually matters",
            "question": "What keeps circling in your mind this week that you haven't fully addressed?",
        },
        "month": {
            "headline": "This Month's Arc — Learning to Trust Fewer Answers",
            "theme": "A month of confronting information overload",
            "what_it_means": "This Full Moon is one peak inside a larger monthly lesson about mental clarity vs. mental noise. The month is teaching you that more information isn't always more clarity.",
            "felt_texture": [
                "Gradual quieting of unnecessary mental chatter",
                "Learning which questions actually need answering",
                "Growing ability to sit with uncertainty",
            ],
            "action": "By month's end, identify the ONE question that actually matters",
            "question": "What is this month teaching you about the difference between thinking and knowing?",
        },
    },
    "Cancer": {
        "today": {
            "headline": "Full Moon in Cancer — Peak Emotional Intensity",
            "theme": "Feelings are at maximum right now",
            "what_it_means": "Old needs are surfacing TODAY. The emotional body is asking for attention — and possibly for something you haven't let yourself ask for.",
            "felt_texture": [
                "Wanting to be held but not wanting to ask",
                "Old family patterns suddenly feeling fresh",
                "Tears for no obvious reason",
            ],
            "action": "Let yourself feel it without needing to fix it today",
            "question": "What emotion is trying to surface right now that you've been holding back?",
        },
        "week": {
            "headline": "Full Moon Week — The Same Feelings Keep Surfacing",
            "theme": "The same emotional undercurrent keeps returning this week",
            "what_it_means": "This week, the same feeling may surface in different contexts — at home, at work, in relationships. The repetition is showing you something unprocessed.",
            "felt_texture": [
                "The same emotional tone coloring different situations",
                "Repeated vulnerability in unexpected moments",
                "Old needs showing up in new contexts",
            ],
            "action": "Notice which feeling keeps returning — it has a message for you",
            "question": "What keeps making you feel the same way this week, even in different situations?",
        },
        "month": {
            "headline": "This Month's Arc — Relearning How to Need",
            "theme": "A month of confronting your relationship with vulnerability",
            "what_it_means": "This Full Moon is one peak inside a larger monthly lesson about emotional needs and how you ask (or don't ask) for them to be met.",
            "felt_texture": [
                "Gradual softening of emotional armor",
                "New ways of expressing need emerging",
                "Old patterns of caretaking being examined",
            ],
            "action": "By month's end, identify one need you've been hiding and find a way to name it",
            "question": "What is this month teaching you about letting yourself need things?",
        },
    },
    "Leo": {
        "today": {
            "headline": "Full Moon in Leo — Peak Need for Recognition",
            "theme": "You want to be SEEN right now",
            "what_it_means": "The need for appreciation is peaking TODAY. Something in you is asking to be acknowledged — and getting frustrated when it's not.",
            "felt_texture": [
                "Frustration when your efforts go unacknowledged",
                "Wanting to perform, even when exhausted",
                "Pride colliding with vulnerability",
            ],
            "action": "Acknowledge yourself first — don't wait for others today",
            "question": "What part of you is asking to be seen right now?",
        },
        "week": {
            "headline": "Full Moon Week — The Same Need for Recognition Returning",
            "theme": "The same desire to be seen keeps surfacing this week",
            "what_it_means": "This week, notice how the same need for acknowledgment shows up in different situations. The repetition is pointing at something deeper than any single interaction.",
            "felt_texture": [
                "The same desire for recognition in different contexts",
                "Repeated moments of wanting to shine",
                "Frustration that keeps finding the same target",
            ],
            "action": "Notice where you keep seeking validation — that's where you need to validate yourself",
            "question": "What keeps triggering the same need to be acknowledged this week?",
        },
        "month": {
            "headline": "This Month's Arc — Redefining What Recognition Means",
            "theme": "A month of confronting your relationship with attention",
            "what_it_means": "This Full Moon is one peak inside a larger monthly lesson about external validation vs. internal worth. The month is teaching you where your real value lives.",
            "felt_texture": [
                "Gradual shift from needing applause to feeling self-worth",
                "New relationship with your own creativity emerging",
                "Old patterns of performing for approval being examined",
            ],
            "action": "By month's end, identify one way you've been seeking outside what can only come from inside",
            "question": "What is this month teaching you about the difference between attention and respect?",
        },
    },
    "Virgo": {
        "today": {
            "headline": "Full Moon in Virgo — Peak Self-Criticism",
            "theme": "You're seeing every flaw right now",
            "what_it_means": "The perfectionist is running the show TODAY. You're noticing what's broken, what's wrong, what needs fixing — and possibly being too hard on yourself.",
            "felt_texture": [
                "Finding fault in everything — including yourself",
                "Anxiety about things being 'good enough'",
                "The urge to fix everything at once",
            ],
            "action": "Name three things that are working BEFORE touching what's broken",
            "question": "What are you being too hard on yourself about right now?",
        },
        "week": {
            "headline": "Full Moon Week — The Same Critical Voice Returning",
            "theme": "The same perfectionist pressure keeps surfacing this week",
            "what_it_means": "This week, the same critical voice may show up in different areas — work, health, relationships. The repetition is showing you a pattern, not a problem list.",
            "felt_texture": [
                "The same anxiety about adequacy in different contexts",
                "Repeated urges to optimize and improve",
                "Self-criticism that keeps finding new targets",
            ],
            "action": "Notice which criticism keeps returning — it's less about the details and more about the fear",
            "question": "What keeps triggering the same self-critical response this week?",
        },
        "month": {
            "headline": "This Month's Arc — Learning the Difference Between Care and Control",
            "theme": "A month of confronting perfectionism",
            "what_it_means": "This Full Moon is one peak inside a larger monthly lesson about improvement vs. self-attack. The month is teaching you when refinement helps and when it hurts.",
            "felt_texture": [
                "Gradual softening of impossible standards",
                "New ability to accept 'good enough'",
                "Old patterns of over-fixing being released",
            ],
            "action": "By month's end, identify one area where perfectionism is actually self-sabotage",
            "question": "What is this month teaching you about the cost of always trying to be better?",
        },
    },
    "Libra": {
        "today": {
            "headline": "Full Moon in Libra — Peak Relationship Tension",
            "theme": "Something in your relationships is coming to a head right now",
            "what_it_means": "The balance is off TODAY. Something you've been tolerating, swallowing, or ignoring in a relationship is demanding attention.",
            "felt_texture": [
                "Wanting harmony but feeling the imbalance",
                "Resentment you've been swallowing",
                "The other person's needs feeling heavy",
            ],
            "action": "Say what you've been editing — the peace you're keeping isn't peaceful",
            "question": "What have you been avoiding saying to keep the peace?",
        },
        "week": {
            "headline": "Full Moon Week — The Same Relational Pattern Returning",
            "theme": "The same imbalance keeps showing up this week",
            "what_it_means": "This week, the same dynamic may repeat across different relationships — the same role you play, the same thing you tolerate. The repetition is the message.",
            "felt_texture": [
                "The same compromise being asked in different contexts",
                "Repeated moments of swallowing your truth",
                "Fairness questions returning from different angles",
            ],
            "action": "Notice which relational pattern keeps repeating — it's asking to be changed",
            "question": "What keeps putting you in the same uncomfortable position this week?",
        },
        "month": {
            "headline": "This Month's Arc — Redefining What Balance Actually Means",
            "theme": "A month of confronting your relationship patterns",
            "what_it_means": "This Full Moon is one peak inside a larger monthly lesson about true balance vs. people-pleasing. The month is teaching you where your real boundaries are.",
            "felt_texture": [
                "Gradual clarity about what you actually need in relationships",
                "New ability to hold your ground without guilt",
                "Old patterns of over-accommodating being examined",
            ],
            "action": "By month's end, identify one relationship pattern that needs to fundamentally change",
            "question": "What is this month teaching you about the difference between harmony and truth?",
        },
    },
    "Scorpio": {
        "today": {
            "headline": "Full Moon in Scorpio — Peak Intensity",
            "theme": "Deep feelings are surfacing right now",
            "what_it_means": "Something wants to be transformed TODAY. The intensity is real — old patterns, old wounds, old power dynamics are asking for attention.",
            "felt_texture": [
                "Intensity in small moments",
                "Obsessive thoughts circling",
                "Old wounds suddenly fresh",
            ],
            "action": "Let something die that's already gone — stop resuscitating it",
            "question": "What are you holding onto that's already over?",
        },
        "week": {
            "headline": "Full Moon Week — The Same Intensity Keeps Returning",
            "theme": "The same deep pattern keeps surfacing this week",
            "what_it_means": "This week, the same intensity may show up in different forms — the same trigger, the same depth, the same power dynamic. The repetition is clearing something.",
            "felt_texture": [
                "The same deep feeling surfacing in different contexts",
                "Repeated moments of emotional intensity",
                "Power dynamics being tested from multiple angles",
            ],
            "action": "Notice what keeps bringing up the same intensity — that's what's ready to transform",
            "question": "What keeps triggering the same deep response this week?",
        },
        "month": {
            "headline": "This Month's Arc — A Cycle of Death and Rebirth",
            "theme": "A month of profound transformation",
            "what_it_means": "This Full Moon is one peak inside a larger monthly process of letting go and rebuilding. The month is asking you to release something fundamental.",
            "felt_texture": [
                "Gradual release of things you thought you couldn't live without",
                "New power emerging from surrender",
                "Old control patterns being dismantled",
            ],
            "action": "By month's end, identify what has died and what has been born in its place",
            "question": "What is this month teaching you about the necessity of endings?",
        },
    },
    "Sagittarius": {
        "today": {
            "headline": "Full Moon in Sagittarius — Peak Restlessness",
            "theme": "You want OUT right now",
            "what_it_means": "The walls feel too close TODAY. Something in you is craving expansion, escape, or just anywhere but here.",
            "felt_texture": [
                "Boredom with everything familiar",
                "Wanting to escape responsibilities",
                "Big promises without follow-through energy",
            ],
            "action": "Expand your perspective before expanding your commitments",
            "question": "What are you trying to escape from right now?",
        },
        "week": {
            "headline": "Full Moon Week — The Same Restlessness Returning",
            "theme": "The same urge to escape keeps surfacing this week",
            "what_it_means": "This week, the same restlessness may show up in different forms — boredom at work, impatience in relationships, craving novelty. The repetition is pointing at what you're avoiding.",
            "felt_texture": [
                "The same boredom surfacing in different areas",
                "Repeated urges to change everything",
                "Wanderlust that keeps returning",
            ],
            "action": "Notice what you keep wanting to escape — running won't solve it",
            "question": "What keeps triggering the same desire to be somewhere else this week?",
        },
        "month": {
            "headline": "This Month's Arc — Finding Freedom Without Fleeing",
            "theme": "A month of confronting what freedom actually means",
            "what_it_means": "This Full Moon is one peak inside a larger monthly lesson about expansion vs. escapism. The month is teaching you the difference between growth and avoidance.",
            "felt_texture": [
                "Gradual clarity about what you're actually seeking",
                "New ways of finding expansion without abandonment",
                "Old patterns of running being examined",
            ],
            "action": "By month's end, identify one thing you've been running from that needs facing",
            "question": "What is this month teaching you about the difference between adventure and avoidance?",
        },
    },
    "Capricorn": {
        "today": {
            "headline": "Full Moon in Capricorn — Peak Pressure",
            "theme": "The weight of responsibility is peaking right now",
            "what_it_means": "Something has to give TODAY. The load you're carrying feels heavier than usual — and some of it may not actually be yours.",
            "felt_texture": [
                "Exhaustion that rest doesn't fix",
                "The urge to push through anyway",
                "Guilt when you stop working",
            ],
            "action": "Put something down — you're carrying weight that isn't yours",
            "question": "What responsibility are you carrying today that isn't actually yours?",
        },
        "week": {
            "headline": "Full Moon Week — The Same Pressure Returning",
            "theme": "The same weight keeps landing on you this week",
            "what_it_means": "This week, the same sense of burden may show up in different areas — work, family, self-expectation. The repetition is showing you a pattern of over-responsibility.",
            "felt_texture": [
                "The same exhaustion surfacing in different contexts",
                "Repeated moments of shouldering too much",
                "Duty that keeps finding new forms",
            ],
            "action": "Notice which responsibilities keep returning — some need to be given back",
            "question": "What keeps putting the same weight on your shoulders this week?",
        },
        "month": {
            "headline": "This Month's Arc — Redefining Success and Rest",
            "theme": "A month of confronting your relationship with achievement",
            "what_it_means": "This Full Moon is one peak inside a larger monthly lesson about ambition vs. burnout. The month is teaching you that sustainable success requires release.",
            "felt_texture": [
                "Gradual permission to rest without guilt",
                "New definition of achievement emerging",
                "Old patterns of overwork being challenged",
            ],
            "action": "By month's end, identify one thing you've been achieving that's costing too much",
            "question": "What is this month teaching you about the real price of your ambitions?",
        },
    },
    "Aquarius": {
        "today": {
            "headline": "Full Moon in Aquarius — Peak Detachment",
            "theme": "You're distancing from your own feelings right now",
            "what_it_means": "Something is being intellectualized TODAY that needs to be felt. The analytical mind is working overtime to avoid the emotional truth.",
            "felt_texture": [
                "Analyzing feelings instead of feeling them",
                "Wanting to fix systems instead of sitting with discomfort",
                "Feeling alien even around familiar people",
            ],
            "action": "Drop into your body — the answer isn't in your head",
            "question": "What are you analyzing right now instead of feeling?",
        },
        "week": {
            "headline": "Full Moon Week — The Same Detachment Returning",
            "theme": "The same emotional distance keeps surfacing this week",
            "what_it_means": "This week, the same pattern of intellectualizing or distancing may repeat. Notice where you keep going to your head to avoid your heart.",
            "felt_texture": [
                "The same emotional bypass in different situations",
                "Repeated urges to understand instead of feel",
                "Alienation that keeps finding new contexts",
            ],
            "action": "Notice where you keep retreating to your mind — your body has a message",
            "question": "What keeps triggering the same retreat into analysis this week?",
        },
        "month": {
            "headline": "This Month's Arc — Reconnecting Head and Heart",
            "theme": "A month of confronting emotional avoidance",
            "what_it_means": "This Full Moon is one peak inside a larger monthly lesson about the relationship between thinking and feeling. The month is teaching you that both are necessary.",
            "felt_texture": [
                "Gradual integration of intellect and emotion",
                "New ability to feel without losing perspective",
                "Old patterns of emotional detachment being softened",
            ],
            "action": "By month's end, identify one feeling you've been explaining away instead of experiencing",
            "question": "What is this month teaching you about the limits of understanding without feeling?",
        },
    },
    "Pisces": {
        "today": {
            "headline": "Full Moon in Pisces — Peak Sensitivity",
            "theme": "Boundaries are dissolving right now",
            "what_it_means": "You're feeling everything TODAY — yours and everyone else's. The usual filters are down, and reality feels fluid.",
            "felt_texture": [
                "Not knowing what's yours vs. what you're absorbing",
                "Dreams more vivid than usual",
                "Wanting to escape into anything but reality",
            ],
            "action": "Ground yourself physically before making any decisions",
            "question": "What emotion are you carrying right now that isn't actually yours?",
        },
        "week": {
            "headline": "Full Moon Week — The Same Overwhelm Returning",
            "theme": "The same sensitivity keeps flooding in this week",
            "what_it_means": "This week, the same boundary dissolution may repeat — absorbing others' emotions, escaping into fantasy, losing yourself in the collective. The pattern needs attention.",
            "felt_texture": [
                "The same overwhelm surfacing in different contexts",
                "Repeated moments of boundary confusion",
                "Escapism that keeps finding new forms",
            ],
            "action": "Notice when you keep losing yourself — those are the moments to practice grounding",
            "question": "What keeps dissolving your boundaries this week?",
        },
        "month": {
            "headline": "This Month's Arc — Learning Boundaries Without Walls",
            "theme": "A month of confronting your relationship with boundaries",
            "what_it_means": "This Full Moon is one peak inside a larger monthly lesson about sensitivity vs. overwhelm. The month is teaching you how to stay open without drowning.",
            "felt_texture": [
                "Gradual clarity about what's yours to feel and what isn't",
                "New ability to be sensitive without being swamped",
                "Old patterns of merging being examined",
            ],
            "action": "By month's end, identify one boundary you need to create to protect your sensitivity",
            "question": "What is this month teaching you about staying open without losing yourself?",
        },
    },
}

# =============================================================================
# HORIZON-SPECIFIC NEW MOON CONTENT
# =============================================================================

NEW_MOON_HORIZONS = {
    "today": {
        "headline_template": "New Moon in {sign} — Fresh Start Energy",
        "theme_template": "Something new is seeding right now",
        "what_it_means_template": "A reset is happening TODAY. Don't force clarity — let the new intention form in the dark.",
        "felt_texture": [
            "Excitement without clarity on direction",
            "Wanting to start but not knowing what",
            "Energy gathering with nowhere to go yet",
        ],
        "action": "Plant a seed — don't expect the harvest yet",
        "question": "What new beginning is trying to form right now?",
    },
    "week": {
        "headline_template": "New Moon Week — New Patterns Emerging",
        "theme_template": "Something new keeps trying to take shape this week",
        "what_it_means_template": "This week, notice what new patterns, intentions, or directions keep appearing. They're not ready to be fully acted on yet, but they're showing you where energy wants to go.",
        "felt_texture": [
            "The same new possibility surfacing in different contexts",
            "Repeated inklings about fresh direction",
            "New energy that keeps returning without full form",
        ],
        "action": "Track what keeps emerging — it's pointing at your next phase",
        "question": "What new direction keeps hinting at itself this week?",
    },
    "month": {
        "headline_template": "This Month's Arc — Seeding a New Chapter",
        "theme_template": "A month of planting what will grow over the coming cycles",
        "what_it_means_template": "This New Moon is the seed point for a larger monthly arc. What you plant now — intentionally or not — will unfold over the coming weeks. Choose your seeds carefully.",
        "felt_texture": [
            "Gradual emergence of new direction",
            "Patience required as new forms take shape",
            "Old patterns naturally fading as new ones grow",
        ],
        "action": "By month's end, identify what has begun to sprout from this lunation's seed",
        "question": "What is this month teaching you about the patience required for new beginnings?",
    },
}

# =============================================================================
# HORIZON-SPECIFIC ECLIPSE CONTENT
# =============================================================================

ECLIPSE_HORIZONS = {
    "solar": {
        "today": {
            "headline": "Solar Eclipse — Portal Moment",
            "theme": "A major life chapter is shifting RIGHT NOW",
            "what_it_means": "This is not a normal day. Something irreversible is happening — an old path closing, a new one opening. You may not see it fully yet.",
            "felt_texture": [
                "Sense that something irreversible is happening",
                "Old identity patterns falling away",
                "Destabilization mixed with liberation",
            ],
            "action": "Don't force decisions — let the eclipse energy move through first",
            "question": "What door is closing that you're not ready to admit?",
        },
        "week": {
            "headline": "Eclipse Week — Rapid Reshuffling",
            "theme": "Multiple shifts are rippling through this week",
            "what_it_means": "This week exists in eclipse shadow. Things are moving faster than usual, changing in ways that won't fully make sense until later. Stay flexible.",
            "felt_texture": [
                "The same destabilization showing up in different areas",
                "Repeated moments of 'this is changing'",
                "Acceleration that's hard to track",
            ],
            "action": "Notice what keeps shifting this week — it's all connected to the larger portal",
            "question": "What keeps changing before you can catch your breath this week?",
        },
        "month": {
            "headline": "This Month's Arc — Eclipse Season Transformation",
            "theme": "A month of non-negotiable change",
            "what_it_means": "This eclipse marks a before/after point in a larger monthly transformation. What changes this month won't change back. The month is asking for surrender, not control.",
            "felt_texture": [
                "Gradual acceptance of irreversible shifts",
                "New identity emerging from released attachments",
                "Old life structures being rebuilt differently",
            ],
            "action": "By month's end, identify what has permanently changed and how you've adapted",
            "question": "What is this month teaching you about accepting change you didn't choose?",
        },
    },
    "lunar": {
        "today": {
            "headline": "Lunar Eclipse — Emotional Release",
            "theme": "Something deep is being released RIGHT NOW",
            "what_it_means": "Old emotional material is surfacing and moving out TODAY. This isn't something to fix — it's something to let go.",
            "felt_texture": [
                "Old feelings surfacing without warning",
                "Hidden relationship dynamics being revealed",
                "What you've suppressed demanding attention",
            ],
            "action": "Let the emotions move through — don't try to control the release",
            "question": "What feeling have you been suppressing that's now demanding to be felt?",
        },
        "week": {
            "headline": "Eclipse Week — Emotional Clearing",
            "theme": "The same old patterns keep surfacing for release this week",
            "what_it_means": "This week, expect emotional material to keep coming up in waves. The same themes may repeat — that's the clearing process.",
            "felt_texture": [
                "The same emotion surfacing in different contexts",
                "Repeated moments of unexpected tears or intensity",
                "Old patterns rising to be finally released",
            ],
            "action": "Let each wave pass without grabbing onto the story — just feel and release",
            "question": "What keeps coming up emotionally this week that wants to finally leave?",
        },
        "month": {
            "headline": "This Month's Arc — Deep Emotional Clearing",
            "theme": "A month of releasing emotional backlog",
            "what_it_means": "This lunar eclipse is clearing emotional material that may have been stuck for years. The month supports deep letting go — don't rush to refill the space.",
            "felt_texture": [
                "Gradual lightening as old emotions are released",
                "New emotional capacity emerging",
                "Space opening for feelings you couldn't access before",
            ],
            "action": "By month's end, notice what emotional weight you no longer carry",
            "question": "What is this month teaching you about the freedom that comes from emotional release?",
        },
    },
}

# =============================================================================
# MONTHLY ARC CONTENT (For when no dominant event)
# =============================================================================

MONTHLY_ARC_THEMES = {
    "cardinal": {  # Aries, Cancer, Libra, Capricorn
        "headline": "A Month of Initiation",
        "theme": "This month is asking you to begin something",
        "what_it_means": "The energy favors starting, deciding, moving. But initiation without follow-through creates chaos. Choose what to start wisely.",
    },
    "fixed": {  # Taurus, Leo, Scorpio, Aquarius
        "headline": "A Month of Stabilization",
        "theme": "This month is asking you to deepen or release",
        "what_it_means": "The energy favors commitment, persistence, or finally letting go of what you've been holding. Half-measures won't work now.",
    },
    "mutable": {  # Gemini, Virgo, Sagittarius, Pisces
        "headline": "A Month of Adaptation",
        "theme": "This month is asking you to adjust and integrate",
        "what_it_means": "The energy favors flexibility, learning, synthesis. Rigid plans will be challenged. Stay curious, not certain.",
    },
}


# =============================================================================
# MAIN HORIZON INTERPRETATION FUNCTIONS
# =============================================================================

def get_horizon_interpretation(
    event_type: str,
    sign: str,
    timeframe: str,  # "today" | "week" | "month"
    moon_data: Dict[str, Any],
    eclipse_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get horizon-specific interpretation for an event.
    
    CRITICAL: Returns DISTINCT content for today vs. week vs. month.
    Same event, different framing.
    """
    
    if "full_moon" in event_type:
        return _get_full_moon_horizon(sign, timeframe, moon_data)
    elif "new_moon" in event_type:
        return _get_new_moon_horizon(sign, timeframe, moon_data)
    elif "eclipse" in event_type:
        eclipse_type = "lunar" if "lunar" in event_type else "solar"
        return _get_eclipse_horizon(eclipse_type, timeframe, eclipse_data)
    else:
        # Fallback for no dominant event
        return _get_no_event_horizon(timeframe, moon_data)


def _get_full_moon_horizon(sign: str, timeframe: str, moon_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get Full Moon interpretation for specific horizon."""
    
    sign_content = FULL_MOON_HORIZONS.get(sign, FULL_MOON_HORIZONS["Aries"])
    horizon_content = sign_content.get(timeframe, sign_content["today"])
    
    return {
        "headline": horizon_content["headline"],
        "theme": horizon_content["theme"],
        "what_it_means": horizon_content["what_it_means"],
        "felt_texture": horizon_content["felt_texture"],
        "action": horizon_content["action"],
        "question": horizon_content["question"],
        "event_type": "full_moon",
        "sign": sign,
        "timeframe": timeframe,
    }


def _get_new_moon_horizon(sign: str, timeframe: str, moon_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get New Moon interpretation for specific horizon."""
    
    horizon_template = NEW_MOON_HORIZONS.get(timeframe, NEW_MOON_HORIZONS["today"])
    
    return {
        "headline": horizon_template["headline_template"].format(sign=sign),
        "theme": horizon_template["theme_template"],
        "what_it_means": horizon_template["what_it_means_template"],
        "felt_texture": horizon_template["felt_texture"],
        "action": horizon_template["action"],
        "question": horizon_template["question"],
        "event_type": "new_moon",
        "sign": sign,
        "timeframe": timeframe,
    }


def _get_eclipse_horizon(eclipse_type: str, timeframe: str, eclipse_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Get Eclipse interpretation for specific horizon."""
    
    type_content = ECLIPSE_HORIZONS.get(eclipse_type, ECLIPSE_HORIZONS["solar"])
    horizon_content = type_content.get(timeframe, type_content["today"])
    
    return {
        "headline": horizon_content["headline"],
        "theme": horizon_content["theme"],
        "what_it_means": horizon_content["what_it_means"],
        "felt_texture": horizon_content["felt_texture"],
        "action": horizon_content["action"],
        "question": horizon_content["question"],
        "event_type": f"eclipse_{eclipse_type}",
        "sign": None,
        "timeframe": timeframe,
    }


def _get_no_event_horizon(timeframe: str, moon_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get interpretation when no dominant event is active."""
    
    phase_name = moon_data.get("phase_name", "Waxing Crescent")
    
    if timeframe == "today":
        return {
            "headline": f"{phase_name} — Subtle Movements",
            "theme": "No major event peaking, but small signals matter",
            "what_it_means": "Today doesn't have a dominant astrological event, but that doesn't mean nothing is happening. Pay attention to the subtle signals.",
            "felt_texture": [
                "Quiet processing happening beneath the surface",
                "Small adjustments being made",
                "Preparation for what's next",
            ],
            "action": "Notice the small signals — they're preparing you for what's coming",
            "question": "What small thing is asking for your attention today?",
            "event_type": "none",
            "sign": None,
            "timeframe": timeframe,
        }
    elif timeframe == "week":
        return {
            "headline": f"{phase_name} Week — Gradual Shifts",
            "theme": "A week of subtle but accumulating changes",
            "what_it_means": "No single event dominates this week, but multiple small shifts are adding up. Track what keeps returning.",
            "felt_texture": [
                "Themes emerging through repetition",
                "Slow build toward next phase",
                "Patterns becoming clearer over days",
            ],
            "action": "Notice what keeps coming back this week — that's where the energy is building",
            "question": "What pattern is becoming clearer as the week progresses?",
            "event_type": "none",
            "sign": None,
            "timeframe": timeframe,
        }
    else:  # month
        return {
            "headline": "This Month's Arc — Integration Phase",
            "theme": "A month of processing rather than peak events",
            "what_it_means": "This month doesn't center on a single dramatic event. Instead, it's asking you to integrate, process, and prepare for what's next.",
            "felt_texture": [
                "Time to catch up with recent changes",
                "Consolidation of new patterns",
                "Quiet preparation for the next cycle",
            ],
            "action": "Use this month to integrate what's already happened before seeking new intensity",
            "question": "What have you learned recently that still needs to be fully absorbed?",
            "event_type": "none",
            "sign": None,
            "timeframe": timeframe,
        }


# =============================================================================
# GUARDRAILS
# =============================================================================

def validate_distinct_horizons(today: Dict, week: Dict, month: Dict) -> bool:
    """
    GUARDRAIL: Ensure all three horizons have distinct content.
    Returns False if any horizon is too similar to another.
    """
    
    # Check headlines are distinct
    headlines = [today.get("headline", ""), week.get("headline", ""), month.get("headline", "")]
    if len(set(headlines)) < 3:
        logger.warning(f"[HorizonGuard] FAIL: Headlines not distinct: {headlines}")
        return False
    
    # Check themes are distinct
    themes = [today.get("theme", ""), week.get("theme", ""), month.get("theme", "")]
    if len(set(themes)) < 3:
        logger.warning(f"[HorizonGuard] FAIL: Themes not distinct: {themes}")
        return False
    
    # Check what_it_means are distinct
    meanings = [today.get("what_it_means", ""), week.get("what_it_means", ""), month.get("what_it_means", "")]
    if len(set(meanings)) < 3:
        logger.warning(f"[HorizonGuard] FAIL: Meanings not distinct: {meanings}")
        return False
    
    logger.info("[HorizonGuard] PASS: All horizons are distinct")
    return True


def get_all_horizons(
    event_type: str,
    sign: str,
    moon_data: Dict[str, Any],
    eclipse_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Get interpretations for all three horizons and validate they're distinct.
    """
    
    today = get_horizon_interpretation(event_type, sign, "today", moon_data, eclipse_data)
    week = get_horizon_interpretation(event_type, sign, "week", moon_data, eclipse_data)
    month = get_horizon_interpretation(event_type, sign, "month", moon_data, eclipse_data)
    
    # Run guardrail
    is_valid = validate_distinct_horizons(today, week, month)
    
    return {
        "today": today,
        "week": week,
        "month": month,
        "validation_passed": is_valid,
    }
