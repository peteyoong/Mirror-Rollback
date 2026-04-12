"""
Home Insight Engine V5 - Pattern Engine Final Form
====================================================

CORE IDENTITY:
Home = Pattern across time (identity + recurrence)
Today = Moment inside the day (situational + interrupt)

Home must feel like: "This keeps happening to me."
NOT: "This is happening today."

V5 RULES:
1. START WITH CONTINUITY - Every insight anchors to recurrence
2. PATTERN > EVENT - Describe loops, tendencies, repeated behavior
3. IDENTITY EDGE (EARNED) - Sharper than Today, but grounded
4. COMPRESS WHAT'S GOING ON - Real behavior loops, no abstraction
5. WHERE THIS SHOWS UP = PRIMARY ANCHOR - One dominant area
6. WHAT YOU MAY BE DOING = CORE SECTION - Must feel like "that's exactly what I do"
7. COST = QUIET BUT REAL - Not dramatic, not preachy
8. THE MOVE = PATTERN-LEVEL - Trajectory shift, not moment interrupt
9. IDENTITY MIRROR = NEW LAYER - One confronting but accurate line

V5 OUTPUT STRUCTURE:
{
    "pattern_label": "Almost Moving" (max 3-4 words),
    "headline": "Pattern-based, not 'today'",
    "identity_mirror": "One sharp identity-level reflection line",
    "whats_going_on": ["Pattern explanations, no abstraction"],
    "where_it_shows_up": "ONE dominant life area",
    "what_you_may_be_doing": ["Repeated behaviors, loops, micro-behaviors"],
    "what_this_creates": "Quiet cost",
    "the_move": "Pattern-level shift, not advice",
    "why_showing_up": {...}  // Collapsible proof layer
}

SUCCESS CRITERIA:
- User reads and feels: "This is me", "This keeps happening", "I didn't realize I do this"
- NOT: "This is interesting", "This sounds like general advice"
"""

import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


# =============================================================================
# V5 PATTERN LABELS - max 3-4 words, identity-level
# =============================================================================

V5_PATTERN_LABELS = {
    "push_vs_hold": [
        "Almost Moving",
        "Stalling At The Edge",
        "Ready But Frozen",
        "The Repeated Pause",
    ],
    "control_vs_flow": [
        "Grip That Returns",
        "The Tight Hold",
        "Still Managing It",
        "Can't Let Go",
    ],
    "precision_vs_progress": [
        "One More Pass",
        "Never Quite Done",
        "The Endless Edit",
        "Polishing Loop",
    ],
    "visible_vs_hidden": [
        "Staying Unseen",
        "The Familiar Shrink",
        "Hiding In Place",
        "Holding It Back",
    ],
    "logic_vs_instinct": [
        "The Overthink Loop",
        "Already Know, Still Checking",
        "Building The Case",
        "Head Over Gut",
    ],
    "self_vs_others": [
        "Giving Yourself Away",
        "Their Needs First",
        "The Silent Trade",
        "Accommodating Again",
    ],
    "rest_vs_push": [
        "Overriding The Signal",
        "Won't Stop Pattern",
        "Pushing Past Empty",
        "The Grind Loop",
    ],
    "clarity_vs_chaos": [
        "Waiting To Know",
        "The Clarity Trap",
        "Thinking In Circles",
        "Fog That Returns",
    ],
    "trust_vs_doubt": [
        "The Doubt Loop",
        "Checking Again",
        "Never Quite Settled",
        "Seeking One More Sign",
    ],
    "expression_vs_suppression": [
        "Swallowing It Again",
        "Words Held Back",
        "The Familiar Silence",
        "Editing To Nothing",
    ],
}


# =============================================================================
# V5 HEADLINES - Pattern-based, recurrence-anchored (NOT "today")
# Uses "keeps", "tends to", "you've been here before"
# =============================================================================

