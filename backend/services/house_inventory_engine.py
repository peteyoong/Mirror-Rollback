"""
House Inventory + Hierarchy Engine
==================================

Build marker: astrology-chat-house-hierarchy-v5

Answers "tell me everything about my Nth house" by aggregating EVERY
computed object whose longitude falls in that house — across natal
planets, angles, nodes, Chiron, Lilith family, asteroids, and the
sect-aware Arabic Lots. Then derives a hierarchy (dominant body,
tension body, field type) so the LLM has structured signal for
master-astrologer synthesis instead of producing a flat list.

The user's v4 complaint was: Chiron in the 3rd house was omitted from
the initial inventory and only surfaced when explicitly asked. This
engine eliminates that failure mode by ALWAYS pulling from the full
natal_object_engine registry before the chat synthesizes.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from calculations.astrology import get_house_for_planet
from services.natal_object_engine import (
    compute_natal_object,
    BUILD_MARKER as _NOE_BUILD_MARKER,
)

logger = logging.getLogger(__name__)

BUILD_MARKER = "astrology-chat-house-hierarchy-v5"

# Object → semantic category, used for hierarchy weighting.
_CATEGORY = {
    "Sun":      "core",        "Moon":      "core",
    "Mercury":  "core",        "Venus":     "core",
    "Mars":     "core",        "Jupiter":   "outer_personal",
    "Saturn":   "structural",  "Uranus":    "transpersonal",
    "Neptune":  "transpersonal","Pluto":     "transpersonal",
    "North Node": "karmic",    "South Node":"karmic",
    "Chiron":   "healing_point",
    "Black Moon Lilith": "shadow_point",
    "True Black Moon Lilith": "shadow_point",
    "Juno":     "asteroid",    "Ceres":     "asteroid",
    "Pallas":   "asteroid",    "Vesta":     "asteroid",
    "Vertex":   "fate_point",  "Anti-Vertex": "fate_point",
    "Lot of Fortune": "lot",   "Lot of Spirit": "lot",
}

# Bodies we will ATTEMPT to compute for every house inventory, even
# if they're not in the stored chart doc. Order matters for the
# "omitted-Chiron" bug — Chiron must always be checked.
_INVENTORY_TARGETS = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "North Node", "South Node",
    "Chiron",
    "Black Moon Lilith",
    "Juno", "Ceres", "Pallas", "Vesta",
    "Vertex",
    "Lot of Fortune", "Lot of Spirit",
]


def _house_of(astro: Dict[str, Any], sid_longitude: float) -> Optional[int]:
    """Compute which house a sidereal longitude falls into using stored cusps."""
    cusps = astro.get("houses") or astro.get("house_cusps")
    if not cusps:
        return None
    try:
        return get_house_for_planet(sid_longitude, cusps)
    except Exception:
        return None


def build_house_inventory(chart: Dict[str, Any], house_number: int) -> Dict[str, Any]:
    """Public API. Aggregates EVERY computed object in the target house.

    Sources (in priority order):
      1. astro.planets  (Sun..Pluto + Chiron + Juno + Earth, when stored)
      2. astro.nodes    (North / South)
      3. astro.angles   (ASC / DSC / MC / IC / Vertex / Anti-Vertex)
      4. natal_object_engine for extended objects not in storage
         (Black Moon Lilith, Lot of Fortune/Spirit, asteroids).

    Build marker: mel-4th-house-inventory-fix-v1
    """
    astro = (chart or {}).get("astrology") or {}
    houses_blob = astro.get("houses") or astro.get("house_cusps") or {}

    # ── House sign + cusp degree ──────────────────────────────────────
    house_sign = None
    cusp_deg = None
    if isinstance(houses_blob, dict):
        # New shape: {"cusps":[...], "formatted_cusps":[{house,sign,...}], ...}
        cusps_list = houses_blob.get("cusps")
        formatted = houses_blob.get("formatted_cusps") or []
        cusp_signs = houses_blob.get("cusp_signs")
        if isinstance(cusps_list, list) and 1 <= house_number <= len(cusps_list):
            try:
                cusp_deg = float(cusps_list[house_number - 1])
            except Exception:
                pass
        if isinstance(cusp_signs, list) and 1 <= house_number <= len(cusp_signs):
            sign_val = cusp_signs[house_number - 1]
            if isinstance(sign_val, str):
                house_sign = sign_val
        if house_sign is None and isinstance(formatted, list):
            for f in formatted:
                if isinstance(f, dict) and f.get("house") == house_number:
                    house_sign = f.get("sign")
                    break
    elif isinstance(houses_blob, list) and 1 <= house_number <= len(houses_blob):
        # Legacy shape: flat list of cusp degrees
        try:
            cusp_deg = float(houses_blob[house_number - 1])
            from calculations.astrology import longitude_to_sign_degree
            sd = longitude_to_sign_degree(
                cusp_deg, tropical_longitude=cusp_deg + 31.2836,
            )
            house_sign = sd.get("sign")
        except Exception:
            pass

    objects_in_house: List[Dict[str, Any]] = []
    classes_included: List[str] = []
    classes_unsupported: List[str] = []
    seen_names: set = set()

    def _add_obj(name: str, placement: Dict[str, Any], source: str) -> None:
        if not name or name in seen_names:
            return
        body_house = placement.get("house")
        if body_house is None and placement.get("longitude") is not None:
            body_house = _house_of(astro, placement["longitude"])
        if body_house != house_number:
            return
        objects_in_house.append({
            "name":      name,
            "category":  _CATEGORY.get(name, "other"),
            "sign":      placement.get("sign"),
            "degree":    placement.get("degree") or placement.get("sign_degree"),
            "house":     house_number,
            "source":    source,
            "formatted": placement.get("formatted"),
            "longitude": placement.get("longitude"),
        })
        seen_names.add(name)
        if name not in classes_included:
            classes_included.append(name)

    # 1) Stored planets (mel-4th-house-inventory-fix-v1)
    stored_planets = astro.get("planets") or {}
    if isinstance(stored_planets, dict):
        for pname, pdata in stored_planets.items():
            if isinstance(pdata, dict):
                _add_obj(pname, pdata, "stored_planets")

    # 2) Stored nodes
    nodes = astro.get("nodes") or {}
    if isinstance(nodes, dict):
        # north/south sub-dicts
        n = nodes.get("north")
        if isinstance(n, dict):
            _add_obj("North Node", n, "stored_nodes")
        s = nodes.get("south")
        if isinstance(s, dict):
            _add_obj("South Node", s, "stored_nodes")

    # 3) Stored angles — assign to natural houses (IC=4, DSC=7, MC=10, ASC=1)
    # Vertex / Anti-Vertex use the longitude → house lookup like planets.
    angles = astro.get("angles") or {}
    if isinstance(angles, dict):
        _angle_natural_house = {
            "asc": 1, "ascendant": 1,
            "dc": 7, "dsc": 7, "descendant": 7,
            "mc": 10, "midheaven": 10,
            "ic": 4, "imum_coeli": 4, "imum coeli": 4,
        }
        for ang_key, ang_data in angles.items():
            if not isinstance(ang_data, dict):
                continue
            canon = {
                "asc": "Ascendant",
                "ascendant": "Ascendant",
                "dc": "Descendant",
                "dsc": "Descendant",
                "descendant": "Descendant",
                "mc": "Midheaven",
                "midheaven": "Midheaven",
                "ic": "IC",
                "imum_coeli": "IC",
                "imum coeli": "IC",
                "vertex": "Vertex",
                "anti_vertex": "Anti-Vertex",
                "anti-vertex": "Anti-Vertex",
                "antivertex": "Anti-Vertex",
            }.get(ang_key.lower())
            if not canon:
                continue
            # Inject natural house for the cusp-axis angles
            ang_copy = dict(ang_data)
            if canon in ("Ascendant", "Descendant", "Midheaven", "IC"):
                ang_copy["house"] = _angle_natural_house.get(ang_key.lower())
            _add_obj(canon, ang_copy, "stored_angles")

    # 4) Extended objects via natal_object_engine (Lilith / Lots / asteroids)
    # Skip names we already added from storage.
    for body_name in _INVENTORY_TARGETS:
        if body_name in seen_names:
            continue
        env = compute_natal_object(chart, body_name)
        if not env.get("success"):
            reason = env.get("reason") or ""
            if reason in ("object_not_wired", "ephemeris_file_missing"):
                classes_unsupported.append(body_name)
            continue
        placement = env.get("placement") or {}
        _add_obj(env.get("object") or body_name, placement, env.get("source") or "natal_object_engine")

    hierarchy = _build_house_hierarchy(objects_in_house, house_sign)

    return {
        "success": True,
        "build_marker": BUILD_MARKER,
        "house_number": house_number,
        "house_sign": house_sign,
        "house_cusp_degree": cusp_deg,
        "objects_in_house": objects_in_house,
        "inventory_complete_for_computed_objects": True,
        "object_classes_included": classes_included,
        "object_classes_unsupported": classes_unsupported,
        **hierarchy,
    }


# ---------------------------------------------------------------------------
# Hierarchy
# ---------------------------------------------------------------------------
# Category weights — higher = more dominance in interpretation.
_CAT_WEIGHT = {
    "core":             10,
    "structural":        9,    # Saturn
    "transpersonal":     8,
    "outer_personal":    7,    # Jupiter
    "karmic":            7,    # Nodes
    "healing_point":     6,    # Chiron
    "shadow_point":      6,    # Lilith
    "fate_point":        5,    # Vertex
    "lot":               5,
    "asteroid":          4,
}


def _build_house_hierarchy(
    objects: List[Dict[str, Any]],
    house_sign: Optional[str],
) -> Dict[str, Any]:
    """Derive dominant_body / tension_body / field_type from the inventory.

    Heuristics (kept deliberately simple):
      • dominant_body = highest-weighted body
      • tension_body  = the body that 'edits' or 'restricts' the dominant
                        (Saturn if present alongside Sun/Moon/Venus; Pluto
                        if present alongside Sun/Moon; Chiron if present
                        alongside Mercury/Sun in a communication-ish house)
      • field_type    = concentrated (3+ same-sign), fragmented (>2 distinct
                        signs), reinforcing (1–2 high-weight bodies same
                        category), contradictory (Saturn vs Sun, Pluto vs
                        Venus, etc.)
      • dominant_sign = mode of signs in house (often == house_sign in
                        equal-house systems but not always)
      • pressure_pattern = short string describing the field
    """
    if not objects:
        return {
            "dominant_body": None,
            "tension_body":  None,
            "house_field_type": "empty",
            "dominant_sign": house_sign,
            "pressure_pattern": "empty house — read by ruler instead",
            "supporting_objects": [],
        }

    scored = sorted(
        objects,
        key=lambda o: _CAT_WEIGHT.get(o.get("category", "other"), 1),
        reverse=True,
    )
    dominant = scored[0]
    dominant_name = dominant["name"]

    # Tension body — find a known editor/disruptor for the dominant
    tension = None
    names = {o["name"] for o in objects}
    if dominant_name in ("Sun", "Moon", "Venus") and "Saturn" in names:
        tension = "Saturn"
    elif dominant_name in ("Sun", "Moon") and "Pluto" in names:
        tension = "Pluto"
    elif dominant_name in ("Sun", "Mercury") and "Chiron" in names:
        tension = "Chiron"
    elif "Saturn" in names and dominant_name != "Saturn":
        tension = "Saturn"

    # Same-sign count
    sign_counts: Dict[str, int] = {}
    for o in objects:
        s = o.get("sign")
        if s:
            sign_counts[s] = sign_counts.get(s, 0) + 1
    dom_sign = max(sign_counts.items(), key=lambda kv: kv[1])[0] if sign_counts else house_sign

    if any(c >= 3 for c in sign_counts.values()):
        field = "concentrated"
    elif len(sign_counts) >= 3 and len(objects) >= 3:
        field = "fragmented"
    elif tension and dominant_name != tension:
        field = "contradictory"
    elif len(objects) <= 2:
        field = "reinforcing" if len(set(_CATEGORY.get(o["name"], "other") for o in objects)) <= 1 else "reinforcing"
    else:
        field = "reinforcing"

    pressure_bits: List[str] = []
    if field == "concentrated":
        pressure_bits.append(f"strong {dom_sign} stacking")
    if tension:
        pressure_bits.append(f"{dominant_name} edited by {tension}")
    if "North Node" in names or "South Node" in names:
        pressure_bits.append("karmic emphasis from nodes")
    if "Chiron" in names:
        pressure_bits.append("Chiron makes the field emotionally loaded")
    if not pressure_bits:
        pressure_bits.append(f"{dominant_name} sets the keynote")

    return {
        "dominant_body": dominant_name,
        "tension_body":  tension,
        "house_field_type": field,
        "dominant_sign": dom_sign,
        "pressure_pattern": "; ".join(pressure_bits),
        "supporting_objects": [o["name"] for o in scored[1:]],
    }


# ---------------------------------------------------------------------------
# Proof block for chat
# ---------------------------------------------------------------------------
def build_house_inventory_proof_block(envelope: Dict[str, Any]) -> str:
    """Build a deterministic system-prompt block from a house-inventory
    envelope. The LLM MUST synthesize from this block, NOT from generic
    house meanings, and MUST include every listed object.
    """
    if not envelope or not envelope.get("success"):
        return (
            "━━━━ HOUSE INVENTORY — ENGINE STATUS ━━━━\n"
            "available: NO\n"
            "INSTRUCTION: state that the house inventory engine couldn't "
            "complete. DO NOT improvise textbook house meaning.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    h = envelope["house_number"]
    objs = envelope["objects_in_house"]
    house_sign = envelope.get("house_sign") or "(cusp sign unknown)"
    obj_lines = []
    for o in objs:
        formatted = o.get("formatted") or f"{o.get('degree')}° {o.get('sign')}"
        obj_lines.append(
            f"  • {o['name']:22s} {formatted:18s}  "
            f"category={o['category']:14s} source={o.get('source','?')}"
        )
    obj_block = "\n".join(obj_lines) if obj_lines else "  (no objects in this house)"

    return (
        f"━━━━ HOUSE INVENTORY — ENGINE OUTPUT: HOUSE {h} ━━━━\n"
        f"house_cusp_sign: {house_sign}\n"
        f"objects_in_house ({len(objs)} total — THIS IS THE COMPLETE LIST):\n"
        f"{obj_block}\n"
        f"\n"
        f"HIERARCHY:\n"
        f"  dominant_body:     {envelope.get('dominant_body')}\n"
        f"  tension_body:      {envelope.get('tension_body')}\n"
        f"  house_field_type:  {envelope.get('house_field_type')}\n"
        f"  dominant_sign:     {envelope.get('dominant_sign')}\n"
        f"  pressure_pattern:  {envelope.get('pressure_pattern')}\n"
        f"  supporting:        {envelope.get('supporting_objects')}\n"
        f"\n"
        f"INSTRUCTION TO YOU (master-astrologer synthesis):\n"
        f"1. You MUST name every object listed above. No omissions. If you\n"
        f"   skip Chiron or any other listed body, your response is wrong.\n"
        f"2. Open with ONE LINE describing the FIELD of this house —\n"
        f"   the pressure_pattern is your starting point. Do NOT open\n"
        f"   with 'The Nth house is the domain of…'.\n"
        f"3. Then weave the bodies together as ONE psychological field,\n"
        f"   not a list. Use the hierarchy: dominant_body sets the\n"
        f"   keynote; tension_body edits or complicates it; supporting\n"
        f"   bodies amplify or modulate.\n"
        f"4. Voice: direct, observant, behavioural. Speak to where this\n"
        f"   shows up in the user's life, not what each placement\n"
        f"   'represents' in textbook astrology.\n"
        f"5. Banned phrases: 'this placement suggests', 'often indicates',\n"
        f"   'may feel', 'typically', 'in astrology', 'this house is the\n"
        f"   domain of', 'does this resonate'. No closing question.\n"
        f"6. Length: 120–220 words.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
