"""
Home Insight Engine V4 - Earned Claims & Progressive Reveal
============================================================

CORE PRINCIPLE:
Every strong statement must be EARNED, not assumed.
User should feel RECOGNIZED, not ACCUSED.

V4 RULES:
1. EARN EVERY CLAIM - No jumping to conclusions without evidence
2. ADD "WHERE THIS SHOWS UP" - Always anchor to real life
3. SHIFT FROM ACCUSATION TO RECOGNITION - "You may be" not "You are"
4. USE PROGRESSIVE REVEAL - Pattern → Where → What → Cost → Move
5. REDUCE ABSOLUTE LANGUAGE - Softer, but still sharp
6. KEEP MIRROR EDGE - But make it provable

V4 OUTPUT STRUCTURE:
{
    "pattern_label": "Still Circling It" (max 4 words),
    "headline": "One grounded sentence",
    "whats_going_on": ["Real-world dynamics"],
    "where_it_shows_up": "Life area anchor",
    "what_you_may_be_doing": ["Observable behaviors"],
    "what_this_creates": "Consequence, not dramatic",
    "the_move": "Small non-prescriptive shift",
    "why_showing_up": {...}  // Hidden proof layer
}

SUCCESS CRITERIA:
- User recognizes it instantly ("oh shit, that's me")
- Does NOT feel judged or accused
- Does NOT ask "how do you know this?"
- Feels slightly seen, not pushed
"""

import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# V4 PATTERN TYPES - Soft Labels (max 4 words)
# =============================================================================

V4_PATTERN_LABELS = {
    "push_vs_hold": [
        "Still Circling It",
        "Close But Waiting",
        "Ready But Pausing",
        "Almost Moving",
    ],
    "control_vs_flow": [
        "Holding Too Tight",
        "Gripping It",
        "Not Letting Go",
        "Over-Managing",
    ],
    "precision_vs_progress": [
        "Still Refining",
        "Not Quite Ready",
        "One More Pass",
        "Polishing It",
    ],
    "visible_vs_hidden": [
        "Staying Small",
        "Holding Back",
        "Not Showing Up",
        "Keeping It In",
    ],
    "logic_vs_instinct": [
        "Overthinking It",
        "Still Researching",
        "Building The Case",
        "Looking For Proof",
    ],
    "self_vs_others": [
        "Giving More Away",
        "Their Needs First",
        "Boundary Not Set",
        "Accommodating Again",
    ],
    "rest_vs_push": [
        "Pushing Through It",
        "Ignoring The Signal",
        "Not Stopping",
        "Overriding Rest",
    ],
    "clarity_vs_chaos": [
        "Waiting For Clarity",
        "Still Uncertain",
        "Looking For Direction",
        "In The Fog",
    ],
    "trust_vs_doubt": [
        "Double-Checking",
        "Not Trusting It",
        "Seeking Reassurance",
        "Still Doubting",
    ],
    "expression_vs_suppression": [
        "Holding It In",
        "Not Saying It",
        "Swallowing Words",
        "Silence Instead",
    ],
}


# =============================================================================
# V4 HEADLINES - Grounded, Specific, Not Accusatory
# Uses "There's" and "You may be" instead of "You are"
# =============================================================================

