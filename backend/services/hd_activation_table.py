"""hd_activation_table.py — Personality and Design Activations
========================================================================

Session-3c Decision 3: surface the full Personality and Design
activation table on `/api/human-design/mechanics/{id}` — 13 activation
points on each side (planets + Earth + Lunar Nodes; the term "planet"
is not accurate for Earth or the Nodes and is intentionally avoided in
user-facing copy)
so the user-facing HD view can render each activation with gate·line
(and colour·tone·base when available) plus its derivation lineage.

Every row in the returned tables carries:
    planet        : e.g. "Sun", "Moon", "Mercury", "North Node"
    side          : "personality" | "design"
    gate          : int  (1..64)
    line          : int  (1..6)
    color         : int  (1..6) | None
    tone          : int  (1..6) | None
    base          : int  (1..5) | None
    formatted     : "gate.line"                           (always)
    full_formatted: "gate.line.color.tone.base"           (when full)
    sign          : zodiac sign of the position (from raw)
    longitude     : sidereal longitude (from raw)         (when available)
    derivation_rule: identifier
    source         : "chart.human_design.<side>.<planet>.gate"

Non-material fields (planetary house, retrograde etc.) are intentionally
left off — this table is for HD, not astrology.

Missing planets are emitted as `MissingSlot` rows rather than being
silently dropped, so the caller can distinguish "planet not in raw
payload" from "planet has no gate".

build_marker: the-mirror-hd-activation-table-v1
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# 13 activation points in canonical HD order (planets + Earth + Nodes)
HD_PLANET_ORDER = (
    "Sun",
    "Earth",
    "Moon",
    "North Node",
    "South Node",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
)

DERIVATION_RULE_ID = "hd_activation_from_raw_planetary_gate_v1"


def _int_or_none(v: Any) -> Optional[int]:
    try:
        if v is None:
            return None
        return int(v)
    except (TypeError, ValueError):
        return None


def _row_for_planet(
    side: str,
    planet: str,
    planet_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build a single activation row. Handles absent-planet + partial-data."""
    if not isinstance(planet_data, dict):
        return {
            "planet": planet,
            "side": side,
            "gate": None,
            "line": None,
            "color": None,
            "tone": None,
            "base": None,
            "formatted": None,
            "full_formatted": None,
            "sign": None,
            "longitude": None,
            "missing": True,
            "missing_reason": "planet_not_in_raw",
            "derivation_rule": DERIVATION_RULE_ID,
            "source": f"chart.human_design.{side}.{planet}",
        }

    gate_block = planet_data.get("gate") or {}
    pos = planet_data.get("position") or {}
    gate = _int_or_none(gate_block.get("gate"))
    line = _int_or_none(gate_block.get("line"))
    color = _int_or_none(gate_block.get("color"))
    tone = _int_or_none(gate_block.get("tone"))
    base = _int_or_none(gate_block.get("base"))
    formatted = gate_block.get("formatted") or (
        f"{gate}.{line}" if gate and line else None
    )
    full_formatted = gate_block.get("full_formatted")
    if not full_formatted and all(
        x is not None for x in (gate, line, color, tone, base)
    ):
        full_formatted = f"{gate}.{line}.{color}.{tone}.{base}"

    missing = gate is None or line is None
    row = {
        "planet": planet,
        "side": side,
        "gate": gate,
        "line": line,
        "color": color,
        "tone": tone,
        "base": base,
        "formatted": formatted,
        "full_formatted": full_formatted,
        "sign": pos.get("sign") if isinstance(pos, dict) else None,
        "longitude": pos.get("longitude") if isinstance(pos, dict) else None,
        "missing": missing,
        "missing_reason": "no_gate_derived" if missing else None,
        "derivation_rule": DERIVATION_RULE_ID,
        "source": f"chart.human_design.{side}.{planet}.gate",
    }
    return row


def build_activation_table(hd_raw: Dict[str, Any]) -> Dict[str, Any]:
    """Return the {personality, design} activation tables.

    hd_raw is the raw HD sub-document from `charts.human_design`
    (i.e. must contain `personality` and `design` planet dicts).
    """
    if not isinstance(hd_raw, dict):
        return {
            "personality": [],
            "design": [],
            "counts": {"personality": 0, "design": 0},
            "missing": True,
            "reason": "no_hd_raw",
            "provenance": {
                "source": "chart.human_design",
                "algorithm": "hd_activation_table_v1",
            },
        }

    p_raw = hd_raw.get("personality") or {}
    d_raw = hd_raw.get("design") or {}
    personality_rows = [
        _row_for_planet("personality", planet, p_raw.get(planet))
        for planet in HD_PLANET_ORDER
    ]
    design_rows = [
        _row_for_planet("design", planet, d_raw.get(planet))
        for planet in HD_PLANET_ORDER
    ]

    p_present = sum(1 for r in personality_rows if not r["missing"])
    d_present = sum(1 for r in design_rows if not r["missing"])

    return {
        "personality": personality_rows,
        "design": design_rows,
        "counts": {
            "personality_present": p_present,
            "design_present": d_present,
            "personality_total": len(personality_rows),
            "design_total": len(design_rows),
        },
        # Session-3d Decision 4 — advanced activation fields
        # (color / tone / base) are computed by the canonical
        # gate-line-color-tone-base subdivision, but no INDEPENDENT
        # reproducible fixture has been added to verify them against a
        # third-party HD source.  Until such calibration ships, the
        # frontend must render gate.line only and treat color/tone/base
        # as PRESENT_BUT_UNVERIFIED.  The values remain in the payload
        # for developer inspection but MUST NOT drive narrative claims.
        "advanced_fields_verified": False,
        "advanced_fields_status": "PRESENT_BUT_UNVERIFIED",
        "advanced_fields_reason": (
            "canonical 6-6-5 subdivision computed from sidereal longitude "
            "but no independent HD calibration fixture yet"
        ),
        "provenance": {
            "source": "chart.human_design",
            "algorithm": "hd_activation_table_v1",
            "planet_order": list(HD_PLANET_ORDER),
        },
        "derivation_rule": DERIVATION_RULE_ID,
    }


__all__ = [
    "build_activation_table",
    "HD_PLANET_ORDER",
    "DERIVATION_RULE_ID",
]
