"""Shared Lens Content Contract V1
====================================================================

Canonical 7-layer envelope every lens deep-dive endpoint returns.

Build marker: lens-content-contract-v1
Project:      The Mirror (Emergent `/app` application)
Session:      The Mirror Session-2 — Shared Lens Content Contract
Docs:         /app/memory/the_mirror_audit_2026_07.md
              /app/memory/the_mirror_roadmap_2026_07.md

Design principles enforced by the schema:

  1. Recognition before advice
     — `at_a_glance.recognition_statement` is required; a lens cannot
       advise before it establishes what it recognises.

  2. Capacity / shadow / tension as distinct fields
     — Every component story has separate `capacity`, `distortion`
       and `productive_tension` fields; renderers cannot merge them
       accidentally.

  3. Calibrated language
     — Content strings are unopinionated by the schema; a linter
       (session-3+) will flag deterministic vocabulary at CI time.

  4. Evidence behind material claims
     — Every `MaterialClaim` MUST carry an `EvidenceRef` list.

  5. No forced cross-lens agreement
     — Lens envelopes are independent; a separate synthesis layer
       (Session-9) is the only place cross-lens claims may live.

  6. Missing information over false coherence
     — `Availability` enum: every content field is either
       `PRESENT`, `PARTIAL`, `UNAVAILABLE`.  Renderers MUST render the
       unavailable state explicitly instead of fabricating.

  7. No single dramatic interpretation dominates the master story
     — Core story has separate `capacity` / `shadow` / `central_tension`
       / `developmental_possibility` slots each requiring their own
       evidence; the enforcement lives in the tests, not the schema.

The schema is intentionally READ-ONLY at wire time.  Adapters produce
these envelopes from the existing lens payloads (never the other way).
"""
from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────
Availability = Literal["present", "partial", "unavailable"]

Confidence = Literal["high", "medium", "emerging", "unknown"]

ContentOrigin = Literal[
    "calculated",   # numeric / geometric derivation
    "assessed",     # user assessment response
    "observed",     # user-provided ground truth
    "inferred",     # deterministic mapping from calculated inputs
    "generated",    # LLM prose (must always carry evidence back-ref)
]

TimeScope = Literal["lifelong", "phase", "year", "season", "day", "now"]


# ─────────────────────────────────────────────────────────────────────
# Common building blocks
# ─────────────────────────────────────────────────────────────────────
class EvidenceRef(BaseModel):
    """A single evidence trace for one interpretive claim.  Every
    material narrative claim in every layer carries a list of these.
    """
    source_lens:     str                       # e.g. "human_design"
    calculation:     str                       # e.g. "field_v3.decision_dynamics"
    factors_used:    List[str] = Field(default_factory=list)
    derivation_rule: Optional[str]  = None     # e.g. "authority_pair=Emotional×Emotional"
    confidence:      Confidence = "unknown"
    origin:          ContentOrigin = "calculated"
    engine_version:  Optional[str]  = None
    computed_at:     Optional[str]  = None     # ISO UTC
    missing_or_disputed: Optional[List[str]] = None


class MaterialClaim(BaseModel):
    """Any interpretive sentence that MUST carry evidence."""
    text:       str
    evidence:   List[EvidenceRef] = Field(default_factory=list)
    origin:     ContentOrigin = "inferred"
    confidence: Confidence = "unknown"


class FactBadge(BaseModel):
    """Calculated fact chip (e.g. Type: Manifestor / Life Path: 11)."""
    label: str
    value: str
    source_calculation: Optional[str] = None
    origin: ContentOrigin = "calculated"


class MissingSlot(BaseModel):
    """Explicit unavailable state — replaces silent fabrication."""
    what:  str
    why:   str
    could_be_shown_if: Optional[str] = None
    availability: Availability = "unavailable"


# ─────────────────────────────────────────────────────────────────────
# 1. AT A GLANCE
# ─────────────────────────────────────────────────────────────────────
class AtAGlanceLayer(BaseModel):
    essential_facts:       List[FactBadge] = Field(default_factory=list)
    recognition_statement: str
    lens_can_claim:        List[str] = Field(default_factory=list)
    lens_cannot_claim:     List[str] = Field(default_factory=list)
    availability:          Availability = "present"