V4_HEADLINES = {
    "push_vs_hold": [
        "There's something you've been preparing to move on — but you haven't fully stepped into it yet.",
        "There's a decision or action that's close to happening — but something keeps it in the waiting room.",
        "You may be circling something that's actually ready to move forward.",
        "There's a conversation or step that feels close — but keeps getting postponed.",
    ],
    "control_vs_flow": [
        "There's something you may be holding onto a little tighter than it needs.",
        "You might be over-managing a situation that would work better with less grip.",
        "There's an outcome you're trying to control — and it may be creating friction.",
        "Something may be asking for space, but you're keeping close watch on it.",
    ],
    "precision_vs_progress": [
        "There's something in your work you're close to acting on — but you keep preparing instead of moving.",
        "You may have something that's ready enough — but you're still refining it.",
        "There's work that's essentially done, but keeps getting one more pass.",
        "Something you've created may be waiting to be seen — while you're still editing.",
    ],
    "visible_vs_hidden": [
        "There may be something you haven't fully put out yet — even though part of you wants it seen.",
        "You might be staying smaller than the space you could actually fill.",
        "There's something you could say or share — but you're holding it back.",
        "Part of you may want to be more visible — while another part keeps you quiet.",
    ],
    "logic_vs_instinct": [
        "You may already know the answer to something — but you're still building the case.",
        "There's a decision your gut has made — but your mind keeps researching.",
        "You might be looking for permission or proof for something you already feel.",
        "There's an instinct you're not following — because the logic isn't fully there yet.",
    ],
    "self_vs_others": [
        "You may be giving more than you're getting in a situation — without naming it.",
        "There might be a boundary that wants to exist — but hasn't been set yet.",
        "You could be prioritizing someone else's comfort over your own truth.",
        "There's a 'yes' you're saying that might actually want to be a 'no'.",
    ],
    "rest_vs_push": [
        "Your system may be asking for a pause — but you're pushing through anyway.",
        "There's a signal to slow down that you might be overriding.",
        "You could be treating tiredness as something to push past, rather than information.",
        "There's a rest your body is requesting — but your mind is arguing with it.",
    ],
    "clarity_vs_chaos": [
        "You may be waiting for clarity that won't come from more thinking.",
        "There's something you're trying to figure out — that might only become clear through action.",
        "You could be searching for certainty in a situation that requires trust.",
        "The direction you're looking for may come from moving, not planning.",
    ],
    "trust_vs_doubt": [
        "You may have already verified something — but you're still not letting yourself trust it.",
        "There's a decision you've made — but you keep second-guessing it.",
        "You might be seeking reassurance that won't come until you act.",
        "Something has been confirmed, but doubt keeps checking again.",
    ],
    "expression_vs_suppression": [
        "There may be something you want to say — but you keep editing it down to silence.",
        "You might be sitting on words that want to come out.",
        "There's a truth you're holding back — even though it's ready.",
        "Something honest may be waiting to be spoken — but you're choosing quiet instead.",
    ],
}


# =============================================================================
# V4 WHAT'S GOING ON - Real-World Dynamics (No Abstract Language)
# =============================================================================

V4_WHATS_GOING_ON = {
    "push_vs_hold": [
        "Something has been building toward a decision point — but the final step hasn't happened.",
        "There's readiness underneath, but also hesitation about timing or certainty.",
        "The mental work has been done. The external move hasn't.",
        "You may be waiting for a feeling of readiness that doesn't arrive until after you act.",
    ],
    "control_vs_flow": [
        "Something wants to unfold, but you're managing it closely.",
        "There's a process or outcome you're tracking more than it may need.",
        "The situation might work better with less involvement from you.",
        "You may be creating friction by trying to ensure a particular result.",
    ],
    "precision_vs_progress": [
        "The work is at a point where it could be shared or shipped — but refinement continues.",
        "Perfection is being pursued, even though done-enough may be available.",
        "You may be using 'not quite ready' as a reason to delay visibility.",
        "The editing has outlasted the improvement it provides.",
    ],
    "visible_vs_hidden": [
        "There's a desire to be seen — but also a pull toward staying safe.",
        "You may be making yourself smaller to avoid attention or judgment.",
        "Something you've created or believe is being kept private when it could be shared.",
        "Visibility feels risky, so invisibility is chosen instead.",
    ],
    "logic_vs_instinct": [
        "The body or gut has given an answer, but the mind is still reviewing.",
        "You may be building justification for something you already feel.",
        "Research or analysis is continuing past the point of usefulness.",
        "There's a knowing that's being verified rather than trusted.",
    ],
    "self_vs_others": [
        "Your needs may be going unnamed while you attend to someone else's.",
        "A pattern of accommodation is active — even when it costs you.",
        "The relationship dynamic is imbalanced, but it hasn't been addressed.",
        "Peace is being kept at the expense of your own truth.",
    ],
    "rest_vs_push": [
        "Your body is signaling fatigue, but your schedule isn't honoring it.",
        "Rest is being treated as weakness rather than maintenance.",
        "The push is costing more than it's producing — but it continues.",
        "There's a pace mismatch between what you need and what you're giving.",
    ],
    "clarity_vs_chaos": [
        "Clarity is being sought through thinking — but it may only come through doing.",
        "The fog isn't lifting because action is what clears it.",
        "You may be waiting for certainty that arrives after movement, not before.",
        "Analysis is replacing experimentation.",
    ],
    "trust_vs_doubt": [
        "Something has been confirmed, but belief hasn't caught up.",
        "You may be seeking external validation for an internal decision.",
        "Doubt is running even when evidence is present.",
        "The checking continues past the point where it adds value.",
    ],
    "expression_vs_suppression": [
        "Words are being held back — even when they're ready.",
        "Honesty is being filtered into silence.",
        "Something wants to be expressed, but safety wins.",
        "The unsaid is building up quietly.",
    ],
}