V5_HEADLINES = {
    "push_vs_hold": [
        "This keeps happening — you reach the point of action, then pause.",
        "You've been here before — ready enough to move, but something holds you back.",
        "There's a pattern of getting to the edge — and then circling instead of stepping.",
        "You tend to prepare fully, then wait for a readiness that never quite arrives.",
    ],
    "control_vs_flow": [
        "You keep tightening your grip on things that would work better with space.",
        "This pattern comes back — the need to manage what wants to move on its own.",
        "You've been here before — holding something close when it's asking for room.",
        "There's a loop where control feels like safety, but creates the friction you're avoiding.",
    ],
    "precision_vs_progress": [
        "This keeps happening — the work is done, but you won't let it be done.",
        "You tend to refine past the point where refinement adds anything.",
        "There's a pattern of using 'not ready' to avoid what comes after completion.",
        "You've been here before — one more edit away from a finish line that keeps moving.",
    ],
    "visible_vs_hidden": [
        "This keeps happening — you have something to offer, but you make yourself smaller.",
        "You tend to pull back right when you could take up more space.",
        "There's a pattern of choosing invisibility when part of you wants to be seen.",
        "You've been here before — staying quiet when you have something worth saying.",
    ],
    "logic_vs_instinct": [
        "You keep doing this — you already know, but you won't let yourself trust it.",
        "There's a pattern of researching past the point of knowing.",
        "You tend to build the case for something your gut already decided.",
        "You've been here before — waiting for your mind to catch up with what you feel.",
    ],
    "self_vs_others": [
        "This keeps happening — you give more than you get, and you don't name it.",
        "There's a pattern of bending toward others' needs at the cost of your own.",
        "You tend to accommodate first and realize the cost later.",
        "You've been here before — saying yes when something in you is saying no.",
    ],
    "rest_vs_push": [
        "This keeps happening — your body asks you to stop, and you override it.",
        "There's a pattern of treating rest as something you'll get to later.",
        "You tend to push through signals that are asking you to slow down.",
        "You've been here before — running on fumes and calling it discipline.",
    ],
    "clarity_vs_chaos": [
        "This keeps happening — you wait for clarity that only comes after you move.",
        "There's a pattern of thinking in circles instead of taking the first step.",
        "You tend to seek certainty before acting — but certainty comes from action.",
        "You've been here before — standing still, waiting to understand before moving.",
    ],
    "trust_vs_doubt": [
        "This keeps happening — you make a decision, then quietly reopen it.",
        "There's a pattern of checking what you've already confirmed.",
        "You tend to seek one more sign when you already have enough.",
        "You've been here before — doubt running even when the evidence is clear.",
    ],
    "expression_vs_suppression": [
        "This keeps happening — you have something to say, and you swallow it.",
        "There's a pattern of editing your truth down to silence.",
        "You tend to choose quiet over honest — even when the words are ready.",
        "You've been here before — holding back what wants to come out.",
    ],
}


# =============================================================================
# V5 IDENTITY MIRROR - One sharp, confronting but accurate line (NEW)
# Must feel like identity-level reflection, not coaching
# =============================================================================

V5_IDENTITY_MIRROR = {
    "push_vs_hold": [
        "This is less about readiness, and more about hesitation at the edge.",
        "You're not stuck — you're pausing at the point where it starts to matter.",
        "The pattern isn't about timing. It's about what happens when the next step is real.",
        "You keep waiting for the fear to leave first. It won't.",
    ],
    "control_vs_flow": [
        "The grip isn't about the situation. It's about what happens if you trust without managing.",
        "You don't control because you're anxious — you control because letting go feels like giving up.",
        "The pattern isn't about the outcome. It's about needing to be the one who shapes it.",
        "What you're holding onto isn't fragile. But the need to hold it is.",
    ],
    "precision_vs_progress": [
        "The editing isn't about quality anymore. It's about not being finished.",
        "You're not perfecting — you're postponing what comes after completion.",
        "The pattern isn't about the work. It's about what it means to release it.",
        "You already know it's ready. The refinement is the delay, not the improvement.",
    ],
    "visible_vs_hidden": [
        "You're not shy — you're protecting something by keeping it out of sight.",
        "The pattern isn't about confidence. It's about what happens when people actually see you.",
        "Staying small isn't a choice you're making — it's a reflex you keep repeating.",
        "You already have what's needed. The hiding is the pattern, not the preparation.",
    ],
    "logic_vs_instinct": [
        "You're not uncertain — you're unwilling to trust what can't be fully explained.",
        "The research isn't for information anymore. It's for permission.",
        "Your gut made this decision a while ago. Your mind just won't sign off.",
        "The pattern isn't about knowing more. It's about trusting what you already know.",
    ],
    "self_vs_others": [
        "You're not generous — you're avoiding the discomfort of saying what you actually need.",
        "The accommodation isn't kindness. It's the path of least resistance.",
        "You keep choosing their ease over your truth. And it costs you quietly.",
        "This isn't about them asking too much. It's about you not claiming enough.",
    ],
    "rest_vs_push": [
        "The push isn't productivity. It's avoidance of what happens when you stop.",
        "You don't rest because stillness feels like falling behind — even when it's not.",
        "The pattern isn't about hard work. It's about not trusting that stopping is safe.",
        "You override your body like it's inconvenient. It's keeping score.",
    ],
    "clarity_vs_chaos": [
        "You're not confused — you're waiting for a certainty that doesn't come before action.",
        "The fog isn't the problem. The refusal to move through it is.",
        "You keep thinking because moving means accepting that you don't have the full picture.",
        "Clarity isn't missing. You're just not ready for what it reveals.",
    ],
    "trust_vs_doubt": [
        "You don't doubt because the evidence is weak. You doubt because trusting feels risky.",
        "The checking isn't careful. It's a loop you can't exit.",
        "You already know. The doubt is just noise that feels responsible.",
        "This isn't about needing more information. It's about needing to believe it's enough.",
    ],
    "expression_vs_suppression": [
        "You're not choosing words carefully — you're choosing silence out of habit.",
        "The pattern isn't about timing. It's about what happens when you actually speak.",
        "You keep editing yourself out of your own conversations.",
        "The silence isn't strategic. It's automatic. And it costs you every time.",
    ],
}


