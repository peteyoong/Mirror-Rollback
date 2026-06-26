"""relationship_hd_field_engine.py — HD Relationship Field Engine V3
======================================================================

Build marker:  relationship-hd-field-v3
Companion to:  services/forum_hd_mapping.py (preserves existing channel
               and gate signal output; this engine ADDS field_v3 +
               diagnostics).

Philosophy
----------
This is **not** a gate interpreter.  It's an **energetic field engine**.
The single question it answers is:

    "What happens to the energetic field when these two people are
     together?"

Everything is derived from already-computed chart fields:
  type, authority, profile, definition, defined_centers,
  undefined_centers, defined_channels, active_gates, variables.

Output is purely additive.  Existing HD signal arrays in
`signals.human_design` remain untouched.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

# Reuse the canonical channel table for electromagnetic / compromise /
# dominance / companion detection.  Falls back gracefully if import
# fails (e.g. unit tests outside backend).
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
    BACKEND = os.path.dirname(HERE)
    if BACKEND not in sys.path:
        sys.path.insert(0, BACKEND)
    from calculations.human_design import HD_CHANNELS_CLEAN
except Exception:  # pragma: no cover
    HD_CHANNELS_CLEAN: List[Tuple] = []

ENGINE_VERSION = "relationship-hd-field-v3"


# ── Forbidden language guard ─────────────────────────────────────────
FORBIDDEN_TOKENS: Tuple[str, ...] = (
    "destiny", "destined", "soulmate", "karmic partner",
    "meant to be", "guaranteed compatibility",
    "prediction", "fortune telling", "fortune-telling",
)


def find_forbidden_language(text: str) -> List[str]:
    if not isinstance(text, str) or not text:
        return []
    lower = text.lower()
    return [t for t in FORBIDDEN_TOKENS if t in lower]


# ─────────────────────────────────────────────────────────────────────
# Type pair narratives (15 unique, undirected by frozenset)
# ─────────────────────────────────────────────────────────────────────
TYPE_PAIR_AURA: Dict[frozenset, str] = {
    frozenset({"Manifestor", "Manifestor"}):
        "Two closed, initiating auras sharing the same field.  Both move first; neither yields by default.  When the rhythm is informed early, momentum compounds.  When it isn't, both feel intruded upon.",
    frozenset({"Manifestor", "Generator"}):
        "{name_a}'s closed aura initiates; {name_b}'s open enveloping aura responds.  Momentum is fastest when {name_a} informs before acting and {name_b} waits to feel into what's offered — direct push doesn't land on a Generator the way it lands on others.",
    frozenset({"Manifestor", "Manifesting Generator"}):
        "Both auras initiate, but {name_b}'s also envelops while {name_a}'s closes.  Two engines on the same field — they can fly together, or they can collide.  Informing each other is the difference.",
    frozenset({"Manifestor", "Projector"}):
        "{name_a}'s closed aura moves into space; {name_b}'s focused aura reads what's moving.  This pairing works through invitation and informing — {name_b} sees clearly but only when {name_a} doesn't move past being seen.",
    frozenset({"Manifestor", "Reflector"}):
        "{name_a}'s closed-and-initiating aura meets {name_b}'s sampling, fluid aura.  Whatever {name_a} initiates, {name_b} will reflect back in time — sometimes amplified, sometimes inverted.  The pairing teaches {name_a} that impact lands long after the action.",
    frozenset({"Generator", "Generator"}):
        "Two open enveloping auras occupying the same space — sustainable life-force when both wait to respond, mutual exhaustion when either pushes initiation.  Decisions made together feel slower but hold longer.",
    frozenset({"Generator", "Manifesting Generator"}):
        "Two response-based auras; one steady, one multi-pass.  {name_b}'s skip-step rhythm can pull {name_a} into action before {name_a}'s sacral has spoken.  When both wait, the pace finds itself.",
    frozenset({"Generator", "Projector"}):
        "{name_a}'s enveloping aura supplies energy; {name_b}'s focused aura supplies recognition.  This is one of the most naturally symbiotic pairings in HD when {name_b} waits to be invited and {name_a} responds to that recognition.",
    frozenset({"Generator", "Reflector"}):
        "{name_a}'s steady energy meets {name_b}'s sampling aura.  {name_b} will pick up {name_a}'s satisfaction or frustration faster than {name_a} does — making {name_b} a real-time mirror of {name_a}'s alignment.",
    frozenset({"Manifesting Generator", "Manifesting Generator"}):
        "Two multi-pass, skip-step auras in the same field.  Lots of motion, lots of false starts, lots of correction.  The pairing thrives when both inform mid-correction instead of waiting for the polished version.",
    frozenset({"Manifesting Generator", "Projector"}):
        "{name_a}'s skip-step energy meets {name_b}'s recognising aura.  {name_b} sees the patterns {name_a} can't see while moving; {name_a} provides the motion {name_b}'s strategy needs.  Invitation and informing both matter here.",
    frozenset({"Manifesting Generator", "Reflector"}):
        "{name_a}'s fast multi-correcting rhythm meets {name_b}'s lunar sampling rhythm.  {name_b} will read whether {name_a}'s motion is signal or noise — and that reading takes 28 days to fully settle.",
    frozenset({"Projector", "Projector"}):
        "Two focused, penetrating auras reading each other.  Recognition is mutual and fast.  Without invitation, both feel unseen; with it, both feel deeply understood.  The challenge is sustaining the field once recognition has been received.",
    frozenset({"Projector", "Reflector"}):
        "{name_a}'s focused aura meets {name_b}'s wide-open sampling aura.  {name_b} feels every recognition {name_a} offers, plus everything else in the room.  {name_a}'s strategy is invitation; {name_b}'s strategy is lunar timing.",
    frozenset({"Reflector", "Reflector"}):
        "Two open lunar auras sampling each other and everything else.  The relationship moves at a 28-day rhythm — what's clear today may not be clear tomorrow, and that's not a problem; it's the system working.",
}


# ─────────────────────────────────────────────────────────────────────
# Authority pair narratives (6 authorities; classical HD typology)
# ─────────────────────────────────────────────────────────────────────
AUTHORITIES = (
    "Emotional", "Sacral", "Splenic", "Ego", "Self-Projected", "Lunar",
    "Mental", "None",
)

AUTHORITY_PAIR: Dict[frozenset, str] = {
    frozenset({"Emotional", "Emotional"}):
        "Both decisions need to ride a wave before they're clear.  Either of you deciding in-the-moment will regret it.  Patience with the other person's wave is the entire practice.",
    frozenset({"Emotional", "Sacral"}):
        "{name_a} needs the wave; {name_b}'s body knows in the moment.  When {name_b} pushes for a decision before {name_a}'s wave has settled, {name_a}'s yes turns into a no within days.  Wait for the wave.",
    frozenset({"Emotional", "Splenic"}):
        "{name_a} processes over time; {name_b} knows in a single split second — and that knowing won't repeat.  {name_b}'s 'now' and {name_a}'s 'after the wave' rarely line up.  Both signals are real; pacing is the bridge.",
    frozenset({"Emotional", "Ego"}):
        "{name_a} needs the wave; {name_b} decides through willpower and commitment.  {name_b} will press for a yes before {name_a} can give one — and {name_a}'s pre-wave yes is unreliable.  Slow it down.",
    frozenset({"Emotional", "Self-Projected"}):
        "{name_a} needs the wave; {name_b} needs to hear themselves speak it.  {name_b} can talk through their clarity while {name_a}'s wave is still cresting — useful, as long as {name_a} doesn't agree mid-wave.",
    frozenset({"Emotional", "Lunar"}):
        "{name_a} needs a wave; {name_b} needs a 28-day cycle.  Almost no decisions should be made on the spot here.  Both signals reward patience; impatience corrupts both.",
    frozenset({"Sacral", "Sacral"}):
        "Both bodies know in the moment.  Decisions land fast — and reverse fast if either of you starts overriding the gut.  Speak the sacral sounds out loud; the room reads them.",
    frozenset({"Sacral", "Splenic"}):
        "Both decide in the moment but through different doors — gut response vs. spontaneous knowing.  When you disagree, it's because one of you has a body-yes and the other has a wisdom-no; both are valid signals.",
    frozenset({"Sacral", "Ego"}):
        "{name_a}'s body responds; {name_b}'s will commits.  Mixed signals get common — body says yes while will says wait, or vice versa.  Distinguish 'this is right' from 'this is mine to commit to'.",
    frozenset({"Sacral", "Self-Projected"}):
        "{name_a} knows through gut response; {name_b} knows by talking it out loud.  {name_b} needs space to speak; {name_a} needs space to feel.  Same answer, two routes.",
    frozenset({"Sacral", "Lunar"}):
        "{name_a}'s body knows now; {name_b} needs 28 days.  Almost every disagreement here is about pacing rather than content.  Patience with the lunar is the practice.",
    frozenset({"Splenic", "Splenic"}):
        "Both of you know in single split-second hits.  The decisions feel obvious in the moment and untransferable later.  If you didn't act on it then, the signal is gone.",
    frozenset({"Splenic", "Ego"}):
        "{name_a} reads in the moment; {name_b} commits through will.  {name_b} can override {name_a}'s split-second wisdom by force of commitment — and usually regrets it.",
    frozenset({"Splenic", "Self-Projected"}):
        "{name_a} reads quietly; {name_b} hears their own truth by speaking.  When {name_b} speaks while {name_a}'s splenic is whispering, the whisper gets missed.  Take turns.",
    frozenset({"Splenic", "Lunar"}):
        "{name_a}'s now-knowing meets {name_b}'s 28-day cycle.  These are on opposite ends of the timing spectrum.  The pairing teaches both of you that 'real' has more than one timestamp.",
    frozenset({"Ego", "Ego"}):
        "Both decide through willpower.  Commitments stack up faster than either can sustain.  The pairing works when both regularly check whether the will still has the heart behind it.",
    frozenset({"Ego", "Self-Projected"}):
        "{name_a} commits through will; {name_b} clarifies by speaking.  {name_b}'s self-projection can lock {name_a} into commitments they made out loud.  Slow down what gets said.",
    frozenset({"Ego", "Lunar"}):
        "Will meets 28-day cycle.  {name_a}'s commitment-pace and {name_b}'s lunar pace are out of sync by default; most friction here is about timing.",
    frozenset({"Self-Projected", "Self-Projected"}):
        "Both of you need to hear yourselves speak to know what's true.  Conversations are decisions in this pairing — the talking IS the process.",
    frozenset({"Self-Projected", "Lunar"}):
        "{name_a} clarifies by speaking; {name_b} clarifies over a 28-day cycle.  {name_b} should not be asked to respond in the conversation; the response will arrive later.",
    frozenset({"Lunar", "Lunar"}):
        "Two 28-day cycles in the same field.  Almost nothing should be decided in the moment.  The pairing works on geological time.",
}


# ─────────────────────────────────────────────────────────────────────
# Center conditioning — what each center does when one defined / one open
# Returns one narrative line per (center, who_defined) where one is
# defined and the other is open.  The OPEN side experiences amplification.
# ─────────────────────────────────────────────────────────────────────
CENTER_CONDITIONING: Dict[str, str] = {
    "Head":          "amplifies mental pressure (questions / inspiration) — open-Head side absorbs the defined-Head side's questions and starts experiencing them as their own",
    "Ajna":          "amplifies certainty — open-Ajna side starts to sound certain about the defined-Ajna side's conclusions",
    "Throat":        "amplifies the urge to speak / manifest — open-Throat side speaks louder and faster than usual",
    "G Center":      "amplifies identity and direction — open-G side starts feeling the defined-G side's sense of self and direction as their own",
    "Heart":         "amplifies willpower and self-worth — open-Heart side starts pushing for commitments and proving themselves",
    "Solar Plexus":  "amplifies emotional waves — open-Solar-Plexus side feels the defined side's emotional weather magnified through them",
    "Sacral":        "amplifies life-force / response — open-Sacral side runs on borrowed energy and overruns its capacity",
    "Spleen":        "amplifies the impulse to hold on — open-Spleen side stays in situations longer than is healthy for them",
    "Root":          "amplifies pressure to finish and move — open-Root side feels rushed and pressured by the defined side's adrenal pace",
}


# Symmetric (both defined / both open) center narratives
CENTER_BOTH_DEFINED: Dict[str, str] = {
    "Head":          "consistent direction of mental inquiry",
    "Ajna":          "shared conceptual framework — both 'know' similarly",
    "Throat":        "two voices in the field; neither yields automatically",
    "G Center":      "two distinct identities and directions; needs explicit space for both",
    "Heart":         "two willpowers — commitments can compete",
    "Solar Plexus":  "two emotional weather systems running simultaneously",
    "Sacral":        "two engines of life-force; sustainable when both wait to respond",
    "Spleen":        "two intuitive radars active at once",
    "Root":          "two pressure systems — pace doubles unless explicitly checked",
}

CENTER_BOTH_OPEN: Dict[str, str] = {
    "Head":          "both reading the room's mental noise instead of generating it",
    "Ajna":          "both holding ideas loosely; certainty arrives from outside",
    "Throat":        "both quieter than usual; speech comes when invited",
    "G Center":      "both sensitive to whose direction is leading right now",
    "Heart":         "neither defaults to willpower; both vulnerable to over-commitment from outside pressure",
    "Solar Plexus":  "no native emotional weather; both amplify whatever wave enters the field",
    "Sacral":        "no native life-force engine; both run on borrowed energy when others are present",
    "Spleen":        "no constant intuition; both hold on through habit instead of body-signal",
    "Root":          "no native pressure; both pace through external rhythm",
}


# ─────────────────────────────────────────────────────────────────────
# Channel category classification — electromagnetic / compromise /
# dominance / companion
# ─────────────────────────────────────────────────────────────────────
def _classify_channels(active_a: Set[int], active_b: Set[int]) -> Dict[str, List[Tuple[int, int]]]:
    """Return {electromagnetic, compromise, dominance, companion} ->
    list of (gate1, gate2) sorted smaller-first."""
    result = {"electromagnetic": [], "compromise": [], "dominance": [], "companion": []}
    seen_pairs: Set[frozenset] = set()
    for ch in HD_CHANNELS_CLEAN:
        g1, g2 = ch[0], ch[1]
        pair = frozenset({g1, g2})
        if pair in seen_pairs: continue
        seen_pairs.add(pair)
        a1, a2 = g1 in active_a, g2 in active_a
        b1, b2 = g1 in active_b, g2 in active_b
        a_has_full = a1 and a2
        b_has_full = b1 and b2
        a_has_one  = (a1 ^ a2)  # exactly one
        b_has_one  = (b1 ^ b2)
        pair_sorted = tuple(sorted((g1, g2)))
        if a_has_full and not (b1 or b2):
            result["dominance"].append(pair_sorted + ("a",))   # type: ignore
        elif b_has_full and not (a1 or a2):
            result["dominance"].append(pair_sorted + ("b",))   # type: ignore
        elif a_has_one and b_has_one:
            if (a1 and b1) or (a2 and b2):
                # Same gate on both sides — companion / friendship
                result["companion"].append(pair_sorted)
            else:
                # Different gates — electromagnetic completion
                result["electromagnetic"].append(pair_sorted)
        elif (a_has_full and b_has_one) or (b_has_full and a_has_one):
            result["compromise"].append(pair_sorted)
    return result


# ─────────────────────────────────────────────────────────────────────
# Energy signature — derived from type-pair + definition-pair
# ─────────────────────────────────────────────────────────────────────
TYPE_SIGNATURE_TOKENS = {
    "Manifestor":            ("Catalyst",   "Initiator"),
    "Generator":             ("Engine",     "Sustainer"),
    "Manifesting Generator": ("Multi-Track Engine", "Hybrid Catalyst"),
    "Projector":             ("Guide",      "Mirror"),
    "Reflector":             ("Sampler",    "Reflective Field"),
}


def _energy_signature(type_a: str, type_b: str) -> str:
    """Generate the one-line signature deterministically.  Uses the
    'primary' label of each type and joins them as 'The X and the Y.'"""
    label_a = TYPE_SIGNATURE_TOKENS.get(type_a, ("Field",))[0]
    label_b = TYPE_SIGNATURE_TOKENS.get(type_b, ("Field",))[0]
    if label_a == label_b:
        return f"Two {label_a}s in the same field."
    return f"The {label_a} and the {label_b}."


# ─────────────────────────────────────────────────────────────────────
# Friction patterns — derived from authority + type combos
# ─────────────────────────────────────────────────────────────────────
def _friction_patterns(type_a: str, type_b: str,
                       auth_a: str, auth_b: str,
                       def_a: str, def_b: str) -> List[str]:
    out: List[str] = []
    # Authority-driven friction
    if "Emotional" in (auth_a, auth_b) and auth_a != auth_b:
        out.append("Deciding before the emotional wave has settled.")
    if "Lunar" in (auth_a, auth_b) and auth_a != auth_b:
        out.append("Asking the lunar-authority side to respond in real time.")
    if auth_a == "Splenic" and auth_b == "Splenic":
        out.append("Acting on a splenic hit one of you missed in the moment.")
    if auth_a == "Sacral" and auth_b == "Sacral":
        out.append("Overriding the gut by talking past the response.")
    if "Ego" in (auth_a, auth_b):
        out.append("Pressing for a commitment before the will has heart behind it.")
    # Type-driven friction
    if "Manifestor" in (type_a, type_b):
        out.append("Acting without informing — the closed aura is read as intrusion when it isn't announced.")
    if "Projector" in (type_a, type_b):
        out.append("Speaking before being invited; bitterness from being unseen.")
    if "Reflector" in (type_a, type_b):
        out.append("Pressuring the reflector for an answer before a 28-day cycle has run.")
    # Definition friction
    if def_a != def_b and (def_a in {"Single", "Split"} or def_b in {"Single", "Split"}):
        out.append("One side completing the other's energy by being present, then withdrawing the completion.")
    return out[:4] or ["Most friction here will be about pacing rather than content."]


# ─────────────────────────────────────────────────────────────────────
# Repair pathway — derived strictly from type + authority + centers
# ─────────────────────────────────────────────────────────────────────
def _repair_pathway(type_a: str, type_b: str,
                    auth_a: str, auth_b: str,
                    open_centers_a: Set[str], open_centers_b: Set[str]) -> List[str]:
    out: List[str] = []
    # Authority-coded repair
    if "Emotional" in (auth_a, auth_b):
        out.append("Sleep on it.  No important decisions until the emotional wave has crested and settled — usually overnight, sometimes longer.")
    if "Lunar" in (auth_a, auth_b):
        out.append("Give the lunar-authority side a full month before treating their position as final.")
    if "Sacral" in (auth_a, auth_b):
        out.append("Re-ask the question and listen for the gut sound.  If the sacral didn't speak, the answer hasn't arrived.")
    if "Splenic" in (auth_a, auth_b):
        out.append("Lower the noise in the field — splenic signals don't repeat and don't survive crowded rooms.")
    # Type-coded repair
    if "Manifestor" in (type_a, type_b):
        out.append("Inform before acting next time.  Half the friction here is intrusion the other person can't name.")
    if "Projector" in (type_a, type_b):
        out.append("Invite recognition explicitly.  The projector side cannot work without it, and the non-projector side needs to know it's still being seen.")
    if "Reflector" in (type_a, type_b):
        out.append("Change the environment.  Reflectors metabolise relationships through location more than through conversation.")
    # Conditioning repair
    if "Solar Plexus" in (open_centers_a | open_centers_b):
        out.append("Separate physically until the emotional weather has cleared.  The open-Solar-Plexus side cannot find its own signal while in the field.")
    if "Sacral" in (open_centers_a | open_centers_b):
        out.append("The open-Sacral side needs to leave the field before they can feel their actual energy level.")
    return out[:5] or ["Pause.  Each of you names what you actually need, without solving anything yet."]


# ─────────────────────────────────────────────────────────────────────
# Centre Conditioning — strongest three asymmetric pairs
# ─────────────────────────────────────────────────────────────────────
CENTER_PRIORITY = [
    "Solar Plexus", "Sacral", "G Center", "Throat",
    "Heart", "Spleen", "Ajna", "Root", "Head",
]


def _centre_conditioning_lines(defined_a: Set[str], defined_b: Set[str],
                               undefined_a: Set[str], undefined_b: Set[str],
                               name_a: str, name_b: str) -> List[str]:
    lines: List[str] = []
    for center in CENTER_PRIORITY:
        a_def = center in defined_a
        b_def = center in defined_b
        a_open = center in undefined_a
        b_open = center in undefined_b
        if a_def and b_open:
            lines.append(
                f"{name_a}'s defined {center} {CENTER_CONDITIONING.get(center, '')}.  "
                f"{name_b} will leave the field carrying impressions of {name_a}'s {center}."
            )
        elif b_def and a_open:
            lines.append(
                f"{name_b}'s defined {center} {CENTER_CONDITIONING.get(center, '')}.  "
                f"{name_a} will leave the field carrying impressions of {name_b}'s {center}."
            )
    return lines[:3]


def _both_centers_lines(defined_a: Set[str], defined_b: Set[str],
                        undefined_a: Set[str], undefined_b: Set[str]) -> List[str]:
    out: List[str] = []
    for center in CENTER_PRIORITY:
        if center in defined_a and center in defined_b:
            out.append(f"Both defined in {center}: {CENTER_BOTH_DEFINED.get(center, '')}.")
        elif center in undefined_a and center in undefined_b:
            out.append(f"Both open in {center}: {CENTER_BOTH_OPEN.get(center, '')}.")
    return out[:2]


# ─────────────────────────────────────────────────────────────────────
# Electromagnetic / Compromise / Dominance narratives
# ─────────────────────────────────────────────────────────────────────
def _electromagnetic_narrative(em_count: int, name_a: str, name_b: str) -> str:
    if em_count == 0:
        return "No electromagnetic completions between you — your charts don't form new channels in each other's presence.  The energy you have together is what you each brought in separately."
    if em_count == 1:
        return f"You complete one channel together that neither of you carries alone.  When you're in the same field, a new current opens that's invisible to either of you in solitude."
    return f"{em_count} channels complete between you when you're in the same field.  These are the energies neither of you consistently carries solo — they only come online together, which is why being apart can feel like losing access to a part of yourself."


def _compromise_narrative(comp_count: int, name_a: str, name_b: str) -> str:
    if comp_count == 0:
        return "No compromise dynamics — neither of you is being asked to half-complete the other's channel."
    return f"{comp_count} compromise dynamic{'s' if comp_count != 1 else ''} between you.  Where one of you has a complete channel and the other has only half, pressure builds for the half-carrying side to bridge what isn't naturally theirs.  Knowing the channel removes most of the pressure."


def _dominance_narrative(dom_a: int, dom_b: int, name_a: str, name_b: str) -> str:
    if not (dom_a or dom_b):
        return "No dominance channels — neither of your energies takes over the field by default."
    parts: List[str] = []
    if dom_a:
        parts.append(f"{dom_a} of {name_a}'s defined channels operate as dominance in the field — {name_b} doesn't have these gates at all and experiences {name_a}'s energy in these channels as the room's energy.")
    if dom_b:
        parts.append(f"{dom_b} of {name_b}'s defined channels operate as dominance — {name_a} doesn't carry these gates and experiences {name_b}'s energy in those channels as the field itself.")
    return "  ".join(parts)


# ─────────────────────────────────────────────────────────────────────
# Field Overview / Growth Edge / Energy Weather
# ─────────────────────────────────────────────────────────────────────
def _field_overview(type_a: str, type_b: str, def_a: str, def_b: str,
                    name_a: str, name_b: str) -> str:
    cell = TYPE_PAIR_AURA.get(frozenset({type_a, type_b})) or \
        "Two distinct aura mechanics share the same field.  Each begins influencing the other before either speaks."
    return cell.format(name_a=name_a, name_b=name_b)


def _growth_edge(type_a: str, type_b: str, auth_a: str, auth_b: str,
                 name_a: str, name_b: str) -> str:
    edges: List[str] = []
    if "Projector" in (type_a, type_b) and "Generator" in (type_a, type_b):
        edges.append(
            "The Projector side learns to wait for the invitation that the Generator side's response provides; "
            "the Generator side learns that the Projector's recognition is real energy, not flattery."
        )
    if "Manifestor" in (type_a, type_b):
        edges.append(
            "The Manifestor side learns that informing is not asking permission — it's lubrication for impact.  "
            "The other side learns that the Manifestor's closed aura isn't withdrawal."
        )
    if "Reflector" in (type_a, type_b):
        edges.append(
            "The Reflector side learns to use this relationship as a barometer rather than as identity.  "
            "The other side learns that their state IS the room — and what they bring is what gets amplified."
        )
    if "Emotional" in (auth_a, auth_b):
        edges.append(
            "Both of you learn that emotional clarity is a 'when', not a 'what' — patience with the wave is the whole skill."
        )
    return "  ".join(edges[:2]) if edges else (
        "Each of you learns the other's pacing.  The growth isn't behavioural — it's the slow rewiring of expectation about how decisions happen."
    )


def _energy_weather(type_a: str, type_b: str,
                    def_a: str, def_b: str) -> str:
    # Single descriptor based on type pair
    pair = frozenset({type_a, type_b})
    if pair == frozenset({"Manifestor", "Manifestor"}): return "High activation, high collision risk.  This is a fast-moving, sometimes electric field."
    if pair == frozenset({"Generator", "Generator"}):    return "Steady, sustainable.  Quiet stabilising energy that holds long-term form."
    if pair == frozenset({"Projector", "Projector"}):    return "Reflective and pressurised at once.  Lots of seeing; sustainable in cycles, not continuously."
    if pair == frozenset({"Reflector", "Reflector"}):    return "Fluid and lunar.  The field changes character with the location and the moon."
    if "Reflector" in pair:                              return "Sensitive and transformative.  The Reflector takes the temperature of everything, including the relationship itself."
    if "Manifestor" in pair and "Generator" in pair:     return "Initiating energy meeting response — high productivity when the rhythm aligns, high friction when it doesn't."
    if "Projector" in pair and "Generator" in pair:      return "Naturally symbiotic.  Energy and recognition flow back and forth easily when invitation is honoured."
    if "Projector" in pair and "Manifestor" in pair:     return "Seen-and-moving.  The Projector reads while the Manifestor moves — needs explicit informing and explicit invitation."
    return "Mixed-rhythm field.  Pace varies by domain and by week."


# ─────────────────────────────────────────────────────────────────────
# Decision dynamics — small helper
# ─────────────────────────────────────────────────────────────────────
def _decision_dynamics(auth_a: str, auth_b: str, name_a: str, name_b: str) -> str:
    cell = AUTHORITY_PAIR.get(frozenset({auth_a, auth_b}))
    if cell:
        return cell.format(name_a=name_a, name_b=name_b)
    return f"{name_a}'s {auth_a} authority and {name_b}'s {auth_b} authority operate on different timescales.  Whoever's authority is slower sets the cadence for shared decisions."


# ─────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────
def compute_hd_relationship_field(
    chart_a: Dict[str, Any],
    chart_b: Dict[str, Any],
    name_a: str = "You",
    name_b: str = "them",
) -> Optional[Dict[str, Any]]:
    """Compute the Phase-3 HD field_v3 + diagnostics enrichment.

    Returns None when either chart lacks the minimum fields needed
    (type + authority).  Output is intended to be merged INTO the
    existing `signals.human_design` dict — no keys collide.
    """
    hd_a = (chart_a or {}).get("human_design") or {}
    hd_b = (chart_b or {}).get("human_design") or {}
    type_a, type_b = hd_a.get("type", ""), hd_b.get("type", "")
    auth_a, auth_b = hd_a.get("authority", ""), hd_b.get("authority", "")
    if not type_a or not type_b or not auth_a or not auth_b:
        return None

    prof_a, prof_b = hd_a.get("profile", ""), hd_b.get("profile", "")
    def_a, def_b = hd_a.get("definition", ""), hd_b.get("definition", "")
    defined_a   = set(hd_a.get("defined_centers")   or [])
    defined_b   = set(hd_b.get("defined_centers")   or [])
    undefined_a = set(hd_a.get("undefined_centers") or [])
    undefined_b = set(hd_b.get("undefined_centers") or [])
    active_a    = set(int(g) for g in (hd_a.get("active_gates") or []) if isinstance(g, (int, str)))
    active_b    = set(int(g) for g in (hd_b.get("active_gates") or []) if isinstance(g, (int, str)))
    chans_a     = hd_a.get("defined_channels") or []
    chans_b     = hd_b.get("defined_channels") or []

    # Channel classification
    classified = _classify_channels(active_a, active_b)
    em_pairs    = classified["electromagnetic"]
    comp_pairs  = classified["compromise"]
    dom_entries = classified["dominance"]
    dom_a = sum(1 for e in dom_entries if e[-1] == "a")
    dom_b = sum(1 for e in dom_entries if e[-1] == "b")
    comp_pairs_pairs = classified["companion"]

    # Center conditioning
    center_lines = _centre_conditioning_lines(
        defined_a, defined_b, undefined_a, undefined_b, name_a, name_b,
    )
    both_lines = _both_centers_lines(defined_a, defined_b, undefined_a, undefined_b)
    conditioning_lines = (center_lines + both_lines)[:3]

    # Build the field_v3 dict
    field_v3 = {
        "energy_signature": _energy_signature(type_a, type_b),
        "field_overview":   _field_overview(type_a, type_b, def_a, def_b, name_a, name_b),
        "aura_dynamics":    TYPE_PAIR_AURA.get(frozenset({type_a, type_b}),
            f"{type_a} aura meets {type_b} aura — two different mechanics sharing the field.").format(name_a=name_a, name_b=name_b),
        "decision_dynamics": _decision_dynamics(auth_a, auth_b, name_a, name_b),
        "centre_conditioning": conditioning_lines,
        "electromagnetic_gifts": _electromagnetic_narrative(len(em_pairs), name_a, name_b),
        "compromise_dynamics":   _compromise_narrative(len(comp_pairs), name_a, name_b),
        "dominance_dynamics":    _dominance_narrative(dom_a, dom_b, name_a, name_b),
        "friction_patterns":     _friction_patterns(type_a, type_b, auth_a, auth_b, def_a, def_b),
        "repair_pathway":        _repair_pathway(type_a, type_b, auth_a, auth_b, undefined_a, undefined_b),
        "growth_edge":           _growth_edge(type_a, type_b, auth_a, auth_b, name_a, name_b),
        "energy_weather":        _energy_weather(type_a, type_b, def_a, def_b),
    }

    diagnostics = {
        "type_pair":            f"{type_a} × {type_b}",
        "authority_pair":       f"{auth_a} × {auth_b}",
        "profile_pair":         f"{prof_a} × {prof_b}",
        "definition_pair":      f"{def_a} × {def_b}",
        "electromagnetic_count": len(em_pairs),
        "electromagnetic_pairs": em_pairs,
        "compromise_count":     len(comp_pairs),
        "compromise_pairs":     comp_pairs,
        "dominance_count":      dom_a + dom_b,
        "dominance_a_count":    dom_a,
        "dominance_b_count":    dom_b,
        "companion_count":      len(comp_pairs_pairs),
        "channel_count_a":      len(chans_a),
        "channel_count_b":      len(chans_b),
        "defined_centers_a":    sorted(defined_a),
        "defined_centers_b":    sorted(defined_b),
        "center_conditioning":  {
            "a_amplifies_b_via": sorted([c for c in defined_a if c in undefined_b]),
            "b_amplifies_a_via": sorted([c for c in defined_b if c in undefined_a]),
            "both_defined":      sorted(defined_a & defined_b),
            "both_open":         sorted(undefined_a & undefined_b),
        },
        "engine_version":       ENGINE_VERSION,
    }

    return {"field_v3": field_v3, "diagnostics": diagnostics}
