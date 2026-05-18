"""
Astrology lens registry — delegates the heavy lifting to the existing
`services.astrology_conversation` module which already indexes planets,
nodes, angles, and houses.  Keeps the original entity-resolution semantics
while plugging into the shared lens_conversation service.
"""

from __future__ import annotations

from typing import Any, Dict, List

from services.astrology_conversation import (
    build_chart_entity_index,
    extract_entities_from_text as _astro_extract,
    format_chart_signals_block,
)


class _AstrologyRegistry:
    lens_name = "astrology"
    lens_label = "Astrology"

    voice_prompt = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LENS VOICE — ASTROLOGY  (interpretive stance: symbolic cartographer)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You read the chart as a symbolic terrain.  You name what the configuration
is doing and where it lives in the user's life.

Reasoning style:
  - Archetypal first, behavioural second.  Name the symbol, then the way
    it lands in real life ("Saturn in the 10th, conjunct the MC — this is
    the long climb made structural").
  - Tension-oriented.  Show where energies pull against each other (sign
    vs house, planet vs aspect, transit vs natal).
  - Contextual.  A planet means different things in different houses with
    different aspects — never extract the placement from its setting.
  - Timing-aware when asked.  Transits, returns, and progressions matter
    here; do not pretend they don't exist.
  - Bound to ground.  Always close the loop back to lived experience —
    family, work, intimacy, body, money, visibility, belonging — not
    cosmic abstraction.

Sentence rhythm:
  Slightly weighted, deliberate.  Allow yourself two-clause sentences
  that hold a tension ("Jupiter expands what it touches; in the 4th, it
  expands family — and family's grip on you.").

FORBIDDEN PHRASINGS (lens-specific):
  - Horoscope-app filler ("Today the cosmos invites you to...")
  - "The universe is asking you to..."
  - "Your stars say..."
  - Vague archetypes with no house grounding ("you are a Jupiter person")
  - Predictive certainty about events.  Stay with patterns, not promises.

Response-architecture weighting (within the universal A–G spine):
  Lean heaviest into  B) SIGNAL (precise placement, house, aspect)
                  and D) BEHAVIOUR (how it lands in domain).
  Use E) SHADOW to name the cost of the placement under pressure.
  F) CONNECTION is where you can briefly note one aspect or transit
  that sharpens the active entity — only when truly relevant.
"""

    def build_index(self, user_context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        chart = user_context.get("chart")
        return build_chart_entity_index(chart)

    def extract_entities_from_text(self, text: str) -> List[str]:
        ents = _astro_extract(text)
        # The astrology helper returns Sign:X labels for disambiguators; the
        # shared resolver expects canonical entity keys that exist in the
        # index, so we strip Sign:X tokens here.
        return [e for e in ents if not e.startswith("Sign:")]

    def referent_patterns(self) -> List[str]:
        return [
            r"\bwhich house\b", r"\bwhat house\b", r"\bthe house\b",
            r"\bwhich sign\b", r"\bwhat sign\b", r"\bthe sign\b",
            r"\bwhich aspect\b", r"\bwhat aspect\b",
            r"\bwhere does .* sit\b", r"\bwhere does that sit\b",
        ]

    def grounding_sources_present(self, user_context: Dict[str, Any]) -> List[str]:
        chart = user_context.get("chart") or {}
        astro = chart.get("astrology") or {}
        present: List[str] = []
        if astro.get("planets"):
            present.append("Sidereal planets")
        if astro.get("houses"):
            present.append("House cusps")
        nodes = astro.get("nodes") or astro.get("lunar_nodes") or {}
        if nodes:
            present.append("Lunar nodes")
        return present

    def missing_sources(self, user_context: Dict[str, Any]) -> List[str]:
        chart = user_context.get("chart") or {}
        astro = chart.get("astrology") or {}
        missing: List[str] = []
        if not (astro.get("planets")):
            missing.append("Sidereal planets")
        if not (astro.get("houses")):
            missing.append("House cusps (requires exact birth time)")
        nodes = astro.get("nodes") or astro.get("lunar_nodes")
        if not nodes:
            missing.append("Lunar nodes")
        return missing

    def format_grounding_block(self, index: Dict[str, Dict[str, Any]]) -> str:
        return format_chart_signals_block(index)


ASTROLOGY_REGISTRY = _AstrologyRegistry()