# =============================================================================
# V5 WHAT'S GOING ON - Pattern loops, no abstraction, no astrology language
# Must describe a LOOP, a TENDENCY, a REPEATED behavior across situations
# =============================================================================

V5_WHATS_GOING_ON = {
    "push_vs_hold": [
        "You get clear enough to move, but not comfortable enough to commit — and this repeats.",
        "The thinking completes, but the action doesn't follow. It happens every time.",
        "You wait for a feeling of certainty that only arrives after action, not before.",
        "Each time you approach the edge, something reasonable-sounding pulls you back.",
    ],
    "control_vs_flow": [
        "You tighten your grip when things start to move — and it keeps creating the tension you're trying to prevent.",
        "There's a loop: you manage, it creates friction, you manage harder.",
        "You step in to ensure an outcome — when stepping back would produce a better one.",
        "The need to shape how things go keeps costing you the ease of letting them happen.",
    ],
    "precision_vs_progress": [
        "Completion keeps getting redefined — the bar moves just enough to delay release.",
        "You use refinement as a reason to stay in the process, avoiding the exposure of being done.",
        "The work has been ready for a while. The editing has outlasted the improvement.",
        "Each round of 'just one more pass' adds less value but more distance from completion.",
    ],
    "visible_vs_hidden": [
        "You shrink in situations where expansion is available — and it keeps happening.",
        "There's a loop: opportunity to be seen → impulse to pull back → regret afterward.",
        "You have something to contribute, but the reflex to stay quiet overrides it.",
        "Visibility triggers a withdrawal response — even when the stakes are low.",
    ],
    "logic_vs_instinct": [
        "You keep gathering information past the point where you already have your answer.",
        "There's a loop: gut says something → mind questions it → action freezes.",
        "You build logical cases for decisions you've already made emotionally.",
        "The research continues because trusting the instinct alone feels irresponsible.",
    ],
    "self_vs_others": [
        "You notice the imbalance after the fact — then adjust next time — then repeat the same pattern.",
        "There's a loop: accommodate → absorb the cost → tell yourself it's fine → do it again.",
        "Your needs don't get named until they've been unmet long enough to hurt.",
        "The accommodation is so automatic it doesn't feel like a choice — but it is.",
    ],
    "rest_vs_push": [
        "The signal to stop arrives, you acknowledge it, and then push through anyway. Repeatedly.",
        "There's a loop: body sends warning → mind overrides → crash comes later.",
        "You treat exhaustion as a problem to solve with more effort — which deepens it.",
        "Rest gets permanently scheduled for 'after' — and after never arrives.",
    ],
    "clarity_vs_chaos": [
        "You stay in thinking mode because moving would mean accepting uncertainty. This repeats.",
        "There's a loop: analyze → still unclear → analyze more → still unclear.",
        "The clarity you're waiting for is on the other side of action, not thought.",
        "Each thinking cycle adds familiarity with the problem but not progress toward a solution.",
    ],
    "trust_vs_doubt": [
        "You decide, then un-decide. The loop eats time and confidence.",
        "There's a pattern: make a choice → feel relief → doubt creeps in → reopen the question.",
        "The checking isn't producing new information, but it keeps running.",
        "Each round of doubt feels responsible, but it's actually just repetition.",
    ],
    "expression_vs_suppression": [
        "The words form, the moment arrives, and then the silence wins. Over and over.",
        "There's a loop: something wants to be said → you edit it → the moment passes → you hold it.",
        "You rehearse what you'd say, but the rehearsal replaces the saying.",
        "The cost of silence accumulates — but each individual instance feels small enough to dismiss.",
    ],
}


