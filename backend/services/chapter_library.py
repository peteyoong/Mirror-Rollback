"""
Chapter Library — Timeline V2 / Phase Architecture
===================================================
Build marker: phase-architecture-v1a

Starter library of existential life chapters that govern a user's
3-9 month phase. Each chapter is authored in Mirror tone (existential,
behavioral, NOT categorical "communication is activated"). Astrology
mechanics live UNDER each chapter as `signal_rules` and are surfaced
in the proof drawer only — never in the visible title.

TONE GUARDRAILS (load-bearing — every chapter's visible copy is
expected to obey these; reviewer agent should flag violations):
  * No Jyotish/Vedic terminology.
  * No deterministic-fate language ("you must", "you should",
    "the universe is making you").
  * No house labels in visible primary copy ("3rd house", "7th house").
  * No generic topic titles ("communication", "relationships",
    "security", "career").
  * No "lens" name in the visible title.
  * Identity-mechanics over identity-traits. Behavior, not essence.

Each chapter ships with FOUR copy slots:
  - title              -> visible primary line (existential)
  - subtitle           -> visible secondary line (1 sentence)
  - body_visible       -> 2-4 sentence recognition paragraph the user reads
  - proof_summary      -> single sentence that lives inside the proof drawer
                          explaining *why* this chapter is the active one
  - proof_internal_topics -> internal categorical reference (NEVER user-facing)

And a single FALLBACK_CHAPTER is provided so the governor can always
return something coherent if scoring fails.

The library is intentionally finite. Phase 1A ships 26 starter chapters;
only "The Cost Of Keeping The Peace" has full signal_rules wired up.
Other chapters have skeleton signal_rules so the architecture validates
end-to-end without claiming false specificity.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


# ---------------------------------------------------------------------------
# Arc taxonomy — narrative archetype of the chapter
# ---------------------------------------------------------------------------
ARC_TYPES = (
    "ending",        # something is closing; cost-of-staying rising
    "threshold",     # crossing into something not yet named
    "identity",      # reorganising who you are at a foundational level
    "integration",   # holding what was already learned, not building new
    "expansion",     # taking on more weight than the prior version of you
    "pressure",      # friction between old structure and new pressure
    "closure",       # active letting-go of a chapter you stayed in too long
)


class SignalRule(TypedDict, total=False):
    """A single deterministic signal that adds to a chapter's score."""
    description: str
    weight: float


class Chapter(TypedDict, total=False):
    chapter_id:           str
    title:                str
    subtitle:             str
    arc_type:             str
    body_visible:         str
    proof_summary:        str
    proof_internal_topics: List[str]   # never user-facing
    signal_rules:         Dict[str, SignalRule]
    # `scored_by` is filled in at runtime by phase_governor; not authored.


