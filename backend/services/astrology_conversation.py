"""
Astrology Chat — Conversational Memory + Entity Tracking
========================================================

Build marker: astrology-chat-memory-v1

This module fixes the P0 failure where the astrology chat behaved as
stateless single-turn retrieval — answering Jupiter, then drifting to
North Node, then to Sun, because referents like "that", "it", and
"which house does that sit in" were never resolved to the entity the
user was actually talking about.

What it does:
    1. Indexes every entity in the user's natal chart (planets, nodes,
       houses, signs, angles) keyed by every name + alias we expect
       the user to use.
    2. Scans the recent conversation history (user + assistant turns)
       for chart-entity mentions and returns them in MRU order.
    3. Resolves referents — when the current user message has no new
       chart entity but contains "that / it / this / which house /
       what house / what sign / what aspect", returns the most recent
       previously-mentioned entity (Active Entity).
    4. Formats two blocks for the LLM system prompt:
         a. ACTIVE ENTITY block — the resolved focus, grounded with its
            sign, house, degree, and a couple of key aspects.
         b. CONVERSATION HISTORY block — the last N turns formatted as
            "User: …" / "Mirror: …" so the LLM stops asking "what were
            we talking about?".
       And a third helper block:
         c. CHART SIGNALS block — supporting context with the rest of
            the chart, in a strict order so the LLM doesn't randomly
            grab unrelated data.

The module is intentionally regex-driven and deterministic.  No LLM
calls here — this is plumbing that runs before every chat turn.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 1.  Aliases — every name a user can use for a planet, house, sign, angle.
# ---------------------------------------------------------------------------

# Lowercase canonical aliases → canonical entity key.  Order matters in a
# few places (longer aliases first to avoid "moon" matching "moon's node").
PLANET_ALIASES: Dict[str, str] = {
    "sun": "Sun",
    "moon": "Moon",
    "mercury": "Mercury",
    "venus": "Venus",
    "mars": "Mars",
    "jupiter": "Jupiter",
    "saturn": "Saturn",
    "uranus": "Uranus",
    "neptune": "Neptune",
    "pluto": "Pluto",
    "chiron": "Chiron",
    # Nodes — keep both poles addressable
    "north node": "North Node",
    "south node": "South Node",
    "rahu": "North Node",
    "ketu": "South Node",
    "true node": "North Node",
    "lunar nodes": "Nodes",
    "nodes": "Nodes",
}

ANGLE_ALIASES: Dict[str, str] = {
    "ascendant": "Ascendant",
    "asc": "Ascendant",
    "rising": "Ascendant",
    "rising sign": "Ascendant",
    "descendant": "Descendant",
    "dsc": "Descendant",
    "midheaven": "Midheaven",
    "mc": "Midheaven",
    "ic": "Imum Coeli",
    "imum coeli": "Imum Coeli",
}

SIGN_NAMES: List[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_ALIASES: Dict[str, str] = {s.lower(): s for s in SIGN_NAMES}

# Ordinal & spelled-out house numbers, plus shorthand like "1h", "4th".
HOUSE_ALIASES: Dict[str, int] = {
    "1st house": 1, "first house": 1, "house 1": 1, "1h": 1, "house one": 1,
    "2nd house": 2, "second house": 2, "house 2": 2, "2h": 2, "house two": 2,
    "3rd house": 3, "third house": 3, "house 3": 3, "3h": 3, "house three": 3,
    "4th house": 4, "fourth house": 4, "house 4": 4, "4h": 4, "house four": 4,
    "5th house": 5, "fifth house": 5, "house 5": 5, "5h": 5, "house five": 5,
    "6th house": 6, "sixth house": 6, "house 6": 6, "6h": 6, "house six": 6,
    "7th house": 7, "seventh house": 7, "house 7": 7, "7h": 7, "house seven": 7,
    "8th house": 8, "eighth house": 8, "house 8": 8, "8h": 8, "house eight": 8,
    "9th house": 9, "ninth house": 9, "house 9": 9, "9h": 9, "house nine": 9,
    "10th house": 10, "tenth house": 10, "house 10": 10, "10h": 10, "house ten": 10,
    "11th house": 11, "eleventh house": 11, "house 11": 11, "11h": 11, "house eleven": 11,
    "12th house": 12, "twelfth house": 12, "house 12": 12, "12h": 12, "house twelve": 12,
}

# Words that signal a referent without naming the entity directly.
REFERENT_PATTERNS = [
    r"\bthat\b", r"\bthis\b", r"\bit\b", r"\bthey\b",
    r"\bwhich house\b", r"\bwhat house\b", r"\bthe house\b",
    r"\bwhich sign\b", r"\bwhat sign\b", r"\bthe sign\b",
    r"\bwhich aspect\b", r"\bwhat aspect\b",
    r"\bwhere does .* sit\b", r"\bwhere does that sit\b",
    r"\bdoes it sit\b", r"\bdoes that sit\b",
    r"\bhow does it\b", r"\bhow does that\b",
]
REFERENT_RE = re.compile("|".join(REFERENT_PATTERNS), re.IGNORECASE)


# ---------------------------------------------------------------------------
# 2.  Chart entity index
# ---------------------------------------------------------------------------

def build_chart_entity_index(chart: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Build an index of every chart entity keyed by canonical name.

    Each entry contains everything we need to ground a focused answer:
        { "Jupiter": {
            "kind": "planet",
            "name": "Jupiter",
            "sign": "Cancer",
            "house": 4,
            "degree": 12.45,
            "retrograde": False,
            "formatted": "Jupiter 12°27' Cancer",
        }, ... }

    Returns {} if chart is missing / malformed.  This function is defensive:
    it never raises — the chat must still answer even if chart data is partial.
    """
    if not chart:
        return {}

    astro = chart.get("astrology", {}) or {}
    planets = astro.get("planets", {}) or {}
    houses = astro.get("houses", {}) or {}
    nodes = astro.get("nodes", {}) or {}

    index: Dict[str, Dict[str, Any]] = {}

    # --- Planets ---------------------------------------------------------
    for canonical in [
        "Sun", "Moon", "Mercury", "Venus", "Mars",
        "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron",
    ]:
        p = planets.get(canonical) or {}
        if not p:
            continue
        index[canonical] = {
            "kind": "planet",
            "name": canonical,
            "sign": p.get("sign"),
            "house": p.get("house"),
            "degree": p.get("degree"),
            "retrograde": p.get("retrograde", False),
            "formatted": p.get("formatted") or _fmt_placement(canonical, p),
        }

    # --- Nodes -----------------------------------------------------------
    nn = nodes.get("north") or nodes.get("north_node") or {}
    sn = nodes.get("south") or nodes.get("south_node") or {}
    # Legacy fallback: lunar_nodes block
    if not nn:
        lunar = astro.get("lunar_nodes", {}) or {}
        nn = lunar.get("north_node") or lunar.get("north") or {}
        sn = lunar.get("south_node") or lunar.get("south") or {}
    # Final fallback: planets dict
    if not nn:
        nn = planets.get("North Node", {}) or planets.get("True Node", {}) or {}

    if nn and nn.get("sign"):
        index["North Node"] = {
            "kind": "node",
            "name": "North Node",
            "sign": nn.get("sign"),
            "house": nn.get("house"),
            "degree": nn.get("degree"),
            "formatted": nn.get("formatted") or _fmt_placement("North Node", nn),
        }
    if sn and sn.get("sign"):
        index["South Node"] = {
            "kind": "node",
            "name": "South Node",
            "sign": sn.get("sign"),
            "house": sn.get("house"),
            "degree": sn.get("degree"),
            "formatted": sn.get("formatted") or _fmt_placement("South Node", sn),
        }

    # --- Angles (Ascendant / Descendant / MC / IC) -----------------------
    cusps = houses.get("formatted_cusps") or []
    if cusps:
        try:
            asc = cusps[0] if len(cusps) > 0 else None
            ic = cusps[3] if len(cusps) > 3 else None
            dsc = cusps[6] if len(cusps) > 6 else None
            mc = cusps[9] if len(cusps) > 9 else None
            if asc:
                index["Ascendant"] = {
                    "kind": "angle", "name": "Ascendant",
                    "sign": asc.get("sign"), "degree": asc.get("degree"),
                    "house": 1, "formatted": asc.get("formatted"),
                }
            if dsc:
                index["Descendant"] = {
                    "kind": "angle", "name": "Descendant",
                    "sign": dsc.get("sign"), "degree": dsc.get("degree"),
                    "house": 7, "formatted": dsc.get("formatted"),
                }
            if mc:
                index["Midheaven"] = {
                    "kind": "angle", "name": "Midheaven",
                    "sign": mc.get("sign"), "degree": mc.get("degree"),
                    "house": 10, "formatted": mc.get("formatted"),
                }
            if ic:
                index["Imum Coeli"] = {
                    "kind": "angle", "name": "Imum Coeli",
                    "sign": ic.get("sign"), "degree": ic.get("degree"),
                    "house": 4, "formatted": ic.get("formatted"),
                }
        except Exception:
            pass  # angles are nice-to-have, never block the chat

    # --- Houses (cusp sign per house, plus tenants) ----------------------
    for h_num in range(1, 13):
        cusp = None
        if len(cusps) >= h_num:
            cusp = cusps[h_num - 1]
        sign_on_cusp = (cusp or {}).get("sign")
        # Find which planets sit in this house
        tenants = [
            name for name, e in index.items()
            if e.get("kind") in ("planet", "node") and e.get("house") == h_num
        ]
        index[f"House {h_num}"] = {
            "kind": "house",
            "name": f"House {h_num}",
            "number": h_num,
            "sign_on_cusp": sign_on_cusp,
            "tenants": tenants,
        }

    return index