# =============================================================================
# V5 WHERE IT SHOWS UP - ONE dominant life area, specific but not scattered
# =============================================================================

V5_WHERE_SHOWS_UP = {
    1: "in how you show up — your presence, your image, how you enter a room",
    2: "around money, self-worth, or how you value what you bring",
    3: "in your conversations — what you say, what you hold back, how you communicate",
    4: "at home, with family, or in your private emotional world",
    5: "in your creative work, self-expression, or anything that carries your name",
    6: "in your work routines, health, or daily structure",
    7: "in your relationships — especially one-on-one dynamics",
    8: "in intimacy, shared resources, or what you let others in on",
    9: "around your beliefs, sense of direction, or what you're building toward",
    10: "in your career, public presence, or professional identity",
    11: "in your friendships, communities, or sense of belonging",
    12: "in your rest, private processing, or inner life",
}

V5_WHERE_CLUSTER_DEFAULT = {
    "push_vs_hold": "decisions, commitments, or anything that requires a final step",
    "control_vs_flow": "situations where outcomes feel uncertain or out of your hands",
    "precision_vs_progress": "your work, projects, or anything you're creating",
    "visible_vs_hidden": "spaces where attention is possible — professional, social, creative",
    "logic_vs_instinct": "choices or directions where logic and feeling don't agree",
    "self_vs_others": "relationships where your needs interact with someone else's",
    "rest_vs_push": "your pace, energy management, or how much you demand from yourself",
    "clarity_vs_chaos": "decisions or plans that feel unresolved or directionless",
    "trust_vs_doubt": "commitments, decisions, or anything you've already chosen",
    "expression_vs_suppression": "conversations, relationships, or any space where honesty is possible",
}


# =============================================================================
# V5 WHAT YOU MAY BE DOING - Loops, repeated actions, micro-behaviors
# THIS IS THE MOST IMPORTANT SECTION
# Must feel like: "That's EXACTLY what I do."
# =============================================================================