# ---------------------------------------------------------------------------
# Fully-authored chapter: "The Cost Of Keeping The Peace"
# ---------------------------------------------------------------------------
COST_OF_KEEPING_THE_PEACE: Chapter = {
    "chapter_id":   "cost_of_keeping_the_peace",
    "title":        "The Cost Of Keeping The Peace",
    "subtitle":     "Where absorbing has started to cost more than naming.",
    "arc_type":     "ending",
    # v2 archetype-differentiation tag — used by the diversity guard.
    # "emotional_permeability" captures the metabolism: pressure
    # processed relationally/emotionally rather than cognitively.
    "existential_family": "emotional_permeability",
    "body_visible": (
        "You're inside a chapter where keeping things smooth has slowly "
        "become more expensive than saying the thing out loud. The "
        "absorbing you used to do without noticing is starting to take "
        "something from you each time. Clarity isn't optional anymore — "
        "it's just delayed."
    ),
    "proof_summary": (
        "Multiple structural pressures are converging on the same edge: "
        "the seam where holding peace through absorption has tipped past "
        "neutral cost."
    ),
    "proof_internal_topics": [
        "communication", "home_family", "partnership_dynamics",
        "emotional_containment", "boundary_pressure",
    ],
    # Each rule is matched by phase_governor.score_chapter().
    # The actual matching logic lives there; this dict just declares
    # which signal IDs feed this chapter and how much they're worth.
    "signal_rules": {
        # HD wiring that makes "absorb the room before deciding" the default
        "hd_open_solar_plexus":             {"weight": 1.2, "description": "Open Solar Plexus — emotional permeability baseline"},
        "hd_open_throat":                   {"weight": 0.8, "description": "Open Throat — containment of what wants to be said"},
        "hd_channel_22":                    {"weight": 0.4, "description": "Gate 22 active — grace / receive the room"},
        "hd_channel_49":                    {"weight": 0.4, "description": "Gate 49 active — tribal-emotional radar"},
        # Astro structural weight on the relational / containment axis
        "astro_saturn_house_3_4_7":         {"weight": 1.4, "description": "Saturn in 3rd/4th/7th — duty/weight on communication, home, or partnership"},
        "astro_saturn_hard_to_moon":        {"weight": 1.2, "description": "Saturn hard aspect Moon — emotional containment becoming costly"},
        "astro_saturn_hard_to_venus":       {"weight": 1.0, "description": "Saturn hard aspect Venus — relational duty pressure"},
        "astro_saturn_hard_to_mercury":     {"weight": 0.8, "description": "Saturn hard aspect Mercury — held/measured communication"},
        "astro_mars_venus_hard":            {"weight": 0.7, "description": "Mars-Venus hard aspect — assertion / harmony tension"},
        "astro_12th_house_moon":            {"weight": 0.6, "description": "Moon in 12th — emotional life running underneath"},
        # Current pressure (when timeline cache exposes year-level themes)
        "timeline_theme_relational":        {"weight": 0.9, "description": "Yearly timeline foregrounds relational/communication pressure"},
        "timeline_theme_boundary":          {"weight": 0.9, "description": "Yearly timeline foregrounds boundary / containment pressure"},
    },
}


# ---------------------------------------------------------------------------
# Starter chapter library (the other 25, scaffolded)
# ---------------------------------------------------------------------------
# Each non-primary chapter has the FULL copy slots filled (so the UI can
# render them if they win), plus a small initial signal_rules block so
# the deterministic shortlist has something to score against.
#
# These scaffolds are intentionally narrower than the primary one — they
# will be deepened chapter-by-chapter as we ship them end-to-end.

def _chapter(
    *,
    chapter_id: str,
    title: str,
    subtitle: str,
    arc_type: str,
    body_visible: str,
    proof_summary: str,
    proof_topics: List[str],
    signal_rules: Optional[Dict[str, SignalRule]] = None,
    existential_family: Optional[str] = None,
) -> Chapter:
    out: Chapter = {
        "chapter_id":             chapter_id,
        "title":                  title,
        "subtitle":               subtitle,
        "arc_type":               arc_type,
        "body_visible":           body_visible,
        "proof_summary":          proof_summary,
        "proof_internal_topics":  proof_topics,
        "signal_rules":           signal_rules or {},
    }
    if existential_family is not None:
        out["existential_family"] = existential_family
    return out