# ─────────────────────────────────────────────────────────────────────
# 2. STRUCTURE
# ─────────────────────────────────────────────────────────────────────
class StructureComponent(BaseModel):
    """One structural unit — e.g. a centre / gate / channel / planet /
    pillar / number / sphere / type indicator."""
    component_id:   str
    label:          str                       # user-facing canonical label
    value:          Optional[Any] = None      # calculated placement
    provenance:     Optional[EvidenceRef] = None
    availability:   Availability = "present"


class StructureLayer(BaseModel):
    components:      List[StructureComponent] = Field(default_factory=list)
    calculation_provenance: Optional[EvidenceRef] = None
    missing:         List[MissingSlot] = Field(default_factory=list)
    availability:    Availability = "present"


# ─────────────────────────────────────────────────────────────────────
# 3. CORE STORY  (schema enforces the 7 required slots)
# ─────────────────────────────────────────────────────────────────────
class CoreStoryLayer(BaseModel):
    essence:                    MaterialClaim
    capacity:                   MaterialClaim
    shadow_or_distortion:       MaterialClaim
    central_tension:            MaterialClaim
    developmental_possibility:  MaterialClaim
    practical_application:      MaterialClaim
    reflection_question:        MaterialClaim
    availability:               Availability = "present"


# ─────────────────────────────────────────────────────────────────────
# 4. COMPONENT STORIES  (one per structural component)
# ─────────────────────────────────────────────────────────────────────
class ComponentStory(BaseModel):
    component_id:            str
    component_type:          str          # "center" / "planet" / "gate" / "number" / ...
    calculated_value:        Optional[Any] = None
    what_it_represents:      MaterialClaim
    why_it_matters:          MaterialClaim
    connections:             List[str] = Field(default_factory=list)   # to other component_ids
    recognition:             MaterialClaim
    capacity:                MaterialClaim
    distortion:              MaterialClaim
    productive_tension:      Optional[MaterialClaim] = None
    what_helps:              MaterialClaim
    evidence:                List[EvidenceRef] = Field(default_factory=list)
    confidence:              Confidence = "unknown"
    availability:            Availability = "present"


class ComponentStoriesLayer(BaseModel):
    stories:      List[ComponentStory] = Field(default_factory=list)
    availability: Availability = "present"


# ─────────────────────────────────────────────────────────────────────
# 5. INTEGRATION
# ─────────────────────────────────────────────────────────────────────
class IntegrationLayer(BaseModel):
    how_they_operate_together: MaterialClaim
    complementary_qualities:   List[MaterialClaim] = Field(default_factory=list)
    contradictions:            List[MaterialClaim] = Field(default_factory=list)
    productive_tensions:       List[MaterialClaim] = Field(default_factory=list)
    unresolved:                List[MissingSlot]    = Field(default_factory=list)
    availability:              Availability = "present"


# ─────────────────────────────────────────────────────────────────────
# 6. EVIDENCE (aggregate — every interpretive layer's evidence rolled up)
# ─────────────────────────────────────────────────────────────────────
class EvidenceLayer(BaseModel):
    """Aggregated `Why Mirror is saying this` bundle.  This is a
    convenience view; individual claims retain their inline evidence."""
    all_refs:      List[EvidenceRef] = Field(default_factory=list)
    disputed:      List[str] = Field(default_factory=list)
    engine_versions: Dict[str, str] = Field(default_factory=dict)
    availability:  Availability = "present"


# ─────────────────────────────────────────────────────────────────────
# 7. TODAY / TIMING
# ─────────────────────────────────────────────────────────────────────
class TimingWindow(BaseModel):
    starts_at:  Optional[str] = None
    ends_at:    Optional[str] = None
    scope:      TimeScope = "day"


class TimingSignal(BaseModel):
    """One currently-active timing factor with the natal structure it
    touches.  Generic daily prose is disallowed by convention — every
    signal must be traceable to a calculated timing factor."""
    current_factor:       str                        # e.g. "Saturn transit"
    structural_target:    str                        # e.g. "natal Venus in 7H"
    interaction:          str                        # e.g. "conjunction 0.4°"
    window:               TimingWindow
    interpretation:       MaterialClaim
    confidence:           Confidence = "unknown"
    evidence:             List[EvidenceRef] = Field(default_factory=list)