V5_WHAT_YOU_MAY_BE_DOING = {
    "push_vs_hold": [
        "Thinking through the next step over and over — without taking it",
        "Starting to act, then finding a reason to wait",
        "Telling yourself you need one more thing before you can move",
        "Rehearsing a conversation in your head instead of having it",
        "Recognizing the pattern mid-loop — and still not breaking it",
    ],
    "control_vs_flow": [
        "Checking on something more often than it changes",
        "Adjusting small details to feel like you're steering the outcome",
        "Struggling to leave things alone — even when intervening doesn't help",
        "Replaying what could go wrong to stay ahead of it",
        "Holding tightly to how something should go — and feeling the strain",
    ],
    "precision_vs_progress": [
        "Doing another pass on something that didn't need it",
        "Moving the finish line forward each time you get close",
        "Using 'almost ready' as a holding pattern you've lived in before",
        "Comparing the current version to an ideal that doesn't exist",
        "Spending more time refining than it took to create",
    ],
    "visible_vs_hidden": [
        "Staying quiet when you have something to say — then wishing you hadn't",
        "Making yourself small in rooms where you could take up more space",
        "Downplaying what you've done when someone notices",
        "Watching others step forward while you stay back — and noticing it",
        "Editing yourself out of visibility, then feeling unseen",
    ],
    "logic_vs_instinct": [
        "Asking someone else's opinion on something you've already decided",
        "Looking up more information when you already have enough to act",
        "Waiting for your mind to agree with what your gut already said",
        "Building a justification for a feeling that doesn't need one",
        "Delaying the step until the logic feels complete — which it never does",
    ],
    "self_vs_others": [
        "Saying yes to something and feeling the cost immediately",
        "Adjusting your plans to fit someone else's — without being asked",
        "Noticing the imbalance but choosing not to address it",
        "Absorbing someone else's discomfort so they don't have to feel it",
        "Not naming what you need — and then being frustrated it wasn't met",
    ],
    "rest_vs_push": [
        "Noticing you're tired and adding one more thing anyway",
        "Skipping rest because stopping feels like falling behind",
        "Treating exhaustion as a problem of willpower, not a signal",
        "Scheduling recovery for 'after this week' — every week",
        "Pushing through a low point instead of pausing at it",
    ],
    "clarity_vs_chaos": [
        "Thinking about the same decision from a new angle — again",
        "Waiting to feel clear before taking a step",
        "Gathering input from others when the confusion is internal",
        "Sitting with the question instead of testing an answer",
        "Planning the plan instead of executing any part of it",
    ],
    "trust_vs_doubt": [
        "Reopening a decision you already closed — just to look at it again",
        "Asking for reassurance about something you already know is right",
        "Feeling settled, then letting one small thought unravel it",
        "Double-checking what you checked yesterday",
        "Holding a decision open because closing it feels permanent",
    ],
    "expression_vs_suppression": [
        "Drafting what you'd say in your head — then discarding it",
        "Choosing the safe response over the honest one",
        "Feeling the words form and then deciding 'now isn't the time'",
        "Letting someone else fill the silence you left on purpose",
        "Carrying unspoken things like a weight you've gotten used to",
    ],
}


# =============================================================================
# V5 WHAT THIS CREATES - Quiet, real cost (not dramatic, not preachy)
# =============================================================================

V5_WHAT_THIS_CREATES = {
    "push_vs_hold": [
        "It stays active in your head, but doesn't move forward. The energy drains without producing.",
        "The decision stays open — which costs more than either direction would.",
        "You carry the weight of something almost-done. Not quite acting. Not quite resting.",
        "Each pause adds familiarity with the pattern — but not progress past it.",
    ],
    "control_vs_flow": [
        "The management creates the tension it was supposed to prevent.",
        "Things that could move naturally stay stuck under your grip.",
        "Your energy goes to holding on — instead of receiving what's trying to arrive.",
        "The control loop is exhausting. But letting go feels worse. So it continues.",
    ],
    "precision_vs_progress": [
        "What's ready to be seen stays hidden inside the revision.",
        "The value of the work remains unclaimed — not because it's not good, but because it's not released.",
        "The gap between creation and visibility keeps widening.",
        "You stay in process when the world is ready for your product.",
    ],
    "visible_vs_hidden": [
        "What you could offer doesn't land — because it's never put forward.",
        "You remain smaller than you could be. Not by ability, but by habit.",
        "The gap between who you are and who people see grows quietly.",
        "Impact that could exist stays theoretical.",
    ],
    "logic_vs_instinct": [
        "The answer you already have stays on hold while you build a case for it.",
        "Time passes in justification when it could pass in action.",
        "The instinct gets quieter the longer you override it.",
        "You lose trust in yourself by refusing to follow what you feel.",
    ],
    "self_vs_others": [
        "Your needs stay underground — and resentment grows in the gap.",
        "The relationship dynamic you're protecting is actually eroding.",
        "The cost of accommodation compounds quietly. It shows up as fatigue or distance.",
        "You keep paying a price you never agreed to — and nobody knows.",
    ],
    "rest_vs_push": [
        "The debt accumulates. Energy, focus, patience — they thin without you noticing.",
        "Productivity drops but effort stays high. The return diminishes.",
        "Your body starts keeping a record your mind won't acknowledge.",
        "The crash doesn't come as a choice — it comes as a wall.",
    ],
    "clarity_vs_chaos": [
        "Time passes without movement. Understanding grows but position doesn't change.",
        "The thinking circles add familiarity, not resolution.",
        "You know the problem better than anyone — but you're no closer to action.",
        "Clarity stays on the other side of a step you're not taking.",
    ],
    "trust_vs_doubt": [
        "Confidence erodes — not because you were wrong, but because you won't let yourself be right.",
        "The doubt loop eats the peace that comes after a good decision.",
        "Each reopening makes the next decision harder to trust too.",
        "You're building a habit of not trusting yourself. And it's compounding.",
    ],
    "expression_vs_suppression": [
        "The unsaid builds up. It shows up as distance, tension, or exhaustion.",
        "Relationships carry an invisible weight of things never spoken.",
        "The gap between what you think and what you say becomes normal. But it costs you.",
        "Each swallowed word makes the next one harder to release.",
    ],
}