_LIBRARY: List[Chapter] = [
    COST_OF_KEEPING_THE_PEACE,
    # ---------------------------------------------------------------------
    # ARCHETYPE DIFFERENTIATION V1 — cognitive recursion chapters.
    # Score against DERIVED SYNTHESIS signals (not raw traits), so users
    # who share a defined Ajna with Pete but lack Mercury-Saturn don't
    # incorrectly land in this family.
    # ---------------------------------------------------------------------
    {
        "chapter_id": "certainty_that_never_arrives",
        "title":      "The Certainty That Never Arrives",
        "subtitle":   "Waiting for an inner ground that doesn't come in the form expected.",
        "arc_type":   "threshold",
        "body_visible": (
            "You're inside a chapter where you've been waiting for a kind of "
            "internal certainty before you move. The version of that "
            "certainty you've been waiting for may not exist in the form you "
            "expect. Refinement has quietly become a way of staying — not "
            "a way of getting closer to ready."
        ),
        "proof_summary": (
            "Multiple structures point to the same loop: thinking is doing "
            "the work that movement was meant to do."
        ),
        "proof_internal_topics": [
            "cognitive_recursion", "certainty_seeking",
            "conceptual_stabilization", "ajna_fixation",
        ],
        # Existential family — used by the v2 shortlist diversity guard.
        "existential_family": "cognitive_recursion",
        # Signal rules score AGAINST derived synthesis signals (not raw
        # traits) so users who share Ajna-defined wiring but lack Mercury-
        # Saturn don't fall into this chapter.
        # NOTE: weights here are intentionally HIGH on the primary derived
        # signals — these signals require the discriminator combination
        # (Ajna + MercSat + G4/G63) to fire, so high weights are SAFE and
        # necessary to overcome emotional_permeability's broader shared-
        # trait scoring stack when both families' signatures co-occur in
        # the same chart (e.g. mental-overcontainment users).
        "signal_rules": {
            "derived_certainty_loop":               {"weight": 2.5, "description": "Defined Ajna + Gate 4/63 + Mercury-Saturn = certainty-seeking loop"},
            "derived_recursive_questioning":        {"weight": 1.2, "description": "G63 + Ajna + Mercury-Saturn = each answer triggers a new question"},
            "derived_stabilization_through_analysis":{"weight": 1.2, "description": "Ajna + LP 7 + Mercury-Saturn = analysis as ground"},
            "derived_proof_before_action":          {"weight": 1.0, "description": "Ajna + Mercury-Saturn + structural anchor = proof gates action"},
            "derived_mental_overcontainment":       {"weight": 1.2, "description": "Ajna + Mercury-Saturn + Open Throat = thinking can't reach speech"},
            "derived_inability_to_conclude_safely": {"weight": 0.6, "description": "Ajna + Mercury-Neptune or G63 = closure feels unsafe"},
            "num_life_path_7":                      {"weight": 0.4, "description": "Life Path 7 — introspective verification path"},
        },
    },
    {
        "chapter_id": "question_stops_protecting_you",
        "title":      "When The Question Stops Protecting You",
        "subtitle":   "Continued questioning has crossed from safety into delay.",
        "arc_type":   "threshold",
        "body_visible": (
            "You're in a chapter where the questions that once kept you from "
            "moving prematurely have started keeping you from moving at all. "
            "The refinement that used to be preparation has quietly become "
            "the new thing you're hiding inside. Conceptual readiness was "
            "never going to be the moment that releases you — and at this "
            "point you've gathered enough."
        ),
        "proof_summary": (
            "The cognitive machinery built to protect you from premature "
            "movement is now functioning as the main brake on any movement."
        ),
        "proof_internal_topics": [
            "endless_refinement", "premature_movement_fear",
            "preparation_as_avoidance", "identity_in_being_ready",
        ],
        "existential_family": "cognitive_recursion",
        "signal_rules": {
            "derived_recursive_questioning":        {"weight": 1.5, "description": "Each answer triggers a new question — the protection loop"},
            "derived_inability_to_conclude_safely": {"weight": 1.5, "description": "Closure can't yet feel safe — refinement persists"},
            "derived_mental_overcontainment":       {"weight": 2.5, "description": "Mental capacity exceeds the system's ability to release it — overcontainment signature"},
            "derived_certainty_loop":               {"weight": 2.0, "description": "Underlying certainty-seeking loop (boosted so cognitive route dominates when present)"},
            "derived_proof_before_action":          {"weight": 1.0, "description": "Proof gates action — the gate has stopped opening"},
            "astro_mutable_mental_overprocessing":  {"weight": 0.4, "description": "Multiple mutable personal planets — endless re-evaluation"},
        },
    },
    _chapter(
        chapter_id="choosing_what_remains",
        title="Choosing What Remains",
        subtitle="The keeping is no longer automatic.",
        arc_type="ending",
        body_visible=(
            "You're inside a chapter where everything that used to stay "
            "by default now has to be actively chosen. What survives this "
            "stretch is what you decide to keep — not what stays because "
            "you didn't move it."
        ),
        proof_summary="A pruning phase: external structures loosening, choice being returned.",
        proof_topics=["pruning", "identity_clarification", "relationship_audit"],
        signal_rules={
            "astro_saturn_return_window":   {"weight": 1.0, "description": "Saturn return window"},
            "astro_pluto_hard_aspect":      {"weight": 0.8, "description": "Pluto transit hard to personal planet"},
        },
    ),
    _chapter(
        chapter_id="end_of_absorbing_everything",
        title="The End Of Absorbing Everything",
        subtitle="The cost of permeability is becoming visible.",
        arc_type="ending",
        existential_family="emotional_permeability",
        body_visible=(
            "You're moving out of a long stretch of taking in more than "
            "was yours. What was once invisible is now showing up as "
            "weight. The system is signalling that the way you carried "
            "the room is no longer sustainable."
        ),
        proof_summary="Permeability mechanics colliding with rising structural weight.",
        proof_topics=["permeability_fatigue", "boundary_repair"],
        signal_rules={
            "hd_open_solar_plexus":          {"weight": 1.0},
            "astro_saturn_hard_to_moon":     {"weight": 1.0},
        },
    ),
    _chapter(
        chapter_id="collapse_of_old_strategy",
        title="The Collapse Of The Old Strategy",
        subtitle="What used to work is no longer holding.",
        arc_type="ending",
        body_visible=(
            "The strategy that used to get you through is quietly losing "
            "traction. Not dramatically — just consistently. This is the "
            "chapter where the old answer stops being the right one, even "
            "though nothing has officially changed."
        ),
        proof_summary="Habituated coping pattern at the end of its useful life.",
        proof_topics=["coping_breakdown", "strategy_obsolescence"],
        signal_rules={
            "astro_saturn_return_window":    {"weight": 0.9},
            "astro_uranus_hard_aspect":      {"weight": 0.8},
        },
    ),
    _chapter(
        chapter_id="when_momentum_stops_working",
        title="When Momentum Stops Working",
        subtitle="Movement is no longer the same as progress.",
        arc_type="pressure",
        existential_family="achievement_axis",
        body_visible=(
            "You're in a chapter where doing more doesn't move the thing "
            "forward anymore. The system that used to convert effort "
            "into outcomes is asking for a different kind of attention — "
            "not more energy."
        ),
        proof_summary="Effort-output curve has flattened; integration over acceleration.",
        proof_topics=["productivity_plateau", "rest_resistance"],
        signal_rules={
            # Achievement-axis users metabolize pressure through momentum.
            # The original Mars-Saturn anchor catches the most explicit
            # form (output-pressure friction). Saturn-Sun + Saturn-angular
            # catch the broader authority-through-pressure variant where
            # identity itself has become structurally weight-bearing.
            "astro_saturn_hard_to_mars":     {"weight": 1.1, "description": "Mars-Saturn — direct output pressure"},
            "astro_saturn_hard_to_sun":      {"weight": 0.9, "description": "Saturn-Sun — identity becoming structurally weight-bearing"},
            "astro_saturn_angular":          {"weight": 0.6, "description": "Saturn on an angle — pressure made structural"},
            "astro_10th_house_emphasis":     {"weight": 0.7, "description": "10th-house stellium — public/output identity"},
            "hd_defined_heart":              {"weight": 0.5, "description": "Defined Heart — willpower channel intact"},
        },
    ),
    _chapter(
        chapter_id="becoming_more_visible",
        title="Becoming More Visible Than Comfortable",
        subtitle="The exposure is not optional.",
        arc_type="threshold",
        body_visible=(
            "You're entering a stretch where you're being seen more than "
            "you've chosen to be. What used to stay in the background is "
            "moving forward — not because you pushed it, but because the "
            "container around it dissolved."
        ),
        proof_summary="Visibility pressure exceeding current comfort baseline.",
        proof_topics=["public_role", "exposure_threshold"],
        signal_rules={
            "astro_transit_through_mc":      {"weight": 1.0},
            "astro_10th_house_emphasis":     {"weight": 0.6},
        },
    ),
    _chapter(
        chapter_id="return_of_meaning",
        title="The Return Of Meaning",
        subtitle="Something that mattered is reappearing.",
        arc_type="threshold",
        body_visible=(
            "A thread that went quiet is asking to be picked back up. "
            "You'll notice it as a small pull toward something you "
            "thought you'd left behind. The chapter is not nostalgic — "
            "it's a recovery of something that wasn't finished."
        ),
        proof_summary="A recurrence signal: prior arc resurfacing for completion.",
        proof_topics=["recurrence", "incomplete_arc"],
        signal_rules={
            "astro_jupiter_return_zone":     {"weight": 0.9},
        },
    ),
    _chapter(
        chapter_id="stepping_into_authority",
        title="Stepping Into Authority Without Permission",
        subtitle="The waiting period is closing.",
        arc_type="threshold",
        body_visible=(
            "You're inside a chapter where the part of you that's been "
            "waiting for an external 'go' is being asked to move without "
            "it. Permission is no longer the gating factor — it's "
            "becoming the bottleneck."
        ),
        proof_summary="Outer permission lag colliding with inner readiness.",
        proof_topics=["self_authority", "permission_pattern"],
        signal_rules={
            "astro_saturn_hard_to_sun":      {"weight": 0.8},
            "hd_projector_or_authority":     {"weight": 0.6},
        },
    ),
    _chapter(
        chapter_id="naming_what_was_avoided",
        title="Naming What's Been Avoided",
        subtitle="The avoidance is now louder than the thing itself.",
        arc_type="threshold",
        body_visible=(
            "There's a single thing you've been managing around for a "
            "long time. The chapter you're in is gradually making it "
            "harder to keep doing that. The weight of the avoidance is "
            "now exceeding the weight of the conversation."
        ),
        proof_summary="Long-standing avoidance topic approaching cost inversion.",
        proof_topics=["avoidance_cost_inversion"],
        signal_rules={
            "astro_pluto_hard_aspect":       {"weight": 1.0},
            "hd_open_throat":                {"weight": 0.6},
        },
    ),
    _chapter(
        chapter_id="when_the_question_changes",
        title="When The Question Changes",
        subtitle="The frame you've been using is dissolving.",
        arc_type="threshold",
        body_visible=(
            "You're moving past the version of the problem you've been "
            "trying to solve. The chapter isn't asking for a better "
            "answer — it's giving you a different question."
        ),
        proof_summary="Schema-level reframe; the prior solution-space is closing.",
        proof_topics=["meaning_reframe", "schema_shift"],
        signal_rules={
            "astro_neptune_hard_aspect":     {"weight": 0.8},
        },
    ),
    _chapter(
        chapter_id="rebuilding_authority",
        title="Rebuilding Authority",
        subtitle="The center of decision is moving back inward.",
        arc_type="identity",
        body_visible=(
            "You're in a chapter where outsourcing the decision is "
            "becoming impossible. The choices have to be made from "
            "the inside, even when there's no external structure left "
            "to lean on."
        ),
        proof_summary="Inner authority being reseated after a period of external lean.",
        proof_topics=["self_authority", "decision_locus"],
        signal_rules={
            "astro_saturn_return_window":    {"weight": 1.2},
            "hd_defined_authority_center":   {"weight": 0.6},
        },
    ),
    _chapter(
        chapter_id="letting_self_be_reorganized",
        title="Letting The Self Be Reorganized",
        subtitle="The shape of who you are is moving.",
        arc_type="identity",
        body_visible=(
            "The version of you that worked last year is being asked to "
            "make room for the version that's coming. This chapter is "
            "less about choosing the new and more about not blocking the "
            "reorganization that's already started."
        ),
        proof_summary="Identity restructuring under outer-planet pressure.",
        proof_topics=["identity_restructure"],
        signal_rules={
            "astro_pluto_hard_aspect":       {"weight": 1.0},
            "astro_uranus_hard_aspect":      {"weight": 0.8},
        },
    ),
    _chapter(
        chapter_id="outgrowing_earlier_version",
        title="Outgrowing The Earlier Version",
        subtitle="The earlier fit no longer fits.",
        arc_type="identity",
        body_visible=(
            "The role, relationship, or rhythm that fit a year or two "
            "ago doesn't quite hold you anymore. Nothing is wrong with "
            "what it was — the chapter is just larger now."
        ),
        proof_summary="Container outgrown; expansion exceeding current frame.",
        proof_topics=["role_outgrowth"],
        signal_rules={"astro_jupiter_transit":      {"weight": 0.8}},
    ),
    _chapter(
        chapter_id="coming_back_into_your_weight",
        title="Coming Back Into Your Own Weight",
        subtitle="The contraction is releasing.",
        arc_type="identity",
        body_visible=(
            "You're in a chapter where the parts of you that got smaller "
            "to stay agreeable, useful or available are quietly taking "
            "their full shape back. It's not a comeback — it's a return "
            "to the room you actually take up."
        ),
        proof_summary="Compression phase ending; full presence returning.",
        proof_topics=["self_expansion", "compression_release"],
        signal_rules={"astro_saturn_off_personal_planet":  {"weight": 0.8}},
    ),
    _chapter(
        chapter_id="integration_phase",
        title="Integrating What This Year Already Taught",
        subtitle="The work now is to keep it.",
        arc_type="integration",
        body_visible=(
            "The hard part of the year is behind you, but the chapter "
            "isn't over. This stretch is for keeping what was learned "
            "without rushing to apply it. Integration is its own work."
        ),
        proof_summary="Post-pressure integration window; consolidation over acquisition.",
        proof_topics=["consolidation"],
        signal_rules={"astro_post_saturn_aspect":    {"weight": 0.7}},
    ),
    _chapter(
        chapter_id="quieter_phase_after_break",
        title="The Quieter Phase After The Break",
        subtitle="The volume is genuinely lower.",
        arc_type="integration",
        body_visible=(
            "After a more visible disruption, you're inside a quieter "
            "chapter. The temptation will be to fill it. The chapter is "
            "asking you not to."
        ),
        proof_summary="Post-rupture quiet; refilling impulse should be paused.",
        proof_topics=["post_rupture_quiet"],
        signal_rules={"astro_after_eclipse_window":  {"weight": 0.7}},
    ),
    _chapter(
        chapter_id="living_with_what_you_know",
        title="Living With What You Now Know",
        subtitle="The information has already arrived.",
        arc_type="integration",
        body_visible=(
            "Something became clear earlier this year that can't be "
            "un-known. This chapter is the slow work of behaving "
            "consistently with what you already see."
        ),
        proof_summary="Knowledge-behavior gap is the active edge.",
        proof_topics=["knowledge_behavior_gap"],
        signal_rules={"astro_mercury_clarity_window": {"weight": 0.5}},
    ),
    _chapter(
        chapter_id="returning_to_center",
        title="Returning To Center",
        subtitle="The orbit is tightening.",
        arc_type="integration",
        body_visible=(
            "You're moving back inward after a stretch of being pulled "
            "outward. The chapter favours the parts of your life closest "
            "to who you are when no one is watching."
        ),
        proof_summary="Inward-orbit phase; periphery losing pull.",
        proof_topics=["inward_orbit"],
        signal_rules={"astro_4th_house_emphasis":    {"weight": 0.7}},
    ),
    _chapter(
        chapter_id="cost_of_expansion",
        title="The Cost Of Expansion",
        subtitle="More is asking for more.",
        arc_type="expansion",
        body_visible=(
            "Something has been growing — visibility, responsibility, "
            "scale, reach. This chapter is the bill that comes with it. "
            "Not punitive — just the structural cost of holding a larger "
            "shape."
        ),
        proof_summary="Expansion pressure outpacing current support architecture.",
        proof_topics=["expansion_cost"],
        signal_rules={"astro_jupiter_transit":       {"weight": 1.0}},
    ),
    _chapter(
        chapter_id="holding_more_than_used_to",
        title="Holding More Than You Used To",
        subtitle="The container is bigger now.",
        arc_type="expansion",
        body_visible=(
            "You're carrying more weight than the version of you from a "
            "year ago could have. The chapter is teaching the muscles "
            "for it, not asking you to enjoy it."
        ),
        proof_summary="Capacity expansion outpacing comfort baseline.",
        proof_topics=["capacity_expansion"],
        signal_rules={"astro_saturn_strong_transit": {"weight": 0.8}},
    ),
    _chapter(
        chapter_id="building_past_safe_edge",
        title="Building Past The Safe Edge",
        subtitle="You're outside the calibrated zone.",
        arc_type="expansion",
        body_visible=(
            "Whatever you're building is now meaningfully beyond what "
            "you've previously stabilised. The chapter is asking for a "
            "different kind of attention — not more confidence."
        ),
        proof_summary="Operating outside the prior stable range.",
        proof_topics=["scale_threshold"],
        signal_rules={"astro_jupiter_to_natal":      {"weight": 0.8}},
    ),
    _chapter(
        chapter_id="friction_old_and_new",
        title="The Friction Between Old And New",
        subtitle="Two versions are sharing the same space.",
        arc_type="pressure",
        body_visible=(
            "An older way of operating and a newer one are running "
            "simultaneously inside you. The friction is structural, not "
            "personal. The chapter is the period where they cannot both "
            "win."
        ),
        proof_summary="Two operating models in active simultaneous use.",
        proof_topics=["model_collision"],
        signal_rules={"astro_uranus_saturn_tension": {"weight": 0.9}},
    ),
    _chapter(
        chapter_id="outside_catches_up_with_inside",
        title="When The Outside Catches Up With The Inside",
        subtitle="The visible is reorganising to match the felt.",
        arc_type="pressure",
        body_visible=(
            "Something you've felt internally for a while is starting "
            "to show up in your external life — relationships, work, "
            "calendar. The chapter is the alignment, even when the "
            "alignment is uncomfortable."
        ),
        proof_summary="Outer life reorganising to match interior shift.",
        proof_topics=["inner_outer_alignment"],
        signal_rules={"astro_pluto_to_angles":       {"weight": 0.9}},
    ),
    _chapter(
        chapter_id="holding_the_line",
        title="Holding The Line",
        subtitle="The boundary has to be paid for repeatedly.",
        arc_type="pressure",
        body_visible=(
            "You're in a chapter where a single boundary has to be held "
            "more than once. Not because it wasn't clear the first time, "
            "but because the field keeps testing whether you meant it."
        ),
        proof_summary="Boundary-maintenance phase, not boundary-creation phase.",
        proof_topics=["boundary_maintenance"],
        signal_rules={"astro_mars_recurring_pressure": {"weight": 0.7}},
    ),
    _chapter(
        chapter_id="closing_a_chapter_stayed_too_long",
        title="Closing A Chapter You Stayed In Too Long",
        subtitle="The exit has been delayed; it's still available.",
        arc_type="closure",
        body_visible=(
            "There's something you've been ready to leave for a while. "
            "The chapter you're in is the closing window — not in a "
            "dramatic sense, just in the sense that the exit is "
            "available and the cost of staying is no longer disguised."
        ),
        proof_summary="Delayed-closure window; cost of staying now visible.",
        proof_topics=["delayed_closure"],
        signal_rules={"astro_saturn_finishing_transit": {"weight": 1.0}},
    ),
    _chapter(
        chapter_id="releasing_what_stopped_belonging",
        title="Releasing What Stopped Belonging To You",
        subtitle="Some of what you carry isn't yours anymore.",
        arc_type="closure",
        body_visible=(
            "Some commitments, roles, relationships, or beliefs that used "
            "to belong to you have quietly stopped. This chapter is the "
            "process of recognising which ones — and putting them down "
            "without ceremony."
        ),
        proof_summary="Ownership audit: roles outgrown but still being carried.",
        proof_topics=["ownership_audit"],
        signal_rules={"astro_north_node_shift":      {"weight": 0.8}},
    ),
]


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------
FALLBACK_CHAPTER: Chapter = {
    "chapter_id":   "active_recalibration",
    "title":        "Inside A Quiet Recalibration",
    "subtitle":     "Nothing dramatic — but something is moving.",
    "arc_type":     "integration",
    "body_visible": (
        "You're in a stretch that doesn't have a single headline yet. "
        "Something is reorganising underneath your normal patterns, "
        "even if it hasn't broken through into the visible parts of "
        "your life. The chapter is asking for attention, not action."
    ),
    "proof_summary":         "No single dominant signal — diffuse repatterning.",
    "proof_internal_topics": ["diffuse_repatterning"],
    "signal_rules":          {},
}


# ---------------------------------------------------------------------------
# Public accessors
# ---------------------------------------------------------------------------
def get_library() -> List[Chapter]:
    """Return all authored chapters (does not include fallback)."""
    return list(_LIBRARY)


def get_chapter_by_id(chapter_id: str) -> Optional[Chapter]:
    for ch in _LIBRARY:
        if ch.get("chapter_id") == chapter_id:
            return ch
    if FALLBACK_CHAPTER.get("chapter_id") == chapter_id:
        return FALLBACK_CHAPTER
    return None


def get_fallback_chapter() -> Chapter:
    return FALLBACK_CHAPTER