def _fmt_placement(name: str, p: Dict[str, Any]) -> str:
    """Best-effort formatter when 'formatted' string isn't pre-baked."""
    sign = p.get("sign") or "Unknown"
    house = p.get("house")
    deg = p.get("degree")
    parts = [name]
    if deg is not None:
        try:
            parts.append(f"{float(deg):.1f}°")
        except Exception:
            pass
    parts.append(sign)
    if house:
        parts.append(f"(House {house})")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# 3.  Entity extraction from a single text string
# ---------------------------------------------------------------------------

def _build_alias_pattern(aliases: Dict[str, str]) -> re.Pattern:
    """Build a single regex that matches any alias, longest first."""
    keys = sorted(aliases.keys(), key=len, reverse=True)
    escaped = [re.escape(k) for k in keys]
    return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)


_PLANET_RE = _build_alias_pattern(PLANET_ALIASES)
_ANGLE_RE = _build_alias_pattern(ANGLE_ALIASES)
_SIGN_RE = _build_alias_pattern(SIGN_ALIASES)
_HOUSE_RE = _build_alias_pattern(HOUSE_ALIASES)


def extract_entities_from_text(text: str) -> List[str]:
    """
    Find every chart-entity reference in a single piece of text.

    Returns canonical entity keys in **left-to-right order of first mention**.
    Deduplicated.  Empty list if no entities found.
    """
    if not text:
        return []
    text_l = text.lower()
    found: List[Tuple[int, str]] = []  # (position, canonical_key)

    for match in _PLANET_RE.finditer(text_l):
        found.append((match.start(), PLANET_ALIASES[match.group(1).lower()]))
    for match in _ANGLE_RE.finditer(text_l):
        found.append((match.start(), ANGLE_ALIASES[match.group(1).lower()]))
    for match in _SIGN_RE.finditer(text_l):
        # Signs alone aren't usually the conversational subject, but they
        # disambiguate referents.  Tag them with a "Sign:" prefix.
        found.append((match.start(), f"Sign:{SIGN_ALIASES[match.group(1).lower()]}"))
    for match in _HOUSE_RE.finditer(text_l):
        found.append((match.start(), f"House {HOUSE_ALIASES[match.group(1).lower()]}"))

    found.sort(key=lambda x: x[0])
    seen, result = set(), []
    for _, key in found:
        if key not in seen:
            seen.add(key)
            result.append(key)
    return result


