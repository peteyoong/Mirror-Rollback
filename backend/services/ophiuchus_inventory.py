"""
Ophiuchus Inventory Engine
==========================

Build marker: ophiuchus-inventory-engine-v1

Deterministic answer for "Do I have Ophiuchus in my chart?" and
"What placements in my chart are in Ophiuchus?".

Companion to `services.house_inventory_engine`. Mirror's canonical
zodiac is the 13-sign Variant A model (`midpoint13_variant_a_v1`)
where Ophiuchus is a first-class sign. When the user asks about
Ophiuchus directly, the prior chat path had no deterministic engine
and the LLM would fall back to its 12-sign RLHF prior and deny
Ophiuchus exists. This module enumerates every chart object with
`sign == "Ophiuchus"` and renders a proof block the LLM must
answer from.

Read-only inspection of `chart.astrology.{planets, angles, nodes}` —
no calculator math, no chart writes, no migrations.

Companion audit:
    /app/backend/audit_reports/ASTROLOGY_CHAT_PARITY_AUDIT.md
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

BUILD_MARKER = "ophiuchus-inventory-engine-v1"

# Canonical Variant A sign name. Other casings ("ophiuchus", "OPHIUCHUS")
# can appear in legacy data; we normalize.
_CANONICAL_SIGN = "Ophiuchus"


def _is_ophi(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return value.strip().lower() == _CANONICAL_SIGN.lower()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_ophiuchus_inventory(chart: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a deterministic envelope describing every Ophiuchus placement
    in the user's stored chart.

    The envelope shape mirrors `services.house_inventory_engine`:

        {
            "success": True,
            "build_marker": "ophiuchus-inventory-engine-v1",
            "has_ophiuchus": bool,
            "placements": [
                {"name": "Neptune",   "kind": "planet", "sign": "Ophiuchus",
                 "house": 5, "degree": 8.30, "formatted": "8.3°Ophiuchus"},
                {"name": "Ascendant", "kind": "angle",  "sign": "Ophiuchus",
                 "house": 1, "degree": 2.50, "formatted": "2.5°Ophiuchus"},
                ...
            ],
            "house_cusps_in_ophiuchus": [12, ...],   # houses whose cusp = Ophiuchus
            "total_placements":   <int>,
        }

    Returns `{"success": False, ...}` only when `chart` is missing /
    malformed; never raises. The "no Ophiuchus" case is a SUCCESSFUL
    inventory with `has_ophiuchus = False`.
    """
    if not chart:
        return {
            "success":              False,
            "build_marker":         BUILD_MARKER,
            "reason":               "no_chart",
            "has_ophiuchus":        False,
            "placements":           [],
            "house_cusps_in_ophiuchus": [],
            "total_placements":     0,
        }

    astro = chart.get("astrology") or {}
    if not isinstance(astro, dict):
        astro = {}

    placements: List[Dict[str, Any]] = []

    # ── Planets (Sun..Pluto + Chiron) ─────────────────────────────
    planets = astro.get("planets") or {}
    if isinstance(planets, dict):
        for name in (
            "Sun", "Moon", "Mercury", "Venus", "Mars",
            "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron",
        ):
            p = planets.get(name)
            if not isinstance(p, dict):
                continue
            if _is_ophi(p.get("sign")):
                placements.append({
                    "name":       name,
                    "kind":       "planet",
                    "sign":       _CANONICAL_SIGN,
                    "house":      p.get("house"),
                    "degree":     p.get("degree"),
                    "formatted":  p.get("formatted")
                                  or _fmt(name, p.get("degree")),
                    "retrograde": bool(p.get("retrograde", False)),
                })

    # ── Lunar Nodes (multiple legacy shapes) ──────────────────────
    nodes = astro.get("nodes") or {}
    if not isinstance(nodes, dict):
        nodes = {}
    lunar_legacy = astro.get("lunar_nodes") or {}
    if not isinstance(lunar_legacy, dict):
        lunar_legacy = {}
    for raw_key, canonical in (
        ("north",      "North Node"),
        ("north_node", "North Node"),
        ("South",      "South Node"),
        ("south",      "South Node"),
        ("south_node", "South Node"),
    ):
        for source_dict in (nodes, lunar_legacy):
            n = source_dict.get(raw_key)
            if isinstance(n, dict) and _is_ophi(n.get("sign")):
                if not any(pl["name"] == canonical for pl in placements):
                    placements.append({
                        "name":      canonical,
                        "kind":      "node",
                        "sign":      _CANONICAL_SIGN,
                        "house":     n.get("house"),
                        "degree":    n.get("degree"),
                        "formatted": n.get("formatted")
                                     or _fmt(canonical, n.get("degree")),
                    })
    # Fallback: planets dict may carry node entries under their canonical name
    for canonical in ("North Node", "South Node"):
        n = planets.get(canonical) if isinstance(planets, dict) else None
        if isinstance(n, dict) and _is_ophi(n.get("sign")):
            if not any(pl["name"] == canonical for pl in placements):
                placements.append({
                    "name":      canonical,
                    "kind":      "node",
                    "sign":      _CANONICAL_SIGN,
                    "house":     n.get("house"),
                    "degree":    n.get("degree"),
                    "formatted": n.get("formatted")
                                 or _fmt(canonical, n.get("degree")),
                })

    # ── Angles (ASC / DC / MC / IC) ───────────────────────────────
    angles = astro.get("angles") or {}
    if not isinstance(angles, dict):
        angles = {}
    for raw_key, canonical, house_num in (
        ("asc",        "Ascendant", 1),
        ("ascendant",  "Ascendant", 1),
        ("dc",         "Descendant", 7),
        ("descendant", "Descendant", 7),
        ("mc",         "Midheaven", 10),
        ("midheaven",  "Midheaven", 10),
        ("ic",         "Imum Coeli", 4),
        ("imum_coeli", "Imum Coeli", 4),
    ):
        a = angles.get(raw_key)
        if isinstance(a, dict) and _is_ophi(a.get("sign")):
            if not any(pl["name"] == canonical for pl in placements):
                placements.append({
                    "name":      canonical,
                    "kind":      "angle",
                    "sign":      _CANONICAL_SIGN,
                    "house":     house_num,
                    "degree":    a.get("degree"),
                    "formatted": a.get("formatted")
                                 or _fmt(canonical, a.get("degree")),
                })

    # ── House cusps in Ophiuchus ──────────────────────────────────
    house_cusps_in_ophi: List[int] = []
    houses = astro.get("houses") or {}
    if isinstance(houses, dict):
        formatted_cusps = houses.get("formatted_cusps") or []
        if isinstance(formatted_cusps, list):
            for idx, cusp in enumerate(formatted_cusps[:12]):
                if isinstance(cusp, dict) and _is_ophi(cusp.get("sign")):
                    house_cusps_in_ophi.append(idx + 1)

    return {
        "success":                  True,
        "build_marker":             BUILD_MARKER,
        "has_ophiuchus":            bool(placements) or bool(house_cusps_in_ophi),
        "placements":               placements,
        "house_cusps_in_ophiuchus": house_cusps_in_ophi,
        "total_placements":         len(placements),
        "engine_version":           chart.get("astrology_engine_version")
                                    or (astro.get("metadata") or {}).get("astrology_engine_version")
                                    or "<unknown>",
    }


