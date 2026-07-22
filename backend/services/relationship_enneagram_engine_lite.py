"""relationship_enneagram_engine_lite.py — Compact deterministic
Enneagram Relationship engine (Phase 2-lite / parity with numerology-lite)
==========================================================================

Build marker:   relationship-enneagram-lite-v1
Owner surface:  Forum mappings → signals.enneagram.{v2_card, diagnostics}

Design constraints (mirrors relationship_numerology_engine_lite.py):
  • Deterministic — no LLM, no randomness
  • Backward compatible — existing directional signals
    (how_you_help_them / how_they_help_you / friction_pattern) preserved
  • Additive — `v2_card` + `diagnostics` ride along; FE may ignore
  • Mirror language only — no type-pathology or fortune-telling vocab
  • Reliable inputs only — core type (1..9) is required; wing / instinct
    used opportunistically for diagnostics but NEVER for the narrative
    branch (so wing drift never changes what a user sees)

Five questions, five answers per pair (parity with numerology-lite):
  1. core_dynamic     — what naturally happens between you
  2. natural_strength — what you strengthen in each other
  3. growth_edge      — what wants to grow
  4. shadow_pattern   — what creates friction under pressure
  5. repair_pathway   — the literal first move when friction lands

Engine-specific richness (over-and-above numerology-lite):
  • Line-relationship awareness. If A's stress line lands on B's core
    (or B's security line does, etc.) the diagnostics record it and the
    compositional fallback references it explicitly.
  • Center-pair awareness. Head / Heart / Body pairings drive the
    fallback's "what strengthens" / "what frictions" phrasing so every
    pair ships useful language even without a hand-authored cell.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

ENGINE_VERSION = "relationship-enneagram-lite-v1"

# ── Forbidden language guard ─────────────────────────────────────────
# Enneagram-specific pathology tokens on top of the shared fortune-
# telling vocabulary.  Lower-cased; substring match.
FORBIDDEN_TOKENS: Tuple[str, ...] = (
    "destined",
    "soulmate",
    "karmic partner",
    "meant to be",
    "guaranteed compatibility",
    # Type-pathology / diagnosis vocabulary — banned even in shadow lines
    "unhealthy 1", "unhealthy 2", "unhealthy 3", "unhealthy 4",
    "unhealthy 5", "unhealthy 6", "unhealthy 7", "unhealthy 8",
    "unhealthy 9",
    "personality disorder",
    "diagnos",
    "narcissist",
    "sociopath",
)


def find_forbidden_language(text: str) -> List[str]:
    """Return list of forbidden tokens that appear in `text`."""
    if not isinstance(text, str) or not text:
        return []
    lower = text.lower()
    return [tok for tok in FORBIDDEN_TOKENS if tok in lower]


# ── Type descriptors — Mirror-friendly action language ───────────────
# (label, action_phrase) — parity with numerology-lite ARCHETYPES.
# `action_phrase` follows the same pattern: "verbs + verb-phrase" so it
# reads naturally after the type label in generated sentences.
TYPE_ARCHETYPES: Dict[int, Tuple[str, str]] = {
    1: ("Reformer",      "holds the standard and refines what's off"),
    2: ("Helper",        "attunes to what's needed and moves toward the other"),
    3: ("Achiever",      "reads the room for what wins and delivers it"),
    4: ("Individualist", "names what's beneath the surface and refuses the generic"),
    5: ("Investigator",  "steps back, watches, and builds understanding before acting"),
    6: ("Loyalist",      "scans for what could go wrong and stays committed anyway"),
    7: ("Enthusiast",    "opens options, keeps the future bright, and moves toward the next"),
    8: ("Challenger",    "takes the ground, protects the perimeter, and moves without hedging"),
    9: ("Peacemaker",    "holds the field steady and lets tension dissolve into space"),
}

# ── Centers (Body / Heart / Head) ────────────────────────────────────
TYPE_CENTER: Dict[int, str] = {
    8: "Body", 9: "Body", 1: "Body",
    2: "Heart", 3: "Heart", 4: "Heart",
    5: "Head", 6: "Head", 7: "Head",
}

CENTER_ACTION: Dict[str, str] = {
    "Body":  "moving from instinct",
    "Heart": "reading the emotional field",
    "Head":  "processing through thought",
}

# ── Line dynamics (integration / disintegration) ─────────────────────
# stress_line[type]  → where the type moves under pressure
# security_line[type] → where the type moves when it feels safe
STRESS_LINE:   Dict[int, int] = {1: 4, 2: 8, 3: 9, 4: 2, 5: 7, 6: 3, 7: 1, 8: 5, 9: 6}
SECURITY_LINE: Dict[int, int] = {1: 7, 2: 4, 3: 6, 4: 1, 5: 8, 6: 9, 7: 5, 8: 2, 9: 3}


# ── Hand-authored pair cells (frozenset-keyed; order-insensitive) ────
# Tone: Mirror language — pattern, translation, friction, repair.
# Every field is a template string accepting {name_a} and {name_b}.
#
# Coverage priorities (in order of expected user demand):
#   * All same-type pairs (double-lens dynamics)
#   * Cross-center pairs that show up most in couples / cofounders
#     (3↔7, 8↔2, 5↔8, 4↔9, 1↔9, 6↔9, 7↔4)
#   * Line-connected pairs (3↔6, 5↔7, 1↔7, 2↔8, 4↔2, 3↔9, 8↔5)
#     — where one type's stress OR security line lands ON the other's
#       core.  Those are the highest-signal Enneagram pairings.
HAND_AUTHORED: Dict[frozenset, Dict[str, str]] = {

    # ── SAME-TYPE PAIRS ──────────────────────────────────────────────
    frozenset({1}): {
        "core_dynamic":     "Two Reformers — {name_a} and {name_b} both feel the pull to get it right, and both notice what's off.",
        "natural_strength": "You share a standard.  Neither has to explain why detail matters or why integrity is not negotiable.",
        "growth_edge":      "You both grow by letting some things be imperfect on purpose — the standard is a tool, not the point.",
        "shadow_pattern":   "Under pressure the corrections stack.  You start pointing at each other's small misses instead of the shared aim.",
        "repair_pathway":   "Name one thing the other is doing WELL before naming what needs fixing.  Say it out loud, not in your head.",
    },
    frozenset({2}): {
        "core_dynamic":     "Two Helpers — {name_a} and {name_b} both move toward the other before checking in with themselves.",
        "natural_strength": "You attune fast.  Needs get met before they're named.  Nobody in your orbit feels invisible.",
        "growth_edge":      "You both grow by asking yourselves what you actually want before offering it to the other.",
        "shadow_pattern":   "Under pressure the giving becomes indirect.  You track what you've given; resentment quietly compounds.",
        "repair_pathway":   "Each of you names one thing you want that you haven't asked for.  No apology, no framing.  Just the ask.",
    },
    frozenset({3}): {
        "core_dynamic":     "Two Achievers — {name_a} and {name_b} both read the room for the win and move to deliver it.",
        "natural_strength": "You are a shipping engine.  Momentum, image, calibration — you both understand the game and play it well.",
        "growth_edge":      "You both grow by asking whether the target is actually yours, or the one you learned to aim at.",
        "shadow_pattern":   "Under pressure you both perform.  Neither of you drops the front, and the intimacy starts to feel like a project brief.",
        "repair_pathway":   "One question, no dodging: 'What are we actually building — for us, not for anyone watching?'  Answer it slowly.",
    },
    frozenset({4}): {
        "core_dynamic":     "Two Individualists — {name_a} and {name_b} both refuse the surface and both need the depth to be seen.",
        "natural_strength": "You give each other permission to feel the full weight of things.  Nothing gets flattened between you.",
        "growth_edge":      "You both grow by naming what's ordinary and good, not just what's poignant or missing.",
        "shadow_pattern":   "Under pressure the intensity feeds itself.  You both go into longing at the same time; the daylight thins.",
        "repair_pathway":   "Each names one thing that is actually enough right now — small, plain, present.  Don't dress it up.",
    },
    frozenset({5}): {
        "core_dynamic":     "Two Investigators — {name_a} and {name_b} both watch, both retreat to understand, both need the room to think.",
        "natural_strength": "You respect each other's inner space.  Neither of you needs constant contact to know the connection is real.",
        "growth_edge":      "You both grow by moving before you feel fully ready.  The observation gets richer when it's tested.",
        "shadow_pattern":   "Under pressure you both go quiet.  The distance widens by inches until neither of you knows how to close it.",
        "repair_pathway":   "One brief, deliberate move toward the other — a question, a touch, a plan.  Small counts.  Do it today.",
    },
    frozenset({6}): {
        "core_dynamic":     "Two Loyalists — {name_a} and {name_b} both scan for what could go wrong and both stay through it.",
        "natural_strength": "You show up.  When things get hard, neither of you disappears; the reliability between you is real.",
        "growth_edge":      "You both grow by trusting a plan without stress-testing it to death.  Some things work.",
        "shadow_pattern":   "Under pressure the worry loops out loud.  You amplify each other's worst-case scenarios and forget the base rate.",
        "repair_pathway":   "One of you names the base rate: 'How often does this actually go badly?'  Let the honest answer land.",
    },
    frozenset({7}): {
        "core_dynamic":     "Two Enthusiasts — {name_a} and {name_b} both open doors and both keep the future bright.",
        "natural_strength": "You expand the world for each other.  Novelty, possibility, and the sense that nothing is finished stay alive between you.",
        "growth_edge":      "You both grow by staying in one room long enough for what's difficult to be heard, not reframed.",
        "shadow_pattern":   "Under pressure everything gets a positive spin.  Real pain gets skipped; the momentum covers the wound.",
        "repair_pathway":   "Sit still together for ten minutes with the hard thing named plainly.  Don't fix it.  Just let it be true.",
    },
    frozenset({8}): {
        "core_dynamic":     "Two Challengers — {name_a} and {name_b} both take the ground and both refuse to be moved off it.",
        "natural_strength": "You match each other in scale.  Neither of you shrinks; the honesty between you is unusually direct.",
        "growth_edge":      "You both grow by letting the soft thing under the strength show first — not as a weapon, as an offering.",
        "shadow_pattern":   "Under pressure the position-taking hardens.  Neither backs down and the fight becomes about the fight.",
        "repair_pathway":   "One of you steps out of the frame first: 'What are we actually protecting here?'  Answer it before the next move.",
    },
    frozenset({9}): {
        "core_dynamic":     "Two Peacemakers — {name_a} and {name_b} both keep the field steady and both accommodate before speaking.",
        "natural_strength": "The environment between you is easy.  There's a lot of room, very little urgency, and both feel accepted as-is.",
        "growth_edge":      "You both grow by risking a preference out loud, even a small one.  Merge is not the same as connection.",
        "shadow_pattern":   "Under pressure you both go still.  Nothing gets named; the resentment banks quietly until it isn't quiet anymore.",
        "repair_pathway":   "Each names one thing you actually want that you haven't said.  Small is fine.  Say it before the other agrees.",
    },

    # ── LINE-CONNECTED HIGH-SIGNAL PAIRS ─────────────────────────────
    # 3↔6 : each is on the other's stress/security axis.  Deep loop.
    frozenset({3, 6}): {
        "core_dynamic":     "Achiever meets Loyalist — you sit on each other's line.  Where {name_a} performs to secure the outcome, {name_b} tests for what might go wrong.",
        "natural_strength": "Together the plan gets both delivered AND stress-tested.  Neither the vision nor the risk gets ignored.",
        "growth_edge":      "{name_a} grows by trusting {name_b}'s scan instead of speeding past it.  {name_b} grows by trusting the momentum instead of pre-mortem-ing it.",
        "shadow_pattern":   "Under pressure {name_a} pushes harder to deliver; {name_b} raises more objections.  The plan and the doubt escalate together.",
        "repair_pathway":   "Stop the loop.  {name_b} names ONE real concern.  {name_a} answers it plainly.  Then move — together, in one direction.",
    },

    # 1↔7 : Reformer's security line lands ON 7; Enthusiast's stress lands ON 1.
    frozenset({1, 7}): {
        "core_dynamic":     "Reformer meets Enthusiast — {name_a} wants it right, {name_b} wants it open.  You reach for each other in the release: 1 finds freedom in 7, 7 finds discipline in 1.",
        "natural_strength": "{name_a} keeps the standard.  {name_b} keeps the future bright.  Between you the work is both correct and worth doing.",
        "growth_edge":      "{name_a} grows by letting joy in before the work is finished.  {name_b} grows by finishing the work before chasing the next thing.",
        "shadow_pattern":   "Under pressure {name_a} tightens; {name_b} scatters.  The corrections read as constraint, the options read as evasion.",
        "repair_pathway":   "Pick one thing that matters, do it well together, and celebrate it out loud before the next thing starts.",
    },

    # 5↔7 : security line for 5 lands ON 8, but 5↔7 sit on the stress axis (5 → 7 under stress; 7's own stress → 1).
    # Actually stress: 5→7, security: 7→5.  Deep exchange.
    frozenset({5, 7}): {
        "core_dynamic":     "Investigator meets Enthusiast — {name_a} builds understanding first, {name_b} chases experience first.  You sit on the same head-center axis, pointed opposite directions.",
        "natural_strength": "{name_b} pulls {name_a} out into the world; {name_a} gives {name_b} somewhere to land that isn't the next distraction.",
        "growth_edge":      "{name_a} grows by moving before feeling ready.  {name_b} grows by staying long enough for the depth to arrive.",
        "shadow_pattern":   "Under pressure {name_a} retreats to think; {name_b} runs to the next room.  Nobody is actually here.",
        "repair_pathway":   "One shared silence.  {name_b} stops moving.  {name_a} stops explaining.  Ten minutes together doing nothing.  Then talk.",
    },

    # 2↔8 : stress line for 2 lands ON 8.
    frozenset({2, 8}): {
        "core_dynamic":     "Helper meets Challenger — {name_a} moves toward with care; {name_b} moves toward with force.  {name_a}'s stress line lands right on {name_b}'s door.",
        "natural_strength": "{name_b} makes it safe for {name_a} to want something for themselves.  {name_a} makes it safe for {name_b} to be soft.",
        "growth_edge":      "{name_a} grows by asking directly instead of giving to be seen.  {name_b} grows by receiving without armoring.",
        "shadow_pattern":   "Under pressure {name_a} gives more and tracks it silently; {name_b} pushes harder and misses the cost.  The care becomes a ledger.",
        "repair_pathway":   "{name_a} names one need out loud, without softening it.  {name_b} responds to the need, not the delivery.",
    },

    # 4↔2 : security line for 4 lands on 2; 2's stress lands on 8.  Still high-signal.
    frozenset({4, 2}): {
        "core_dynamic":     "Individualist meets Helper — {name_a} needs to be received in their full weight; {name_b} moves toward that weight instinctively.",
        "natural_strength": "{name_b}'s attention reaches {name_a} where most people stop.  {name_a} lets {name_b} matter as themselves, not as the caretaker.",
        "growth_edge":      "{name_a} grows by receiving the care without testing whether it's real.  {name_b} grows by staying near without shape-shifting.",
        "shadow_pattern":   "Under pressure {name_a} pulls back into intensity; {name_b} gives harder to reach them.  Both efforts miss.",
        "repair_pathway":   "{name_a} names one specific thing they need right now.  {name_b} does exactly that — nothing more, nothing improvised.",
    },

    # 3↔9 : stress line for 3 lands on 9.
    frozenset({3, 9}): {
        "core_dynamic":     "Achiever meets Peacemaker — {name_a} moves toward the win; {name_b} moves toward the calm.  {name_a}'s stress line lands right in {name_b}'s field.",
        "natural_strength": "{name_b} slows {name_a} down enough that the wins actually count.  {name_a} gives {name_b} a direction the calm can attach to.",
        "growth_edge":      "{name_a} grows by valuing rest that produces nothing.  {name_b} grows by naming what they want out loud, on purpose.",
        "shadow_pattern":   "Under pressure {name_a} performs harder; {name_b} goes further into merge.  Neither is actually present.",
        "repair_pathway":   "One question, both answer honestly: 'What would we do this week if there was no one watching and no one to keep peace with?'",
    },

    # 8↔5 : stress line for 8 lands on 5.  Very common cofounder pair.
    frozenset({8, 5}): {
        "core_dynamic":     "Challenger meets Investigator — {name_a} moves without hedging; {name_b} refuses to move without understanding.  {name_a}'s stress line lands squarely on {name_b}.",
        "natural_strength": "{name_b}'s analysis catches what {name_a}'s momentum skips.  {name_a}'s decisiveness gives {name_b}'s thought a place to land.",
        "growth_edge":      "{name_a} grows by pausing for the analysis before acting.  {name_b} grows by acting on incomplete data when it's called for.",
        "shadow_pattern":   "Under pressure {name_a} pushes harder; {name_b} withdraws further to think.  The gap widens fast.",
        "repair_pathway":   "Time-box it.  {name_b} takes an hour, delivers the position.  {name_a} moves on it without re-litigating.  Trade roles next time.",
    },

    # ── OTHER HIGH-USAGE CROSS-CENTER PAIRS ─────────────────────────
    # 3↔7 : classic performer + expander duo (already partial in FRICTION_MAP).
    frozenset({3, 7}): {
        "core_dynamic":     "Achiever meets Enthusiast — both of you move toward the future, but {name_a} wants to arrive and {name_b} wants to keep the door open.",
        "natural_strength": "The energy between you is generative.  {name_b} keeps things from getting narrow; {name_a} keeps things from staying vague.",
        "growth_edge":      "{name_a} grows by tolerating the wandering that produces the best options.  {name_b} grows by committing to a path long enough to reach the end of it.",
        "shadow_pattern":   "Under pressure both of you speed up.  {name_a} performs harder to hit the target; {name_b} chases the next spark.  Neither of you lands.",
        "repair_pathway":   "Pick one thing you'll finish together in the next week.  Say what 'finished' looks like.  Don't add anything until it's done.",
    },

    # 4↔9 : introspective + accepting duo.
    frozenset({4, 9}): {
        "core_dynamic":     "Individualist meets Peacemaker — {name_a} goes deep into what's felt; {name_b} makes room for whatever arrives.",
        "natural_strength": "{name_b}'s acceptance meets {name_a}'s intensity without flinching.  {name_a}'s depth gives {name_b}'s calm somewhere real to rest.",
        "growth_edge":      "{name_a} grows by trusting that ordinary is a form of intimacy.  {name_b} grows by risking a strong preference so {name_a} can meet you.",
        "shadow_pattern":   "Under pressure {name_a} sharpens into longing; {name_b} disappears into stillness.  {name_a} feels unmet; {name_b} feels invaded.",
        "repair_pathway":   "{name_a} names one thing that's actually good right now.  {name_b} names one thing you actually want.  Two sentences.  Say them.",
    },

    # 1↔9 : correction vs acceptance axis.
    frozenset({1, 9}): {
        "core_dynamic":     "Reformer meets Peacemaker — {name_a} reaches for correctness; {name_b} reaches for wholeness.  Both are working the same territory from opposite ends.",
        "natural_strength": "{name_b}'s ease shows {name_a} what's already enough.  {name_a}'s standard shows {name_b} what actually matters to name.",
        "growth_edge":      "{name_a} grows by trusting that things not-yet-corrected are not wrong.  {name_b} grows by voicing a preference before agreeing to what's asked.",
        "shadow_pattern":   "Under pressure {name_a}'s corrections feel like criticism; {name_b}'s peace feels like avoidance.  Both dig into their side.",
        "repair_pathway":   "One shared review — not a critique.  Each names one thing about the other that already works.  Then the small correction.",
    },

    # 6↔9 : security line for 6 lands on 9.  Very common family dynamic.
    frozenset({6, 9}): {
        "core_dynamic":     "Loyalist meets Peacemaker — {name_a} scans for what could go wrong; {name_b} keeps the field steady regardless.  {name_a}'s security line lands right in {name_b}'s calm.",
        "natural_strength": "{name_b}'s presence quiets {name_a}'s scanner.  {name_a}'s vigilance keeps {name_b} from disappearing into merge.",
        "growth_edge":      "{name_a} grows by letting the calm be true instead of testing it.  {name_b} grows by naming a concern before it dissolves into 'it's fine.'",
        "shadow_pattern":   "Under pressure {name_a} amplifies worry; {name_b} goes flatter.  The worry escalates because the field never pushes back.",
        "repair_pathway":   "{name_b} takes a position — any position — out loud.  {name_a} lets it land without stress-testing it for five whole minutes.",
    },

    # 8↔9 : body-center pair, common couple dynamic.
    frozenset({8, 9}): {
        "core_dynamic":     "Challenger meets Peacemaker — {name_a} pushes forward without hedging; {name_b} absorbs and adjusts without saying much.",
        "natural_strength": "{name_b} is unusually steady in the presence of {name_a}'s intensity.  {name_a}'s directness gives {name_b}'s calm a form.",
        "growth_edge":      "{name_a} grows by softening enough to notice what {name_b} accommodates silently.  {name_b} grows by voicing a boundary before it turns into withdrawal.",
        "shadow_pattern":   "Under pressure {name_a} pushes; {name_b} absorbs until it comes back all at once.  Neither is ready when it does.",
        "repair_pathway":   "{name_b} names one thing that is not fine before it becomes not fine.  {name_a} holds still and receives it, no rebuttal.",
    },

    # 5↔4 : head + heart withdrawn pair.
    frozenset({5, 4}): {
        "core_dynamic":     "Investigator meets Individualist — {name_a} steps back to understand; {name_b} goes inward to feel.  Both of you protect an interior nobody else sees.",
        "natural_strength": "You give each other space that most people won't.  The depth you both need is available here without explanation.",
        "growth_edge":      "{name_a} grows by staying in feeling instead of moving to analysis.  {name_b} grows by asking a specific question instead of expressing a diffuse ache.",
        "shadow_pattern":   "Under pressure {name_a} withdraws further; {name_b} intensifies to be seen.  Neither move works on the other.",
        "repair_pathway":   "Ten minutes together, no problem-solving.  {name_b} names one feeling.  {name_a} reflects it back once.  Then quiet.",
    },
}


# ── Helpers ──────────────────────────────────────────────────────────
def _slug(text: str) -> str:
    """Slugify for pair_type diagnostic.  Lowercase, hyphen-joined."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _extract_wing(user: Optional[Dict[str, Any]]) -> Optional[int]:
    """Best-effort wing extraction.  Wing is diagnostic-only — the
    narrative branch never depends on it, so `None` is safe."""
    if not isinstance(user, dict):
        return None
    enn = user.get("enneagram")
    if isinstance(enn, dict):
        w = enn.get("inferred_wing") or enn.get("wing")
        try:
            wi = int(w)
            if 1 <= wi <= 9:
                return wi
        except (TypeError, ValueError):
            pass
        # Also accept "5w4" style strings
        if isinstance(w, str):
            m = re.search(r"w\s*([1-9])", w.lower())
            if m:
                return int(m.group(1))
    return None