# =============================================================================
# V5 THE MOVE - Pattern-level trajectory shift (NOT moment interrupt)
# Today = interrupt ("just notice"), Home = trajectory shift ("start trusting")
# =============================================================================

V5_THE_MOVE = {
    "push_vs_hold": [
        "You don't need to resolve all of it. Just move the part you already understand.",
        "Stop waiting for the fear to leave. It comes with you — and that's fine.",
        "The readiness you're looking for arrives after the step, not before it.",
        "Pick the smallest version of the action. Take it before the thinking starts again.",
    ],
    "control_vs_flow": [
        "Start trusting that something can go right without your hand on it.",
        "Let one thing unfold without managing it — and notice what happens.",
        "The ease you're looking for is on the other side of loosening the grip.",
        "You don't have to control less. Just notice what happens when you do.",
    ],
    "precision_vs_progress": [
        "Release it at the point you'd normally start another pass. That's the moment.",
        "Let 'done enough' exist as a real category — not a compromise.",
        "The world will respond to what you release. Not to what you're still editing.",
        "Completion isn't about the work being perfect. It's about you letting it go.",
    ],
    "visible_vs_hidden": [
        "Take up the space before you feel ready to. The readiness follows.",
        "Say the thing. Share the work. Let yourself be seen — once — and notice.",
        "Visibility doesn't require confidence. It requires one step before the reflex kicks in.",
        "Let one part of you be seen that usually stays hidden. Just once.",
    ],
    "logic_vs_instinct": [
        "Let the gut lead one decision. Just once. See what happens.",
        "You already know. Stop building the case and act on it.",
        "Trust doesn't arrive from more information. It arrives from following through.",
        "The proof you're waiting for only comes after you trust.",
    ],
    "self_vs_others": [
        "Name one need out loud. Not aggressively. Just honestly.",
        "Let your truth exist for a moment without editing it for someone else's comfort.",
        "You're allowed to matter as much as them. Start acting like it.",
        "Say no once. Just to see what happens.",
    ],
    "rest_vs_push": [
        "Stop before you feel like you should. That's the practice.",
        "Let one thing be enough for today. Not as defeat. As design.",
        "Rest isn't a reward for finishing. It's part of the work.",
        "Trust that stopping won't cost you what you think it will.",
    ],
    "clarity_vs_chaos": [
        "Take one step before you feel clear. Clarity follows movement.",
        "Stop solving it in your head. Let the first imperfect action teach you.",
        "The fog clears when you walk through it — not when you study it.",
        "You're not missing information. You're missing momentum.",
    ],
    "trust_vs_doubt": [
        "Let one decision be final. Not perfect — final. See how it feels.",
        "The peace you're looking for comes from not reopening, not from checking again.",
        "You already have enough to trust. The doubt is a habit, not a signal.",
        "Close it. Walk away. Let the relief teach you something.",
    ],
    "expression_vs_suppression": [
        "Say one true thing you've been holding. Don't edit it. Just say it.",
        "Let honesty exist for a moment — even if it's uncomfortable.",
        "The silence costs more than the words would. You already know this.",
        "Speak before the filter kicks in. Just once. See what it changes.",
    ],
}


# =============================================================================
# MAIN V5 GENERATION FUNCTION
# =============================================================================