# ---------------------------------------------------------------------------
# 4.  Active entity resolution across conversation history
# ---------------------------------------------------------------------------

def resolve_active_entity(
    user_message: str,
    history: List[Dict[str, str]],
    chart_index: Dict[str, Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Resolve the conversational focus.

    Strategy:
      1. If the current user message names a chart entity directly → use it.
      2. Else, if the message contains a referent ("that", "it", "which house"…),
         scan history in reverse and return the most recently-mentioned entity.
      3. Else, fall back to the most recent entity (if any) so the LLM stays
         on thread instead of drifting.

    Returns: (entity_dict_or_None, source_label)
      where source_label is one of:
        "current"      → entity named in current message
        "referent"     → referent resolved from history
        "carryover"    → no referent, no entity named; carried over from prior turn
        "none"         → no entity in scope (LLM should ask, not guess)
    """
    # 1. Did the current message name an entity directly?
    current_entities = extract_entities_from_text(user_message)
    # Filter to entities that actually exist in the chart (skip Sign:X — those
    # are disambiguators, not subjects).  House N and angles are valid subjects.
    current_real = [e for e in current_entities if not e.startswith("Sign:")]

    has_referent = bool(REFERENT_RE.search(user_message or ""))

    # Split current entities by kind so we can apply the right precedence.
    current_planets_nodes_angles = [
        e for e in current_real
        if chart_index.get(e, {}).get("kind") in ("planet", "node", "angle")
    ]
    current_houses = [
        e for e in current_real
        if chart_index.get(e, {}).get("kind") == "house"
    ]

    # If the user explicitly names a PLANET / NODE / ANGLE in the current
    # message, that always wins — even over a referent.  ("I was asking
    # about Jupiter" must snap focus back to Jupiter.)
    if current_planets_nodes_angles:
        first = current_planets_nodes_angles[0]
        return chart_index[first], "current"

    # If the user names ONLY a house (and no planet/node/angle) AND uses a
    # referent — e.g. "Oh so that sits in house 4 for me?" — they are
    # CONFIRMING the placement, not changing the subject.  Resolve the
    # referent from history first; if that fails, fall through to the house.
    if has_referent and current_houses:
        for turn in reversed(history or []):
            content = turn.get("content", "") if isinstance(turn, dict) else ""
            ents = extract_entities_from_text(content)
            ents_real = [
                e for e in ents
                if not e.startswith("Sign:")
                and chart_index.get(e, {}).get("kind") in ("planet", "node", "angle")
            ]
            if ents_real:
                return chart_index[ents_real[0]], "referent"
        # No prior planet/node/angle to anchor to → fall back to the named house.
        return chart_index[current_houses[0]], "current"

    # If the user names a house without a referent, treat the house itself
    # as the active subject.
    if current_houses:
        return chart_index[current_houses[0]], "current"

    # 2 & 3. Scan history in reverse for the most recent entity.
    for turn in reversed(history or []):
        content = turn.get("content", "") if isinstance(turn, dict) else ""
        ents = extract_entities_from_text(content)
        ents_real = [e for e in ents if not e.startswith("Sign:") and e in chart_index]
        if not ents_real:
            continue
        for kind_pref in ("planet", "node", "angle"):
            for e in ents_real:
                if chart_index.get(e, {}).get("kind") == kind_pref:
                    return chart_index[e], ("referent" if has_referent else "carryover")
        # Otherwise return the first
        return chart_index[ents_real[0]], ("referent" if has_referent else "carryover")

    return None, "none"


# ---------------------------------------------------------------------------
# 5.  Prompt block formatters
# ---------------------------------------------------------------------------

def format_history_block(history: List[Dict[str, str]], max_turns: int = 6) -> str:
    """
    Format the last `max_turns` user+assistant pairs as a clean block.
    Truncates very long messages so we don't blow the context window.
    """
    if not history:
        return ""
    # Take the last max_turns*2 messages (user+assistant)
    recent = history[-(max_turns * 2):]
    lines = ["--- CONVERSATION HISTORY (most recent last) ---"]
    for msg in recent:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "user")
        content = (msg.get("content") or "").strip()
        if len(content) > 800:
            content = content[:800] + "…"
        label = "User" if role == "user" else "Mirror"
        lines.append(f"{label}: {content}")
    return "\n".join(lines)


def format_active_entity_block(
    entity: Optional[Dict[str, Any]],
    source: str,
    chart_index: Dict[str, Dict[str, Any]],
) -> str:
    """
    Build the ACTIVE ENTITY block that tells the LLM what 'that / it / this'
    refers to.  This block is the single most important fix.
    """
    if not entity:
        return (
            "--- ACTIVE ENTITY ---\n"
            "No specific chart entity is in active focus.\n"
            "If the user references 'that' / 'it' / 'which house' without a named entity,\n"
            "ASK which placement they mean.  DO NOT guess and DO NOT drift to an unrelated\n"
            "planet, node, or house."
        )

    kind = entity.get("kind", "")
    name = entity.get("name", "")
    sign = entity.get("sign")
    house = entity.get("house")
    deg = entity.get("degree")

    placement_line = name
    extras: List[str] = []
    if sign:
        extras.append(sign)
    if house:
        extras.append(f"House {house}")
    if deg is not None:
        try:
            extras.append(f"{float(deg):.1f}°")
        except Exception:
            pass
    if extras:
        placement_line += " — " + ", ".join(extras)

    source_explainer = {
        "current": "named in the current user message",
        "referent": "RESOLVED from prior turns (user used 'that' / 'it' / 'which house')",
        "carryover": "carried over from the most recent turn (user did not name a new entity)",
        "none": "none",
    }.get(source, "")

    block = [
        "--- ACTIVE ENTITY (conversational focus) ---",
        f"Active focus: {placement_line}",
        f"How resolved: {source_explainer}",
    ]

    # For houses, list tenants explicitly
    if kind == "house":
        tenants = entity.get("tenants") or []
        sign_on_cusp = entity.get("sign_on_cusp")
        if sign_on_cusp:
            block.append(f"Cusp sign: {sign_on_cusp}")
        if tenants:
            block.append(f"Planets/nodes in this house: {', '.join(tenants)}")

    # For planets / nodes / angles, add 1-2 sibling facts (which house, which sign).
    elif kind in ("planet", "node", "angle"):
        # If house number known, surface the house's cusp sign + co-tenants for richer answers
        if house:
            house_entity = chart_index.get(f"House {house}")
            if house_entity:
                co = [t for t in (house_entity.get("tenants") or []) if t != name]
                if co:
                    block.append(f"Co-tenants in House {house}: {', '.join(co)}")
                cusp = house_entity.get("sign_on_cusp")
                if cusp and cusp != sign:
                    block.append(f"House {house} cusp sign: {cusp}")

    block.append(
        "RULE: Answer the user's question about THIS entity specifically.  Do NOT pivot\n"
        "to a different planet, node, sign, or house unless the user explicitly asks."
    )
    return "\n".join(block)


def format_chart_signals_block(chart_index: Dict[str, Dict[str, Any]]) -> str:
    """
    Compact, deterministic dump of the rest of the chart so the LLM has a
    grounded source of truth and never has to invent placements.

    Order matters: luminaries → personal planets → social → outer → nodes → angles.
    """
    if not chart_index:
        return ""

    order = [
        "Sun", "Moon", "Mercury", "Venus", "Mars",
        "Jupiter", "Saturn",
        "Uranus", "Neptune", "Pluto", "Chiron",
        "North Node", "South Node",
        "Ascendant", "Descendant", "Midheaven", "Imum Coeli",
    ]
    lines = ["--- CHART SIGNALS (grounded source of truth) ---"]
    for key in order:
        e = chart_index.get(key)
        if not e:
            continue
        sign = e.get("sign") or "Unknown"
        house = e.get("house")
        deg = e.get("degree")
        bits: List[str] = [key, sign]
        if house:
            bits.append(f"House {house}")
        if deg is not None:
            try:
                bits.append(f"{float(deg):.1f}°")
            except Exception:
                pass
        lines.append("  - " + " · ".join(bits))

    # Add house-level summary (cusp signs)
    lines.append("Houses (cusp signs):")
    for h in range(1, 13):
        he = chart_index.get(f"House {h}")
        if not he:
            continue
        cusp = he.get("sign_on_cusp") or "?"
        tenants = he.get("tenants") or []
        tenant_str = f" [tenants: {', '.join(tenants)}]" if tenants else ""
        lines.append(f"  - House {h}: cusp {cusp}{tenant_str}")

    lines.append(
        "RULE: Only reference placements that appear above.  If a placement isn't\n"
        "listed, say 'I don't have that data' rather than guessing."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 6.  Debug payload
# ---------------------------------------------------------------------------

def build_debug_payload(
    active_entity: Optional[Dict[str, Any]],
    source: str,
    history_entities: List[str],
    chart_index_size: int,
) -> Dict[str, Any]:
    """Small JSON payload returned alongside the chat reply for inspection."""
    return {
        "marker": "astrology-chat-memory-v1",
        "active_entity": (
            {
                "name": active_entity.get("name"),
                "kind": active_entity.get("kind"),
                "sign": active_entity.get("sign"),
                "house": active_entity.get("house"),
            } if active_entity else None
        ),
        "active_entity_source": source,
        "recent_history_entities": history_entities[:12],
        "chart_index_size": chart_index_size,
    }