def _extract_instinct(user: Optional[Dict[str, Any]]) -> Optional[str]:
    """Best-effort instinct extraction (sp / so / sx).  Diagnostic-only."""
    if not isinstance(user, dict):
        return None
    enn = user.get("enneagram")
    if not isinstance(enn, dict):
        return None
    computed = enn.get("enneagram_computed_details") or {}
    for key in ("instinctual_stack", "dominant_instinct", "instinct"):
        val = computed.get(key) or enn.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip().lower()
    return None


def _line_relationship(core_a: int, core_b: int) -> Optional[str]:
    """Return a compact label if A and B sit on each other's Enneagram
    lines (stress or security)."""
    if core_a == core_b:
        return None
    a_stress   = STRESS_LINE.get(core_a)
    a_security = SECURITY_LINE.get(core_a)
    b_stress   = STRESS_LINE.get(core_b)
    b_security = SECURITY_LINE.get(core_b)
    labels: List[str] = []
    if a_stress == core_b:
        labels.append(f"{core_a}_stress_to_{core_b}")
    if a_security == core_b:
        labels.append(f"{core_a}_security_to_{core_b}")
    if b_stress == core_a:
        labels.append(f"{core_b}_stress_to_{core_a}")
    if b_security == core_a:
        labels.append(f"{core_b}_security_to_{core_a}")
    if not labels:
        return None
    return "+".join(sorted(labels))