def generate_home_insight_v5(
    cluster: str,
    house: Optional[int] = None,
    trigger_confidence: str = "recurring_only",
    signals_summary: Optional[List[str]] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate V5 Home Insight - Pattern Engine Final Form.
    
    Key difference from V4:
    - Pattern across time (not daily event)
    - Identity Mirror line (new layer)
    - Recurrence language throughout
    - Pattern-level trajectory shifts
    """
    # Generate seed for variety
    if seed is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seed = int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16)
    
    # Get templates for this cluster (default to push_vs_hold)
    pattern_labels = V5_PATTERN_LABELS.get(cluster, V5_PATTERN_LABELS["push_vs_hold"])
    headlines = V5_HEADLINES.get(cluster, V5_HEADLINES["push_vs_hold"])
    identity_mirrors = V5_IDENTITY_MIRROR.get(cluster, V5_IDENTITY_MIRROR["push_vs_hold"])
    whats_going_on = V5_WHATS_GOING_ON.get(cluster, V5_WHATS_GOING_ON["push_vs_hold"])
    what_doing = V5_WHAT_YOU_MAY_BE_DOING.get(cluster, V5_WHAT_YOU_MAY_BE_DOING["push_vs_hold"])
    what_creates = V5_WHAT_THIS_CREATES.get(cluster, V5_WHAT_THIS_CREATES["push_vs_hold"])
    the_moves = V5_THE_MOVE.get(cluster, V5_THE_MOVE["push_vs_hold"])
    
    # Select items with variety using seed
    pattern_label = pattern_labels[seed % len(pattern_labels)]
    headline = headlines[seed % len(headlines)]
    identity_mirror = identity_mirrors[seed % len(identity_mirrors)]
    
    # Select 2-3 items for whats_going_on (pattern loops)
    wgo_start = seed % max(1, len(whats_going_on) - 2)
    selected_wgo = whats_going_on[wgo_start:wgo_start + 3]
    if len(selected_wgo) < 2:
        selected_wgo = whats_going_on[:3]
    
    # Select 2-3 items for what_doing (repeated behaviors)
    wd_start = (seed + 1) % max(1, len(what_doing) - 2)
    selected_doing = what_doing[wd_start:wd_start + 3]
    if len(selected_doing) < 2:
        selected_doing = what_doing[:3]
    
    # Select consequence (quiet cost)
    consequence = what_creates[seed % len(what_creates)]
    
    # Select the move (pattern-level shift)
    the_move = the_moves[seed % len(the_moves)]
    
    # Build "where it shows up" - ONE dominant life area
    if house and house in V5_WHERE_SHOWS_UP:
        where_shows_up = f"Mostly {V5_WHERE_SHOWS_UP[house]}"
    else:
        default_where = V5_WHERE_CLUSTER_DEFAULT.get(cluster, "situations that ask for a next step")
        where_shows_up = f"Mostly in {default_where}"
    
    # Build hidden "why showing up" layer (proof, not main story)
    why_showing_up = None
    if signals_summary:
        why_showing_up = {
            "signals": signals_summary,
            "trigger_confidence": trigger_confidence,
            "note": "These patterns and signals inform this insight — not today's events, but recurring themes.",
        }
    
    return {
        "success": True,
        "version": "v5_pattern_engine",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        # V5 MANDATORY STRUCTURE
        "pattern_label": pattern_label,
        "headline": headline,
        "identity_mirror": identity_mirror,
        "whats_going_on": selected_wgo,
        "where_it_shows_up": where_shows_up,
        "what_you_may_be_doing": selected_doing,
        "what_this_creates": consequence,
        "the_move": the_move,
        # HIDDEN PROOF LAYER
        "why_showing_up": why_showing_up,
        # METADATA
        "cluster": cluster,
        "house": house,
        "trigger_confidence": trigger_confidence,
    }


def build_v5_narrative(insight: Dict[str, Any]) -> str:
    """Build a narrative string from V5 insight for backward compatibility."""
    parts = []
    
    # Pattern label
    parts.append(f"**{insight['pattern_label'].upper()}**")
    parts.append("")
    
    # Headline
    parts.append(insight["headline"])
    parts.append("")
    
    # Identity Mirror
    parts.append(f"_{insight['identity_mirror']}_")
    parts.append("")
    
    # What's going on
    parts.append("**What's going on:**")
    for item in insight["whats_going_on"]:
        parts.append(f"• {item}")
    parts.append("")
    
    # Where it shows up
    parts.append(f"**Where this shows up:**")
    parts.append(insight["where_it_shows_up"])
    parts.append("")
    
    # What you may be doing
    parts.append("**What you may be doing:**")
    for item in insight["what_you_may_be_doing"]:
        parts.append(f"• {item}")
    parts.append("")
    
    # What this creates
    parts.append("**What this creates:**")
    parts.append(insight["what_this_creates"])
    parts.append("")
    
    # The move
    parts.append(f"**The move:** {insight['the_move']}")
    
    return "\n".join(parts)