# =============================================================================
# V4 WHERE IT SHOWS UP - Life Area Anchors
# =============================================================================

V4_WHERE_SHOWS_UP = {
    1: "how you present yourself and show up in the world",
    2: "money, resources, or how you value yourself",
    3: "conversations, decisions, or daily communication",
    4: "home, family, or your private emotional space",
    5: "creative work, self-expression, or things you want seen",
    6: "work routines, health habits, or daily structure",
    7: "relationships, partnerships, or one-on-one dynamics",
    8: "intimacy, shared resources, or what you let others see",
    9: "beliefs, direction, or long-term meaning",
    10: "career, public presence, or how you're perceived professionally",
    11: "friendships, community, or group belonging",
    12: "rest, private reflection, or what you process alone",
}

V4_WHERE_CLUSTER_DEFAULT = {
    "push_vs_hold": "a decision, conversation, or action you've been considering",
    "control_vs_flow": "something you're managing or watching closely",
    "precision_vs_progress": "work or a project you've been developing",
    "visible_vs_hidden": "something you could share or express more publicly",
    "logic_vs_instinct": "a choice or direction you've been analyzing",
    "self_vs_others": "a relationship or situation where your needs interact with someone else's",
    "rest_vs_push": "your pace, energy, or how much you're giving",
    "clarity_vs_chaos": "something you're trying to figure out or understand",
    "trust_vs_doubt": "something you've verified but keep questioning",
    "expression_vs_suppression": "something you could say but haven't",
}


# =============================================================================
# V4 WHAT YOU MAY BE DOING - Observable Behaviors (Must Feel Recognizable)
# =============================================================================

V4_WHAT_YOU_MAY_BE_DOING = {
    "push_vs_hold": [
        "Thinking through the next step — but not taking it yet",
        "Preparing to say or do something — then pulling back",
        "Waiting for the 'right moment' that keeps not arriving",
        "Rehearsing a conversation or decision internally",
        "Telling yourself you need more information before acting",
    ],
    "control_vs_flow": [
        "Checking in on something more often than needed",
        "Adjusting details that don't significantly change the outcome",
        "Finding it hard to step back and let things play out",
        "Over-preparing for scenarios that may not happen",
        "Holding tightly to how something 'should' go",
    ],
    "precision_vs_progress": [
        "Doing another round of edits on something essentially complete",
        "Telling yourself it's not quite ready — even though it might be",
        "Delaying sharing or sending because of minor imperfections",
        "Using 'quality' as a reason to postpone",
        "Refining past the point of meaningful improvement",
    ],
    "visible_vs_hidden": [
        "Keeping something to yourself that could be shared",
        "Staying quiet when you have something to contribute",
        "Making yourself smaller in a room where you could take up space",
        "Editing your truth before it comes out — or not letting it out at all",
        "Watching from the side instead of stepping in",
    ],
    "logic_vs_instinct": [
        "Researching something you've already decided on",
        "Asking others for input when you already know your answer",
        "Building a case for something you feel but can't fully explain",
        "Delaying action until the logic catches up with the instinct",
        "Second-guessing a gut feeling because it doesn't have 'proof'",
    ],
    "self_vs_others": [
        "Saying yes when part of you wants to say no",
        "Adjusting your plans to fit someone else's preferences",
        "Not naming what you need in a relationship or situation",
        "Keeping peace by staying quiet about something that bothers you",
        "Giving more energy than you're receiving — without addressing it",
    ],
    "rest_vs_push": [
        "Working past the point of productivity",
        "Ignoring physical signals that say 'slow down'",
        "Telling yourself rest is for later — even when you need it now",
        "Treating tiredness as a problem to solve, not a message to hear",
        "Adding more to a day that's already full",
    ],
    "clarity_vs_chaos": [
        "Thinking through the same thing in circles",
        "Waiting for certainty before taking a step",
        "Looking for answers in research or conversation — instead of action",
        "Staying in planning mode when doing would reveal more",
        "Holding off because you 'need to understand it first'",
    ],
    "trust_vs_doubt": [
        "Double-checking something you've already confirmed",
        "Asking for reassurance after you've made a decision",
        "Revisiting a choice you already made — reopening the debate",
        "Looking for one more sign before you trust what you know",
        "Feeling unsettled even when the facts are clear",
    ],
    "expression_vs_suppression": [
        "Thinking of what to say — then deciding not to say it",
        "Editing your words until nothing comes out",
        "Choosing silence to avoid discomfort or conflict",
        "Holding back an honest reaction in the moment",
        "Letting something go unsaid — again",
    ],
}