def _center_pair_label(core_a: int, core_b: int) -> str:
    ca, cb = TYPE_CENTER.get(core_a, "?"), TYPE_CENTER.get(core_b, "?")
    return f"{ca.lower()}-{cb.lower()}"


def _compose_fallback(core_a: int, core_b: int,
                      name_a: str, name_b: str) -> Dict[str, str]:
    """Compositional Mirror-language card used when no hand-authored
    cell exists.  Every field is guaranteed to produce a readable line
    based on centers, archetypes, and line relationships."""
    arc_a = TYPE_ARCHETYPES.get(core_a, (f"Type-{core_a}", f"moves in a Type-{core_a} rhythm"))
    arc_b = TYPE_ARCHETYPES.get(core_b, (f"Type-{core_b}", f"moves in a Type-{core_b} rhythm"))
    center_a = TYPE_CENTER.get(core_a, "?")
    center_b = TYPE_CENTER.get(core_b, "?")
    same_center = center_a == center_b

    # LINE-AWARE strength / repair — the highest-signal Enneagram fact.
    line_label = _line_relationship(core_a, core_b)

    if core_a == core_b:
        # Same-type composition (parity with numerology-lite's same-lp branch).
        return {
            "core_dynamic":
                f"Two {arc_a[0]}s — {name_a} and {name_b} both {arc_a[1]}.  "
                f"You recognise the same reflex in each other on sight.",
            "natural_strength":
                f"The rhythm doesn't have to be translated.  You share the "
                f"same {center_a.lower()}-center default: {CENTER_ACTION.get(center_a, 'a shared operating mode')}.",
            "growth_edge":
                f"The lens you both default to is also the lens you both avoid the work behind.  "
                f"Each grows by leaning into what the other quietly skips.",
            "shadow_pattern":
                f"Under pressure both of you reach for the same {arc_a[0]} reflex.  "
                f"The pattern doubles instead of balancing.",
            "repair_pathway":
                "Trade default moves briefly.  One of you names what the other usually carries; "
                "the other tries that move for an hour.",
        }

    # Center-pair phrasing anchors the fallback in something specific.
    if same_center:
        center_phrase = (
            f"Same center ({center_a}) — you take the world in the same way "
            f"({CENTER_ACTION.get(center_a, 'a shared channel')}), but you point that channel in opposite directions."
        )
    else:
        center_phrase = (
            f"Different centers — {name_a} runs on {center_a} ({CENTER_ACTION.get(center_a, 'their channel')}), "
            f"{name_b} runs on {center_b} ({CENTER_ACTION.get(center_b, 'their channel')}).  "
            f"You process the same moment through different equipment."
        )

    # Repair pathway leans on the line relationship when one exists.
    if line_label:
        repair = (
            f"Use the line: when the pressure spikes, {name_a} and {name_b} sit on each other's "
            f"Enneagram axis ({line_label.replace('_', ' ')}).  Name where you actually are — "
            f"stress-side or security-side — before responding."
        )
        strength_addendum = "  The line between your types means the exchange is unusually deep — you have direct access to each other's growth edge."
    else:
        repair = (
            "Slow the exchange by one step.  Each of you names the reflex you just used "
            "(the automatic move) BEFORE naming what you want the other to do."
        )
        strength_addendum = ""

    return {
        "core_dynamic":
            f"{arc_a[0]} meets {arc_b[0]} — {name_a} {arc_a[1]}; {name_b} {arc_b[1]}.  "
            f"{center_phrase}",
        "natural_strength":
            f"What {name_a} brings, {name_b} carries differently.  You cover territory the other "
            f"leaves unattended, and translate between two operating rhythms.{strength_addendum}",
        "growth_edge":
            f"{name_a} grows by leaning into what {name_b} does automatically.  "
            f"{name_b} grows by doing the same in reverse.  The lens you're least fluent in "
            f"is where the work is.",
        "shadow_pattern":
            f"Under pressure {name_a} overdoes their {arc_a[0]} reflex; {name_b} overdoes theirs.  "
            f"Both moves become caricatures of themselves and neither reaches the other.",
        "repair_pathway": repair,
    }