class TodayTimingLayer(BaseModel):
    signals:       List[TimingSignal] = Field(default_factory=list)
    missing:       List[MissingSlot]   = Field(default_factory=list)
    availability:  Availability = "present"


# ─────────────────────────────────────────────────────────────────────
# Envelope — every lens deep-dive endpoint returns this shape
# ─────────────────────────────────────────────────────────────────────
class LensEnvelope(BaseModel):
    lens:                    str                # "human_design" / "astrology" / "numerology" / "bazi" / "enneagram" / "gene_keys"
    envelope_version:        str = "lens-content-contract-v1"
    engine_version:          Optional[str] = None
    computed_at:             Optional[str] = None

    at_a_glance:             AtAGlanceLayer
    structure:               StructureLayer
    core_story:              CoreStoryLayer
    component_stories:       ComponentStoriesLayer
    integration:             IntegrationLayer
    evidence:                EvidenceLayer
    today_timing:            TodayTimingLayer

    # Progressive-disclosure hint the FE uses to decide default fold state.
    progressive_disclosure_order: List[str] = Field(
        default_factory=lambda: [
            "at_a_glance", "structure", "core_story",
            "component_stories", "integration", "evidence", "today_timing",
        ]
    )

    # ── Governance guards ────────────────────────────────────────────
    def validate_governance(self) -> List[str]:
        """Return a list of governance-violation strings; empty when
        the envelope satisfies all product-level rules.  Tests use this
        to enforce the CONTENT GOVERNANCE requirements from the spec."""
        problems: List[str] = []

        # Every MaterialClaim must have >= 1 EvidenceRef unless the
        # containing layer's availability is 'unavailable'.
        def _check_claim(loc: str, claim: MaterialClaim):
            if not claim.text or not claim.text.strip():
                problems.append(f"{loc}: empty text")
                return
            if not claim.evidence:
                problems.append(f"{loc}: no evidence for material claim")

        if self.core_story.availability == "present":
            _check_claim("core_story.essence", self.core_story.essence)
            _check_claim("core_story.capacity", self.core_story.capacity)
            _check_claim("core_story.shadow_or_distortion", self.core_story.shadow_or_distortion)
            _check_claim("core_story.central_tension", self.core_story.central_tension)
            _check_claim("core_story.developmental_possibility", self.core_story.developmental_possibility)
            _check_claim("core_story.practical_application", self.core_story.practical_application)
            # reflection_question is a claim but the evidence bar is lower
            if not self.core_story.reflection_question.text:
                problems.append("core_story.reflection_question: empty")

        # Capacity / shadow / tension distinctness enforcement per component.
        for i, s in enumerate(self.component_stories.stories):
            if s.availability != "present":
                continue
            if s.capacity.text and s.distortion.text and \
               s.capacity.text.strip().lower() == s.distortion.text.strip().lower():
                problems.append(
                    f"component_stories.stories[{i}] ({s.component_id}): "
                    f"capacity == distortion (must be distinct)"
                )

        # Timing signals must have current_factor + structural_target + window.
        for i, sig in enumerate(self.today_timing.signals):
            if not sig.current_factor or not sig.structural_target:
                problems.append(f"today_timing.signals[{i}]: missing current_factor or structural_target")
            if not sig.window or not sig.window.scope:
                problems.append(f"today_timing.signals[{i}]: missing timing window")

        return problems


__all__ = [
    "Availability", "Confidence", "ContentOrigin", "TimeScope",
    "EvidenceRef", "MaterialClaim", "FactBadge", "MissingSlot",
    "AtAGlanceLayer", "StructureLayer", "StructureComponent",
    "CoreStoryLayer", "ComponentStoriesLayer", "ComponentStory",
    "IntegrationLayer", "EvidenceLayer",
    "TodayTimingLayer", "TimingSignal", "TimingWindow",
    "LensEnvelope",
]
