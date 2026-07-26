"""lens_content_adapter.py — Adapt existing lens payloads → LensEnvelope
==========================================================================

Session-2 architectural requirement: DO NOT duplicate calculation
engines.  This module is a THIN, PURE READ layer that takes whatever the
existing endpoints already produce for a lens and re-shapes it into the
shared `LensEnvelope` contract from `lens_content_contract.py`.

Not shipped yet: fully populated envelopes for every lens.  What IS
shipped is the machinery so Session-3+ lens rebuilds can incrementally
populate their envelope without touching the response shape.

Availability rule: whenever data is missing for a layer, the layer is
emitted with `availability="unavailable"` and a MissingSlot explaining
what would be shown when the underlying calculation exists.

build_marker: lens-content-adapter-v1
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from services.lens_content_contract import (
    Availability,
    AtAGlanceLayer, ComponentStoriesLayer, ComponentStory,
    CoreStoryLayer, EvidenceLayer, EvidenceRef, FactBadge,
    IntegrationLayer, LensEnvelope, MaterialClaim, MissingSlot,
    StructureComponent, StructureLayer,
    TodayTimingLayer, TimingSignal, TimingWindow,
)
from services.hd_center_canonical import (
    canonicalize_centers, CANONICAL_CENTERS,
)


ADAPTER_VERSION = "lens-content-adapter-v1"


# ─────────────────────────────────────────────────────────────────────
# Common helpers
# ─────────────────────────────────────────────────────────────────────
def _missing(what: str, why: str,
             could_be_shown_if: Optional[str] = None) -> MissingSlot:
    return MissingSlot(
        what=what, why=why, could_be_shown_if=could_be_shown_if,
        availability="unavailable",
    )


def _unavailable_claim(what: str) -> MaterialClaim:
    return MaterialClaim(
        text=f"({what}: not yet available)",
        evidence=[],
        origin="inferred",
        confidence="unknown",
    )


def _unavailable_layer_evidence(lens: str,
                                what: str) -> List[EvidenceRef]:
    return [EvidenceRef(
        source_lens=lens,
        calculation="unavailable",
        derivation_rule=f"{what} not yet plumbed to contract",
        origin="calculated",
        confidence="unknown",
    )]


def _empty_layers_for(lens: str, engine_version: Optional[str] = None,
                      computed_at: Optional[str] = None
                      ) -> Dict[str, Any]:
    """Return the six non-envelope layers pre-populated with
    availability='unavailable' so a downstream adapter only fills the
    layers it actually has data for.  All layers keep a stable shape."""
    return {
        "at_a_glance": AtAGlanceLayer(
            recognition_statement=f"({lens} recognition statement: not yet available)",
            availability="unavailable",
        ),
        "structure": StructureLayer(
            missing=[_missing(
                what="Structural table",
                why=f"{lens} structure not yet adapted",
                could_be_shown_if=f"session-3+ populates {lens} adapter",
            )],
            availability="unavailable",
        ),
        "core_story": CoreStoryLayer(
            essence=_unavailable_claim("essence"),
            capacity=_unavailable_claim("capacity"),
            shadow_or_distortion=_unavailable_claim("shadow"),
            central_tension=_unavailable_claim("central tension"),
            developmental_possibility=_unavailable_claim("possibility"),
            practical_application=_unavailable_claim("practical"),
            reflection_question=MaterialClaim(
                text="(reflection question: not yet available)",
                origin="inferred", confidence="unknown",
            ),
            availability="unavailable",
        ),
        "component_stories": ComponentStoriesLayer(availability="unavailable"),
        "integration": IntegrationLayer(
            how_they_operate_together=_unavailable_claim("integration"),
            availability="unavailable",
        ),
        "evidence": EvidenceLayer(availability="unavailable"),
        "today_timing": TodayTimingLayer(availability="unavailable"),
    }


# ─────────────────────────────────────────────────────────────────────
# Adapter: Human Design
# ─────────────────────────────────────────────────────────────────────
def adapt_human_design(hd_summary: Dict[str, Any],
                       hd_centers: Optional[Dict[str, Any]] = None,
                       hd_deep_dive: Optional[Dict[str, Any]] = None,
                       ) -> LensEnvelope:
    """Adapt the existing HD payloads into a `LensEnvelope`.  Currently
    populates AT A GLANCE + STRUCTURE (both fully) plus stubs.  Rest
    remain unavailable until Session-3."""
    engine = None
    if isinstance(hd_deep_dive, dict):
        engine = hd_deep_dive.get("engine_version") or (
            (hd_deep_dive.get("diagnostics") or {}).get("engine_version")
        )
    layers = _empty_layers_for("human_design", engine_version=engine)

    # ── AT A GLANCE — real content available ─────────────────────────
    # Summary endpoint nests core fields under `core_mechanics`; also
    # accept legacy top-level keys as a fallback.
    core = (hd_summary or {}).get("core_mechanics") \
        if isinstance(hd_summary, dict) else None
    src_dict = core if isinstance(core, dict) else (hd_summary or {})
    facts: List[FactBadge] = []
    for lbl, key in (("Type", "type"), ("Strategy", "strategy"),
                     ("Authority", "authority"), ("Profile", "profile"),
                     ("Definition", "definition"),
                     ("Incarnation Cross", "incarnation_cross")):
        v = src_dict.get(key) if isinstance(src_dict, dict) else None
        if v:
            facts.append(FactBadge(
                label=lbl,
                value=str(v.get("name") if isinstance(v, dict) else v),
                source_calculation=f"human_design.{key}",
                origin="calculated",
            ))
    if facts:
        recog = (
            f"{facts[0].value} {'· ' + facts[1].value if len(facts) > 1 else ''}"
            f" — the mechanics of how you're wired to move, decide and be recognised."
        ).strip()
        layers["at_a_glance"] = AtAGlanceLayer(
            essential_facts=facts,
            recognition_statement=recog,
            lens_can_claim=[
                "Your energetic type and mechanics.",
                "Where consistent energy is available.",
                "How you're wired to make decisions correctly for you.",
            ],
            lens_cannot_claim=[
                "Personality traits or Enneagram-style motivations.",
                "Fate, timing predictions, or destiny.",
                "Psychological diagnosis.",
            ],
            availability="present",
        )

    # ── STRUCTURE — centres, gates, channels ─────────────────────────
    struct_components: List[StructureComponent] = []
    if isinstance(hd_centers, dict) and isinstance(hd_centers.get("centers"), list):
        for c in hd_centers["centers"]:
            if not isinstance(c, dict):
                continue
            struct_components.append(StructureComponent(
                component_id=f"center:{(c.get('display_name') or c.get('center_name') or 'unknown').lower().replace(' ', '_').replace('/', '_')}",
                label=c.get("display_name") or c.get("center_name") or "Center",
                value={
                    "defined": bool(c.get("defined")),
                    "gates_present": c.get("gates_present") or [],
                },
                provenance=EvidenceRef(
                    source_lens="human_design",
                    calculation="human_design.centers[]",
                    factors_used=["chart.human_design.defined_centers", "chart.human_design.gates"],
                    origin="calculated",
                    confidence="high",
                    engine_version=engine,
                ),
            ))
    if struct_components:
        layers["structure"] = StructureLayer(
            components=struct_components,
            calculation_provenance=EvidenceRef(
                source_lens="human_design",
                calculation="human_design.centers + gates",
                origin="calculated",
                confidence="high",
                engine_version=engine,
            ),
            availability="present",
        )

    return LensEnvelope(
        lens="human_design",
        engine_version=engine,
        **layers,
    )


# ─────────────────────────────────────────────────────────────────────
# Adapter: True Sidereal Astrology (Variant-A)
# ─────────────────────────────────────────────────────────────────────
def adapt_astrology(chart: Dict[str, Any]) -> LensEnvelope:
    """Adapt the Variant-A True Sidereal chart into a `LensEnvelope`.
    Only STRUCTURE + AT A GLANCE are populated in Session-2.  Every
    planet is emitted as a StructureComponent whose `value` includes
    both `degree_within_sign` (real, CAN exceed 30°) AND `sign_width`
    so downstream FE can render the "constellation-relative" label."""
    layers = _empty_layers_for("astrology")
    natal = (chart or {}).get("natal") or {}
    planets = natal.get("planets") or {}
    angles  = natal.get("angles")  or {}

    struct_components: List[StructureComponent] = []
    if isinstance(planets, dict):
        for name, p in planets.items():
            if not isinstance(p, dict):
                continue
            struct_components.append(StructureComponent(
                component_id=f"planet:{name.lower().replace(' ', '_')}",
                label=name,
                value={
                    "sign":                p.get("sign"),
                    "degree_within_sign":  p.get("degree"),  # variant-A real width
                    "absolute_longitude":  p.get("longitude"),
                    "constellation_width": p.get("sign_width"),
                    "degree_label": "constellation-relative degree",
                },
                provenance=EvidenceRef(
                    source_lens="astrology",
                    calculation="astrology.natal.planets",
                    factors_used=["absolute_longitude", "variant_a_boundary_table"],
                    derivation_rule="variant_a_13sign_midpoint_boundaries",
                    origin="calculated",
                    confidence="high",
                ),
            ))
    if isinstance(angles, dict):
        for k in ("asc", "dc", "mc", "ic"):
            a = angles.get(k)
            if isinstance(a, dict):
                struct_components.append(StructureComponent(
                    component_id=f"angle:{k}",
                    label=k.upper(),
                    value={
                        "sign":               a.get("sign"),
                        "degree_within_sign": a.get("degree"),
                        "absolute_longitude": a.get("longitude"),
                        "degree_label": "constellation-relative degree",
                    },
                    provenance=EvidenceRef(
                        source_lens="astrology",
                        calculation=f"astrology.natal.angles.{k}",
                        origin="calculated",
                        confidence="high",
                    ),
                ))

    if struct_components:
        layers["structure"] = StructureLayer(
            components=struct_components,
            calculation_provenance=EvidenceRef(
                source_lens="astrology",
                calculation="astrology.chart",
                factors_used=["variant_a_13sign_midpoint_boundaries"],
                derivation_rule="attribute_sign_midpoint13_variant_a",
                origin="calculated",
                confidence="high",
            ),
            missing=[_missing(
                what="Ophiuchus / advanced-body coverage",
                why="Session-5 scope",
            )],
            availability="present",
        )

    # AT A GLANCE — real minimal content available
    sun = (planets.get("Sun") if isinstance(planets, dict) else None) or {}
    moon = (planets.get("Moon") if isinstance(planets, dict) else None) or {}
    asc = angles.get("asc") if isinstance(angles, dict) else None
    if sun.get("sign") or moon.get("sign") or (asc and asc.get("sign")):
        facts = []
        if sun.get("sign"):
            facts.append(FactBadge(
                label="Sun", value=f"{sun.get('sign')} {sun.get('degree', '')}°",
                source_calculation="astrology.natal.planets.Sun",
            ))
        if moon.get("sign"):
            facts.append(FactBadge(
                label="Moon", value=f"{moon.get('sign')} {moon.get('degree', '')}°",
                source_calculation="astrology.natal.planets.Moon",
            ))
        if asc and asc.get("sign"):
            facts.append(FactBadge(
                label="Ascendant",
                value=f"{asc.get('sign')} {asc.get('degree', '')}°",
                source_calculation="astrology.natal.angles.asc",
            ))
        layers["at_a_glance"] = AtAGlanceLayer(
            essential_facts=facts,
            recognition_statement=(
                "A cosmic timing lens read through Variant-A True Sidereal — "
                "constellations have unequal widths, so some valid degrees exceed 30°."
            ),
            lens_can_claim=[
                "Symbolic timing and archetypal weather.",
                "Where structural patterns of self / relating / doing tend to gather.",
            ],
            lens_cannot_claim=[
                "Specific future events.",
                "Character diagnosis or fate.",
            ],
            availability="present",
        )

    return LensEnvelope(
        lens="astrology",
        engine_version="variant_a_13sign_midpoint",
        **layers,
    )


# ─────────────────────────────────────────────────────────────────────
# Adapter: stubs for remaining lenses (session-3+ will populate)
# ─────────────────────────────────────────────────────────────────────
def adapt_numerology(payload: Dict[str, Any]) -> LensEnvelope:
    return LensEnvelope(lens="numerology", **_empty_layers_for("numerology"))


def adapt_bazi(payload: Dict[str, Any]) -> LensEnvelope:
    return LensEnvelope(lens="bazi", **_empty_layers_for("bazi"))


def adapt_enneagram(payload: Dict[str, Any]) -> LensEnvelope:
    return LensEnvelope(lens="enneagram", **_empty_layers_for("enneagram"))


def adapt_gene_keys(payload: Dict[str, Any]) -> LensEnvelope:
    return LensEnvelope(lens="gene_keys", **_empty_layers_for("gene_keys"))


__all__ = [
    "ADAPTER_VERSION",
    "adapt_human_design", "adapt_astrology", "adapt_numerology",
    "adapt_bazi", "adapt_enneagram", "adapt_gene_keys",
]