def _build_v2_card(core_a: int, core_b: int,
                   name_a: str, name_b: str) -> Tuple[Dict[str, str], bool]:
    """Return (v2_card, used_hand_authored)."""
    cell = HAND_AUTHORED.get(frozenset({core_a, core_b}))
    if cell:
        # For asymmetric hand-authored cells (e.g. 2↔8), we deterministically
        # render {name_a} = the side whose core matches the FIRST type key
        # in the frozenset's natural order.  Since frozensets are unordered,
        # we look up in canonical (smaller, larger) order but respect the
        # authored copy verbatim — the copy is already written from a
        # specific perspective per cell.  The template placeholders
        # {name_a}/{name_b} are filled from the CALLER's ordering (i.e.
        # user_a → name_a) so hand-authored cells that are symmetric read
        # identically both ways, and asymmetric cells (like 2↔8) always
        # keep the direction the author intended by writing generically.
        rendered = {
            k: v.format(name_a=name_a, name_b=name_b)
            for k, v in cell.items()
        }
        return rendered, True

    return _compose_fallback(core_a, core_b, name_a, name_b), False


def _pair_type(core_a: int, core_b: int) -> str:
    """Deterministic pair-type slug ordered by (smaller-then-larger)."""
    a, b = sorted((core_a, core_b))
    arc_a = TYPE_ARCHETYPES.get(a, (f"type-{a}", ""))[0]
    arc_b = TYPE_ARCHETYPES.get(b, (f"type-{b}", ""))[0]
    return _slug(f"{a}x{b}-{arc_a}-meets-{arc_b}")