# =============================================================================
# V4 WHAT THIS CREATES - Consequence (Not Dramatic, Just Real)
# =============================================================================

V4_WHAT_THIS_CREATES = {
    "push_vs_hold": [
        "It stays in motion internally — but doesn't move forward externally.",
        "The readiness stays unused. The moment stays unclaimed.",
        "You carry the weight of something undone — without the relief of doing it.",
        "The decision remains open — which takes more energy than closing it.",
    ],
    "control_vs_flow": [
        "The grip creates the very friction you're trying to avoid.",
        "Things that could flow get stuck because you're holding too tight.",
        "Your energy goes to managing — instead of receiving.",
        "What could be easy becomes effortful.",
    ],
    "precision_vs_progress": [
        "The work stays invisible — even though it's ready to be seen.",
        "Progress pauses while perfection is pursued.",
        "What could be out in the world stays inside the revision.",
        "The value of the work remains unclaimed.",
    ],
    "visible_vs_hidden": [
        "What could be seen stays hidden — and so does its impact.",
        "You remain smaller than you could be — by choice, but not happily.",
        "The thing you could contribute doesn't land.",
        "Others don't see what you could offer — because you haven't shown it.",
    ],
    "logic_vs_instinct": [
        "The decision stays open — even though you already know.",
        "Energy goes to justification instead of action.",
        "Time passes while you build a case for something you've already felt.",
        "You wait for your mind to catch up to what your body already said.",
    ],
    "self_vs_others": [
        "Your needs stay unmet — because they were never named.",
        "The imbalance continues — quietly, but consistently.",
        "Resentment may build where boundaries weren't set.",
        "You lose energy maintaining a dynamic that doesn't serve you.",
    ],
    "rest_vs_push": [
        "The fatigue builds — even as you push past it.",
        "Your body keeps score, even when your mind doesn't.",
        "The push becomes less effective, but doesn't stop.",
        "You pay later for what you're not honoring now.",
    ],
    "clarity_vs_chaos": [
        "Clarity stays out of reach — because it comes from doing, not thinking.",
        "The fog persists while you wait for it to lift.",
        "The direction you're looking for doesn't arrive through analysis.",
        "Time passes without movement — because movement is what reveals the way.",
    ],
    "trust_vs_doubt": [
        "Doubt continues to run — even when it's not providing new information.",
        "Energy goes to checking instead of acting.",
        "The decision you've made doesn't feel finished — because you keep reopening it.",
        "The relief of closure doesn't arrive — because you don't let it.",
    ],
    "expression_vs_suppression": [
        "What could be said stays inside — building quietly.",
        "The silence costs more than the words would.",
        "The unsaid accumulates — creating distance or weight.",
        "You carry what you could release — just by speaking.",
    ],
}


# =============================================================================
# V4 THE MOVE - Small, Non-Prescriptive Shift
# =============================================================================

V4_THE_MOVE = {
    "push_vs_hold": [
        "You don't need to leap. Just take the smallest version of the step — today.",
        "Just say 10% more than you normally would — and notice what shifts.",
        "Just let one thing move forward without perfect certainty.",
        "Just notice the next time you're about to wait — and don't.",
    ],
    "control_vs_flow": [
        "Just step back from one thing you're managing — and see what happens.",
        "Just let something unfold without adjusting it for 24 hours.",
        "Just notice where you're gripping — and soften slightly.",
        "Just trust one outcome without checking on it.",
    ],
    "precision_vs_progress": [
        "Just let something be done — even if it's not perfect.",
        "Just share or send one thing before the next round of edits.",
        "Just notice when 'not ready' is a delay, not a truth.",
        "Just release something at 85% — and see what happens.",
    ],
    "visible_vs_hidden": [
        "Just say a little more than you normally would.",
        "Just take up a little more space than feels safe.",
        "Just share one thing you've been keeping to yourself.",
        "Just let one part of you be seen that usually stays hidden.",
    ],
    "logic_vs_instinct": [
        "Just act on one instinct without building the full case first.",
        "Just trust one gut feeling — even without the proof.",
        "Just let one decision stand without more research.",
        "Just notice when you're seeking permission for something you already know.",
    ],
    "self_vs_others": [
        "Just name one thing you need — out loud.",
        "Just say no to one thing you want to say no to.",
        "Just notice when you're about to accommodate — and pause.",
        "Just let your truth exist for a moment — before editing it.",
    ],
    "rest_vs_push": [
        "Just honor one signal your body is sending.",
        "Just stop 10 minutes earlier than you planned.",
        "Just let one thing be 'enough' for today.",
        "Just notice the push — and soften into it, even slightly.",
    ],
    "clarity_vs_chaos": [
        "Just take one small action — and let clarity follow.",
        "Just move on one thing — even without full understanding.",
        "Just hold the 'not knowing' without trying to fix it.",
        "Just trust that the next step will reveal the one after.",
    ],
    "trust_vs_doubt": [
        "Just let one thing be decided — without checking again.",
        "Just trust what you've already confirmed.",
        "Just notice when you're seeking reassurance — and stop.",
        "Just let one doubt pass without following it.",
    ],
    "expression_vs_suppression": [
        "Just say one thing you've been holding back.",
        "Just let one truth out — unedited.",
        "Just notice when you're about to swallow words — and speak instead.",
        "Just let silence not win — once.",
    ],
}