# ---------------------------------------------------------------------------
# Proof block for chat
# ---------------------------------------------------------------------------

def build_ophiuchus_inventory_proof_block(envelope: Dict[str, Any]) -> str:
    """Render the inventory envelope as a deterministic LLM-facing block.

    The LLM MUST answer from this block — it cannot deny Ophiuchus or
    cite "traditional astrology" once this block is in the prompt.
    """
    if not envelope or not envelope.get("success"):
        return (
            "━━━━ OPHIUCHUS INVENTORY — ENGINE STATUS ━━━━\n"
            "available: NO  (no chart available)\n"
            "INSTRUCTION: state plainly that you cannot find the user's chart. "
            "Do NOT fall back to generic Ophiuchus opinions.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    has_ophi = bool(envelope.get("has_ophiuchus"))
    placements = envelope.get("placements") or []
    cusps = envelope.get("house_cusps_in_ophiuchus") or []
    engine = envelope.get("engine_version", "<unknown>")

    if not has_ophi:
        return (
            "━━━━ OPHIUCHUS INVENTORY — ENGINE OUTPUT ━━━━\n"
            f"canonical_engine: {engine}  (13-sign Variant A — Ophiuchus first-class)\n"
            "has_ophiuchus_placement: NO\n"
            "house_cusps_in_ophiuchus: (none)\n"
            "\n"
            "INSTRUCTION (deterministic answer — no hedging):\n"
            " 1. Confirm Mirror runs on a 13-sign canonical zodiac in which\n"
            "    Ophiuchus is a first-class sign.\n"
            " 2. State plainly that THIS user has NO planets, angles, nodes,\n"
            "    OR house cusps in Ophiuchus.\n"
            " 3. DO NOT say 'I don't have reliable data', 'traditional\n"
            "    astrology does not recognize Ophiuchus', 'Mirror uses\n"
            "    the 12-sign zodiac', 'this depends on the system', or any\n"
            "    variant. The data is complete; the answer is simply NO.\n"
            " 4. Length: 1–2 sentences. No closing question.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    # Edge case: house cusp(s) in Ophiuchus but no body / angle placements.
    # This means a house BORDERS Ophiuchus but no body actually sits in it.
    # The honest answer is "you have an Ophiuchus cusp on House N, but no
    # planets / angles / nodes are actually in Ophiuchus".
    if not placements and cusps:
        cusps_str = ", ".join(str(c) for c in cusps)
        return (
            "━━━━ OPHIUCHUS INVENTORY — ENGINE OUTPUT ━━━━\n"
            f"canonical_engine: {engine}  (13-sign Variant A — Ophiuchus first-class)\n"
            "has_ophiuchus_placement: PARTIAL  (house cusp only, no body placements)\n"
            f"house_cusps_in_ophiuchus: {cusps}\n"
            "placements_in_ophiuchus: (none — no planet, angle, or node sits in Ophiuchus)\n"
            "\n"
            "INSTRUCTION TO YOU (deterministic — no hedging):\n"
            f" 1. State that Mirror's 13-sign canonical engine ({engine}) places\n"
            f"    the cusp of House {cusps_str} in Ophiuchus.\n"
            " 2. State plainly that NO planet, angle, or lunar node is actually\n"
            "    IN Ophiuchus for this user — the sign appears only as the cusp\n"
            "    boundary of the listed house(s).\n"
            " 3. DO NOT say 'I don't have reliable data on Ophiuchus', 'traditional\n"
            "    astrology does not recognize Ophiuchus', or 'Mirror uses the\n"
            "    12-sign zodiac'. The 13-sign engine is canonical here.\n"
            " 4. Length: 1–2 sentences. No closing question.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    lines: List[str] = []
    for p in placements:
        formatted = p.get("formatted") or f"{p.get('degree')}° Ophiuchus"
        house = p.get("house")
        kind = p.get("kind", "?")
        retro = " (Rx)" if p.get("retrograde") else ""
        if house:
            lines.append(f"  • {p['name']:14s} {formatted:22s} House {house}  ({kind}){retro}")
        else:
            lines.append(f"  • {p['name']:14s} {formatted:22s}            ({kind}){retro}")
    placements_block = "\n".join(lines) if lines else "  (no body/angle/node placements)"

    cusps_block = (
        f"house_cusps_in_ophiuchus: {cusps}"
        if cusps
        else "house_cusps_in_ophiuchus: (none)"
    )

    return (
        "━━━━ OPHIUCHUS INVENTORY — ENGINE OUTPUT ━━━━\n"
        f"canonical_engine: {engine}  (13-sign Variant A — Ophiuchus first-class)\n"
        f"has_ophiuchus_placement: YES  ({len(placements)} placement(s))\n"
        f"{cusps_block}\n"
        f"\n"
        f"placements_in_ophiuchus (THIS IS THE COMPLETE LIST):\n"
        f"{placements_block}\n"
        f"\n"
        f"INSTRUCTION TO YOU (deterministic — no hedging, no 'traditional astrology'):\n"
        f" 1. Confirm yes — this user DOES have placement(s) in Ophiuchus.\n"
        f" 2. Name EVERY placement above by body name, sign 'Ophiuchus',\n"
        f"    and house number (when present). No omissions. If you skip\n"
        f"    one, the answer is wrong.\n"
        f" 3. Mirror uses the 13-sign canonical engine ({engine}); Ophiuchus\n"
        f"    is real here. Do NOT add disclaimers about 'traditional\n"
        f"    astrology', '12-sign zodiac', or 'depending on the system'.\n"
        f" 4. Voice: direct, observant, behavioural. Speak about Ophiuchus\n"
        f"    as a threshold / integration sign (not a void). Do not\n"
        f"    paraphrase as Scorpio or Sagittarius.\n"
        f" 5. Banned openers: 'I don\u2019t have reliable data', 'I can\u2019t\n"
        f"    see your data', 'Traditional astrology does not recognize',\n"
        f"    'Your chart does not include Ophiuchus'. These are the bug,\n"
        f"    not the answer.\n"
        f" 6. Length: 80–180 words. No closing question.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt(name: str, degree: Any) -> str:
    try:
        d = float(degree)
        return f"{d:.1f}\u00b0Ophiuchus"
    except Exception:
        return f"Ophiuchus"


__all__ = [
    "BUILD_MARKER",
    "build_ophiuchus_inventory",
    "build_ophiuchus_inventory_proof_block",
]