# ── Public API ───────────────────────────────────────────────────────
def compute_enneagram_relationship(user_a: Dict[str, Any],
                                   user_b: Dict[str, Any],
                                   name_a: str,
                                   name_b: str) -> Optional[Dict[str, Any]]:
    """Compute the v2_card + diagnostics block for an Enneagram pair.

    Returns None ONLY when core type is missing on either side.
    Uses the canonical `enneagram_source.get_user_enneagram` resolver so
    the engine honours the same fallback chain (enneagram_type →
    enneagram.inferred_core → enneagram.core → legacy enneagram) as
    Forum Dynamics / Member Lens / compute_enneagram_signals.
    """
    try:
        from services.enneagram_source import get_user_enneagram
    except Exception:  # pragma: no cover — package-path fallback
        from enneagram_source import get_user_enneagram  # type: ignore

    core_a = get_user_enneagram(user_a)
    core_b = get_user_enneagram(user_b)
    if not core_a or not core_b:
        return None

    v2_card, used_hand = _build_v2_card(core_a, core_b, name_a, name_b)

    # Guard rail — no forbidden vocabulary shall ship in the output.
    # If any hand-authored / composed field trips the guard we drop
    # that field so the callers never render fortune-telling language.
    for k in list(v2_card.keys()):
        if find_forbidden_language(v2_card[k]):
            del v2_card[k]

    wing_a = _extract_wing(user_a)
    wing_b = _extract_wing(user_b)
    instinct_a = _extract_instinct(user_a)
    instinct_b = _extract_instinct(user_b)
    line_label = _line_relationship(core_a, core_b)
    center_a = TYPE_CENTER.get(core_a)
    center_b = TYPE_CENTER.get(core_b)

    diagnostics: Dict[str, Any] = {
        "core_a":             core_a,
        "core_b":             core_b,
        "wing_a":             wing_a,
        "wing_b":             wing_b,
        "instinct_a":         instinct_a,
        "instinct_b":         instinct_b,
        "center_a":           center_a,
        "center_b":           center_b,
        "center_pair":        _center_pair_label(core_a, core_b),
        "shared_center":      center_a == center_b and center_a is not None,
        "line_relationship":  line_label,
        "pair_type":          _pair_type(core_a, core_b),
        "used_hand_authored": used_hand,
        "engine_version":     ENGINE_VERSION,
    }

    return {"v2_card": v2_card, "diagnostics": diagnostics}