# =============================================================================
# MAIN V4 GENERATION FUNCTION
# =============================================================================

def generate_home_insight_v4(
    cluster: str,
    house: Optional[int] = None,
    trigger_confidence: str = "recurring_only",
    signals_summary: Optional[List[str]] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate V4 Home Insight with earned claims and progressive reveal.
    
    V4 OUTPUT STRUCTURE:
    {
        "pattern_label": "Still Circling It",
        "headline": "Grounded, specific, not accusatory",
        "whats_going_on": ["Real-world dynamics"],
        "where_it_shows_up": "Life area anchor",
        "what_you_may_be_doing": ["Observable behaviors"],
        "what_this_creates": "Consequence, not dramatic",
        "the_move": "Small non-prescriptive shift",
        "why_showing_up": {...}  // Hidden proof layer
    }
    """
    # Generate seed for variety
    if seed is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        seed = int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16)
    
    # Get templates for this cluster (default to push_vs_hold)
    pattern_labels = V4_PATTERN_LABELS.get(cluster, V4_PATTERN_LABELS["push_vs_hold"])
    headlines = V4_HEADLINES.get(cluster, V4_HEADLINES["push_vs_hold"])
    whats_going_on = V4_WHATS_GOING_ON.get(cluster, V4_WHATS_GOING_ON["push_vs_hold"])
    what_doing = V4_WHAT_YOU_MAY_BE_DOING.get(cluster, V4_WHAT_YOU_MAY_BE_DOING["push_vs_hold"])
    what_creates = V4_WHAT_THIS_CREATES.get(cluster, V4_WHAT_THIS_CREATES["push_vs_hold"])
    the_moves = V4_THE_MOVE.get(cluster, V4_THE_MOVE["push_vs_hold"])
    
    # Select items with variety
    pattern_label = pattern_labels[seed % len(pattern_labels)]
    headline = headlines[seed % len(headlines)]
    
    # Select 2-3 items for whats_going_on
    wgo_start = seed % max(1, len(whats_going_on) - 2)
    selected_wgo = whats_going_on[wgo_start:wgo_start + 3]
    
    # Select 2-3 items for what_doing
    wd_start = seed % max(1, len(what_doing) - 2)
    selected_doing = what_doing[wd_start:wd_start + 3]
    
    # Select consequence
    consequence = what_creates[seed % len(what_creates)]
    
    # Select the move
    the_move = the_moves[seed % len(the_moves)]
    
    # Build "where it shows up" anchor
    if house and house in V4_WHERE_SHOWS_UP:
        where_shows_up = f"This may be showing up around {V4_WHERE_SHOWS_UP[house]}."
    else:
        default_where = V4_WHERE_CLUSTER_DEFAULT.get(cluster, "something you've been working through")
        where_shows_up = f"This may be showing up around {default_where}."
    
    # Build hidden "why showing up" layer (proof, not main story)
    why_showing_up = None
    if signals_summary:
        why_showing_up = {
            "signals": signals_summary,
            "trigger_confidence": trigger_confidence,
            "note": "These are the patterns informing this insight.",
        }
    
    return {
        "success": True,
        "version": "v4_earned_claims",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        # V4 MANDATORY STRUCTURE
        "pattern_label": pattern_label,
        "headline": headline,
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


def build_v4_narrative(insight: Dict[str, Any]) -> str:
    """Build a narrative string from V4 insight for backward compatibility."""
    parts = []
    
    # Pattern label
    parts.append(f"**{insight['pattern_label'].upper()}**")
    parts.append("")
    
    # Headline
    parts.append(insight["headline"])
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
